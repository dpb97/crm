"""Ensure the environment's default admin user holds full rights.

Some environments (dev benches, fresh installs) run under a single "default"
user that must not be blocked by the LCS Access Profile / visibility layer.
That user is named by an environment variable so it stays configurable per
deployment instead of being hard-coded:

    env  LCS_DEFAULT_ADMIN   (preferred, 12-factor / .env)
    conf lcs_default_admin   (site_config.json fallback — same pattern as the
                              Entra credentials in entra_config.py)

The role granted is ``System Manager`` — Frappe's superuser role, which also
bypasses the whole LCS visibility service (see visibility/service.py), i.e.
"all rights".

This runs on every ``bench migrate`` (after_migrate hook), so it is idempotent
and a newly configured value takes effect on the next migrate. When nothing is
configured it is a no-op, so production stays untouched unless an operator
opts in.
"""

from __future__ import annotations

import os

import frappe

ENV_KEY = "LCS_DEFAULT_ADMIN"
CONF_KEY = "lcs_default_admin"
ALL_RIGHTS_ROLE = "System Manager"


def _default_admin() -> str | None:
    """The configured default-admin user — env first, then site config."""
    val = os.environ.get(ENV_KEY)
    if not val:
        try:
            val = frappe.conf.get(CONF_KEY)
        except Exception:  # noqa: BLE001 — conf may be unavailable in some contexts
            val = None
    return (val or "").strip() or None


def ensure_default_admin() -> None:
    """Grant System Manager to the configured default-admin user (idempotent)."""
    user = _default_admin()
    if not user:
        return

    if not frappe.db.exists("User", user):
        frappe.logger("lcs").warning(
            f"LCS default admin '{user}' is configured but no such User exists — skipping."
        )
        return

    if ALL_RIGHTS_ROLE in frappe.get_roles(user):
        return

    doc = frappe.get_doc("User", user)
    doc.add_roles(ALL_RIGHTS_ROLE)  # idempotent — never duplicates the role row
    frappe.logger("lcs").info(
        f"Granted '{ALL_RIGHTS_ROLE}' to LCS default admin '{user}'."
    )
