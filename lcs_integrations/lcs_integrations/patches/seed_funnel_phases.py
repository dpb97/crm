"""Seed the editable funnel phase definitions with the defaults that were
previously hardcoded in FunnelFlowBar.vue. Idempotent: existing phases are
never overwritten so manager edits survive migrations."""

from __future__ import annotations

import frappe

PHASES = [
    {
        "stage": "Neu",
        "entity_group": "Lead",
        "funnel_index": 0,
        "description": "Neuer Interessent — noch nicht kontaktiert. Quelle erfassen und Verantwortlichen zuordnen.",
        "criteria": "Quelle hinterlegt\nVerantwortlicher gesetzt",
        "fields_to_fill": "source\nlead_owner\nsales_manager",
    },
    {
        "stage": "Kontaktiert",
        "entity_group": "Lead",
        "funnel_index": 1,
        "description": "Erstkontakt erfolgt. Ansprechpartner und Bedarf klären.",
        "criteria": "Ansprechpartner bekannt\nBedarf grob erfasst",
        "fields_to_fill": "email\nmobile_no",
    },
    {
        "stage": "Qualifiziert",
        "entity_group": "Lead",
        "funnel_index": 2,
        "description": "Bedarf und Budgetrahmen bestätigt — Übergang ins Angebot.",
        "criteria": "Budgetrahmen bekannt\nZeitrahmen geklärt\nEntscheidungsebene identifiziert",
        "fields_to_fill": "territory\nannual_revenue\nexpected_start_date",
    },
    {
        "stage": "Budget",
        "entity_group": "Angebot",
        "funnel_index": 3,
        "description": "Budgetschätzung erstellt — grobe Hausnummer für den Kunden.",
        "criteria": "Budgetschätzung dokumentiert",
        "fields_to_fill": "annual_revenue\nprobability\nestimated_value",
    },
    {
        "stage": "Richtpreis",
        "entity_group": "Angebot",
        "funnel_index": 4,
        "description": "Interner Richtpreis kalkuliert.",
        "criteria": "Richtpreis hinterlegt",
        "fields_to_fill": "probability\nclose_date\nestimated_value",
    },
    {
        "stage": "Angebot",
        "entity_group": "Angebot",
        "funnel_index": 5,
        "description": "Verbindliches Angebot gelegt — Status und Gültigkeitsdatum gesetzt.",
        "criteria": "Angebot erstellt\nGültig-bis gesetzt\nDokumente angehängt",
        "fields_to_fill": "close_date\nprobability\nexpected_close_date\nestimated_value",
    },
    {
        "stage": "Verhandlung",
        "entity_group": "Angebot",
        "funnel_index": 6,
        "description": "Angebot in Verhandlung — Konditionen und Liefertermin final klären.",
        "criteria": "Verhandlungspunkte erfasst",
        "fields_to_fill": "probability\nclose_date\nexpected_close_date",
    },
    {
        "stage": "Auftrag",
        "entity_group": "Projekt",
        "funnel_index": 7,
        "description": "Gewonnen — wird zum laufenden Projekt (Ausführung in ERPNext).",
        "criteria": "Angebot akzeptiert\nProjekt angelegt",
        "fields_to_fill": "expected_start_date\nestimated_value",
    },
]


def execute() -> None:
    if not frappe.db.exists("DocType", "LCS Funnel Phase"):
        return
    created = 0
    for p in PHASES:
        if frappe.db.exists("LCS Funnel Phase", p["stage"]):
            continue
        doc = frappe.new_doc("LCS Funnel Phase")
        doc.update(p)
        doc.insert(ignore_permissions=True)
        created += 1
    if created:
        print(f"seed_funnel_phases: created {created} phase(s)")
    frappe.db.commit()
