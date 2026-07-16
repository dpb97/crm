import frappe
from frappe import _

from lcs_integrations.teams import notifications as teams_notifications


def on_project_phase_change(doc, method=None):
    """Send notifications when project phase changes (email + Teams).

    Initial inserts are skipped — `has_value_changed` returns True against
    the empty default at insert time, which would otherwise spam every
    new project as a phase-change event.
    """
    before = doc.get_doc_before_save()
    if before is None:
        return  # initial insert — no real phase change yet
    if not doc.has_value_changed("phase"):
        return

    old_phase = before.phase

    frappe.publish_realtime(
        "lcs_project_phase_change",
        {
            "project": doc.name,
            "project_name": doc.project_name,
            "old_phase": old_phase,
            "new_phase": doc.phase,
        },
    )

    # Email notification to salesperson — best-effort, do not block the save
    # if the bench has no outgoing email account configured.
    if doc.salesperson:
        try:
            frappe.sendmail(
                recipients=[doc.salesperson],
                subject=_("Project {0}: Phase changed to {1}").format(
                    doc.project_name, doc.phase
                ),
                message=_("The project {0} ({1}) has moved from {2} to {3}.").format(
                    doc.project_name,
                    doc.project_number,
                    old_phase or "New",
                    doc.phase,
                ),
                delayed=True,
            )
        except Exception as exc:  # noqa: BLE001 — best-effort
            frappe.log_error(title="phase_change_email", message=str(exc))

    # Teams notification (best-effort)
    try:
        teams_notifications.notify_phase_change(doc, old_phase=old_phase, new_phase=doc.phase)
    except Exception as exc:  # noqa: BLE001 — best-effort
        frappe.log_error(title="teams_notifications.notify_phase_change", message=str(exc))


def on_high_probability(doc, method=None):
    """Notify when opportunity score exceeds the configured threshold."""
    settings = frappe.get_cached_doc("LCS Outlook Sync Settings")
    threshold = float(settings.high_probability_threshold or 75)

    score = doc.total_score or 0
    if score <= threshold:
        return

    old_doc = doc.get_doc_before_save()
    if old_doc and (old_doc.total_score or 0) > threshold:
        return  # already notified on a previous save

    # Email — best-effort, do not block save when no outgoing account exists
    managers = frappe.get_all(
        "Has Role", filters={"role": "Sales Manager"}, pluck="parent"
    )
    if managers:
        try:
            frappe.sendmail(
                recipients=managers,
                subject=_("High-probability opportunity: {0}").format(doc.project),
                message=_(
                    "The opportunity score for {0} has exceeded {1}% (now {2}%)."
                ).format(doc.project, round(threshold, 1), round(score, 1)),
                delayed=True,
            )
        except Exception as exc:  # noqa: BLE001 — best-effort
            frappe.log_error(title="high_probability_email", message=str(exc))

    # Teams (best-effort)
    try:
        teams_notifications.notify_high_probability(doc, score=score)
    except Exception as exc:  # noqa: BLE001 — best-effort
        frappe.log_error(title="teams_notifications.notify_high_probability", message=str(exc))
