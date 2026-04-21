"""
Service layer for Fusion Manage integration.

Pulls item metadata for linked LCS Projects on a schedule (hourly) and
caches it on the project record so the UI doesn't need to hit Fusion
on every render.
"""

import frappe
from lcs_integrations.fusion_manage.client import FusionManageClient


def sync_linked_projects():
    """Scheduled hourly — refresh metadata for every project with a Fusion item link."""
    if not frappe.db.exists("DocType", "LCS Fusion Manage Settings"):
        return
    settings = frappe.get_single("LCS Fusion Manage Settings")
    if not settings.enabled:
        return

    projects = frappe.get_all(
        "LCS Project",
        filters={"fusion_item_id": ["is", "set"]},
        fields=["name", "fusion_workspace", "fusion_item_id"],
    )
    if not projects:
        return

    client = FusionManageClient()
    for p in projects:
        try:
            item = client.get_item(p.fusion_workspace, p.fusion_item_id)
            frappe.db.set_value("LCS Project", p.name, {
                "fusion_item_number": item.get("number") or item.get("itemNumber"),
                "fusion_item_description": item.get("description"),
                "fusion_item_state": item.get("currentState") or item.get("state"),
                "fusion_last_sync": frappe.utils.now_datetime(),
            })
        except Exception as e:
            frappe.log_error(f"Fusion sync failed for {p.name}: {e}", "fusion_manage.sync")
    frappe.db.commit()


@frappe.whitelist()
def search_items(query: str, workspace: str = None):
    """Endpoint for frontend autocomplete when linking a project to a PLM item."""
    settings = frappe.get_single("LCS Fusion Manage Settings")
    ws = workspace or settings.default_workspace
    if not ws:
        return []
    client = FusionManageClient()
    return client.search_items(ws, query)


@frappe.whitelist()
def get_deep_link(workspace: str, item_id: str) -> str:
    client = FusionManageClient()
    return client.deep_link(workspace, item_id)
