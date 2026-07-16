import frappe
from frappe.model.document import Document


class LCSFunnelPhase(Document):
    def on_update(self):
        frappe.cache().delete_value("lcs_funnel_phases")

    def on_trash(self):
        frappe.cache().delete_value("lcs_funnel_phases")
