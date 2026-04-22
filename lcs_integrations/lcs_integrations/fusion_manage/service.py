"""
Service layer for Fusion Manage — frontend-facing whitelisted endpoints
+ scheduled pull of linked-project metadata.

All endpoints degrade gracefully when the integration is disabled or
not authorized: they return empty payloads instead of raising, so the
SPA can render a "not connected" state rather than an error.
"""

from __future__ import annotations

import frappe
from datetime import datetime

from lcs_integrations.fusion_manage.client import FusionManageClient
from lcs_integrations.fusion_manage.auth import FusionAuthError


def sync_linked_projects():
    """Scheduler-driven: refresh metadata for every LCS Project that
    has a Fusion item link."""
    if not frappe.db.exists("DocType", "LCS Fusion Manage Settings"):
        return
    settings = frappe.get_single("LCS Fusion Manage Settings")
    if not settings.enabled:
        return

    try:
        client = FusionManageClient()
    except FusionAuthError:
        return  # Not authorized yet; next cron cycle will retry

    projects = frappe.get_all(
        "LCS Project",
        filters={"fusion_item_id": ["is", "set"]},
        fields=["name", "fusion_workspace", "fusion_item_id"],
    )
    if not projects:
        return

    errors = 0
    for p in projects:
        if not p.fusion_workspace:
            continue
        try:
            item = client.get_item(p.fusion_workspace, p.fusion_item_id, use_cache=False)
            frappe.db.set_value("LCS Project", p.name, {
                "fusion_item_number": item.get("number") or item.get("itemNumber"),
                "fusion_item_description": item.get("description") or item.get("title"),
                "fusion_item_state": item.get("currentState") or item.get("state"),
                "fusion_last_sync": frappe.utils.now_datetime(),
            })
        except Exception as e:
            errors += 1
            frappe.log_error(f"Fusion sync failed for {p.name}: {e}", "fusion_manage.sync")

    # Update overall sync health record
    settings.reload()
    if errors == 0:
        settings.last_sync_at = datetime.now()
        settings.last_sync_error = None
    else:
        settings.last_sync_error = f"{errors} projects failed to sync"
    settings.save(ignore_permissions=True)
    frappe.db.commit()


# ---- Whitelisted frontend endpoints ----

@frappe.whitelist()
def list_workspaces() -> list[dict]:
    """Return the tenant's workspaces so the user can pick one."""
    try:
        return FusionManageClient().list_workspaces()
    except FusionAuthError:
        return []
    except Exception as e:
        frappe.log_error(f"list_workspaces failed: {e}", "fusion_manage.api")
        return []


@frappe.whitelist()
def search_items(query: str, workspace: str | None = None) -> list[dict]:
    """Type-ahead for linking a project to a Fusion item."""
    if not query or len(query) < 2:
        return []
    settings = frappe.get_single("LCS Fusion Manage Settings")
    ws = workspace or settings.default_workspace
    if not ws:
        return []
    try:
        return FusionManageClient().search_items(ws, query)
    except FusionAuthError:
        return []
    except Exception as e:
        frappe.log_error(f"search_items failed: {e}", "fusion_manage.api")
        return []


@frappe.whitelist()
def get_bom_tree(project: str) -> dict:
    """Return the BOM for the item linked to the given LCS Project, or an
    empty payload if the project isn't linked."""
    doc = frappe.get_doc("LCS Project", project)
    if not doc.fusion_workspace or not doc.fusion_item_id:
        return {"linked": False, "rows": []}
    try:
        client = FusionManageClient()
        rows = client.get_bom(doc.fusion_workspace, doc.fusion_item_id, depth=3)
        item = client.get_item(doc.fusion_workspace, doc.fusion_item_id)
        return {
            "linked": True,
            "item": {
                "number": item.get("number") or item.get("itemNumber"),
                "description": item.get("description") or item.get("title"),
                "state": item.get("currentState") or item.get("state"),
            },
            "rows": rows,
        }
    except FusionAuthError as e:
        return {"linked": True, "error": str(e), "rows": []}
    except Exception as e:
        frappe.log_error(f"get_bom_tree failed for {project}: {e}", "fusion_manage.api")
        return {"linked": True, "error": "Fusion API call failed", "rows": []}


@frappe.whitelist()
def link_project_to_item(project: str, workspace: str, item_id: str) -> dict:
    """Associate an LCS Project with a Fusion Manage item + fetch initial metadata."""
    if not frappe.db.exists("LCS Project", project):
        frappe.throw(f"LCS Project {project} not found")

    # Populate metadata immediately so the user sees the item number etc. without waiting for the hourly sync
    item = {}
    try:
        item = FusionManageClient().get_item(workspace, item_id)
    except Exception as e:
        frappe.log_error(f"Could not fetch item {item_id} during link: {e}", "fusion_manage.api")

    frappe.db.set_value("LCS Project", project, {
        "fusion_workspace": workspace,
        "fusion_item_id": item_id,
        "fusion_item_number": item.get("number") or item.get("itemNumber"),
        "fusion_item_description": item.get("description") or item.get("title"),
        "fusion_item_state": item.get("currentState") or item.get("state"),
        "fusion_last_sync": frappe.utils.now_datetime(),
    })
    frappe.db.commit()
    return {"ok": True, "item": item}


@frappe.whitelist()
def unlink_project(project: str) -> dict:
    """Remove the Fusion Manage link from a project."""
    frappe.db.set_value("LCS Project", project, {
        "fusion_workspace": None,
        "fusion_item_id": None,
        "fusion_item_number": None,
        "fusion_item_description": None,
        "fusion_item_state": None,
        "fusion_last_sync": None,
    })
    frappe.db.commit()
    return {"ok": True}


@frappe.whitelist()
def get_deep_link(workspace: str, item_id: str) -> str:
    try:
        return FusionManageClient().deep_link(workspace, item_id)
    except FusionAuthError:
        return ""
