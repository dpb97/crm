import frappe
from frappe.model.document import Document


class LCSOffer(Document):
    def on_trash(self):
        """Clear back-links on ERPNext Quotation + Sales Order when this
        offer is deleted — leaves the commercial artefacts intact but
        removes the stale pointer back to a non-existent offer."""
        import frappe as _frappe
        if self.erpnext_quotation and _frappe.db.exists("Quotation", self.erpnext_quotation):
            _frappe.db.set_value("Quotation", self.erpnext_quotation, "lcs_offer", None)
        if self.erpnext_sales_order and _frappe.db.exists("Sales Order", self.erpnext_sales_order):
            _frappe.db.set_value("Sales Order", self.erpnext_sales_order, "lcs_project", None)
    def validate(self):
        self.validate_version()
        self.sync_project_phase()

    def validate_version(self):
        """Ensure version increments per project."""
        if not self.version:
            max_version = frappe.db.sql(
                "SELECT MAX(version) FROM `tabLCS Offer` WHERE project = %s AND name != %s",
                (self.project, self.name or ""),
            )[0][0]
            self.version = (max_version or 0) + 1

    def sync_project_phase(self):
        """Keep project phase in sync with offer status for clarity."""
        if not self.project:
            return
        status_to_phase = {
            "Sent": "Offer",
            "In Review": "Negotiation",
            "Accepted": "Order",
            "Rejected": "Lost",
        }
        new_phase = status_to_phase.get(self.status)
        if new_phase:
            current_phase = frappe.db.get_value("LCS Project", self.project, "phase")
            phase_order = ["Inquiry", "Offer", "Negotiation", "Order", "Execution", "Completed", "Lost"]
            if phase_order.index(new_phase) > phase_order.index(current_phase or "Inquiry"):
                frappe.db.set_value("LCS Project", self.project, "phase", new_phase)

        # When offer accepted, copy its value into project's angebot_total
        if self.status == "Accepted" and self.value:
            frappe.db.set_value("LCS Project", self.project, "angebot_total", self.value)
