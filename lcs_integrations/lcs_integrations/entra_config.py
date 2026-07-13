"""Single source for the Entra/Graph credentials.

Reads from the OS environment first (12-factor / .env), then falls back to
Frappe's site config (`site_config.json` → frappe.conf). The site-config
fallback lets the credentials survive a plain `bench start` without any
`.env` sourcing — the standard Frappe place for secrets.

site_config keys (lowercase): entra_tenant_id, entra_client_id,
entra_client_secret.
"""

from __future__ import annotations

import os

import frappe

REQUIRED = ("ENTRA_TENANT_ID", "ENTRA_CLIENT_ID", "ENTRA_CLIENT_SECRET")


def entra(key: str, default: str | None = None) -> str | None:
    """Entra credential from env (preferred) or site config."""
    val = os.environ.get(key)
    if val:
        return val
    try:
        val = frappe.conf.get(key.lower())
    except Exception:  # noqa: BLE001 — no request context / conf missing
        val = None
    return val if val else default


def missing_keys() -> list[str]:
    """Which required Entra credentials are not configured (env or conf)."""
    return [k for k in REQUIRED if not entra(k)]
