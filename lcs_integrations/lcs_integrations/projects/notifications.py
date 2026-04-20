import frappe
from frappe import _


def on_project_phase_change(doc, method=None):
    """Send notification when project phase changes."""
    if doc.has_value_changed("phase"):
        old_phase = (
            doc.get_doc_before_save().phase if doc.get_doc_before_save() else None
        )
        frappe.publish_realtime(
            "lcs_project_phase_change",
            {
                "project": doc.name,
                "project_name": doc.project_name,
                "old_phase": old_phase,
                "new_phase": doc.phase,
            },
        )
        # Email notification to salesperson
        if doc.salesperson:
            frappe.sendmail(
                recipients=[doc.salesperson],
                subject=_("Project {0}: Phase changed to {1}").format(
                    doc.project_name, doc.phase
                ),
                message=_(
                    "The project {0} ({1}) has moved from {2} to {3}."
                ).format(
                    doc.project_name,
                    doc.project_number,
                    old_phase or "New",
                    doc.phase,
                ),
            )


def on_high_probability(doc, method=None):
    """Notify when opportunity score exceeds 75%."""
    if doc.total_score and doc.total_score > 75:
        old_doc = doc.get_doc_before_save()
        if old_doc and (old_doc.total_score or 0) <= 75:
            managers = frappe.get_all(
                "Has Role", filters={"role": "Sales Manager"}, pluck="parent"
            )
            if managers:
                frappe.sendmail(
                    recipients=managers,
                    subject=_("High-probability opportunity: {0}").format(
                        doc.project
                    ),
                    message=_(
                        "The opportunity score for {0} has exceeded 75% (now {1}%)."
                    ).format(doc.project, round(doc.total_score, 1)),
                )
