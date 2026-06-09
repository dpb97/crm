import frappe
from frappe.model.document import Document


class LCSAccessProfile(Document):
    def on_update(self):
        """Invalidate cached user profiles when the profile changes — otherwise
        the permission_query_conditions hook keeps serving stale rules."""
        frappe.cache().delete_key("lcs_access_profile_cache")
