"""CRM-Domaene von pilanda_sales — Verknuepfung Project ↔ CRM Deal.

Project-Objekt-SSOT: die `crm_deal`-Verknuepfung gehoert der CRM-Domaene
(pilanda_sales · CRM, Owner Dominik) und ist bewusst NICHT in
pilanda_sales/custom_fields.py definiert (ein Eigentuemer je Feld).

Abgrenzung zu `lcs_integrations` (CRM-Fork-App): dort leben die Felder an
den CRM-DocTypes (`lcs_project`, `lcs_offer`, `sales_manager`, `lcs_score`,
`erpnext_customer`). HIER lebt nur die Gegenrichtung am ERPNext-`Project`:
welcher CRM Deal hat dieses Projekt gewonnen. Namespace `custom_sales_`.

Die crm-App ist optional (required_apps = erpnext + pilanda_theme) — auf
Sites ohne Frappe CRM wird das Feld uebersprungen, nicht angelegt.

Idempotent via `after_migrate` (hooks.py).
"""

from __future__ import annotations

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

CRM_CUSTOM_FIELDS = {
    "Project": [
        {
            "fieldname": "custom_sales_crm_deal",
            "label": "CRM Deal",
            "fieldtype": "Link",
            "options": "CRM Deal",
            "insert_after": "custom_sales_customer_short",
            "description": (
                "Gewinnender CRM Deal (Frappe CRM), aus dem dieses Projekt "
                "entstanden ist. Gesetzt von der Lead→Deal→Project-Pipeline."
            ),
        },
    ],
}


def ensure_crm_custom_fields() -> None:
    """Idempotent: legt das crm_deal-Feld an, sofern Frappe CRM installiert ist."""
    if not frappe.db.exists("DocType", "CRM Deal"):
        return
    create_custom_fields(CRM_CUSTOM_FIELDS, ignore_validate=True)
