import frappe
from frappe.model.document import Document
from pypika import functions as fn


class LCSOffer(Document):
    def on_trash(self):
        """Clear back-links on ERPNext Quotation + Sales Order when this
        offer is deleted — leaves the commercial artefacts intact but
        removes the stale pointer back to a non-existent offer."""
        if self.erpnext_quotation and frappe.db.exists("Quotation", self.erpnext_quotation):
            frappe.db.set_value("Quotation", self.erpnext_quotation, "lcs_offer", None)
        if self.erpnext_sales_order and frappe.db.exists("Sales Order", self.erpnext_sales_order):
            frappe.db.set_value("Sales Order", self.erpnext_sales_order, "lcs_project", None)

    def validate(self):
        self.validate_version()
        self.sync_project_phase()

    def validate_version(self):
        """Ensure version increments per project.

        Uses frappe.qb instead of raw SQL so schema renames on tabLCS Offer
        don't silently break this path.
        """
        if self.version:
            return
        Offer = frappe.qb.DocType("LCS Offer")
        query = (
            frappe.qb.from_(Offer)
            .select(fn.Max(Offer.version).as_("max_version"))
            .where(Offer.project == self.project)
        )
        if self.name:
            query = query.where(Offer.name != self.name)
        result = query.run(as_dict=True)
        max_version = (result[0].get("max_version") if result else None) or 0
        self.version = max_version + 1

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
