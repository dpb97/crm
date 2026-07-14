"""
Auto-create an LCS Project whenever a CRM Deal moves to status 'Won'.

Closes the forward automation gap in the Lead → Deal → Project flow:
previously an admin had to click a button (or call the whitelisted
create_project_from_deal endpoint) to spin up a project when a deal
landed. Now it's hands-off.

Idempotent: if the deal already has an LCS Project linked back to it
(via LCS Project.deal field) we skip — double-save or migrate re-runs
don't duplicate projects.
"""

import frappe


WON_STATUSES = {"Won", "Ordered"}  # tolerate different CRM Deal Status naming


def on_deal_update(doc, method=None):
    """CRM Deal on_update hook. Fires on every save — quick early-exit
    for deals that are still in-flight."""
    status = (doc.get("status") or "").strip()
    if not status:
        return

    # Only act on wins, and only once per deal
    status_label = _resolve_status_label(status)
    if status_label not in WON_STATUSES:
        return

    # Already linked? (either the deal points at a project or a project points at this deal)
    existing = frappe.db.get_value("LCS Project", {"deal": doc.name}, "name")
    if existing:
        return

    try:
        project_name = _create_project_from_deal(doc)
        if project_name:
            frappe.msgprint(
                f"Auto-created LCS Project <a href='/crm/projects/{project_name}'>{project_name}</a> "
                f"for won deal {doc.name}",
                alert=True,
                indicator="green",
            )
    except Exception as e:
        frappe.log_error(
            f"Auto-project creation failed for deal {doc.name}: {e}",
            "cross_module.deal_to_project",
        )


def _resolve_status_label(status_value: str) -> str:
    """CRM Deal.status may be either a direct string or a Link to
    CRM Deal Status — normalise to the display label so we can
    compare against WON_STATUSES reliably."""
    # If the status is already a known label, return as-is
    if status_value in WON_STATUSES:
        return status_value
    # Otherwise try to resolve as a CRM Deal Status record
    if frappe.db.exists("CRM Deal Status", status_value):
        return status_value  # record name equals label in frappe/crm
    return status_value


def _create_project_from_deal(deal) -> str | None:
    """Build the LCS Project record from the deal's fields. Keeps the
    mapping in one place so future fields (value, probability, etc.)
    are easy to add."""
    # Figure out a sensible project type from the deal's notes or name,
    # mirroring the back-fill heuristic so behaviour is consistent.
    project_type = _infer_type_from_deal(deal)

    project = frappe.new_doc("LCS Project")
    project.project_name = _safe_name(deal)
    project.project_type = project_type
    # "Won" is the order/Auftrag phase (displayed as "Auftrag"). "Order" was a
    # legacy value that isn't in the phase Select — writing it left projects in
    # an invalid state and broke the ERPNext handoff. A won deal skips the early
    # sales phases straight to the order stage.
    project.phase = "Won"
    project.status = "Active"
    project.deal = deal.name
    if deal.get("organization"):
        project.organization = deal.organization
    # Attempt to pull the salesperson from the deal's owner
    if deal.get("deal_owner"):
        project.salesperson = deal.deal_owner
    # Commercial: if the deal tracked a value, prefill budget
    if deal.get("annual_revenue"):
        project.budget_customer = deal.annual_revenue
    # expected_close_date from the deal's close_date
    if deal.get("close_date"):
        project.expected_close_date = deal.close_date
    project.insert(ignore_permissions=True)
    frappe.db.commit()
    return project.name


def _safe_name(deal) -> str:
    """CRM Deal names aren't guaranteed unique across projects — if
    another project already has this name, append the deal number."""
    base = deal.get("deal_name") or deal.name
    if not frappe.db.exists("LCS Project", {"project_name": base}):
        return base
    return f"{base} ({deal.name})"


def _infer_type_from_deal(deal) -> str:
    """Look at the deal's name + notes for product keywords — same rules
    as the BSM back-fill so behaviour is predictable."""
    haystack = " ".join([
        deal.get("deal_name") or "",
        deal.get("organization") or "",
        deal.get("no_of_employees") or "",  # some fields leak product words
    ]).lower()

    import re
    if re.search(r"\bseilbahn\w*|\bcable[\s-]?cran\w*", haystack):
        return "SB"
    if re.search(r"\bwinde\w*|\bwinch\w*", haystack):
        return "WI"
    if re.search(r"\blift\w*", haystack):
        return "LL"
    if re.search(r"\bsonder|\bspecial|\baftersales|\bservice", haystack):
        return "SK"
    return "Other"
