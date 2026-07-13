"""Entra (MSAL/OIDC) Social Login provider registration for Frappe.

Frappe's `Social Login Key` DocType represents OIDC providers. This module
exposes a helper that installs / updates the key during bench migration. The
actual login flow is handled entirely by Frappe's built-in OAuth2 client — we
only need the right URLs and scopes for Entra.
"""

from __future__ import annotations

import os

import frappe


ENTRA_KEY_NAME = "entra"


def install_or_update() -> None:
    """Idempotent: create / refresh the Entra Social Login Key."""
    from lcs_integrations.entra_config import entra

    tenant = entra("ENTRA_TENANT_ID", "common")
    client_id = entra("ENTRA_CLIENT_ID", "")
    client_secret = entra("ENTRA_CLIENT_SECRET", "")
    authority = f"https://login.microsoftonline.com/{tenant}"
    doc = frappe.get_doc("Social Login Key", ENTRA_KEY_NAME) if frappe.db.exists(
        "Social Login Key", ENTRA_KEY_NAME
    ) else frappe.new_doc("Social Login Key")
    doc.social_login_provider = "Custom"
    doc.provider_name = "Microsoft Entra"
    doc.client_id = client_id
    doc.client_secret = client_secret
    doc.authorize_url = f"{authority}/oauth2/v2.0/authorize"
    doc.access_token_url = f"{authority}/oauth2/v2.0/token"
    doc.base_url = authority
    doc.api_endpoint = "https://graph.microsoft.com/oidc/userinfo"
    doc.auth_url_data = '{"response_type": "code", "scope": "openid email profile User.Read"}'
    doc.user_id_property = "email"
    doc.enable_social_login = 1
    doc.save(ignore_permissions=True)
    frappe.db.commit()
