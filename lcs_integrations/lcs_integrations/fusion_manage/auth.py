"""
Autodesk Forge / Fusion Manage OAuth2 — authorization_code + refresh_token.

Two flows supported:
1. Interactive authorization_code flow — admin clicks "Connect" in the
   settings page, gets redirected to Autodesk, comes back with a code
   that we exchange for tokens. Only done once per tenant install.
2. Automatic refresh_token flow — called by get_access_token() whenever
   the cached access_token is within 60 seconds of expiry.

Stored credentials:
- client_id / client_secret: from Autodesk Developer Portal, manual entry
- access_token / refresh_token: auto-populated after authorization
- token_expires_at: computed from Autodesk's response
"""

from __future__ import annotations

import frappe
import requests
from datetime import datetime, timedelta
from urllib.parse import urlencode


AUTODESK_AUTH_URL = "https://developer.api.autodesk.com/authentication/v2/authorize"
AUTODESK_TOKEN_URL = "https://developer.api.autodesk.com/authentication/v2/token"

# Refresh when token is this close to expiry (seconds)
REFRESH_WINDOW_SEC = 60


def get_access_token() -> str:
    """Return a valid bearer token for Fusion Manage API calls.

    Transparently refreshes if the stored token is near expiry. Raises
    if there's no token at all (integration not yet authorized).
    """
    settings = frappe.get_single("LCS Fusion Manage Settings")
    if not settings.access_token:
        raise FusionAuthError("Fusion Manage is not authorized yet. Visit the settings page and click Connect.")

    expires_at = settings.token_expires_at
    if expires_at:
        if isinstance(expires_at, str):
            expires_at = datetime.fromisoformat(expires_at)
        if expires_at > datetime.now() + timedelta(seconds=REFRESH_WINDOW_SEC):
            return settings.get_password("access_token")

    # Token expired or near expiry — refresh
    _refresh_tokens(settings)
    settings.reload()
    return settings.get_password("access_token")


def _refresh_tokens(settings) -> None:
    """Exchange refresh_token for a new access_token+refresh_token pair."""
    if not settings.refresh_token:
        raise FusionAuthError("No refresh_token stored. Re-authorize the integration.")

    data = {
        "grant_type": "refresh_token",
        "refresh_token": settings.get_password("refresh_token"),
        "client_id": settings.client_id,
    }
    auth = (settings.client_id, settings.get_password("client_secret")) if settings.client_secret else None
    r = requests.post(AUTODESK_TOKEN_URL, data=data, auth=auth, timeout=15)
    if r.status_code >= 400:
        _record_error(settings, f"Refresh failed: HTTP {r.status_code} {r.text[:200]}")
        raise FusionAuthError(f"Token refresh failed: {r.status_code}")
    payload = r.json()
    _store_tokens(settings, payload)


def build_authorize_url(state: str = "") -> str:
    """Return the URL a user should visit to authorize this integration."""
    settings = frappe.get_single("LCS Fusion Manage Settings")
    if not settings.client_id:
        raise FusionAuthError("client_id not configured in settings")
    params = {
        "response_type": "code",
        "client_id": settings.client_id,
        "redirect_uri": settings.redirect_uri,
        "scope": settings.scopes or "data:read",
        "state": state or frappe.generate_hash(length=16),
    }
    return f"{AUTODESK_AUTH_URL}?{urlencode(params)}"


@frappe.whitelist()
def start_oauth() -> dict:
    """Return the URL the admin UI should open in a new tab."""
    frappe.only_for("System Manager")
    return {"url": build_authorize_url()}


@frappe.whitelist(allow_guest=True)
def oauth_callback(code: str = None, state: str = None, error: str = None):
    """Autodesk redirects the user back here with a ?code=… query param.

    Whitelisted allow_guest because Autodesk is the caller; we check the
    session user has permission below before persisting tokens.
    """
    if error:
        frappe.respond_as_web_page(
            "Fusion Manage Authorization Failed",
            f"Autodesk returned an error: {error}",
            indicator_color="red",
        )
        return
    if not code:
        frappe.respond_as_web_page(
            "Fusion Manage Authorization Failed",
            "No authorization code was returned by Autodesk.",
            indicator_color="red",
        )
        return

    # Only an authenticated System Manager can complete the flow
    if frappe.session.user == "Guest" or "System Manager" not in frappe.get_roles(frappe.session.user):
        frappe.respond_as_web_page(
            "Unauthorized",
            "You must be signed in as System Manager to connect Fusion Manage.",
            indicator_color="red",
        )
        return

    settings = frappe.get_single("LCS Fusion Manage Settings")
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": settings.redirect_uri,
        "client_id": settings.client_id,
    }
    auth = (settings.client_id, settings.get_password("client_secret")) if settings.client_secret else None
    r = requests.post(AUTODESK_TOKEN_URL, data=data, auth=auth, timeout=15)
    if r.status_code >= 400:
        _record_error(settings, f"Authorize failed: HTTP {r.status_code} {r.text[:200]}")
        frappe.respond_as_web_page(
            "Fusion Manage Authorization Failed",
            f"Token exchange failed: HTTP {r.status_code}",
            indicator_color="red",
        )
        return

    _store_tokens(settings, r.json())
    frappe.respond_as_web_page(
        "Fusion Manage Connected",
        "The integration is now authorized. You can close this tab and return to the settings page.",
        indicator_color="green",
    )


def _store_tokens(settings, payload: dict) -> None:
    """Persist the token bundle Autodesk returned."""
    expires_in = int(payload.get("expires_in", 3600))
    settings.access_token = payload["access_token"]
    if payload.get("refresh_token"):
        settings.refresh_token = payload["refresh_token"]
    settings.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
    settings.last_token_refresh = datetime.now()
    settings.last_sync_error = None
    settings.save(ignore_permissions=True)
    frappe.db.commit()


def _record_error(settings, message: str) -> None:
    settings.last_sync_error = message
    try:
        settings.save(ignore_permissions=True)
        frappe.db.commit()
    except Exception:
        pass
    frappe.log_error(message, "fusion_manage.auth")


class FusionAuthError(Exception):
    """Raised when we can't obtain a usable access token."""
    pass


@frappe.whitelist()
def connection_status() -> dict:
    """For the settings page to display current state."""
    frappe.only_for("System Manager")
    settings = frappe.get_single("LCS Fusion Manage Settings")
    now = datetime.now()
    expires = settings.token_expires_at
    if isinstance(expires, str):
        try:
            expires = datetime.fromisoformat(expires)
        except ValueError:
            expires = None
    state = "disconnected"
    if settings.access_token and expires:
        if expires > now:
            state = "connected"
        else:
            state = "expired"
    return {
        "state": state,
        "tenant": settings.tenant,
        "expires_at": str(expires) if expires else None,
        "last_refresh": str(settings.last_token_refresh) if settings.last_token_refresh else None,
        "last_error": settings.last_sync_error,
    }
