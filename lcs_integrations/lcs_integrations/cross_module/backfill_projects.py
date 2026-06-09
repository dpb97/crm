"""
Back-fill LCS Projects from existing BSM Projects.

Historically the automation only flows CRM → BSM (a new Sales Order
spawns a BSM Project). That leaves all the construction sites that
already existed before the CRM rollout invisible to Sales, Forecasting,
and the access-profile view.

This module creates an LCS Project for every BSM Project that doesn't
already have one linked, and wires the back-links both ways so the
UI's integration panel picks them up.

Usage:
    # Dry-run — report what would happen without writing anything
    bench --site lcs.local execute lcs_integrations.cross_module.backfill_projects.run \\
        --kwargs '{"dry_run": true}'

    # Commit the back-fill
    bench --site lcs.local execute lcs_integrations.cross_module.backfill_projects.run

    # Only active projects (skip Completed/Cancelled)
    bench --site lcs.local execute lcs_integrations.cross_module.backfill_projects.run \\
        --kwargs '{"only_active": true}'
"""

import frappe
import re


@frappe.whitelist()
def api_backfill(dry_run: bool = False, only_active: bool = True) -> dict:
    """Whitelisted wrapper so admins can trigger back-fill from the SPA
    without SSH access. Only System Manager + Sales Manager allowed."""
    frappe.only_for(["System Manager", "Sales Manager"])
    # Coerce string params from HTTP form data
    if isinstance(dry_run, str):
        dry_run = dry_run.lower() in ("1", "true", "yes")
    if isinstance(only_active, str):
        only_active = only_active.lower() in ("1", "true", "yes")
    return run(dry_run=dry_run, only_active=only_active)


# Map BSM project-name prefixes to the LCS project_type taxonomy.
# Prefix check is case-insensitive; extend this list as LCS introduces
# new product lines.
PREFIX_TO_TYPE = [
    (re.compile(r"^SB[-_]", re.I), "SB"),    # Seilbahn
    (re.compile(r"^WI[-_]", re.I), "WI"),    # Winde
    (re.compile(r"^LL[-_]", re.I), "LL"),    # Liftanlage
    (re.compile(r"^SK[-_]", re.I), "SK"),    # Sonderkonstruktion
    (re.compile(r"^AS[-_]", re.I), "SK"),    # Aftersales → special
]


def run(dry_run: bool = False, only_active: bool = False) -> dict:
    """Create an LCS Project for every unlinked BSM Project.

    Returns a summary of what happened:
      { created: int, skipped: int, already_linked: int, errors: int, projects: [ ... ] }
    """
    if not frappe.db.exists("DocType", "BSM Project"):
        return {"error": "BSM Project DocType not installed"}

    filters = {}
    if only_active:
        filters["status"] = "Active"

    bsm_projects = frappe.get_all(
        "BSM Project",
        filters=filters,
        fields=[
            "name", "project_name", "project_code", "status", "customer",
            "start_date", "end_date", "location_name", "external_id",
        ],
    )

    summary = {
        "created": 0,
        "skipped": 0,
        "already_linked": 0,
        "errors": 0,
        "dry_run": bool(dry_run),
        "projects": [],
    }

    for bsm in bsm_projects:
        # Already linked? Skip.
        existing = frappe.db.get_value("LCS Project", {"bsm_project": bsm.name}, "name")
        if existing:
            summary["already_linked"] += 1
            continue

        try:
            report = _backfill_one(bsm, dry_run=dry_run)
            summary["projects"].append(report)
            if report["action"] == "created":
                summary["created"] += 1
            elif report["action"] == "skipped":
                summary["skipped"] += 1
        except Exception as e:
            summary["errors"] += 1
            summary["projects"].append({"bsm": bsm.name, "action": "error", "reason": str(e)})
            frappe.log_error(f"Back-fill failed for {bsm.name}: {e}", "backfill_projects")

    if not dry_run:
        frappe.db.commit()

    _print_summary(summary)
    return summary


def _backfill_one(bsm: dict, dry_run: bool) -> dict:
    """Create one LCS Project from a BSM Project row. Returns a report dict."""
    project_name = bsm.project_name or bsm.name
    project_type = _infer_type(project_name)
    organization = _ensure_organization(bsm.customer, dry_run=dry_run)
    country = _map_country(bsm.location_name)

    phase = _status_to_phase(bsm.status)
    status = _bsm_status_to_lcs_status(bsm.status)

    report = {
        "bsm": bsm.name,
        "bsm_name": project_name,
        "project_type": project_type,
        "organization": organization,
        "country": country,
        "phase": phase,
        "status": status,
    }

    if dry_run:
        report["action"] = "would-create"
        return report

    # Create the LCS Project
    doc = frappe.new_doc("LCS Project")
    doc.project_name = project_name
    doc.project_type = project_type
    doc.phase = phase
    doc.status = status
    if organization:
        doc.organization = organization
    if country:
        doc.country = country
    if bsm.start_date:
        doc.expected_close_date = bsm.end_date or bsm.start_date
    # Store BSM code as the project_abbr for quick reference
    if bsm.project_code:
        # project_abbr is Data(5) — truncate safely
        doc.project_abbr = str(bsm.project_code)[:5]
    # Keep a breadcrumb in notes that this project came from BSM so
    # future back-fills and audits can trace the origin.
    doc.notes = _origin_note(bsm)
    # Note: we link to BSM BEFORE insert to bypass the bsm_sync hook which
    # would otherwise try to create a new BSM Project for us.
    doc.bsm_project = bsm.name
    doc.insert(ignore_permissions=True)

    # Write back the lcs_project link on the BSM Project
    # (custom field was installed by patches/v1_0/install_custom_fields.py)
    _has_cf = frappe.db.get_value("Custom Field", {"dt": "BSM Project", "fieldname": "lcs_project"})
    if _has_cf:
        frappe.db.set_value("BSM Project", bsm.name, "lcs_project", doc.name, update_modified=False)

    # Mirror the most recent files attached to the BSM Project onto the
    # LCS Project so sales can see the contract, offer PDF, plans, etc.
    # without jumping between apps.
    files_copied = _copy_attachments(bsm.name, doc.name)
    report["files_copied"] = files_copied

    report["action"] = "created"
    report["lcs_project"] = doc.name
    return report


def _origin_note(bsm: dict) -> str:
    """Seed the notes field with where the project came from."""
    lines = [f"[Imported from BSM Project {bsm.name}]"]
    if bsm.customer:
        lines.append(f"Customer: {bsm.customer}")
    if bsm.location_name:
        lines.append(f"Location: {bsm.location_name}")
    if bsm.start_date:
        lines.append(f"Started: {bsm.start_date}")
    if bsm.end_date:
        lines.append(f"Planned end: {bsm.end_date}")
    if bsm.project_code:
        lines.append(f"BSM project code: {bsm.project_code}")
    return "\n".join(lines)


def _copy_attachments(bsm_name: str, lcs_name: str) -> int:
    """Duplicate the File rows attached to the BSM Project onto the LCS Project.

    We copy the metadata (same file_url, is_private, folder) — not the
    bytes — so attachments show up on both records without doubling
    storage. Limited to the 20 most recent files.
    """
    files = frappe.get_all(
        "File",
        filters={"attached_to_doctype": "BSM Project", "attached_to_name": bsm_name},
        fields=["name", "file_url", "file_name", "is_private", "folder"],
        order_by="creation desc",
        limit=20,
    )
    count = 0
    for f in files:
        try:
            new_file = frappe.new_doc("File")
            new_file.file_url = f.file_url
            new_file.file_name = f.file_name
            new_file.is_private = f.is_private
            new_file.folder = f.folder
            new_file.attached_to_doctype = "LCS Project"
            new_file.attached_to_name = lcs_name
            new_file.insert(ignore_permissions=True)
            count += 1
        except Exception as e:
            frappe.log_error(
                f"Could not mirror file {f.name} to {lcs_name}: {e}",
                "backfill_projects.attach",
            )
    return count


def _infer_type(project_name: str) -> str:
    """Map BSM project name prefix to LCS project_type."""
    if not project_name:
        return "Other"
    for pattern, t in PREFIX_TO_TYPE:
        if pattern.match(project_name):
            return t
    return "Other"


def _status_to_phase(bsm_status: str) -> str:
    """Active construction → Execution. Completed → Completed. Everything else → Execution."""
    if (bsm_status or "").lower() == "completed":
        return "Completed"
    return "Execution"


def _bsm_status_to_lcs_status(bsm_status: str) -> str:
    mapping = {
        "Active": "Active",
        "Completed": "Completed",
        "On Hold": "On Hold",
        "Cancelled": "Cancelled",
    }
    return mapping.get(bsm_status, "Active")


def _ensure_organization(customer_name: str, dry_run: bool) -> str | None:
    """Make sure a CRM Organization exists matching the BSM customer name."""
    if not customer_name:
        return None
    if frappe.db.exists("CRM Organization", customer_name):
        return customer_name
    if dry_run:
        return customer_name  # report what we would use
    org = frappe.new_doc("CRM Organization")
    org.organization_name = customer_name
    org.insert(ignore_permissions=True)
    return org.name


def _map_country(location_name: str) -> str | None:
    """Try to map BSM location string to a valid Country record."""
    if not location_name:
        return None
    # Direct match
    if frappe.db.exists("Country", location_name):
        return location_name
    # Common aliases — extend as needed
    aliases = {
        "deutschland": "Germany",
        "österreich": "Austria",
        "schweiz": "Switzerland",
        "italien": "Italy",
        "frankreich": "France",
        "spanien": "Spain",
        "china": "China",
        "japan": "Japan",
        "usa": "United States",
        "canada": "Canada",
        "worldwide": None,
    }
    normalized = location_name.strip().lower()
    if normalized in aliases:
        mapped = aliases[normalized]
        if mapped and frappe.db.exists("Country", mapped):
            return mapped
    return None


def _print_summary(summary: dict) -> None:
    prefix = "[DRY-RUN] " if summary["dry_run"] else ""
    print(f"\n{prefix}=== Back-fill summary ===")
    print(f"  Created:        {summary['created']}")
    print(f"  Already linked: {summary['already_linked']}")
    print(f"  Skipped:        {summary['skipped']}")
    print(f"  Errors:         {summary['errors']}")
    print()

    for p in summary["projects"][:40]:
        action = p.get("action", "?")
        if action in ("created", "would-create"):
            marker = "+" if action == "created" else "?"
            # Guard Nones before format — organization/country may be missing
            name = (p.get("bsm_name") or "?")[:38]
            ptype = p.get("project_type") or "?"
            org = (p.get("organization") or "-")[:35]
            country = p.get("country") or "-"
            print(f"  [{marker}] {name:<40}  {ptype:<5}  {org:<36}  {country}")
        elif action == "error":
            print(f"  [!] {p.get('bsm', '?')} — {p.get('reason', '')}")
