import frappe
from frappe import _


@frappe.whitelist()
def get_project_list(filters=None, order_by="modified desc", limit=20, start=0):
    """Get paginated project list for CRM frontend."""
    return frappe.get_list(
        "LCS Project",
        filters=filters,
        fields=[
            "name",
            "project_name",
            "project_number",
            "project_type",
            "project_abbr",
            "country",
            "phase",
            "status",
            "salesperson",
            "organization",
            "probability",
            "estimated_value",
            "modified",
        ],
        order_by=order_by,
        start=int(start),
        page_length=int(limit),
    )


@frappe.whitelist()
def get_project_summary():
    """Dashboard summary data."""
    LCSProject = frappe.qb.DocType("LCS Project")
    from pypika import functions as fn

    phases = (
        frappe.qb.from_(LCSProject)
        .select(LCSProject.phase, fn.Count("*").as_("count"), fn.Sum(LCSProject.estimated_value).as_("value"))
        .groupby(LCSProject.phase)
        .run(as_dict=True)
    )
    types = (
        frappe.qb.from_(LCSProject)
        .select(LCSProject.project_type, fn.Count("*").as_("count"))
        .groupby(LCSProject.project_type)
        .run(as_dict=True)
    )
    countries = (
        frappe.qb.from_(LCSProject)
        .select(LCSProject.country, fn.Count("*").as_("count"), fn.Sum(LCSProject.estimated_value).as_("value"))
        .groupby(LCSProject.country)
        .run(as_dict=True)
    )
    return {"phases": phases, "types": types, "countries": countries}


@frappe.whitelist()
def get_project_map_data():
    """Get project data with coordinates for map display."""
    projects = frappe.get_all(
        "LCS Project",
        filters={"status": ["!=", "Cancelled"]},
        fields=[
            "name",
            "project_name",
            "project_number",
            "project_type",
            "country",
            "phase",
            "status",
            "salesperson",
            "estimated_value",
            "probability",
        ],
    )
    # Enrich with country coordinates
    for p in projects:
        if p.country:
            coords = frappe.db.get_value(
                "Country", p.country, ["latitude", "longitude"]
            )
            if coords:
                p["latitude"], p["longitude"] = coords
            else:
                p["latitude"], p["longitude"] = None, None
    return [p for p in projects if p.get("latitude")]


@frappe.whitelist()
def get_opportunity_matrix(project):
    """Get opportunity matrix entries for a project."""
    return frappe.get_all(
        "LCS Opportunity Matrix",
        filters={"project": project},
        fields="*",
    )


@frappe.whitelist()
def get_project_offers(project):
    """Get all offers for a project, ordered by version descending."""
    return frappe.get_all(
        "LCS Offer",
        filters={"project": project},
        fields=[
            "name",
            "offer_title",
            "version",
            "status",
            "offer_date",
            "valid_until",
            "value",
            "currency",
            "probability",
            "won_lost_reason",
            "modified",
        ],
        order_by="version desc",
    )


@frappe.whitelist()
def get_offer_templates(project_type=None):
    """Get active offer templates, optionally filtered by project type."""
    filters = {"is_active": 1}
    if project_type:
        # Accept templates matching this type or marked for All
        filters_sql = ["is_active = 1", "(project_type = %s OR project_type = 'All' OR project_type IS NULL OR project_type = '')"]
        return frappe.db.sql(
            f"SELECT name, template_name, project_type, default_title, default_validity_days, "
            f"default_probability, default_notes, usage_count "
            f"FROM `tabLCS Offer Template` WHERE {' AND '.join(filters_sql)} "
            f"ORDER BY usage_count DESC, template_name ASC",
            (project_type,),
            as_dict=True,
        )
    return frappe.get_all(
        "LCS Offer Template",
        filters=filters,
        fields=["name", "template_name", "project_type", "default_title",
                "default_validity_days", "default_probability", "default_notes", "usage_count"],
        order_by="usage_count desc, template_name asc",
    )


@frappe.whitelist()
def create_offer_from_template(template_name, project_name):
    """Create a new LCS Offer from a template, with placeholder substitution."""
    template = frappe.get_doc("LCS Offer Template", template_name)
    project = frappe.get_doc("LCS Project", project_name)

    # Placeholder substitution in title
    title = template.default_title or f"Offer for {project.project_name}"
    title = (title
             .replace("{project_number}", project.project_number or "")
             .replace("{project_name}", project.project_name or ""))

    offer = frappe.new_doc("LCS Offer")
    offer.project = project_name
    offer.offer_title = title
    offer.status = "Draft"
    offer.probability = template.default_probability
    offer.notes = template.default_notes
    offer.offer_date = frappe.utils.nowdate()
    if template.default_validity_days:
        offer.valid_until = frappe.utils.add_days(
            frappe.utils.nowdate(), template.default_validity_days
        )
    # Prefill value from project's richtpreis or budget
    offer.value = project.richtpreis or project.budget_customer or 0
    offer.insert(ignore_permissions=True)

    # Track template usage
    frappe.db.set_value("LCS Offer Template", template_name, {
        "usage_count": (template.usage_count or 0) + 1,
        "last_used": frappe.utils.now_datetime(),
    })
    frappe.db.commit()
    return offer.name


@frappe.whitelist()
def get_source_analytics():
    """Aggregate project counts and pipeline value by source channel."""
    LCSProject = frappe.qb.DocType("LCS Project")
    from pypika import functions as fn
    return (
        frappe.qb.from_(LCSProject)
        .select(
            LCSProject.source,
            fn.Count("*").as_("count"),
            fn.Sum(LCSProject.estimated_value).as_("value"),
            fn.Avg(LCSProject.probability).as_("avg_probability"),
        )
        .where(LCSProject.status != "Cancelled")
        .groupby(LCSProject.source)
        .run(as_dict=True)
    )


@frappe.whitelist()
def get_forecast(period="month", months_ahead=12):
    """
    Return weighted revenue forecast aggregated by close period.

    Logic:
    - Uses expected_close_date if set, else offer valid_until, else modified+30d
    - Weighted = estimated_value × probability / 100
    - Active projects only (excludes Completed/Lost/Cancelled)
    """
    import datetime
    months_ahead = int(months_ahead)

    projects = frappe.get_all(
        "LCS Project",
        filters={
            "phase": ["not in", ["Completed", "Lost"]],
            "status": ["!=", "Cancelled"],
        },
        fields=[
            "name", "project_name", "project_number", "project_type",
            "phase", "estimated_value", "probability",
            "expected_close_date", "modified",
        ],
    )

    today = datetime.date.today()
    buckets = {}

    for p in projects:
        close = p.expected_close_date
        if not close:
            # Fallback: latest offer valid_until
            offer_dates = frappe.db.sql(
                "SELECT MAX(valid_until) FROM `tabLCS Offer` WHERE project = %s",
                (p.name,),
            )[0][0]
            close = offer_dates or (today + datetime.timedelta(days=30))
        if isinstance(close, str):
            close = datetime.datetime.strptime(close, "%Y-%m-%d").date()

        if period == "quarter":
            q = (close.month - 1) // 3 + 1
            key = f"{close.year}-Q{q}"
        elif period == "year":
            key = f"{close.year}"
        else:
            key = close.strftime("%Y-%m")

        bucket = buckets.setdefault(key, {"period": key, "projects": [], "total_value": 0, "weighted_value": 0})
        weighted = (p.estimated_value or 0) * (p.probability or 0) / 100
        bucket["total_value"] += p.estimated_value or 0
        bucket["weighted_value"] += weighted
        bucket["projects"].append({
            "name": p.name,
            "project_name": p.project_name,
            "project_number": p.project_number,
            "project_type": p.project_type,
            "phase": p.phase,
            "value": p.estimated_value,
            "probability": p.probability,
            "weighted": weighted,
        })

    return sorted(buckets.values(), key=lambda b: b["period"])


@frappe.whitelist()
def create_project_from_deal(deal_name):
    """Create an LCS Project from a CRM Deal."""
    deal = frappe.get_doc("CRM Deal", deal_name)
    project = frappe.new_doc("LCS Project")
    project.project_name = deal.deal_name or deal.lead_name or deal.name
    project.organization = deal.organization
    project.deal = deal_name
    project.salesperson = deal.deal_owner
    project.estimated_value = deal.annual_revenue
    project.phase = "Inquiry"
    project.status = "Open"
    project.insert(ignore_permissions=True)
    frappe.db.commit()
    return project.name
