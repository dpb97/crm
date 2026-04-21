"""
LMS Training compliance checker for project team members.

For each team member on an LCS Project, verifies that all required
trainings (required_trainings child table) have a valid LMS Course
enrollment / completion linked to the member's HRMS Employee.

Runs when the team table changes and updates training_status per row.
"""

from datetime import date
from dateutil.relativedelta import relativedelta

import frappe


def on_project_validate(doc, method=None):
    """Re-evaluate every team member's training_status when the doc saves."""
    if not doc.team_members or not doc.required_trainings:
        return
    if not frappe.db.exists("DocType", "LMS Course"):
        return
    if not frappe.db.exists("DocType", "LMS Batch Enrollment") and not frappe.db.exists("DocType", "LMS Enrollment"):
        return

    required_courses = [(r.course, r.is_mandatory, r.validity_months) for r in doc.required_trainings if r.course]
    if not required_courses:
        return

    today = date.today()
    for member in doc.team_members:
        if not member.employee:
            member.training_status = "Unknown"
            continue
        user = frappe.db.get_value("Employee", member.employee, "user_id")
        if not user:
            member.training_status = "Unknown"
            continue

        member.training_status = _evaluate_member(user, required_courses, today)


def _evaluate_member(user, required_courses, today):
    """Return one of Compliant / Missing Certifications / Expiring Soon."""
    expiring_soon = False
    missing = False

    enrollment_doctype = "LMS Enrollment" if frappe.db.exists("DocType", "LMS Enrollment") else "LMS Batch Enrollment"

    for course, is_mandatory, validity_months in required_courses:
        enrollment = frappe.db.get_value(
            enrollment_doctype,
            {"member": user, "course": course, "progress": 100},
            ["modified"],
            as_dict=True,
        )
        if not enrollment:
            # Try non-progress-based membership
            enrollment = frappe.db.get_value(
                enrollment_doctype,
                {"member": user, "course": course},
                ["modified"],
                as_dict=True,
            )
        if not enrollment:
            if is_mandatory:
                missing = True
            continue

        # Check expiry
        if validity_months and enrollment.modified:
            expires = enrollment.modified.date() + relativedelta(months=validity_months)
            if expires < today:
                if is_mandatory:
                    missing = True
            elif (expires - today).days < 30:
                expiring_soon = True

    if missing:
        return "Missing Certifications"
    if expiring_soon:
        return "Expiring Soon"
    return "Compliant"


@frappe.whitelist()
def get_training_summary(project):
    """Dashboard endpoint: return compliance counts for a project."""
    doc = frappe.get_doc("LCS Project", project)
    summary = {"Compliant": 0, "Missing Certifications": 0, "Expiring Soon": 0, "Unknown": 0, "total": 0}
    for m in doc.team_members or []:
        summary[m.training_status or "Unknown"] += 1
        summary["total"] += 1
    return summary
