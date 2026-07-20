"""Rueckbau der abgeloesten Desk-Page `sales-dashboard` (Marco 20.07.2026).

Das Vertrieb-Modul-Dashboard von Anfang Juli wurde durch das EINE
Vertriebs-Dashboard der CRM-SPA (/crm/dashboard, Menuepunkt "Dashboard")
abgeloest; die Quelldateien sind aus dem Repo entfernt. Dieser Patch
raeumt den zugehoerigen Page-Datensatz aus der Datenbank, damit
/app/sales-dashboard sauber "nicht gefunden" liefert statt einer
Seitenleiche. Idempotent.
"""

import frappe


def execute():
    if frappe.db.exists("Page", "sales-dashboard"):
        frappe.delete_doc("Page", "sales-dashboard", force=True, ignore_missing=True)
