import frappe
from frappe.model.document import Document


class LCSUserPreferences(Document):
    def validate(self):
        # Limit users to one preferences record each — autoname=field:user
        # already enforces this at the DB level, but validate keeps the
        # error message clean for UI callers.
        if self.is_new() and frappe.db.exists("LCS User Preferences", self.user):
            frappe.throw(
                f"Preferences already exist for user {self.user}. Open the existing record instead."
            )
