import frappe
from frappe.model.document import Document


class LCSOffer(Document):
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
            # Only move forward, never backward automatically
            phase_order = ["Inquiry", "Offer", "Negotiation", "Order", "Execution", "Completed", "Lost"]
            if phase_order.index(new_phase) > phase_order.index(current_phase or "Inquiry"):
                frappe.db.set_value("LCS Project", self.project, "phase", new_phase)
