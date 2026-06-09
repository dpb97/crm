"""Seed the default redirect_uri for new OAuth2 fields on upgrade."""

import frappe


def execute():
    if not frappe.db.exists("DocType", "LCS Fusion Manage Settings"):
        return
    settings = frappe.get_single("LCS Fusion Manage Settings")
    # Only set default if field is empty — don't clobber manual configuration
    if not getattr(settings, "redirect_uri", None):
        site_url = frappe.utils.get_url()
        settings.redirect_uri = f"{site_url}/api/method/lcs_integrations.fusion_manage.auth.oauth_callback"
    if not getattr(settings, "scopes", None):
        settings.scopes = "data:read data:write"
    settings.save(ignore_permissions=True)
    frappe.db.commit()
