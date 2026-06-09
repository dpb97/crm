"""Whitelisted API for the Teams activity widget.

Returns project-level Teams metadata (link, team-id, channel-id) plus the
list of channels the project's team carries, so the UI can render a
direct-jump panel without scraping the project doc.
"""

from __future__ import annotations

from typing import Any

import frappe

from lcs_integrations.outlook_sync.graph_client import GraphClient, GraphClientError


@frappe.whitelist()
def get_project_teams_info(project: str) -> dict[str, Any]:
    """Aggregate Teams info for one LCS Project.

    Channels are read from Microsoft Graph live so the UI always shows
    what actually exists on the team — including channels that were
    added or renamed outside provisioning.
    """
    if not project:
        frappe.throw("project is required")

    proj = frappe.get_doc("LCS Project", project)
    settings = frappe.get_cached_doc("LCS Outlook Sync Settings")

    info: dict[str, Any] = {
        "project": proj.name,
        "project_name": proj.project_name,
        "team_link": proj.team_link or None,
        "team_id": proj.get("teams_team_id") or None,
        "notifications_channel_id": proj.get("teams_notifications_channel_id") or None,
        "notifications_channel_name": settings.notifications_channel_name or "01-Sales",
        "teams_notifications_enabled": bool(settings.enable_teams_notifications),
        "channels": [],
        "error": None,
    }

    if not info["team_id"]:
        return info

    try:
        client = GraphClient()
        try:
            channels = client.team_channels_list(info["team_id"])
        finally:
            client.close()
    except GraphClientError as exc:
        info["error"] = str(exc)
        return info

    for ch in channels:
        info["channels"].append(
            {
                "id": ch.get("id"),
                "name": ch.get("displayName"),
                "description": ch.get("description"),
                "web_url": ch.get("webUrl"),
            }
        )
    return info
