"""
Autodesk Fusion Manage (PLM 360) REST client.

Fusion Manage uses v3 REST APIs under {tenant}.autodeskplm360.net/api/rest/v3.
Auth: OAuth2 bearer token (managed via Frappe Single DocType below).

Scope of this client for Phase-1:
- Read workspace item by ID  (for deep-link verification + status pull)
- Read BOM for an item        (pull item list into quotations later)
- Search items by number       (autocomplete on project form)

Write APIs (create items, push change orders) intentionally left for a
later phase — LCS workflow currently drives PLM manually.
"""

from __future__ import annotations

import frappe
import requests


class FusionManageClient:
    def __init__(self):
        settings = frappe.get_single("LCS Fusion Manage Settings")
        self.tenant = settings.tenant
        self.token = settings.get_password("access_token") if settings.access_token else None
        self.base_url = f"https://{self.tenant}.autodeskplm360.net/api/rest/v3"

    @property
    def _headers(self):
        if not self.token:
            raise ValueError("Fusion Manage access_token not configured")
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json",
        }

    def get_item(self, workspace_id: str, item_id: str) -> dict:
        url = f"{self.base_url}/workspaces/{workspace_id}/items/{item_id}"
        r = requests.get(url, headers=self._headers, timeout=15)
        r.raise_for_status()
        return r.json()

    def search_items(self, workspace_id: str, query: str, limit: int = 20) -> list[dict]:
        url = f"{self.base_url}/workspaces/{workspace_id}/items"
        r = requests.get(
            url,
            headers=self._headers,
            params={"search": query, "limit": limit},
            timeout=15,
        )
        r.raise_for_status()
        payload = r.json()
        return payload.get("items", [])

    def get_bom(self, workspace_id: str, item_id: str) -> list[dict]:
        url = f"{self.base_url}/workspaces/{workspace_id}/items/{item_id}/bom"
        r = requests.get(url, headers=self._headers, timeout=30)
        r.raise_for_status()
        return r.json().get("rows", [])

    def deep_link(self, workspace_id: str, item_id: str) -> str:
        """URL a user can open in the browser to view the item in Fusion Manage."""
        return f"https://{self.tenant}.autodeskplm360.net/plm/workspaces/{workspace_id}/items/{item_id}"
