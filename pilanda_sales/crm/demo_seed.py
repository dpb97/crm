"""LCS-Erweiterung des CRM-Demo-Seeds (Marco 20.07.2026).

Dominiks Seed (crm.demo.api.create_demo_data — 12 Leads, 7 Deals mit
deal_value, Activities/Notes/Tasks/Call-Logs) wird ausgeführt, falls noch
nicht geschehen, und um die LCS-Dimension erweitert, damit alle Flächen
(Kanban-Summen, Umsatztrend, Prognose, Projektkarte, Marktaufteilung,
Vertriebsprojekte, Gantt) echte Daten zeigen:

  1. Die aus ERPNext migrierten Bestands-Deals (Opportunity-Übernahme
     16.07., deal_value=0) werden angereichert — Seilkran-Größenordnungen
     (0,4–14 M€), Wahrscheinlichkeiten, gestreute Abschlusstermine
     (−3 … +9 Monate), Territorium/Land. NUR leere/0-Felder werden
     gesetzt (idempotent, keine echten Eingaben überschrieben).
  2. Drei zusätzliche große Anlagenbau-Verkaufschancen (neue Firmen),
     damit in Summe deutlich >10 Projekte verschiedener Größe entstehen
     (der lcs_integrations-Hook erzeugt je Deal das LCS Project).

Lauf:  bench --site lcs.local execute pilanda_sales.crm.demo_seed.execute
"""

from datetime import timedelta

import frappe
from frappe.utils import nowdate, add_days

STATE_KEY = "lcs_sales_demo_extension"

# Anreicherung der Migrations-Deals: (wert €, wahrscheinlichkeit %,
# tage_bis_abschluss, territorium, land) — Reihenfolge = creation asc.
_ENRICH = [
    (2_400_000, 65, 120, "Österreich", "Austria"),
    (14_000_000, 40, 270, "Schweiz", "Switzerland"),
    (850_000, 80, 45, "Norwegen", "Norway"),
    (5_600_000, 55, 180, "Chile", "Chile"),
    (420_000, 90, 21, "Österreich", "Austria"),
    (7_800_000, 35, 240, "Nepal", "Nepal"),
    (1_950_000, 70, 90, "Kanada", "Canada"),
    (3_300_000, 50, 150, "Italien", "Italy"),
]

# Zusätzliche Anlagenbau-Deals (Firma, wert, wahrscheinlichkeit, tage, land).
_EXTRA = [
    ("Verbund Hydro Power", 9_500_000, 45, 210, "Austria"),
    ("Statkraft Fjellanlegg", 6_200_000, 60, 160, "Norway"),
    ("Andritz Alpine Projects", 1_150_000, 75, 60, "Switzerland"),
]


def _first_open_status() -> str:
    row = frappe.get_all(
        "CRM Deal Status", filters={"type": ["not in", ["Won", "Lost"]]},
        fields=["name"], order_by="position asc", limit=1,
    )
    return row[0].name if row else frappe.db.get_value("CRM Deal Status", {}, "name")


def _territory(name: str) -> str | None:
    return name if frappe.db.exists("CRM Territory", name) else None


def execute() -> dict:
    stats = {"dominik_seed": "übersprungen", "angereichert": 0, "neu": 0, "fehler": []}

    # 1. Dominiks Seed (einmalig; eigener State-Key in crm.demo.api).
    if not frappe.db.get_default("crm_demo_data_created"):
        from crm.demo.api import create_demo_data

        create_demo_data()
        stats["dominik_seed"] = "ausgeführt"

    # 2. Migrations-Deals anreichern (nur leere Felder, idempotent).
    migrated = frappe.get_all(
        "CRM Deal",
        filters={"deal_value": ["in", [0, None]]},
        fields=["name"], order_by="creation asc", limit_page_length=0,
    )
    for i, row in enumerate(migrated):
        if i >= len(_ENRICH):
            break
        wert, prob, tage, terr, land = _ENRICH[i]
        try:
            doc = frappe.get_doc("CRM Deal", row.name)
            if not doc.deal_value:
                doc.deal_value = wert
            if not doc.get("expected_deal_value"):
                doc.expected_deal_value = round(wert * prob / 100)
            if not doc.probability:
                doc.probability = prob
            if not doc.get("expected_closure_date"):
                doc.expected_closure_date = add_days(nowdate(), tage)
            if not doc.get("territory") and _territory(terr):
                doc.territory = terr
            if not doc.get("country"):
                doc.country = land
            doc.save(ignore_permissions=True)
            stats["angereichert"] += 1
        except Exception as e:
            stats["fehler"].append(f"{row.name}: {e}")

    # 3. Zusätzliche große Anlagenbau-Deals (einmalig über State-Key).
    if not frappe.db.get_default(STATE_KEY):
        status = _first_open_status()
        for firma, wert, prob, tage, land in _EXTRA:
            try:
                if not frappe.db.exists("CRM Organization", firma):
                    org = frappe.new_doc("CRM Organization")
                    org.organization_name = firma
                    org.insert(ignore_permissions=True)
                deal = frappe.new_doc("CRM Deal")
                deal.organization = firma
                deal.status = status
                deal.deal_value = wert
                deal.expected_deal_value = round(wert * prob / 100)
                deal.probability = prob
                deal.expected_closure_date = add_days(nowdate(), tage)
                deal.country = land
                deal.insert(ignore_permissions=True)
                stats["neu"] += 1
            except Exception as e:
                stats["fehler"].append(f"{firma}: {e}")
        frappe.db.set_default(STATE_KEY, "1")

    frappe.db.commit()
    print("LCS_DEMO_SEED:", stats)
    return stats
