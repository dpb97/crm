"""Teams channel notifications via Microsoft Graph (Adaptive Cards).

Fired by document hooks on `LCS Project` (phase change) and
`LCS Opportunity Matrix` (high probability). The actual e-mail dispatch
remains in `projects/notifications.py`; this module is the parallel Teams
channel.

Channel resolution:
1. If the project carries `teams_notifications_channel_id`, use that.
2. Otherwise, look up the channel whose `displayName` matches
   `LCS Outlook Sync Settings.notifications_channel_name` (default
   `01-Sales`) on the project's `teams_team_id`, cache the ID on the
   project row, then post.
3. If neither team ID nor channel can be resolved, log and bail — do not
   throw. Notifications are best-effort; failures must not block saves.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import get_url

from lcs_integrations.outlook_sync.graph_client import GraphClient, GraphClientError


def _settings():
    return frappe.get_cached_doc("LCS Outlook Sync Settings")


def _resolve_channel(project_doc) -> tuple[str, str] | None:
    team_id = (project_doc.get("teams_team_id") or "").strip()
    if not team_id:
        return None

    channel_id = (project_doc.get("teams_notifications_channel_id") or "").strip()
    if channel_id:
        return team_id, channel_id

    s = _settings()
    target_name = (s.notifications_channel_name or "01-Sales").strip()

    client = GraphClient()
    try:
        channels = client.team_channels_list(team_id)
    except GraphClientError as exc:
        frappe.log_error(title="teams_notifications", message=f"channel list: {exc}")
        return None
    finally:
        client.close()

    found = next((c for c in channels if (c.get("displayName") or "").strip() == target_name), None)
    if not found:
        return None

    channel_id = found.get("id")
    if not channel_id:
        return None
    frappe.db.set_value(
        "LCS Project", project_doc.name, "teams_notifications_channel_id", channel_id
    )
    return team_id, channel_id


def _post(team_id: str, channel_id: str, *, subject: str, card: dict[str, Any]) -> None:
    s = _settings()
    if not s.enable_teams_notifications:
        return
    client = GraphClient()
    try:
        client.team_channel_post_message(team_id, channel_id, subject=subject, adaptive_card=card)
    except GraphClientError as exc:
        frappe.log_error(title="teams_notifications", message=str(exc))
    finally:
        client.close()


def _project_url(project_name: str) -> str:
    return f"{get_url()}/crm/lcs-projects/{project_name}"


def _adaptive_card(*, title: str, facts: list[tuple[str, str]], action_url: str) -> dict[str, Any]:
    return {
        "type": "AdaptiveCard",
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "version": "1.4",
        "body": [
            {"type": "TextBlock", "size": "Medium", "weight": "Bolder", "text": title},
            {
                "type": "FactSet",
                "facts": [{"title": k, "value": v} for k, v in facts],
            },
        ],
        "actions": [
            {"type": "Action.OpenUrl", "title": "Open in CRM", "url": action_url},
        ],
    }


# ----------------------------------------------------------- Public hooks


def notify_phase_change(project_doc, *, old_phase: str | None, new_phase: str | None) -> None:
    s = _settings()
    if not (s.enable_teams_notifications and s.notify_phase_change):
        return
    target = _resolve_channel(project_doc)
    if not target:
        return
    team_id, channel_id = target

    facts = [
        ("Project", f"{project_doc.project_name} ({project_doc.project_number})"),
        ("From", old_phase or "—"),
        ("To", new_phase or "—"),
    ]
    if project_doc.salesperson:
        facts.append(("Salesperson", project_doc.salesperson))
    card = _adaptive_card(
        title=f"Phase changed: {old_phase or '—'} → {new_phase or '—'}",
        facts=facts,
        action_url=_project_url(project_doc.name),
    )
    _post(team_id, channel_id, subject=f"Phase change: {project_doc.project_name}", card=card)


def notify_high_probability(matrix_doc, *, score: float) -> None:
    s = _settings()
    if not (s.enable_teams_notifications and s.notify_high_probability):
        return
    if not matrix_doc.project:
        return

    project_doc = frappe.get_doc("LCS Project", matrix_doc.project)
    target = _resolve_channel(project_doc)
    if not target:
        return
    team_id, channel_id = target

    facts = [
        ("Project", f"{project_doc.project_name} ({project_doc.project_number})"),
        ("Score", f"{round(score, 1)} %"),
        ("Classification", matrix_doc.classification or "—"),
    ]
    if project_doc.salesperson:
        facts.append(("Salesperson", project_doc.salesperson))
    card = _adaptive_card(
        title=f"High-probability opportunity: {round(score, 1)} %",
        facts=facts,
        action_url=_project_url(project_doc.name),
    )
    _post(team_id, channel_id, subject=f"High-probability: {project_doc.project_name}", card=card)
