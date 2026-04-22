"""
Autodesk Fusion Manage (PLM 360) REST v3 client.

All write operations are intentionally omitted until the bi-directional
sync design is approved — the client is read-only by contract.

Authentication is delegated to `fusion_manage.auth.get_access_token()`
which transparently refreshes when needed.

Results from single-item reads are cached in Redis for 60 seconds so
repeated UI queries (e.g. opening the same project twice) don't hit
Autodesk every time.
"""

from __future__ import annotations

import frappe
import requests
import json
from functools import lru_cache

from lcs_integrations.fusion_manage.auth import get_access_token


DEFAULT_BASE_URL_TEMPLATE = "https://{tenant}.autodeskplm360.net/api/rest/v3"

REDIS_CACHE_NAMESPACE = "fusion_manage"
ITEM_CACHE_TTL_SEC = 60
WORKSPACE_CACHE_TTL_SEC = 300


class FusionManageClient:
    """Stateless wrapper around the Fusion Manage v3 REST API."""

    def __init__(self):
        settings = frappe.get_single("LCS Fusion Manage Settings")
        self.settings = settings
        self.tenant = settings.tenant or ""
        override = getattr(settings, "api_base_url_override", None)
        self.base_url = (override or DEFAULT_BASE_URL_TEMPLATE.format(tenant=self.tenant)).rstrip("/")

    # ---- internal helpers ----

    def _headers(self) -> dict:
        token = get_access_token()
        return {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def _get(self, path: str, params: dict | None = None, timeout: int = 15) -> dict:
        url = f"{self.base_url}{path}"
        r = requests.get(url, headers=self._headers(), params=params or {}, timeout=timeout)
        if r.status_code == 401:
            # Expired / revoked — force a refresh + retry once
            frappe.cache().hdel(REDIS_CACHE_NAMESPACE, f"token-failed")
            r = requests.get(url, headers=self._headers(), params=params or {}, timeout=timeout)
        r.raise_for_status()
        return r.json() if r.text else {}

    # ---- workspace ----

    def list_workspaces(self) -> list[dict]:
        cached = frappe.cache().hget(REDIS_CACHE_NAMESPACE, "workspaces")
        if cached:
            return cached
        payload = self._get("/workspaces")
        workspaces = payload.get("items", payload) if isinstance(payload, dict) else payload
        # Keep the shape predictable for the frontend
        normalized = [
            {
                "id": w.get("id") or w.get("urn") or w.get("workspaceId"),
                "name": w.get("name") or w.get("title"),
                "type": w.get("type") or w.get("workspaceType"),
            }
            for w in workspaces or []
        ]
        frappe.cache().hset(REDIS_CACHE_NAMESPACE, "workspaces", normalized)
        frappe.cache().expire(REDIS_CACHE_NAMESPACE, WORKSPACE_CACHE_TTL_SEC)
        return normalized

    # ---- items ----

    def search_items(self, workspace_id: str, query: str, limit: int = 20) -> list[dict]:
        payload = self._get(
            f"/workspaces/{workspace_id}/items",
            params={"search": query, "limit": limit},
        )
        items = payload.get("items", payload) if isinstance(payload, dict) else payload
        return [
            {
                "id": i.get("id") or i.get("urn"),
                "number": i.get("number") or i.get("itemNumber"),
                "description": i.get("description") or i.get("title"),
                "state": i.get("currentState") or i.get("state"),
            }
            for i in items or []
        ]

    def get_item(self, workspace_id: str, item_id: str, use_cache: bool = True) -> dict:
        key = f"item:{workspace_id}:{item_id}"
        if use_cache:
            cached = frappe.cache().hget(REDIS_CACHE_NAMESPACE, key)
            if cached:
                return cached
        payload = self._get(f"/workspaces/{workspace_id}/items/{item_id}")
        frappe.cache().hset(REDIS_CACHE_NAMESPACE, key, payload)
        frappe.cache().expire(REDIS_CACHE_NAMESPACE, ITEM_CACHE_TTL_SEC)
        return payload

    # ---- BOM ----

    def get_bom(self, workspace_id: str, item_id: str, depth: int = 3) -> list[dict]:
        """Return flat BOM rows. Fusion returns one row per immediate child;
        we recursively expand up to `depth` levels so the UI can render a
        tree without N round-trips.
        """
        rows = self._get_bom_level(workspace_id, item_id)
        if depth > 1:
            for row in rows:
                child_id = row.get("child_id")
                if child_id:
                    row["children"] = self.get_bom(workspace_id, child_id, depth - 1)
                else:
                    row["children"] = []
        return rows

    def _get_bom_level(self, workspace_id: str, item_id: str) -> list[dict]:
        try:
            payload = self._get(f"/workspaces/{workspace_id}/items/{item_id}/bom")
        except requests.HTTPError as e:
            if e.response is not None and e.response.status_code == 404:
                return []
            raise
        rows = payload.get("rows", payload) if isinstance(payload, dict) else payload
        return [
            {
                "child_id": r.get("childId") or r.get("id"),
                "child_number": r.get("childNumber") or r.get("number"),
                "child_name": r.get("childName") or r.get("description"),
                "quantity": r.get("quantity") or r.get("qty") or 1,
                "unit": r.get("unit") or r.get("uom"),
                "state": r.get("state") or r.get("currentState"),
            }
            for r in rows or []
        ]

    # ---- URLs ----

    def deep_link(self, workspace_id: str, item_id: str) -> str:
        """URL a user can open in the browser to view the item in Fusion Manage."""
        if not self.tenant:
            return ""
        return f"https://{self.tenant}.autodeskplm360.net/plm/workspaces/{workspace_id}/items/{item_id}"
