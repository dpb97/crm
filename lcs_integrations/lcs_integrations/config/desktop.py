"""Workspace / menu configuration for the LCS Integrations app.

Kept minimal: integrations are configured from a single settings page. Marketing
and Campaign menus from the upstream CRM are hidden via `hidden_modules`.
"""

from __future__ import annotations


def get_data() -> list[dict]:
    return [
        {
            "module_name": "LCS Integrations",
            "category": "Modules",
            "label": "LCS Integrations",
            "icon": "octicon octicon-plug",
            "type": "module",
            "description": "abas ERP, Proxess DMS, Outlook sync and lead scoring.",
        },
    ]
