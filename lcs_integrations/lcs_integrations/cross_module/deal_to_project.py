"""
Unified Deal ↔ LCS Project bridge.

The LCS Project is the single sales entity in the CRM. It is created as soon as
a CRM Deal exists (lead conversion / new deal) via ``on_deal_insert`` — so the
opportunity is one record from the very start, not only once the deal is won.
The project spans the whole sales cycle (offers, pricing, negotiation) and only
hands off to ERP execution at the "Won" (Auftrag) phase.

``on_deal_update`` keeps the order boundary in sync: when a deal is won, the
linked project advances to "Won". Legacy deals that predate unified creation
(no linked project) get one created here as a fallback.

Idempotent throughout: creation is skipped when a project already links back to
the deal (LCS Project.deal), so re-saves / migrate re-runs never duplicate.
"""

import frappe


WON_STATUSES = {"Won", "Ordered"}  # tolerate different CRM Deal Status naming

# CRM Deal status -> initial LCS Project phase. A fresh deal starts at the first
# sales stage; the phase then advances via offers / manual edits / winning.
STATUS_TO_PHASE = {
    "Qualification": "Qualified",
    "Demo/Making": "Budget",
    "Proposal/Quotation": "Offer",
    "Negotiation": "Negotiation",
    "Ready to Close": "Negotiation",
    "Won": "Won",
    "Ordered": "Won",
    "Lost": "Lost",
}

# Phases we never regress away from when a deal is (re-)won.
_TERMINAL_PHASES = {"Won", "Execution", "Completed", "Lost"}


def on_deal_insert(doc, method=None):
    """CRM Deal after_insert — spin up the unified LCS Project immediately, so
    the opportunity is one record from the start."""
    if frappe.db.get_value("LCS Project", {"deal": doc.name}, "name"):
        return
    try:
        _create_project_from_deal(doc, phase=_phase_for_status(doc))
    except Exception as e:
        frappe.log_error(
            f"Auto-project creation on insert failed for deal {doc.name}: {e}",
            "cross_module.deal_to_project",
        )


def on_deal_update(doc, method=None):
    """CRM Deal on_update — keep the order boundary in sync. On win, advance the
    linked project to 'Won' (Auftrag); create one for legacy deals that have no
    project yet."""
    status = (doc.get("status") or "").strip()
    if not status:
        return
    if _resolve_status_label(status) not in WON_STATUSES:
        return

    existing = frappe.db.get_value("LCS Project", {"deal": doc.name}, "name")
    if existing:
        _advance_to_won(existing)
        return

    # Legacy deal without a project (created before unified creation).
    try:
        project_name = _create_project_from_deal(doc, phase="Won")
        if project_name:
            frappe.msgprint(
                f"Auto-created LCS Project <a href='/crm/projects/{project_name}'>{project_name}</a> "
                f"for won deal {doc.name}",
                alert=True,
                indicator="green",
            )
    except Exception as e:
        frappe.log_error(
            f"Auto-project creation on win failed for deal {doc.name}: {e}",
            "cross_module.deal_to_project",
        )


def _advance_to_won(project_name: str) -> None:
    """Move a linked project to the 'Won' (Auftrag) phase without regressing a
    project that is already won / in execution / closed."""
    phase = frappe.db.get_value("LCS Project", project_name, "phase")
    if phase in _TERMINAL_PHASES:
        return
    project = frappe.get_doc("LCS Project", project_name)
    project.phase = "Won"
    project.save(ignore_permissions=True)


def _phase_for_status(deal) -> str:
    label = _resolve_status_label((deal.get("status") or "").strip())
    return STATUS_TO_PHASE.get(label, "Qualified")


def _resolve_status_label(status_value: str) -> str:
    """CRM Deal.status may be a direct string or a Link to CRM Deal Status —
    normalise to the display label for comparison."""
    if status_value in WON_STATUSES:
        return status_value
    if frappe.db.exists("CRM Deal Status", status_value):
        return status_value  # record name equals label in frappe/crm
    return status_value


def _create_project_from_deal(deal, phase: str = "Qualified") -> str | None:
    """Build the LCS Project from the deal's fields at the given phase. Keeps the
    field mapping in one place."""
    project = frappe.new_doc("LCS Project")
    project.project_name = _safe_name(deal)
    project.project_type = _infer_type_from_deal(deal)
    project.phase = phase
    project.status = "Active" if phase in ("Won", "Execution") else "Open"
    project.deal = deal.name
    if deal.get("organization"):
        project.organization = deal.organization
    if deal.get("deal_owner"):
        project.salesperson = deal.deal_owner
    if deal.get("annual_revenue"):
        project.budget_customer = deal.annual_revenue
    if deal.get("close_date"):
        project.expected_close_date = deal.close_date
    project.insert(ignore_permissions=True)
    return project.name


def _safe_name(deal) -> str:
    """CRM Deal names aren't guaranteed unique across projects — if another
    project already has this name, append the deal number."""
    base = deal.get("deal_name") or deal.name
    if not frappe.db.exists("LCS Project", {"project_name": base}):
        return base
    return f"{base} ({deal.name})"


def _infer_type_from_deal(deal) -> str:
    """Look at the deal's name + org for product keywords — same rules as the
    BSM back-fill so behaviour is predictable."""
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
