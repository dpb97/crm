"""Territory-based auto-assignment for Lead / Deal / LCS Project.

A document carrying a `country` value is matched against the LCS Sales
Territory child-table `countries`. The first matching territory wins
and its `sales_manager` (or `sales_manager_code` as fallback) is
copied onto the document. Existing manual assignments are never
overwritten.

The Country -> Territory map is cached for the lifetime of the worker;
LCSSalesTerritory.on_update / on_trash invalidate it.
"""

from __future__ import annotations

import json
from typing import Optional

import frappe


CACHE_KEY = "lcs_country_territory_map"


def _get_country_map() -> dict[str, str]:
    """Return {country_name: territory_name}.

    Cached. Built by scanning the `countries` child table of every
    active LCS Sales Territory.
    """
    cached = frappe.cache().get_value(CACHE_KEY)
    if cached:
        try:
            return json.loads(cached)
        except (TypeError, ValueError):
            pass

    rows = frappe.db.sql(
        """
        SELECT child.country, parent.name AS territory
        FROM   `tabLCS Sales Territory Country` child
        JOIN   `tabLCS Sales Territory` parent ON parent.name = child.parent
        WHERE  parent.is_active = 1
        """,
        as_dict=True,
    )
    mapping = {r["country"]: r["territory"] for r in rows}
    frappe.cache().set_value(CACHE_KEY, json.dumps(mapping))
    return mapping


def _territory_for_country(country: Optional[str]) -> Optional[str]:
    if not country:
        return None
    return _get_country_map().get(country)


def _resolve_owner(territory_name: str) -> tuple[Optional[str], Optional[str]]:
    """Return (user_email, code) for the territory's sales manager."""
    if not territory_name:
        return None, None
    row = frappe.db.get_value(
        "LCS Sales Territory",
        territory_name,
        ("sales_manager", "sales_manager_code"),
        as_dict=True,
    )
    if not row:
        return None, None
    return row.get("sales_manager"), row.get("sales_manager_code")


def _apply(doc, country_fieldname: str, sales_manager_field: str) -> None:
    if doc.get(sales_manager_field):
        return  # respect manual assignment
    country = doc.get(country_fieldname)
    if not country:
        return
    territory = _territory_for_country(country)
    if not territory:
        return
    user, _code = _resolve_owner(territory)
    if user:
        doc.set(sales_manager_field, user)


def on_crm_lead_before_insert(doc, method=None):
    _apply(doc, "country", "sales_manager")


def on_crm_deal_before_insert(doc, method=None):
    _apply(doc, "country", "sales_manager")


def on_lcs_project_before_insert(doc, method=None):
    _apply(doc, "country", "sales_manager")
