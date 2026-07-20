"""Demo-Datenwelt-Überführung (Marco-GO 20.07.2026, „Bestandsprojekte
überführen, Demo-Testfirmen überführen").

Zwei idempotente Schritte auf der Dev-Site:

1. firmen(): Dominiks generische Demo-Firmen (Acme, TechStart, …) werden in
   die LCS-Anlagenbau-Welt überführt. CRM Organization wird per rename_doc
   umbenannt (zieht alle Link-Felder mit: CRM Deal.organization,
   LCS Project.organization); CRM Lead.organization ist ein Data-Feld und
   wird explizit nachgezogen. „Test Loyalty Customer" bleibt bewusst
   unangetastet (Spiegel eines ERPNext-Test-Fixtures — Rename würde den
   Ein-Weg-Sync desynchronisieren).

2. projekt_namen(): Bestandsprojekte, deren project_name noch die Deal-ID
   trägt (Fork-Lücke deal_name, s. pilanda_sales/Entwicklungsplan.md),
   bekommen einen sprechenden Namen (Firma + Typ) — und der zugehörige
   CRM Deal erhält denselben Namen in deal_name (Custom Field der
   CRM-Domäne), damit der Bestand am neuen Namensmodell teilnimmt.

Lauf:  bench --site lcs.local execute pilanda_sales.crm.demo_ueberfuehrung.execute
"""

from __future__ import annotations

import frappe

# Generisch → LCS-Anlagenbau-Welt (plausible Energie-/Infrastruktur-Kunden).
FIRMEN_MAPPING = {
    "Acme Corp": "Axpo Hydro Schweiz AG",
    "TechStart Inc": "Tiroler Wasserkraft AG",
    "PivotTech Solutions": "Marti Tunnelbau AG",
    "Meridian Systems": "Implenia Schweiz AG",
    "ScaleUp Labs": "Kraftwerke Oberhasli AG",
    "Vertex Analytics": "Illwerke VKW AG",
    "Forge Digital": "Porr Bau GmbH",
    "Prestiga-Biz": "Webuild S.p.A.",
}

# Sprechende Typ-Bezeichnungen für Projektnamen (Select-Codes aus LCS Project).
_TYP_LABEL = {
    "SB": "Seilbahn",
    "WI": "Winde",
    "LL": "Lastenaufzug",
    "SK": "Seilkran",
    "Other": "Projekt",
}


def firmen() -> dict:
    stats = {"umbenannt": 0, "leads_nachgezogen": 0, "uebersprungen": 0}
    for alt, neu in FIRMEN_MAPPING.items():
        if not frappe.db.exists("CRM Organization", alt):
            stats["uebersprungen"] += 1
            continue
        if frappe.db.exists("CRM Organization", neu):
            frappe.throw(
                f"Ziel-Firma '{neu}' existiert bereits — Mapping prüfen "
                f"(Quelle '{alt}')."
            )
        frappe.rename_doc("CRM Organization", alt, neu)
        if frappe.db.has_column("CRM Organization", "organization_name"):
            frappe.db.set_value("CRM Organization", neu, "organization_name", neu,
                                update_modified=False)
        stats["umbenannt"] += 1
        # CRM Lead.organization ist Data → rename_doc greift nicht.
        leads = frappe.get_all("CRM Lead", filters={"organization": alt}, pluck="name")
        for lead in leads:
            frappe.db.set_value("CRM Lead", lead, "organization", neu,
                                update_modified=False)
        stats["leads_nachgezogen"] += len(leads)
    return stats


def projekt_namen() -> dict:
    stats = {"umbenannt": 0, "deal_name_gesetzt": 0, "ohne_quelle": 0}
    rows = frappe.get_all(
        "LCS Project",
        filters={"project_name": ["like", "CRM-DEAL-%"]},
        fields=["name", "project_name", "organization", "project_type", "deal"],
    )
    for p in rows:
        typ = _TYP_LABEL.get(p.project_type or "", "Projekt")
        if not p.organization:
            stats["ohne_quelle"] += 1
            continue
        sprechend = f"{typ} {p.organization}"
        frappe.db.set_value("LCS Project", p.name, "project_name", sprechend,
                            update_modified=False)
        stats["umbenannt"] += 1
        if p.deal and frappe.db.has_column("CRM Deal", "deal_name"):
            frappe.db.set_value("CRM Deal", p.deal, "deal_name", sprechend,
                                update_modified=False)
            stats["deal_name_gesetzt"] += 1
    return stats


def execute() -> dict:
    out = {"firmen": firmen(), "projekte": projekt_namen()}
    frappe.db.commit()
    print(out)
    return out
