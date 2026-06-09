"""
Unified integration-status endpoint for LCS Project.

Returns the state of every external system we integrate with so the
frontend can render a single "360° view" panel without N round-trips.
"""

import frappe


@frappe.whitelist()
def get_integration_status(project):
    """Return per-system state for one LCS Project.

    Response shape:
      {
        "crm":     { linked: bool, deal: str|None, organization: str|None },
        "erpnext": { customer: str|None, quotation: str|None, sales_order: str|None, status: str },
        "bsm":     { project: str|None, status: str|None, defects_open: int },
        "hrms":    { project_manager: str|None, team_size: int, training: {...} },
        "lms":     { required_courses: int, team_compliant: int, team_missing: int },
        "fusion":  { workspace: str|None, item_id: str|None, number: str|None, state: str|None, last_sync: str|None }
      }
    """
    doc = frappe.get_doc("LCS Project", project)

    status = {
        "crm": _crm_status(doc),
        "erpnext": _erpnext_status(doc),
        "bsm": _bsm_status(doc),
        "hrms": _hrms_status(doc),
        "lms": _lms_status(doc),
        "fusion": _fusion_status(doc),
    }
    return status


def _crm_status(doc):
    return {
        "linked": bool(doc.deal or doc.organization),
        "deal": doc.deal,
        "organization": doc.organization,
    }


def _erpnext_status(doc):
    quotations = []
    sales_orders = []
    if frappe.db.exists("DocType", "Quotation"):
        quotations = frappe.get_all(
            "Quotation",
            filters={"lcs_offer": ["in", [o.name for o in frappe.get_all("LCS Offer", filters={"project": doc.name})]]},
            fields=["name", "status"],
        ) if frappe.db.get_value("Custom Field", {"dt": "Quotation", "fieldname": "lcs_offer"}) else []
    if frappe.db.exists("DocType", "Sales Order"):
        sales_orders = frappe.get_all(
            "Sales Order",
            filters={"lcs_project": doc.name},
            fields=["name", "status", "per_delivered"],
        ) if frappe.db.get_value("Custom Field", {"dt": "Sales Order", "fieldname": "lcs_project"}) else []

    status = "Not linked"
    if sales_orders:
        status = sales_orders[0]["status"] or "Draft"
    elif quotations:
        status = f"Quote {quotations[0]['status']}"
    elif doc.erpnext_customer:
        status = "Customer only"

    return {
        "customer": doc.erpnext_customer,
        "quotation": quotations[0]["name"] if quotations else None,
        "sales_order": sales_orders[0]["name"] if sales_orders else None,
        "status": status,
        "quotation_count": len(quotations),
        "sales_order_count": len(sales_orders),
    }


def _bsm_status(doc):
    if not doc.bsm_project or not frappe.db.exists("DocType", "BSM Project"):
        return {"project": None, "status": None, "defects_open": 0}
    bsm = frappe.db.get_value("BSM Project", doc.bsm_project, ["name", "status"], as_dict=True) or {}
    defects_open = 0
    if frappe.db.exists("DocType", "BSM Defect"):
        defects_open = frappe.db.count("BSM Defect", {"project": doc.bsm_project, "status": ["!=", "Closed"]})
    return {
        "project": bsm.get("name"),
        "status": bsm.get("status"),
        "defects_open": defects_open,
    }


def _hrms_status(doc):
    pm_name = None
    if doc.project_manager:
        pm_name = frappe.db.get_value("Employee", doc.project_manager, "employee_name")
    team_size = len(doc.team_members or [])
    # Aggregate training status from team
    training = {"Compliant": 0, "Missing Certifications": 0, "Expiring Soon": 0, "Unknown": 0}
    for m in doc.team_members or []:
        training[m.training_status or "Unknown"] = training.get(m.training_status or "Unknown", 0) + 1
    return {
        "project_manager": pm_name,
        "project_manager_id": doc.project_manager,
        "team_size": team_size,
        "training": training,
    }


def _lms_status(doc):
    required = len(doc.required_trainings or [])
    compliant = sum(1 for m in (doc.team_members or []) if m.training_status == "Compliant")
    missing = sum(1 for m in (doc.team_members or []) if m.training_status == "Missing Certifications")
    return {
        "required_courses": required,
        "team_compliant": compliant,
        "team_missing": missing,
    }


def _fusion_status(doc):
    return {
        "workspace": doc.fusion_workspace,
        "item_id": doc.fusion_item_id,
        "number": doc.fusion_item_number,
        "state": doc.fusion_item_state,
        "last_sync": str(doc.fusion_last_sync) if doc.fusion_last_sync else None,
    }
