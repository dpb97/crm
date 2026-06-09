"""LCS network follow-ups (W-01..W-06).

Built on the stock Frappe ToDo so we inherit list, calendar and
assigned-to-me views for free. The LCS fields (`lcs_kind`,
`lcs_reason`, `lcs_*` notification flags, `lcs_fired_at`) discriminate
follow-ups from generic tasks and drive dispatch.

Sichtbarkeit:
  - Owner (assigned user) sieht eigene Follow-ups vollständig.
  - Manager (User.sales_manager Custom Field, falls vorhanden — sonst
    Role 'Sales Manager') sieht Follow-ups seines Teams, wenn
    `lcs_visible_to_manager=1`. Andere Sales-Kollegen sehen sie nicht.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

import frappe
from frappe import _


QUICK_PRESETS_DAYS: dict[str, int] = {
    "1m": 30,
    "3m": 90,
    "6m": 180,
    "1y": 365,
}


# ---------------------------------------------------------------------------
# API: schedule / reschedule / mark done
# ---------------------------------------------------------------------------

@frappe.whitelist()
def schedule_followup(
    *,
    contact: Optional[str] = None,
    reference_type: Optional[str] = None,
    reference_name: Optional[str] = None,
    preset: Optional[str] = None,
    date: Optional[str] = None,
    reason: Optional[str] = None,
    assigned_to: Optional[str] = None,
    notify_email: int = 1,
    notify_teams: int = 1,
    notify_push: int = 1,
    visible_to_manager: int = 1,
) -> str:
    """Create a new follow-up ToDo. Returns the ToDo name.

    Either `preset` (1m/3m/6m/1y) or explicit `date` must be supplied.
    """
    if preset and preset not in QUICK_PRESETS_DAYS:
        frappe.throw(_("Unknown preset {0}").format(preset))

    if preset:
        due_date = (datetime.now() + timedelta(days=QUICK_PRESETS_DAYS[preset])).date()
    elif date:
        due_date = datetime.fromisoformat(date).date()
    else:
        frappe.throw(_("Either 'preset' or 'date' is required"))

    description_parts: list[str] = []
    if contact:
        description_parts.append(f"Contact: {contact}")
    if reason:
        description_parts.append(reason)
    description = "\n".join(description_parts) or _("Network follow-up")

    todo = frappe.get_doc({
        "doctype": "ToDo",
        "allocated_to": assigned_to or frappe.session.user,
        "description": description,
        "date": due_date,
        "reference_type": reference_type or ("Contact" if contact else None),
        "reference_name": reference_name or contact,
        "priority": "Medium",
        "lcs_kind": "Follow-up",
        "lcs_reason": reason,
        "lcs_visible_to_manager": int(visible_to_manager),
        "lcs_notify_email": int(notify_email),
        "lcs_notify_teams": int(notify_teams),
        "lcs_notify_push": int(notify_push),
    })
    todo.insert(ignore_permissions=False)
    return todo.name


@frappe.whitelist()
def reschedule_followup(name: str, *, preset: Optional[str] = None, date: Optional[str] = None) -> str:
    todo = frappe.get_doc("ToDo", name)
    if preset and preset not in QUICK_PRESETS_DAYS:
        frappe.throw(_("Unknown preset {0}").format(preset))
    if preset:
        todo.date = (datetime.now() + timedelta(days=QUICK_PRESETS_DAYS[preset])).date()
    elif date:
        todo.date = datetime.fromisoformat(date).date()
    else:
        frappe.throw(_("Either 'preset' or 'date' is required"))
    # Clear the dispatched stamp so the scheduler picks it up again.
    todo.lcs_fired_at = None
    todo.status = "Open"
    todo.save()
    return todo.name


@frappe.whitelist()
def complete_followup(name: str, *, next_preset: Optional[str] = None) -> Optional[str]:
    """Mark the current follow-up Closed. If next_preset is given, clone
    it forward at the new due date and return the new ToDo name."""
    todo = frappe.get_doc("ToDo", name)
    todo.status = "Closed"
    todo.save()
    if not next_preset:
        return None
    return schedule_followup(
        contact=todo.reference_name if todo.reference_type == "Contact" else None,
        reference_type=todo.reference_type,
        reference_name=todo.reference_name,
        preset=next_preset,
        reason=todo.lcs_reason,
        assigned_to=todo.allocated_to,
        notify_email=todo.lcs_notify_email,
        notify_teams=todo.lcs_notify_teams,
        notify_push=todo.lcs_notify_push,
        visible_to_manager=todo.lcs_visible_to_manager,
    )


# ---------------------------------------------------------------------------
# Scheduler: dispatch due reminders
# ---------------------------------------------------------------------------

def dispatch_due_reminders() -> None:
    """Run every 15 minutes via hooks.scheduler_events.

    Picks ToDos with kind=Follow-up, status=Open, date<=today, not yet
    dispatched, and fires Email / Teams / Push depending on flags.
    """
    today = frappe.utils.nowdate()
    due = frappe.get_all(
        "ToDo",
        filters={
            "lcs_kind": "Follow-up",
            "status": "Open",
            "date": ["<=", today],
            "lcs_fired_at": ["is", "not set"],
        },
        fields=[
            "name", "allocated_to", "description", "reference_type",
            "reference_name", "lcs_reason", "lcs_notify_email",
            "lcs_notify_teams", "lcs_notify_push",
        ],
        limit=200,
    )
    for row in due:
        try:
            _dispatch_one(row)
            frappe.db.set_value("ToDo", row["name"], "lcs_fired_at", frappe.utils.now())
        except Exception:
            frappe.log_error(
                title=f"LCS follow-up dispatch failed: {row['name']}",
                message=frappe.get_traceback(),
            )
    frappe.db.commit()


def _dispatch_one(row: dict) -> None:
    user = row.get("allocated_to")
    if not user:
        return
    subject = _("LCS Follow-up due")
    body_lines = [
        f"Due: {frappe.utils.nowdate()}",
        f"Reason: {row.get('lcs_reason') or '-'}",
    ]
    if row.get("reference_type") and row.get("reference_name"):
        body_lines.append(f"Reference: {row['reference_type']} {row['reference_name']}")
    body = "\n".join(body_lines)

    if row.get("lcs_notify_email"):
        try:
            frappe.sendmail(recipients=[user], subject=subject, message=body, now=True)
        except Exception:
            frappe.log_error(title="LCS follow-up email failed", message=frappe.get_traceback())

    if row.get("lcs_notify_teams"):
        _post_teams(user=user, subject=subject, body=body)

    if row.get("lcs_notify_push"):
        _push(user=user, subject=subject, body=body)


def _post_teams(*, user: str, subject: str, body: str) -> None:
    """Soft dependency on the teams module. If it isn't wired up yet
    we just skip — no hard error so other channels still fire."""
    try:
        from lcs_integrations.teams import api as teams_api  # type: ignore
    except Exception:
        return
    notify = getattr(teams_api, "notify_user", None)
    if callable(notify):
        notify(user=user, title=subject, text=body)


def _push(*, user: str, subject: str, body: str) -> None:
    """Use Frappe's built-in System Notification so the existing
    mobile-app push channel picks it up. Cheap, always available."""
    try:
        frappe.publish_realtime(
            event="lcs_followup_due",
            message={"subject": subject, "body": body},
            user=user,
        )
    except Exception:
        frappe.log_error(title="LCS follow-up push failed", message=frappe.get_traceback())


# ---------------------------------------------------------------------------
# Permission: limit Follow-up visibility to owner + their sales manager
# ---------------------------------------------------------------------------

def todo_query_conditions(user: Optional[str] = None) -> str:
    """Return a SQL filter for ToDo so that LCS Follow-ups are scoped
    to (a) owner, (b) sales manager of the owner, (c) System Manager."""
    user = user or frappe.session.user
    if "System Manager" in frappe.get_roles(user):
        return ""

    user_esc = frappe.db.escape(user)
    # Subordinates whose `sales_manager` Custom Field on User equals me.
    # Falls back to allocated_to=user when no manager mapping exists.
    return f"""
        (
            `tabToDo`.lcs_kind IS NULL
            OR `tabToDo`.lcs_kind != 'Follow-up'
            OR `tabToDo`.allocated_to = {user_esc}
            OR (
                `tabToDo`.lcs_visible_to_manager = 1
                AND `tabToDo`.allocated_to IN (
                    SELECT name FROM `tabUser`
                    WHERE  sales_manager = {user_esc}
                )
            )
        )
    """
