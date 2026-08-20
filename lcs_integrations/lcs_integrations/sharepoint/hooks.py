"""Auto-create a SharePoint page per LCS Project (for file upload).

Runs on project creation AND on every update (idempotent — it only acts while
the project has no page yet, so it also covers phase changes). FAIL-SAFE: it
never blocks or breaks a project save, and is a complete no-op until activated.

ACTIVATION (both are the customer's / admin's job — the CRM cannot do them):
  1. Grant the Entra app 'LCS CRM Integration' the Graph permission
     Sites.ReadWrite.All  with admin consent.
  2. Set site_config `lcs_sharepoint_site` to the target site, e.g.
     "lcs-group.sharepoint.com:/sites/Projekte"  (or its full https URL).

The page-creation Graph call (graph_client.create_page) still needs one
validation pass against the real tenant once activated.
"""

from __future__ import annotations

import frappe


def _site() -> str:
    return (frappe.conf.get("lcs_sharepoint_site") or "").strip()


def _enqueue(project: str) -> None:
    if not _site():
        return
    frappe.enqueue(
        "lcs_integrations.sharepoint.hooks.ensure_project_page",
        queue="short",
        project=project,
        enqueue_after_commit=True,
    )


def on_project_after_insert(doc, method=None) -> None:
    _enqueue(doc.name)


def on_project_on_update(doc, method=None) -> None:
    # Ensure the page exists on any change (covers "also on phase change").
    if not doc.get("lcs_sharepoint_url"):
        _enqueue(doc.name)


def ensure_project_page(project: str) -> None:
    """Create + publish the project's SharePoint page and store its URL. Idempotent
    and fail-safe."""
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
            title = f"{doc.project_number or ''} {doc.project_name or ''}".strip() or doc.name
            page = gc.create_page(sid, doc.project_number or doc.name, title)
            url = page.get("webUrl")
            if url:
                frappe.db.set_value("LCS Project", project, "lcs_sharepoint_url", url, update_modified=False)
                frappe.db.commit()
        finally:
            gc.close()
    except Exception as e:  # noqa: BLE001 — SharePoint must never break a save
        frappe.log_error(f"SharePoint page for {project}: {e}", "sharepoint")
