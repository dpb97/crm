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
    # Enrich with country centroid coordinates (Frappe's Country DocType
    # has no lat/long fields — resolved from a static table instead).
    # Return ALL projects: the dashboard needs full totals, the map
    # skips entries without coordinates itself.
    from lcs_integrations.projects.country_coords import get_coords

    for p in projects:
        coords = get_coords(p.country)
        p["latitude"], p["longitude"] = coords if coords else (None, None)
    return projects


# Phase → cable-crane lifecycle state (PpGeoMap marker colour). Acquisition
# until Order; Execution = building; Completed = operating.
_GEO_STATE = {
    "Qualified": "akquise", "Budget": "akquise", "Richtpreis": "akquise",
    "Offer": "akquise", "Negotiation": "akquise", "Won": "akquise",
    "Execution": "bau", "Completed": "betrieb", "Lost": "akquise",
}
# Project type → PpGeoMap marker shape (only the shapes it knows).
_GEO_TYP = {"SB": "SB", "WI": "WI", "SK": "SK"}


def _typ_from_number(number):
    """Plant type from the project number prefix (LCS-SB-…/-SK-…/-WI-…) when the
    project_type field is empty — the number always carries it."""
    parts = str(number or "").split("-")
    return parts[1] if len(parts) > 1 and parts[1] in _GEO_TYP else None


def _typ_from_name(name):
    """Last-resort plant type from keywords in the project name."""
    n = str(name or "").lower()
    if "seilkran" in n or "kranbahn" in n or "kran" in n:
        return "SK"
    if "winde" in n or "vorschub" in n:
        return "WI"
    if "seilbahn" in n:  # incl. Material-/Lastenseilbahn
        return "SB"
    return None


def _approx_routes(items):
    """Turn single-location projects (no surveyed masts) into schematic 2-point
    routes so every construction site shows as a valley↔mountain pair, not a lone
    dot. Valley = country centroid (ringed apart when several share a country),
    mountain = a small fixed offset. Flagged `approx` so the map draws them
    dashed and without a (meaningless) span length."""
    import math
    from collections import defaultdict

    by = defaultdict(list)
    for it in items:
        by[tuple(it["_c"])].append(it)

    out = []
    for (lat, lng), grp in by.items():
        n = len(grp)
        for i, it in enumerate(grp):
            if n > 1:
                r = 0.22 + 0.03 * n
                ang = 2 * math.pi * i / n
                tlat = round(lat + r * math.sin(ang), 6)
                tlng = round(lng + r * math.cos(ang) / max(math.cos(math.radians(lat)), 0.1), 6)
            else:
                tlat, tlng = round(lat, 6), round(lng, 6)
            it.pop("_c", None)
            it["tal"] = [tlat, tlng]
            it["berg"] = [round(tlat + 0.05, 6), round(tlng + 0.035, 6)]
            it["approx"] = True
            out.append(it)
    return out


def _coord(value):
    """A mast coordinate, or None when it is not really set. Frappe Float
    fields default to 0.0, so an unfilled mast reads as 0°/0° — the Null Island
    point in the Gulf of Guinea, never a cable-crane location. Without this the
    whole map collapses onto that one spot and no project ever falls back to
    its country pin."""
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    return f if f else None


@frappe.whitelist()
def get_project_geo():
    """Cable-route map data for PpGeoMap. Projects that carry both mast
    coordinates become `masten` (valley↔mountain route); the rest fall back to
    a country-centroid `pin`. Marker shape follows project_type, colour follows
    the phase-derived lifecycle state; the span label is computed client-side."""
    projects = frappe.get_all(
        "LCS Project",
        filters={"status": ["!=", "Cancelled"]},
        fields=[
            "name", "project_name", "project_number", "project_type", "phase",
            "organization", "salesperson", "estimated_value", "country",
            "valley_mast_latitude", "valley_mast_longitude",
            "mountain_mast_latitude", "mountain_mast_longitude",
        ],
    )
    from lcs_integrations.projects.country_coords import get_coords

    masten, approx = [], []
    for p in projects:
        tal_lat, tal_lng = _coord(p.valley_mast_latitude), _coord(p.valley_mast_longitude)
        berg_lat, berg_lng = _coord(p.mountain_mast_latitude), _coord(p.mountain_mast_longitude)
        base = {
            "nr": p.project_number or p.name,
            "n": p.project_name or p.name,
            "firma": p.organization or "",
            "phase": p.phase or "",
            "state": _GEO_STATE.get(p.phase, "akquise"),
            "wert": p.estimated_value or 0,
            "wer": p.salesperson or "",
        }
        typ = _GEO_TYP.get(p.project_type) or _typ_from_number(p.project_number) or _typ_from_name(p.project_name)
        if typ:
            base["typ"] = typ

        if None not in (tal_lat, tal_lng, berg_lat, berg_lng):
            masten.append({**base, "tal": [tal_lat, tal_lng], "berg": [berg_lat, berg_lng]})
        else:
            coords = get_coords(p.country)
            if coords:
                approx.append({**base, "_c": [coords[0], coords[1]]})

    # Every remaining project becomes a schematic 2-point route (min. 2 points).
    masten += _approx_routes(approx)
    return {"masten": masten, "pins": []}


def _spread(pins):
    """Pull pins that share a country centroid apart onto a small ring. Without
    it every project of a country stacks on the exact same point and only the
    topmost one can be clicked."""
    import math
    from collections import defaultdict

    by_pos = defaultdict(list)
    for pin in pins:
        by_pos[(pin["ll"][0], pin["ll"][1])].append(pin)

    for (lat, lng), group in by_pos.items():
        if len(group) < 2:
            continue
        radius = 0.25 + 0.03 * len(group)   # degrees; keeps the group inside its country
        for i, pin in enumerate(group):
            angle = 2 * math.pi * i / len(group)
            pin["ll"] = [
                round(lat + radius * math.sin(angle), 6),
                round(lng + radius * math.cos(angle) / max(math.cos(math.radians(lat)), 0.1), 6),
            ]
    return pins


@frappe.whitelist()
def get_opportunity_matrix(project):
    """Get opportunity matrix entries for a project."""
    return frappe.get_all(
        "LCS Opportunity Matrix",
        filters={"project": project},
        fields="*",
    )


@frappe.whitelist()
def save_opportunity_matrix(project, technical_fit=0, commercial_fit=0,
                            relationship_strength=0, competition_level=0,
                            strategic_importance=0):
    """Upsert the opportunity-matrix scores for a project (one row per project).
    Derived fields (total_score, weighted_probability, classification,
    activity_level) and the project's probability are recomputed by the
    doctype's validate()."""
    if not frappe.has_permission("LCS Project", ptype="write", doc=project):
        frappe.throw(_("Not permitted"), frappe.PermissionError)

    scores = {
        "technical_fit": int(technical_fit or 0),
        "commercial_fit": int(commercial_fit or 0),
        "relationship_strength": int(relationship_strength or 0),
        "competition_level": int(competition_level or 0),
        "strategic_importance": int(strategic_importance or 0),
    }
    name = frappe.db.get_value("LCS Opportunity Matrix", {"project": project}, "name")
    if name:
        doc = frappe.get_doc("LCS Opportunity Matrix", name)
    else:
        doc = frappe.new_doc("LCS Opportunity Matrix")
        doc.project = project
        doc.organization = frappe.db.get_value("LCS Project", project, "organization")
    doc.update(scores)
    doc.save(ignore_permissions=True)
    frappe.db.commit()
    return {
        "name": doc.name,
        "total_score": doc.total_score,
        "weighted_probability": doc.weighted_probability,
        "classification": doc.classification,
        "activity_level": doc.activity_level,
    }


@frappe.whitelist()
def get_execution_summary(project: str) -> dict:
    """Pull Tasks + Time Logs + Costing from the linked ERPNext Project
    so the LCS Project detail page can show execution data without the
    user navigating away.
    """
    if not frappe.has_permission("LCS Project", ptype="read", doc=project):
        frappe.throw("Not permitted", frappe.PermissionError)

    lcs = frappe.db.get_value(
        "LCS Project", project, ["erpnext_project"], as_dict=True
    ) or {}
    erp_name = lcs.get("erpnext_project")
    if not erp_name or not frappe.db.exists("Project", erp_name):
        return {"linked": False, "erpnext_project": None, "tasks": [], "time_logs": [], "totals": {}}

    # Schema-tolerant: only request fields that actually exist on the
    # local Project DocType (ERPNext drops/renames between versions).
    project_meta = frappe.get_meta("Project")
    available = {f.fieldname for f in project_meta.fields}
    wanted = [
        "name", "status", "expected_start_date", "expected_end_date",
        "actual_start_date", "actual_end_date", "percent_complete",
        "estimated_costing", "total_billed_amount", "total_consumed_material_cost",
        "project_manager",
    ]
    safe_fields = ["name"] + [f for f in wanted if f != "name" and f in available]
    erp = frappe.db.get_value("Project", erp_name, safe_fields, as_dict=True) or {}

    tasks = []
    if frappe.db.exists("DocType", "Task"):
        tasks = frappe.get_all(
            "Task",
            filters={"project": erp_name},
            fields=[
                "name", "subject", "status", "priority", "exp_start_date",
                "exp_end_date", "progress", "_assign",
            ],
            order_by="exp_start_date asc, creation asc",
            limit_page_length=200,
        )

    time_logs = []
    if frappe.db.exists("DocType", "Timesheet Detail"):
        time_logs = frappe.db.sql(
            """SELECT td.name, td.activity_type, td.from_time, td.to_time,
                      td.hours, td.billing_hours, td.billing_amount, td.costing_amount,
                      td.parent AS timesheet, ts.employee, ts.employee_name
               FROM `tabTimesheet Detail` td
               JOIN `tabTimesheet` ts ON ts.name = td.parent
               WHERE td.project = %s
               ORDER BY td.from_time DESC
               LIMIT 100""",
            (erp_name,),
            as_dict=True,
        )

    totals = {
        "estimated": erp.get("estimated_costing") or 0,
        "billed": erp.get("total_billed_amount") or 0,
        "costing": erp.get("total_consumed_material_cost") or 0,
        "percent_complete": erp.get("percent_complete") or 0,
    }

    return {
        "linked": True,
        "erpnext_project": erp_name,
        "erpnext_status": erp.get("status"),
        "expected_start_date": str(erp.get("expected_start_date") or ""),
        "expected_end_date": str(erp.get("expected_end_date") or ""),
        "tasks": tasks,
        "time_logs": time_logs,
        "totals": totals,
    }


@frappe.whitelist()
def find_project_for(doctype: str, name: str):
    """
    Resolve the LCS Project linked to a CRM Deal or CRM Lead so the
    upstream detail pages can render a "Go to Project" chip.

    Uses the existing deal/lead link graph:
      - For CRM Deal: LCS Project where deal = <name>
      - For CRM Lead: LCS Project where deal.lead = <name> (via any deal)
    """
    if not frappe.has_permission(doctype, ptype="read", doc=name):
        return None

    if doctype == "CRM Deal":
        return frappe.db.get_value(
            "LCS Project",
            {"deal": name},
            ["name", "project_name", "project_number", "project_type", "phase", "status"],
            as_dict=True,
        )

    if doctype == "CRM Lead":
        deals = frappe.get_all("CRM Deal", filters={"lead": name}, pluck="name")
        if not deals:
            return None
        return frappe.db.get_value(
            "LCS Project",
            {"deal": ["in", deals]},
            ["name", "project_name", "project_number", "project_type", "phase", "status"],
            as_dict=True,
        )

    return None


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
            "value_eur",
            "exchange_rate_to_eur",
            "rate_frozen_at",
            "probability",
            "lost_reason",
            "won_notes",
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
            "phase", "estimated_value", "probability", "salesperson",
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
            "salesperson": p.salesperson,
            "value": p.estimated_value,
            "probability": p.probability,
            "weighted": weighted,
        })

    return sorted(buckets.values(), key=lambda b: b["period"])


@frappe.whitelist()
def create_project_from_deal(deal_name):
    """Create an LCS Project from a CRM Deal.

    Permission: user must be allowed to read the source deal AND create
    LCS Project records. The underlying `.insert(ignore_permissions=True)`
    below is for bypassing the validate-hook's idempotency check, not for
    bypassing auth.
    """
    if not frappe.has_permission("CRM Deal", ptype="read", doc=deal_name):
        frappe.throw("Not permitted to read this deal", frappe.PermissionError)
    if not frappe.has_permission("LCS Project", ptype="create"):
        frappe.throw("Not permitted to create projects", frappe.PermissionError)

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


@frappe.whitelist()
def create_project_from_lead(lead_name):
    """Create an LCS Project directly from a CRM Lead (Interessent → Vertriebs-
    projekt). Carries the funnel position forward: a qualified lead starts the
    project at the Qualified phase. Idempotent per lead (skips if already made)."""
    if not frappe.has_permission("CRM Lead", ptype="read", doc=lead_name):
        frappe.throw("Not permitted to read this lead", frappe.PermissionError)
    if not frappe.has_permission("LCS Project", ptype="create"):
        frappe.throw("Not permitted to create projects", frappe.PermissionError)

    existing = frappe.db.get_value("LCS Project", {"lead": lead_name}, "name")
    if existing:
        return existing

    lead = frappe.get_doc("CRM Lead", lead_name)
    project = frappe.new_doc("LCS Project")
    project.project_name = lead.organization or lead.lead_name or lead.name
    project.organization = lead.organization
    project.salesperson = lead.lead_owner
    project.estimated_value = lead.annual_revenue
    if frappe.get_meta("LCS Project").has_field("lead"):
        project.lead = lead_name
    # Qualified leads enter the project at Qualified; earlier leads at the start.
    project.phase = "Qualified" if (lead.status or "").lower().startswith("qualif") else "Qualified"
    project.status = "Open"
    project.insert(ignore_permissions=True)
    frappe.db.commit()
    return project.name


@frappe.whitelist()
def get_project_primary_contact(project):
    """Primary contact of a project (perm-safe: reads the child table via
    get_all so Sales Users don't hit 'LCS Project Contact' permission errors)."""
    rows = frappe.get_all(
        "LCS Project Contact",
        filters={"parent": project, "parenttype": "LCS Project"},
        fields=["contact", "is_primary"],
        order_by="is_primary desc, idx asc",
        limit=1,
    )
    if not rows:
        return None
    return frappe.db.get_value(
        "Contact", rows[0].contact, ["full_name", "email_id", "mobile_no"], as_dict=True
    )


@frappe.whitelist()
def get_contact_projects(contact):
    """LCS Projects this contact is linked to (via the project contacts table)."""
    cf = next(
        (f.fieldname for f in frappe.get_meta("LCS Project Contact").fields
         if f.fieldtype == "Link" and f.options == "Contact"),
        "contact",
    )
    parents = frappe.get_all("LCS Project Contact", filters={cf: contact}, pluck="parent")
    if not parents:
        return []
    return frappe.get_all(
        "LCS Project",
        filters={"name": ["in", list(set(parents))]},
        fields=["name", "project_name", "project_number", "phase", "status", "country", "estimated_value"],
        order_by="modified desc",
    )


@frappe.whitelist()
def get_my_project_feed(limit=12):
    """Dashboard top feed: recent mails + notes across the current user's
    LCS Projects, plus the user's notifications."""
    user = frappe.session.user
    limit = int(limit or 12)

    # "My projects" — salesperson, sales manager, or owner.
    mine = set()
    for field in ("salesperson", "sales_manager", "owner"):
        mine.update(frappe.get_all("LCS Project", filters={field: user}, pluck="name"))
    project_names = list(mine)

    activity = []
    if project_names:
        # docname -> speaking project name, so the feed shows "Bridge Erection
        # Crane" instead of "LCS-PROJ-2026-0033".
        labels = {
            n: (frappe.db.get_value("LCS Project", n, "project_name") or n)
            for n in project_names
        }
        for c in frappe.get_all(
            "Communication",
            filters={
                "reference_doctype": "LCS Project",
                "reference_name": ["in", project_names],
                "communication_type": "Communication",
            },
            fields=["name", "subject", "sender", "recipients", "content",
                    "sent_or_received", "communication_medium", "reference_name", "creation"],
            order_by="creation desc",
            limit=limit,
        ):
            activity.append({
                "kind": "mail",
                "name": c.name,
                "title": c.subject or _("(no subject)"),
                "meta": c.sender,
                "recipients": c.recipients,
                "content": c.content,
                "medium": c.communication_medium,
                "direction": c.sent_or_received,
                "project": c.reference_name,
                "project_label": labels.get(c.reference_name, c.reference_name),
                "time": str(c.creation),
            })
        # Notes are intentionally excluded from the dashboard feed — mails only.
        activity.sort(key=lambda x: x["time"], reverse=True)
        activity = activity[:limit]

    notifications = frappe.get_all(
        "Notification Log",
        filters={"for_user": user},
        fields=["subject", "type", "document_type", "document_name", "read", "creation"],
        order_by="creation desc",
        limit=10,
    )
    for note in notifications:
        note["subject"] = frappe.utils.strip_html(note.get("subject") or "")[:160]
        note["creation"] = str(note["creation"])

    return {
        "activity": activity,
        "notifications": notifications,
        "project_count": len(project_names),
    }


@frappe.whitelist()
def get_market_assignment():
    """Market-split assignment dashboard.

    Combines the static LCS Sales Territory / Segment ownership (the
    "Marktaufteilung") with the total leads, deals and projects assigned
    across each sales manager's territories. The counts are totals (all
    statuses), not an open/closed split. Powers the SPA dashboard.
    """
    if not frappe.has_permission("LCS Sales Territory", "read"):
        frappe.throw(_("Not permitted to view the market assignment."), frappe.PermissionError)

    territories = frappe.get_all(
        "LCS Sales Territory",
        filters={"is_active": 1},
        fields=[
            "name", "region", "sub_region", "priority",
            "sales_manager_code", "sales_manager",
            "deputy_sales_manager_code", "deputy_sales_manager", "agent_name",
        ],
        order_by="region asc, territory_name asc",
        limit=0,
    )

    # child rows in one query each → {territory: [..]}
    countries_by_terr: dict[str, list[str]] = {}
    for r in frappe.get_all(
        "LCS Sales Territory Country", fields=["parent", "country"], limit=0
    ):
        countries_by_terr.setdefault(r.parent, []).append(r.country)

    segcount_by_terr: dict[str, int] = {}
    for r in frappe.get_all(
        "LCS Sales Territory Segment", filters={"is_active": 1},
        fields=["parent"], limit=0,
    ):
        segcount_by_terr[r.parent] = segcount_by_terr.get(r.parent, 0) + 1

    # Opportunity counts grouped by country, one pass per doctype.
    # `doctype` is an internal constant (no injection surface).
    def _by_country(doctype: str) -> dict[str, int]:
        rows = frappe.db.sql(
            """
            SELECT country, COUNT(name) AS n
            FROM   `tab{0}`
            WHERE  country IS NOT NULL AND country != ''
            GROUP BY country
            """.format(doctype.replace("`", "")),
            as_dict=True,
        )
        return {r["country"]: r["n"] for r in rows}

    leads_c = _by_country("CRM Lead")
    deals_c = _by_country("CRM Deal")
    proj_c = _by_country("LCS Project")

    # Representative map coordinate per territory = centroid of the country
    # centroids it owns. Reuses the same static country-centroid table the
    # pipeline map already relies on (Frappe's Country DocType has no lat/long);
    # this adds only a geographic reference for the region, no business data.
    from lcs_integrations.projects.country_coords import get_coords

    def _territory_centroid(country_list: list[str]):
        pts = [c for c in (get_coords(x) for x in country_list) if c]
        if not pts:
            return None, None
        return (
            round(sum(p[0] for p in pts) / len(pts), 4),
            round(sum(p[1] for p in pts) / len(pts), 4),
        )

    # Display name for only the handful of users referenced as (deputy) managers.
    needed_users = {t.sales_manager for t in territories if t.sales_manager}
    needed_users |= {t.deputy_sales_manager for t in territories if t.deputy_sales_manager}
    user_names = {
        u.name: (u.full_name or u.name)
        for u in frappe.get_all(
            "User", filters={"name": ["in", list(needed_users)]},
            fields=["name", "full_name"], limit=0,
        )
    } if needed_users else {}

    PRIO = ("Go", "Watch", "Maintain", "Exit")
    managers: dict[str, dict] = {}
    rows = []
    total_countries = 0
    prio_totals = {p: 0 for p in PRIO}
    claimed_countries: set[str] = set()

    for t in territories:
        # Each country belongs to exactly one territory; if data lists it under
        # several, attribute it once (first territory wins, as auto-assign does).
        countries = [c for c in countries_by_terr.get(t.name, []) if c not in claimed_countries]
        claimed_countries.update(countries)
        total_countries += len(countries)
        leads = sum(leads_c.get(c, 0) for c in countries)
        deals = sum(deals_c.get(c, 0) for c in countries)
        projects = sum(proj_c.get(c, 0) for c in countries)

        # Coordinate from the territory's full country membership (not just the
        # deduplicated attribution list) so the marker stays geographically true.
        lat, lon = _territory_centroid(countries_by_terr.get(t.name, []))

        rows.append({
            "territory": t.name,
            "region": t.region,
            "sub_region": t.sub_region,
            "priority": t.priority,
            "code": t.sales_manager_code,
            "user": t.sales_manager,
            "user_name": user_names.get(t.sales_manager),
            "deputy_code": t.deputy_sales_manager_code,
            "deputy_user": t.deputy_sales_manager,
            "agent": t.agent_name,
            "latitude": lat,
            "longitude": lon,
            "countries": countries,
            "country_count": len(countries),
            "segment_count": segcount_by_terr.get(t.name, 0),
            "leads": leads,
            "deals": deals,
            "projects": projects,
        })

        code = t.sales_manager_code or "—"
        m = managers.setdefault(code, {
            "code": code,
            "user": t.sales_manager,
            "user_name": user_names.get(t.sales_manager) or code,
            "territories": 0,
            "countries": 0,
            "leads": 0,
            "deals": 0,
            "projects": 0,
            "priority": {p: 0 for p in PRIO},
        })
        m["territories"] += 1
        m["countries"] += len(countries)
        m["leads"] += leads
        m["deals"] += deals
        m["projects"] += projects
        if t.priority in m["priority"]:
            m["priority"][t.priority] += 1
        if t.priority in prio_totals:
            prio_totals[t.priority] += 1
        if not m["user"] and t.sales_manager:
            m["user"] = t.sales_manager
            m["user_name"] = user_names.get(t.sales_manager) or code

    manager_list = sorted(managers.values(), key=lambda x: -x["territories"])

    # Segment responsibility matrix.
    segments = frappe.get_all(
        "LCS Segment Responsibility",
        fields=["segment", "lead_code", "deputy_code"],
        order_by="segment asc", limit=0,
    )

    return {
        "summary": {
            "territories": len(territories),
            "countries": total_countries,
            "managers": len([m for m in manager_list if m["code"] != "—"]),
            "segments": frappe.db.count("LCS Segment", {"is_active": 1}),
            "priority": prio_totals,
        },
        "managers": manager_list,
        "territories": rows,
        "segments": segments,
    }


@frappe.whitelist()
def get_network_graph(limit_orgs=14, per_org=8):
    """Relationship graph: companies + their people (who works with whom),
    plus career-history edges (where a person worked before)."""
    limit_orgs = int(limit_orgs)
    per_org = int(per_org)
    orgs = {
        o.name: (o.organization_name or o.name)
        for o in frappe.get_all("CRM Organization", fields=["name", "organization_name"], limit_page_length=0)
    }
    contacts = frappe.get_all(
        "Contact",
        fields=["name", "full_name", "company_name", "previous_companies", "designation"],
        limit_page_length=0,
    )
    by_org = {}
    for c in contacts:
        if c.company_name and c.company_name in orgs:
            by_org.setdefault(c.company_name, []).append(c)
    keep = sorted(by_org.keys(), key=lambda k: -len(by_org[k]))[:limit_orgs]
    keep_set = set(keep)

    nodes, edges, seen = [], [], set()
    clink = {}  # company<->company links (people moving between them)
    for org in keep:
        nodes.append({"id": "org::" + org, "label": orgs[org], "type": "company", "size": len(by_org[org])})
    # company links from ALL contacts (career history), not just the shown ones
    for c in contacts:
        cur = c.company_name
        if cur not in keep_set:
            continue
        for prev in (c.previous_companies or "").split(","):
            prev = prev.strip()
            if prev and prev in keep_set and prev != cur:
                key = tuple(sorted([cur, prev]))
                clink[key] = clink.get(key, 0) + 1
    for org in keep:
        for c in by_org[org][:per_org]:
            pid = "person::" + c.name
            if pid in seen:
                continue
            seen.add(pid)
            nodes.append({"id": pid, "label": c.full_name or c.name, "type": "person",
                          "role": c.designation or "", "org": org, "contact": c.name})
            edges.append({"source": pid, "target": "org::" + org, "kind": "works_at"})
            for prev in (c.previous_companies or "").split(","):
                prev = prev.strip()
                if prev and prev in keep_set and prev != org:
                    edges.append({"source": pid, "target": "org::" + prev, "kind": "worked_at"})
    company_edges = [
        {"source": "org::" + a, "target": "org::" + b, "weight": w}
        for (a, b), w in clink.items()
    ]
    return {"nodes": nodes, "edges": edges, "company_edges": company_edges}


@frappe.whitelist()
def get_funnel_phases():
    """Editable funnel phase definitions for the FunnelFlowBar.

    Managers maintain them via Settings -> Funnel Phases (LCS Funnel
    Phase doctype); cached until a phase is edited.
    """
    cached = frappe.cache().get_value("lcs_funnel_phases")
    if cached:
        return cached
    rows = frappe.get_all(
        "LCS Funnel Phase",
        fields=["stage", "entity_group", "funnel_index", "description", "criteria", "fields_to_fill"],
        order_by="funnel_index asc",
        limit_page_length=0,
    )
    out = {}
    for r in rows:
        out[r.stage] = {
            "group": r.entity_group,
            "index": r.funnel_index,
            "desc": r.description or "",
            "criteria": [c.strip() for c in (r.criteria or "").splitlines() if c.strip()],
            "fields": [f.strip() for f in (r.fields_to_fill or "").splitlines() if f.strip()],
        }
    frappe.cache().set_value("lcs_funnel_phases", out)
    return out


@frappe.whitelist()
def get_phase_field_defs(doctype: str, fieldnames):
    """Field definitions for the phase panel's inline filling.

    Silently skips fieldnames the doctype doesn't have, so one phase
    config can serve CRM Lead, CRM Deal and LCS Project pages alike.
    """
    import json as _json

    if isinstance(fieldnames, str):
        fieldnames = _json.loads(fieldnames)
    if doctype not in ("CRM Lead", "CRM Deal", "LCS Project"):
        frappe.throw(_("Unsupported doctype"), frappe.PermissionError)
    if not frappe.has_permission(doctype, "read"):
        frappe.throw(_("Not permitted"), frappe.PermissionError)

    skip_types = {"Section Break", "Column Break", "Tab Break", "HTML", "Table", "Table MultiSelect"}
    meta = frappe.get_meta(doctype)
    out = []
    for fn in fieldnames:
        df = meta.get_field(fn)
        if not df or df.fieldtype in skip_types:
            continue
        out.append({
            "fieldname": fn,
            "label": df.label,
            "fieldtype": df.fieldtype,
            "options": df.options or "",
        })
    return out


@frappe.whitelist()
def reassign_territory(territory: str, sales_manager_code: str | None = None, sales_manager: str | None = None) -> dict:
    """Remap a territory to a different sales manager from the market-assignment
    UI. Sets the code AND the user link together so the view stays consistent,
    and — via the LCS Sales Territory controller's on_update — clears the
    country->territory cache so new leads/deals/projects auto-assign to the new
    owner. Managers + System Managers only; existing records are NOT reassigned.
    """
    frappe.only_for(["System Manager", "Sales Manager"])
    if not frappe.db.exists("LCS Sales Territory", territory):
        frappe.throw(_("Territory not found."))
    doc = frappe.get_doc("LCS Sales Territory", territory)
    if sales_manager_code is not None:
        doc.sales_manager_code = sales_manager_code or None
    if sales_manager is not None:
        doc.sales_manager = sales_manager or None
    doc.save(ignore_permissions=True)
    frappe.db.commit()
    return {
        "ok": True,
        "territory": territory,
        "sales_manager_code": doc.sales_manager_code,
        "sales_manager": doc.sales_manager,
    }


@frappe.whitelist()
def reassign_country(country: str, target_territory: str) -> dict:
    """Move a single country to another Sales Territory (per-country market
    reassignment, finer than reassign_territory). Removes the country from every
    other active territory and adds it to the target; idempotent. The controller
    on_update clears the country->territory cache so new records route to the new
    owner. Managers + System Managers only; existing records are NOT reassigned.
    """
    frappe.only_for(["System Manager", "Sales Manager"])
    if not frappe.db.exists("LCS Sales Territory", target_territory):
        frappe.throw(_("Territory not found."))

    for terr in frappe.get_all("LCS Sales Territory", filters={"is_active": 1}, pluck="name"):
        if terr == target_territory:
            continue
        doc = frappe.get_doc("LCS Sales Territory", terr)
        keep = [c for c in doc.countries if c.country != country]
        if len(keep) != len(doc.countries):
            doc.set("countries", keep)
            doc.save(ignore_permissions=True)

    target = frappe.get_doc("LCS Sales Territory", target_territory)
    if not any(c.country == country for c in target.countries):
        target.append("countries", {"country": country})
        target.save(ignore_permissions=True)
    frappe.db.commit()
    return {"ok": True, "country": country, "territory": target_territory,
            "sales_manager_code": target.sales_manager_code}


@frappe.whitelist()
def get_organization_emails(organization: str) -> list[dict]:
    """Communications linked to a CRM Organization — the mailbox-synced customer
    mail. The upstream Organization page has no email view, so this backs the
    LCS "Emails" tab. Returns newest first with a plain-text preview."""
    if not frappe.has_permission("CRM Organization", doc=organization):
        frappe.throw(_("Not permitted"), frappe.PermissionError)
    rows = frappe.get_all(
        "Communication",
        filters={"reference_doctype": "CRM Organization", "reference_name": organization},
        fields=["name", "sender", "subject", "sent_or_received", "communication_date", "content"],
        order_by="communication_date desc",
        limit=200,
    )
    import html as _html
    for r in rows:
        text = _html.unescape(frappe.utils.strip_html(r.get("content") or ""))
        r["preview"] = " ".join(text.split())[:160]
        r.pop("content", None)
    return rows


@frappe.whitelist()
def get_communication_email(name: str) -> dict:
    """Full body of one Communication for the org Emails-tab reader modal."""
    c = frappe.db.get_value(
        "Communication",
        name,
        ["subject", "sender", "recipients", "sent_or_received", "communication_date",
         "content", "reference_doctype", "reference_name", "message_id", "user"],
        as_dict=True,
    )
    if not c:
        frappe.throw(_("Email not found"))
    if c.reference_doctype == "CRM Organization" and c.reference_name:
        if not frappe.has_permission("CRM Organization", doc=c.reference_name):
            frappe.throw(_("Not permitted"), frappe.PermissionError)
    # Fetch attachments on demand: inline images into the body, list files.
    from lcs_integrations.outlook_sync.attachments import enrich_email
    c = enrich_email(c)
    return c


@frappe.whitelist()
def get_contact_emails(contact) -> list[dict]:
    """Email Communications linked to a contact — via the timeline link table or
    a direct reference — newest first, with a plain-text preview. Backs the
    contact Emails tab (same shape as get_organization_emails)."""
    if not frappe.has_permission("Contact", doc=contact):
        frappe.throw(_("Not permitted"), frappe.PermissionError)

    rows = frappe.db.sql(
        """
        SELECT DISTINCT comm FROM (
            SELECT cl.parent AS comm
            FROM `tabCommunication Link` cl
            JOIN `tabCommunication` c ON c.name = cl.parent
            WHERE cl.link_doctype = 'Contact' AND cl.link_name = %(c)s
              AND c.communication_medium = 'Email'
            UNION
            SELECT c.name AS comm
            FROM `tabCommunication` c
            WHERE c.reference_doctype = 'Contact' AND c.reference_name = %(c)s
              AND c.communication_medium = 'Email'
        ) t
        """,
        {"c": contact},
        as_dict=True,
    )
    ids = [r.comm for r in rows]
    if not ids:
        return []

    emails = frappe.get_all(
        "Communication",
        filters={"name": ["in", ids]},
        fields=["name", "sender", "recipients", "subject", "sent_or_received",
                "communication_date", "content"],
        order_by="communication_date desc",
        limit=200,
    )
    import html as _html
    for e in emails:
        text = _html.unescape(frappe.utils.strip_html(e.get("content") or ""))
        e["preview"] = " ".join(text.split())[:160]
        e.pop("content", None)
    return emails


@frappe.whitelist()
def get_contact_email_counts(contacts) -> dict:
    """Count e-mail Communications directly linked to each contact — via the
    timeline link table (Communication Link) or a direct reference. Batched for
    the contact list views. Returns {contact_name: count}. UNION dedupes a
    communication that is both referenced and timeline-linked."""
    import json

    if isinstance(contacts, str):
        contacts = json.loads(contacts)
    contacts = [c for c in (contacts or []) if c]
    if not contacts:
        return {}

    rows = frappe.db.sql(
        """
        SELECT contact, COUNT(*) AS n FROM (
            SELECT cl.link_name AS contact, c.name AS comm
            FROM `tabCommunication Link` cl
            JOIN `tabCommunication` c ON c.name = cl.parent
            WHERE cl.link_doctype = 'Contact' AND cl.link_name IN %(contacts)s
              AND c.communication_medium = 'Email'
            UNION
            SELECT c.reference_name AS contact, c.name AS comm
            FROM `tabCommunication` c
            WHERE c.reference_doctype = 'Contact' AND c.reference_name IN %(contacts)s
              AND c.communication_medium = 'Email'
        ) t GROUP BY contact
        """,
        {"contacts": tuple(contacts)},
        as_dict=True,
    )
    return {r.contact: r.n for r in rows}


# --------------------------------------------------------------------------- #
#  Sales Meeting — committee view (agenda + the three funnel stages)          #
# --------------------------------------------------------------------------- #

_SM_ACTIVE_PROJECT = ["Qualified", "Budget", "Richtpreis", "Offer", "Negotiation"]
_SM_ACTIVE_LEAD = ["New", "Contacted", "Nurture", "Qualified"]


def _sm_meeting_date(meeting_date=None):
    """Resolve the meeting date: explicit arg, else the most recent agenda date,
    else today."""
    if meeting_date:
        return frappe.utils.getdate(meeting_date)
    last = frappe.get_all(
        "LCS Sales Meeting Agenda", fields=["meeting_date"],
        order_by="meeting_date desc", limit=1,
    )
    return frappe.utils.getdate(last[0].meeting_date) if last else frappe.utils.today()


@frappe.whitelist()
def get_sales_meeting_agenda(meeting_date=None):
    """Committee view for the weekly sales meeting: the agenda for one meeting
    (decide-directly-at-the-point flow) plus the three funnel stages
    (opportunities / leads / sales projects) as compact cards, the last
    decisions and the meeting frame for the inspector default content."""
    mdate = _sm_meeting_date(meeting_date)

    items = frappe.get_all(
        "LCS Sales Meeting Agenda",
        filters={"meeting_date": mdate},
        fields=["name", "sort_index", "status", "topic", "reference_object",
                "reference_doctype", "reference_name", "responsible",
                "decision", "decided_on"],
        order_by="sort_index asc, creation asc",
        limit_page_length=0,
    )
    agenda, archived_count = [], 0
    for i, a in enumerate(items):
        if a.status == "Archived":
            archived_count += 1
            continue
        agenda.append({
            "name": a.name, "nr": len(agenda) + 1, "topic": a.topic,
            "object": a.reference_object or "", "responsible": a.responsible or "",
            "status": a.status, "decision": a.decision or "",
            "ref_doctype": a.reference_doctype or "", "ref_name": a.reference_name or "",
        })

    # Last decisions (across the whole doctype, for the inspector timeline).
    decided = frappe.get_all(
        "LCS Sales Meeting Agenda",
        filters={"status": ["in", ["Decided", "Archived"]], "decided_on": ["is", "set"]},
        fields=["topic", "reference_object", "decision", "decided_on"],
        order_by="decided_on desc", limit=6,
    )
    decisions = [{
        "topic": d.topic, "object": d.reference_object or "",
        "decision": d.decision or "", "on": str(d.decided_on) if d.decided_on else "",
    } for d in decided]

    # Stage 1 — opportunities (CRM Deal, open).
    deals = frappe.get_all(
        "CRM Deal",
        filters={"status": ["not in", ["Won", "Lost"]]},
        fields=["name", "organization", "annual_revenue", "status", "deal_owner"],
        order_by="annual_revenue desc", limit=6,
    )
    chancen = [{
        "id": d.name, "name": d.organization or d.name, "org": d.organization or "",
        "value": d.annual_revenue or 0, "status": d.status or "", "owner": d.deal_owner or "",
    } for d in deals]

    # Stage 2 — leads (CRM Lead, active).
    lead_rows = frappe.get_all(
        "CRM Lead",
        filters={"status": ["in", _SM_ACTIVE_LEAD]},
        fields=["name", "lead_name", "organization", "status", "lead_owner"],
        order_by="modified desc", limit=6,
    )
    leads = [{
        "id": l.name, "name": l.lead_name or l.organization or l.name,
        "org": l.organization or "", "status": l.status or "", "owner": l.lead_owner or "",
    } for l in lead_rows]

    # Stage 3 — sales projects (LCS Project, active phases).
    proj_rows = frappe.get_all(
        "LCS Project",
        filters={"phase": ["in", _SM_ACTIVE_PROJECT]},
        fields=["name", "project_name", "project_number", "phase", "estimated_value"],
        order_by="estimated_value desc", limit=6,
    )
    projekte = [{
        "id": p.name, "nr": p.project_number or "", "name": p.project_name or p.name,
        "phase": p.phase or "", "value": p.estimated_value or 0,
    } for p in proj_rows]

    # Meeting frame (KV shown as inspector default content) — raw values,
    # Cross-entity star-flagged items (projects / leads / deals) — the "flagged
    # important" surface the committee reviews first.
    important = []
    for p in frappe.get_all("LCS Project", filters={"is_important": 1},
                            fields=["name", "project_name", "project_number", "phase", "salesperson", "estimated_value"]):
        important.append({"entity": "project", "name": p.name, "label": p.project_name or p.name,
                          "sub": p.project_number, "status": p.phase, "person": p.salesperson,
                          "value": p.estimated_value or 0})
    for l in frappe.get_all("CRM Lead", filters={"is_important": 1},
                            fields=["name", "lead_name", "organization", "status", "lead_owner", "annual_revenue"]):
        important.append({"entity": "lead", "name": l.name, "label": l.lead_name or l.name,
                          "sub": l.organization, "status": l.status, "person": l.lead_owner,
                          "value": l.annual_revenue or 0})
    for d in frappe.get_all("CRM Deal", filters={"is_important": 1},
                            fields=["name", "organization", "status", "deal_owner", "annual_revenue"]):
        important.append({"entity": "deal", "name": d.name, "label": d.organization or d.name,
                          "sub": d.name, "status": d.status, "person": d.deal_owner,
                          "value": d.annual_revenue or 0})

    # the SPA composes the (i18n) labels.
    frame = {
        "meeting_date": str(mdate),
        "open_points": len(agenda),
        "decided_points": len([a for a in agenda if a["status"] == "Decided"]),
        "archived_points": archived_count,
        "opportunities": len(chancen),
        "leads": len(leads),
        "projects": len(projekte),
        "important": len(important),
    }

    return {
        "meeting_date": str(mdate), "agenda": agenda, "archived_count": archived_count,
        "chancen": chancen, "leads": leads, "projekte": projekte,
        "decisions": decisions, "important": important, "frame": frame,
    }


@frappe.whitelist()
def sales_meeting_add(topic, meeting_date=None, reference_object=None,
                      responsible=None, reference_doctype=None, reference_name=None):
    """Create a new open agenda point for a meeting."""
    doc = frappe.get_doc({
        "doctype": "LCS Sales Meeting Agenda",
        "meeting_date": frappe.utils.getdate(meeting_date) if meeting_date else frappe.utils.today(),
        "topic": topic,
        "reference_object": reference_object,
        "reference_doctype": reference_doctype,
        "reference_name": reference_name,
        "responsible": responsible or frappe.session.user,
        "status": "Open",
    })
    doc.insert()
    return {"name": doc.name}


@frappe.whitelist()
def sales_meeting_decide(name, decision=None):
    """Mark an agenda point as decided and append the decision to the minutes.
    Archiving stays a manual, separate step (the salesperson decides)."""
    doc = frappe.get_doc("LCS Sales Meeting Agenda", name)
    doc.status = "Decided"
    if decision is not None:
        doc.decision = decision
    doc.save()
    return {"name": doc.name, "status": doc.status, "decided_on": str(doc.decided_on or "")}


@frappe.whitelist()
def sales_meeting_archive(name):
    """Archive a decided agenda point (removes it from the live list; the
    counter stays visible)."""
    doc = frappe.get_doc("LCS Sales Meeting Agenda", name)
    doc.status = "Archived"
    doc.save()
    return {"name": doc.name, "status": doc.status}


# --------------------------------------------------------------------------- #
#  Call logs (Calls page — klickdummy "Anrufe" design)                        #
# --------------------------------------------------------------------------- #

def _resolve_call_party(value):
    """Resolve the external party of a call (a phone/e-mail) to a contact
    name + company. Returns (person, company). Falls back to the raw value."""
    if not value:
        return "", ""
    # A Frappe User (e.g. the internal caller "Administrator") → full name.
    if frappe.db.exists("User", value):
        return frappe.db.get_value("User", value, "full_name") or value, ""
    # Contact by e-mail or phone/mobile.
    fields = ["first_name", "last_name", "company_name"]
    row = None
    if "@" in value:
        hit = frappe.get_all("Contact Email", filters={"email_id": value}, fields=["parent"], limit=1)
        if hit:
            row = frappe.db.get_value("Contact", hit[0].parent, fields, as_dict=True)
    else:
        hit = frappe.get_all("Contact Phone", filters={"phone": value}, fields=["parent"], limit=1)
        if hit:
            row = frappe.db.get_value("Contact", hit[0].parent, fields, as_dict=True)
    if row:
        person = " ".join(p for p in [row.first_name, row.last_name] if p) or value
        return person, row.company_name or ""
    return value, ""


@frappe.whitelist()
def get_call_logs(limit=200):
    """Call-log board for the Calls page: one row per CRM Call Log with the
    external person + company, direction, duration, the telephony status as the
    result pill and the linked object (deal/lead/project)."""
    logs = frappe.get_all(
        "CRM Call Log",
        fields=["name", "type", "status", "duration", "from", "to", "start_time",
                "reference_doctype", "reference_docname"],
        order_by="start_time desc",
        limit_page_length=int(limit or 200),
    )
    rows = []
    for c in logs:
        outgoing = (c.type or "").lower() == "outgoing"
        party = c.get("to") if outgoing else c.get("from")
        person, company = _resolve_call_party(party)

        # Linked object → a readable label (project number / lead / deal name).
        obj = ""
        if c.reference_docname:
            if c.reference_doctype == "LCS Project":
                obj = frappe.db.get_value("LCS Project", c.reference_docname, "project_number") or c.reference_docname
            else:
                obj = c.reference_docname

        rows.append({
            "id": c.name,
            "date": str(c.start_time) if c.start_time else "",
            "person": person,
            "company": company,
            "direction": "ausgehend" if outgoing else "eingehend",
            "duration": int(c.duration) if c.duration else 0,
            "status": c.status or "",
            "object": obj,
            "ref_doctype": c.reference_doctype or "",
            "ref_name": c.reference_docname or "",
        })
    return {"rows": rows, "total": len(rows)}


# --------------------------------------------------------------------------- #
#  Notes (Notizen page — klickdummy design; text notes + voice notes)         #
# --------------------------------------------------------------------------- #

def _user_name(user):
    return frappe.db.get_value("User", user, "full_name") or user if user else ""


@frappe.whitelist()
def get_notes(limit=200):
    """Notes board for the Notizen page: a union of FCRM Note (Textnotiz) and
    LCS Audio Transcription Job (Sprachnotiz) so the Art column is real. One row
    per note with title, linked object, author and creation time."""
    lim = int(limit or 200)
    rows = []

    for n in frappe.get_all(
        "FCRM Note",
        fields=["name", "title", "content", "owner", "creation",
                "reference_doctype", "reference_docname"],
        order_by="creation desc", limit_page_length=lim,
    ):
        obj = ""
        if n.reference_docname:
            if n.reference_doctype == "LCS Project":
                obj = frappe.db.get_value("LCS Project", n.reference_docname, "project_number") or n.reference_docname
            else:
                obj = n.reference_docname
        rows.append({
            "id": n.name, "doctype": "FCRM Note", "art": "text",
            "title": n.title or (frappe.utils.strip_html(n.content or "")[:80]) or _("Untitled"),
            "object": obj, "author": _user_name(n.owner), "time": str(n.creation),
            "ref_doctype": n.reference_doctype or "", "ref_name": n.reference_docname or "",
        })

    for j in frappe.get_all(
        "LCS Audio Transcription Job",
        fields=["name", "comment", "new_transcript", "original_transcript",
                "owner", "creation", "project"],
        order_by="creation desc", limit_page_length=lim,
    ):
        transcript = j.new_transcript or j.original_transcript or ""
        title = j.comment or (transcript[:80] if transcript else _("Voice note"))
        obj = frappe.db.get_value("LCS Project", j.project, "project_number") or j.project if j.project else ""
        rows.append({
            "id": j.name, "doctype": "LCS Audio Transcription Job", "art": "voice",
            "title": title, "object": obj or "", "author": _user_name(j.owner),
            "time": str(j.creation),
            "ref_doctype": "LCS Project" if j.project else "", "ref_name": j.project or "",
        })

    rows.sort(key=lambda r: r["time"], reverse=True)
    return {"rows": rows[:lim], "total": len(rows)}


# --------------------------------------------------------------------------- #
#  Chancen (funnel entry — opportunities from the Pilot scout / inbound)       #
# --------------------------------------------------------------------------- #

_CHANCE_LIST_FIELDS = [
    "name", "chance_no", "title", "source", "source_detail", "client", "company",
    "country", "order_value", "deadline", "score", "relevance", "status",
    "responsible", "crm_lead",
]


@frappe.whitelist()
def get_chances(source=None):
    """List Chancen for the funnel-entry table (Chance → Lead → Projekt)."""
    filters = {"status": ["!=", "Keine Chance"]}
    if source and source != "Alle":
        filters["source"] = source
    rows = frappe.get_all(
        "LCS Chance", filters=filters, fields=_CHANCE_LIST_FIELDS,
        order_by="score desc", limit_page_length=0,
    )
    for r in rows:
        r["id"] = r["name"]
    # "Keine Chance (Quartal)" — dismissed chances in the last 90 days.
    dismissed = frappe.db.count(
        "LCS Chance",
        {"status": "Keine Chance", "modified": [">=", frappe.utils.add_days(frappe.utils.today(), -90)]},
    )
    return {"rows": rows, "total": len(rows), "dismissed_quarter": dismissed}


@frappe.whitelist()
def get_chance(name):
    """Full detail of one Chance (Ausschreibung · Scoutbewertung · Geo · Vertrieb)."""
    doc = frappe.get_doc("LCS Chance", name)
    return doc.as_dict()


@frappe.whitelist()
def chance_to_lead(name):
    """The salesperson took contact → create a CRM Lead from the Chance, link it
    and flip the status. Idempotent: returns the existing lead if already made."""
    doc = frappe.get_doc("LCS Chance", name)
    if doc.crm_lead and frappe.db.exists("CRM Lead", doc.crm_lead):
        return {"lead": doc.crm_lead, "status": doc.status, "created": False}

    lead = frappe.new_doc("CRM Lead")
    lead.organization = doc.company or doc.client or doc.title
    lead.lead_name = doc.title
    if doc.country:
        lead.territory = None  # keep territory routing to the shell; country is on the org
    lead.status = "New"
    lead.source = "Existing Customer" if doc.source == "Empfehlung" else None
    lead.insert(ignore_permissions=True)

    doc.crm_lead = lead.name
    doc.status = "Kontakt aufgenommen"
    doc.save(ignore_permissions=True)
    return {"lead": lead.name, "status": doc.status, "created": True}


@frappe.whitelist()
def chance_dismiss(name):
    """Mark a Chance as 'Keine Chance' (drops out of the live list; still counted)."""
    doc = frappe.get_doc("LCS Chance", name)
    doc.status = "Keine Chance"
    doc.save(ignore_permissions=True)
    return {"name": doc.name, "status": doc.status}


_CHANCE_MATRIX_FIELDS = (
    "technical_fit", "commercial_fit", "relationship_strength",
    "competition_level", "strategic_importance",
)


def _next_chance_no():
    """Next free CH-### number (mirrors the Pilot-Scout import format)."""
    top = 99
    for no in frappe.get_all("LCS Chance", pluck="chance_no"):
        if no and no.startswith("CH-"):
            try:
                top = max(top, int(no[3:]))
            except (ValueError, TypeError):
                pass
    return f"CH-{top + 1}"


@frappe.whitelist()
def create_chance_from_contact(contact):
    """A contact can spawn an opportunity → create a fresh LCS Chance prefilled
    from the contact, ready for the Opportunity Matrix.
    Flow: Kontakt → Chance → Lead → Projekt."""
    c = frappe.get_doc("Contact", contact)
    company = c.company_name or c.full_name or contact
    doc = frappe.new_doc("LCS Chance")
    doc.chance_no = _next_chance_no()
    doc.title = company
    doc.source = "Anfrage (Mail/Telefon)"
    doc.source_detail = c.full_name or contact
    doc.client = c.company_name or ""
    doc.company = c.company_name or ""
    doc.status = "Neu"
    doc.insert(ignore_permissions=True)
    return {"name": doc.name, "chance_no": doc.chance_no}


@frappe.whitelist()
def get_chance_by_lead(lead):
    """The LCS Chance that originated a lead (chance.crm_lead == lead), with its
    Opportunity-Matrix scores. Returns {} when the lead has no linked chance."""
    name = frappe.db.get_value("LCS Chance", {"crm_lead": lead}, "name")
    if not name:
        return {}
    doc = frappe.get_doc("LCS Chance", name)
    out = {"name": doc.name, "chance_no": doc.chance_no, "title": doc.title,
           "score": doc.score, "status": doc.status,
           "order_value": doc.order_value, "country": doc.country,
           "deadline": doc.deadline}
    for f in _CHANCE_MATRIX_FIELDS:
        out[f] = doc.get(f) or 0
    return out


@frappe.whitelist()
def get_sales_dashboard():
    """Aggregates for the sales landing dashboard: the six KPI cards, the
    weighted pipeline-by-phase bars and the projects-by-type donut. Pilot,
    activities and markets widgets use their own existing endpoints."""
    q_start = frappe.utils.add_days(frappe.utils.today(), -90)

    pilot_hits = frappe.db.count("LCS Chance", {"source": "Pilot-Scout"})
    chances_open = frappe.db.count("LCS Chance", {"status": ["in", ["Neu", "Relevant"]]})
    lost_lead = ["Lost", "Junk", "Unqualified", "Do Not Contact", "Converted"]
    leads_active = frappe.db.count("CRM Lead", {"status": ["not in", lost_lead]})
    projects_total = frappe.db.count("LCS Project")
    no_chance = frappe.db.count(
        "LCS Chance", {"status": "Keine Chance", "modified": [">=", q_start]}
    )
    lost_projects = frappe.db.count(
        "LCS Project", {"phase": "Lost", "modified": [">=", q_start]}
    )

    projects = frappe.get_all(
        "LCS Project",
        fields=["phase", "project_type", "estimated_value", "probability"],
        limit_page_length=0,
    )
    PHASE_BUCKET = {
        "Qualified": "Projektierung", "Budget": "Projektierung", "Richtpreis": "Projektierung",
        "Offer": "Angebot", "Negotiation": "Verhandlung", "Won": "Gewonnen",
    }
    BUCKET_ORDER = ["Projektierung", "Angebot", "Verhandlung", "Gewonnen"]
    TYPE_LABELS = {"SB": "Seilbahn", "SK": "Seilkran", "WI": "Winde", "LL": "Lift", "Other": "Sonstige"}
    buckets = {b: 0.0 for b in BUCKET_ORDER}
    types: dict[str, int] = {}
    pipeline_weighted = 0.0
    for p in projects:
        w = (p.estimated_value or 0) * (p.probability or 0) / 100.0
        if p.phase not in ("Lost", "Completed"):
            pipeline_weighted += w
        bucket = PHASE_BUCKET.get(p.phase)
        if bucket:
            buckets[bucket] += w
        label = TYPE_LABELS.get(p.project_type, p.project_type or "Sonstige")
        types[label] = types.get(label, 0) + 1

    return {
        "kpis": {
            "pilot_hits": pilot_hits,
            "chances_open": chances_open,
            "leads_active": leads_active,
            "projects_total": projects_total,
            "pipeline_weighted": pipeline_weighted,
            "no_chance": no_chance,
            "lost": lost_projects,
        },
        "pipeline_by_phase": [{"label": b, "weighted": buckets[b]} for b in BUCKET_ORDER],
        "projects_by_type": [
            {"label": k, "count": v} for k, v in sorted(types.items(), key=lambda x: -x[1])
        ],
    }


_FREE_MAIL = {
    "gmail.com", "googlemail.com", "outlook.com", "hotmail.com", "yahoo.com",
    "gmx.de", "gmx.net", "web.de", "t-online.de", "icloud.com", "me.com", "aol.com",
}


def _email_domain(email):
    """Company-identifying domain of an email, or '' for free-mail / no address."""
    email = (email or "").strip().lower()
    if "@" not in email:
        return ""
    dom = email.rsplit("@", 1)[1]
    return "" if dom in _FREE_MAIL else dom


@frappe.whitelist()
def link_company_by_domain(contact):
    """Connect a contact to its company via the email domain: match a CRM
    Organization whose website carries the domain, else adopt the company_name
    other contacts on the same domain already use. Persists company_name (and a
    CRM Organization dynamic link when an org matched)."""
    doc = frappe.get_doc("Contact", contact)
    email = doc.email_id or (doc.email_ids[0].email_id if doc.email_ids else "")
    dom = _email_domain(email)
    if not dom:
        return {"linked": False, "reason": "no_domain"}

    org_name = company = via = None
    for o in frappe.get_all("CRM Organization", fields=["name", "organization_name", "website"], limit=0):
        w = (o.website or "").lower()
        if w and dom in w:
            org_name, company, via = o.name, o.organization_name, "website"
            break
    if not company:
        counts = {}
        for p in frappe.get_all(
            "Contact",
            filters={"email_id": ["like", "%@" + dom], "company_name": ["is", "set"]},
            fields=["company_name"], limit=0,
        ):
            if p.company_name and p.company_name != (doc.company_name or ""):
                counts[p.company_name] = counts.get(p.company_name, 0) + 1
        if counts:
            company = max(counts, key=counts.get)
            via = "peers"
            org_name = frappe.db.get_value("CRM Organization", {"organization_name": company}, "name")

    if not company:
        return {"linked": False, "reason": "no_match", "domain": dom}

    doc.company_name = company
    if org_name and not any(
        l.link_doctype == "CRM Organization" and l.link_name == org_name for l in (doc.links or [])
    ):
        doc.append("links", {"link_doctype": "CRM Organization", "link_name": org_name})
    doc.save(ignore_permissions=True)
    return {"linked": True, "company": company, "organization": org_name, "via": via, "domain": dom}


# --------------------------------------------------------------- Phase gates

_PHASE_ORDER = ["Qualified", "Budget", "Richtpreis", "Offer", "Negotiation", "Won", "Execution", "Completed"]


def _phase_idx(phase):
    return _PHASE_ORDER.index(phase) if phase in _PHASE_ORDER else -1


def enforce_phase_gates(doc, method=None):
    """Block advancing an LCS Project past a phase until its prerequisites are
    met (business process flow). Only checks gates NEWLY crossed on this save, so
    existing records and backwards moves are never blocked:
      · → Budget      requires the questionaire to be uploaded
      · → Richtpreis  requires a customer budget OR "budget unknown"
      · → Offer       requires a Richtpreis OR "Richtpreis not possible"
    """
    if not doc.get("phase") or doc.get("phase") == "Lost":
        return
    before = doc.get_doc_before_save()
    if before is None:
        return  # new project (e.g. auto-created from a won deal) — no gate on creation
    old_idx = _phase_idx(before.phase)
    new_idx = _phase_idx(doc.phase)
    if new_idx <= old_idx:  # not advancing / moving back
        return

    if new_idx >= 1 and old_idx < 1 and not doc.get("questionaire"):
        frappe.throw(_("Please upload the questionaire before moving to Budget."))
    if new_idx >= 2 and old_idx < 2 and not (doc.get("budget_customer") or doc.get("budget_unknown")):
        frappe.throw(_("Enter the project budget or mark it as unknown before Richtpreis."))
    if new_idx >= 3 and old_idx < 3 and not (doc.get("richtpreis") or doc.get("richtpreis_impossible")):
        frappe.throw(_("Enter the Richtpreis or mark it as not possible before the Offer phase."))


# --------------------------------------------------------------- Offer approvals

_OWNER_THRESHOLD_EUR = 2_000_000


def offer_needs_owner(doc):
    """Owner sign-off is required above EUR 2m (value_eur is the FX-frozen EUR
    amount; falls back to the raw value)."""
    return (doc.get("value_eur") or doc.get("value") or 0) >= _OWNER_THRESHOLD_EUR


# Only holders of the matching role may give each approval (System Manager may
# always override). The roles are created idempotently by a patch.
_APPROVAL_ROLES = {
    "approval_ceo": "LCS Offer Approver CEO",
    "approval_cfo_coo": "LCS Offer Approver CFO-COO",
    "approval_owner": "LCS Offer Approver Owner",
}


def on_offer_approval_validate(doc, method=None):
    """Release + signature workflow for a binding offer:
      · an approval may only be given by a holder of the matching role (or a
        System Manager); ticking stamps WHO approved, unticking clears it,
      · owner approval is mandatory above EUR 2m,
      · the offer can only be marked signed once every required approval is in.
    """
    user = frappe.session.user
    roles = set(frappe.get_roles(user))
    for chk, by in (
        ("approval_ceo", "approval_ceo_by"),
        ("approval_cfo_coo", "approval_cfo_coo_by"),
        ("approval_owner", "approval_owner_by"),
    ):
        if doc.get(chk):
            if not doc.get(by):
                # newly given approval — the acting user must hold the role
                needed = _APPROVAL_ROLES[chk]
                if "System Manager" not in roles and needed not in roles:
                    frappe.throw(_("You are not authorised to give this approval: {0}").format(_(needed)))
                doc.set(by, user)
        else:
            doc.set(by, None)

    needs_owner = offer_needs_owner(doc)
    if doc.get("signed"):
        missing = []
        if not doc.get("approval_ceo"):
            missing.append(_("CEO"))
        if not doc.get("approval_cfo_coo"):
            missing.append(_("CFO/COO"))
        if needs_owner and not doc.get("approval_owner"):
            missing.append(_("owner"))
        if missing:
            frappe.throw(_("Cannot sign — missing approval:") + " " + ", ".join(missing))
        if not doc.get("signed_on"):
            doc.signed_on = frappe.utils.now_datetime()
    elif doc.get("signed_on"):
        doc.signed_on = None


# --------------------------------------------------------------- Relations (child tables)

_RELATION_FIELDS = {
    ("CRM Organization", "lcs_relations"),
    ("Contact", "lcs_relations"),
    ("Contact", "lcs_employment"),
}


@frappe.whitelist()
def get_relations(doctype, name, fieldname):
    """Read a relation child table (cross-org / person relationships)."""
    if (doctype, fieldname) not in _RELATION_FIELDS:
        frappe.throw(_("Unsupported relation field."))
    if not frappe.has_permission(doctype, "read", doc=name):
        frappe.throw(_("Not permitted"), frappe.PermissionError)
    doc = frappe.get_doc(doctype, name)
    return [row.as_dict() for row in (doc.get(fieldname) or [])]


@frappe.whitelist()
def save_relations(doctype, name, fieldname, rows):
    """Replace a relation child table with the given rows and save. Rows is a
    JSON list of dicts. Only the whitelisted relation fields are editable."""
    if (doctype, fieldname) not in _RELATION_FIELDS:
        frappe.throw(_("Unsupported relation field."))
    if not frappe.has_permission(doctype, "write", doc=name):
        frappe.throw(_("Not permitted"), frappe.PermissionError)
    if isinstance(rows, str):
        rows = frappe.parse_json(rows)
    doc = frappe.get_doc(doctype, name)
    doc.set(fieldname, [])
    for r in (rows or []):
        doc.append(fieldname, {k: v for k, v in r.items() if not str(k).startswith("_") and k not in ("name", "idx", "parent", "parenttype", "parentfield")})
    doc.save(ignore_permissions=True)
    return {"ok": True, "count": len(doc.get(fieldname) or [])}
