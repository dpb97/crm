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


@frappe.whitelist()
def get_opportunity_matrix(project):
    """Get opportunity matrix entries for a project."""
    return frappe.get_all(
        "LCS Opportunity Matrix",
        filters={"project": project},
        fields="*",
    )


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
def get_sales_meeting_data():
    """Sales-meeting board mirroring the LCS Excel protocol: one row per
    active opportunity with PL/PN, last comment, responsible (Wer), next
    action + due (KW), status/phase, chance %, value, sector."""
    import datetime

    ACTIVE = ["Qualified", "Budget", "Richtpreis", "Offer", "Negotiation"]
    projects = frappe.get_all(
        "LCS Project",
        filters={"phase": ["in", ACTIVE]},
        fields=[
            "name", "project_name", "project_number", "project_type", "phase",
            "status", "country", "salesperson", "sales_manager", "probability",
            "estimated_value", "is_important",
        ],
        order_by="is_important desc, probability desc, estimated_value desc",
        limit_page_length=0,
    )
    today = datetime.date.today()
    rows, total, weighted, due_count = [], 0.0, 0.0, 0
    for p in projects:
        last = frappe.get_all(
            "Comment",
            filters={"reference_doctype": "LCS Project", "reference_name": p.name,
                     "comment_type": ["in", ["Comment", "Info"]]},
            fields=["content", "creation"], order_by="creation desc", limit=1,
        )
        comment = frappe.utils.strip_html(last[0].content or "")[:240] if last else ""
        task = frappe.get_all(
            "CRM Task",
            filters={"reference_doctype": "LCS Project", "reference_docname": p.name,
                     "status": ["in", ["Todo", "Backlog", "In Progress"]]},
            fields=["title", "due_date"], order_by="due_date asc", limit=1,
        )
        next_action = task[0].title if task else ""
        due = task[0].due_date if task else None
        kw = ""
        if due:
            try:
                kw = "KW" + str(frappe.utils.getdate(due).isocalendar()[1])
            except Exception:
                kw = ""
        val = p.estimated_value or 0
        prob = p.probability or 0
        w = val * prob / 100.0
        total += val
        weighted += w
        if due and frappe.utils.getdate(due) <= frappe.utils.add_days(today, 7):
            due_count += 1
        rows.append({
            "name": p.name, "project_name": p.project_name, "project_number": p.project_number,
            "type": p.project_type, "phase": p.phase, "status": p.status, "country": p.country,
            "salesperson": p.salesperson, "comment": comment, "next_action": next_action,
            "due": str(due) if due else "", "kw": kw, "probability": prob, "value": val,
            "weighted": w, "is_important": p.is_important,
        })
    # Star-flagged items across all entities surface here too.
    important = []
    for p in frappe.get_all("LCS Project", filters={"is_important": 1},
                            fields=["name", "project_name", "project_number", "phase", "salesperson", "estimated_value"]):
        important.append({"entity": "project", "name": p.name, "label": p.project_name,
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

    # Active leads — top of the funnel, reviewed in the meeting too.
    leads = frappe.get_all(
        "CRM Lead",
        filters={"status": ["in", ["New", "Contacted", "Nurture", "Qualified"]]},
        fields=["name", "lead_name", "organization", "status", "lead_owner",
                "annual_revenue", "is_important"],
        order_by="is_important desc, modified desc",
        limit_page_length=0,
    )

    return {"rows": rows, "important": important, "leads": leads, "summary": {
        "count": len(rows), "total": total, "weighted": weighted,
        "due_actions": due_count, "important": len(important), "leads": len(leads),
    }}


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
