"""
Auto-create an ERPNext Project when an LCS Project enters Order or
Execution phase, so resource/capacity planning has a place to live
while the project is still active (not just after closure).

Why two project DocTypes:
  - LCS Project owns sales-pipeline data (phase, source, 3-stage
    pricing, opportunity matrix, win probability).
  - ERPNext Project owns execution data (tasks, time logs, costing,
    gantt, billing, percent_complete).

Both are linked 1:1 — neither duplicates the other's domain.

Idempotent: if LCS Project.erpnext_project is already set, the hook
no-ops. Re-saving the LCS Project never spawns a second ERPNext one.
"""

import frappe


# Phases at which an ERPNext Project is genuinely useful for planning.
# Order = sales done, planning starts.  Execution = on-site work running.
TRIGGER_PHASES = {"Order", "Execution"}


def on_lcs_project_update(doc, method=None):
    """LCS Project on_update hook. Creates the ERPNext Project when the
    project first enters a planning-relevant phase."""
    if not frappe.db.exists("DocType", "Project"):
        return  # ERPNext not installed
    if doc.get("erpnext_project"):
        return  # Already linked
    if (doc.get("phase") or "") not in TRIGGER_PHASES:
        return

    try:
        project_name = _create_erpnext_project(doc)
        if project_name:
            doc.db_set("erpnext_project", project_name, update_modified=False)
            frappe.msgprint(
                f"Auto-created ERPNext Project "
                f"<a href='/app/project/{project_name}'>{project_name}</a> "
                f"for resource planning.",
                alert=True,
                indicator="blue",
            )
    except Exception as e:
        frappe.log_error(
            f"ERPNext Project auto-create failed for {doc.name}: {e}",
            "cross_module.erpnext_project_sync",
        )


def _create_erpnext_project(lcs) -> str | None:
    """Build (or adopt) the ERPNext Project for this LCS Project.

    Sales-side data is intentionally NOT mirrored — that lives only in
    LCS Project. We only push execution-relevant fields.

    Adoption: if an ERPNext Project with the same project_name already
    exists, link to it (via the lcs_project back-field) instead of
    creating a duplicate. project_name has a UNIQUE constraint in
    ERPNext, so this isn't optional.
    """
    meta = frappe.get_meta("Project")
    fields = {f.fieldname for f in meta.fields}

    # Adoption path
    existing = frappe.db.get_value("Project", {"project_name": lcs.project_name}, "name")
    if existing:
        # Make sure the back-link exists
        if "lcs_project" in fields:
            frappe.db.set_value("Project", existing, "lcs_project", lcs.name, update_modified=False)
        return existing

    # Creation path
    project = frappe.new_doc("Project")
    project.project_name = lcs.project_name
    if "lcs_project" in fields:
        project.lcs_project = lcs.name

    # Customer — pulled from the LCS link, not duplicated
    if "customer" in fields and lcs.get("erpnext_customer"):
        project.customer = lcs.erpnext_customer

    # Status mapping — LCS phase to ERPNext Project status
    if "status" in fields:
        if lcs.get("phase") == "Completed":
            project.status = "Completed"
        elif lcs.get("phase") == "Lost":
            project.status = "Cancelled"
        else:
            project.status = "Open"

    # Dates — use what the sales side has
    if "expected_start_date" in fields and lcs.get("expected_close_date"):
        project.expected_start_date = lcs.expected_close_date
    if "expected_end_date" in fields and lcs.get("expected_close_date"):
        project.expected_end_date = frappe.utils.add_months(lcs.expected_close_date, 6)

    # Estimated cost — use the formal angebot_total (best available estimate)
    if "estimated_costing" in fields:
        project.estimated_costing = lcs.get("angebot_total") or lcs.get("estimated_value") or 0

    # Project Manager
    if "project_manager" in fields and lcs.get("project_manager"):
        # ERPNext uses User for project_manager, not Employee — translate via Employee.user_id
        user_id = frappe.db.get_value("Employee", lcs.project_manager, "user_id")
        if user_id:
            project.project_manager = user_id

    project.insert(ignore_permissions=True)
    frappe.db.commit()
    return project.name


@frappe.whitelist()
def backfill_erpnext_projects(dry_run: bool = False) -> dict:
    """Create ERPNext Projects for every LCS Project already in
    Order/Execution phase that doesn't have one yet."""
    frappe.only_for(["System Manager", "Sales Manager"])
    if isinstance(dry_run, str):
        dry_run = dry_run.lower() in ("1", "true", "yes")

    if not frappe.db.exists("DocType", "Project"):
        return {"error": "ERPNext Project not installed"}

    candidates = frappe.get_all(
        "LCS Project",
        filters={
            "phase": ["in", list(TRIGGER_PHASES)],
            "erpnext_project": ["in", ["", None]],
        },
        fields=["name", "project_name"],
    )

    summary = {"checked": len(candidates), "created": 0, "errors": 0,
               "dry_run": bool(dry_run), "changes": []}

    for c in candidates:
        try:
            doc = frappe.get_doc("LCS Project", c.name)
            if dry_run:
                summary["changes"].append({"lcs": c.name, "action": "would-create",
                                           "project_name": c.project_name})
                continue
            project_name = _create_erpnext_project(doc)
            if project_name:
                doc.db_set("erpnext_project", project_name, update_modified=False)
                summary["created"] += 1
                summary["changes"].append({
                    "lcs": c.name, "action": "created",
                    "project_name": c.project_name, "erpnext": project_name,
                })
        except Exception as e:
            summary["errors"] += 1
            summary["changes"].append({"lcs": c.name, "action": "error", "reason": str(e)})

    if not dry_run:
        frappe.db.commit()

    prefix = "[DRY-RUN] " if dry_run else ""
    print(f"\n{prefix}=== ERPNext Project back-fill ===")
    print(f"  Candidates: {summary['checked']}")
    print(f"  Created:    {summary['created']}")
    print(f"  Errors:     {summary['errors']}")
    for c in summary["changes"][:30]:
        a = c["action"]
        marker = {"created": "+", "would-create": "?", "error": "!"}.get(a, "?")
        name = (c.get("project_name") or "?")[:40]
        if a == "created":
            print(f"  [{marker}] {name:<42} → {c.get('erpnext')}")
        else:
            print(f"  [{marker}] {name:<42}  {a}")
    return summary
