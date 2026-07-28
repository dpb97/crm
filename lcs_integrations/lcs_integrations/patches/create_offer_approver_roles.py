import frappe

# Roles that authorise an offer approval (see on_offer_approval_validate).
# Assign them to the actual CEO / CFO-COO / owner users in the Desk.
_ROLES = [
    "LCS Offer Approver CEO",
    "LCS Offer Approver CFO-COO",
    "LCS Offer Approver Owner",
]


def execute():
    for role in _ROLES:
        if not frappe.db.exists("Role", role):
            frappe.get_doc({"doctype": "Role", "role_name": role, "desk_access": 1}).insert(
                ignore_permissions=True
            )
