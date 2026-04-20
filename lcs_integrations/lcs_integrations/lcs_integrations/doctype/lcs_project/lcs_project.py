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
