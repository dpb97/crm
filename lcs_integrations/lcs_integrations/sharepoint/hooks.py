"""Auto-create a SharePoint upload FOLDER per LCS Project.

Creates a folder '<project number> <name>' in the target site's default document
library and stores its URL on the project (lcs_sharepoint_url). Runs on project
creation AND on every update (idempotent — it only acts while the project has no
folder yet, so it also covers phase changes). FAIL-SAFE: never blocks/breaks a
save, and is a complete no-op until activated.

ACTIVATION:
  1. Grant the Entra app the Graph permission Sites.ReadWrite.All (admin consent).
  2. Set site_config `lcs_sharepoint_site` to the target site, e.g.
     "lcscable.sharepoint.com:/sites/<Site>"  (or its full https URL).
"""

from __future__ import annotations

import frappe


def _site() -> str:
    return (frappe.conf.get("lcs_sharepoint_site") or "").strip()


def _enqueue(project: str) -> None:
    if not _site():
        return
    frappe.enqueue(
        "lcs_integrations.sharepoint.hooks.ensure_project_folder",
        queue="short",
        project=project,
        enqueue_after_commit=True,
    )


def on_project_after_insert(doc, method=None) -> None:
    _enqueue(doc.name)


def on_project_on_update(doc, method=None) -> None:
    # Ensure the folder exists on any change (covers "also on phase change").
    if not doc.get("lcs_sharepoint_url"):
        _enqueue(doc.name)


def ensure_project_folder(project: str) -> None:
    """Create the project's upload folder in the SharePoint document library and
    store its URL on the project. Idempotent and fail-safe."""
    try:
        site = _site()
        if not site:
            return
        doc = frappe.db.get_value(
            "LCS Project", project,
            ["name", "project_number", "project_name", "lcs_sharepoint_url"],
            as_dict=True,
        )
        if not doc or doc.lcs_sharepoint_url:
            return
        from lcs_integrations.outlook_sync.graph_client import GraphClient

        gc = GraphClient()
        try:
            sid = gc.site_id(site)
            if not sid:
                return
            drive_id = gc.default_drive_id(sid)
            if not drive_id:
                return
            name = f"{doc.project_number or ''} {doc.project_name or ''}".strip() or doc.name
            item = gc.ensure_folder(drive_id, name)
            url = item.get("webUrl")
            if url:
                frappe.db.set_value("LCS Project", project, "lcs_sharepoint_url", url, update_modified=False)
                frappe.db.commit()
        finally:
            gc.close()
    except Exception as e:  # noqa: BLE001 — SharePoint must never break a save
        frappe.log_error(f"SharePoint folder for {project}: {e}", "sharepoint")
