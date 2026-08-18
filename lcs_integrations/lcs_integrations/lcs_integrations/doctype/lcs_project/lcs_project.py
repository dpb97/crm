import frappe
from frappe.model.document import Document


class LCSProject(Document):
    def before_insert(self):
        if not self.project_number:
            self.project_number = self.generate_project_number()

    def generate_project_number(self):
        """Generate project number like LCS-SB-2026-001"""
        year = frappe.utils.nowdate()[:4]
        prefix = f"LCS-{self.project_type or 'XX'}-{year}"
        count = frappe.db.count(
            "LCS Project", filters={"project_number": ["like", f"{prefix}-%"]}
        )
        return f"{prefix}-{(count + 1):03d}"

    def validate(self):
        if self.project_abbr:
            self.project_abbr = self.project_abbr.upper()
        self.backfill_estimated_value()
        self.enforce_customer_and_salesperson()

    def enforce_customer_and_salesperson(self):
        """A project created/edited by a user must always name a customer and a
        salesperson. Automated creators (deal->project, BSM backfill, lead->project)
        insert with ignore_permissions=True and are intentionally exempt, since
        their source records may not carry both fields yet."""
        if self.flags.ignore_permissions:
            return
        if not self.organization:
            frappe.throw(frappe._("Please select a customer for the project."))
        if not self.salesperson:
            frappe.throw(frappe._("Please select a sales rep (Vertrieb) for the project."))

    def backfill_estimated_value(self):
        """Estimated value falls back: Angebot → Richtpreis → Budget.
        User can still override manually, but only applies the fallback
        when estimated_value is empty."""
        if not self.estimated_value:
            self.estimated_value = self.angebot_total or self.richtpreis or self.budget_customer or 0
