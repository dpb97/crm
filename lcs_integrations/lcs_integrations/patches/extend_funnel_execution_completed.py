"""Extend the Projekt funnel group with Ausführung + Abgeschlossen.

The BPF ended at Auftrag (Won); projects in Execution/Completed collapsed onto
the last stage. Add the two final stages so the flow reads Auftrag -> Ausführung
-> Abgeschlossen (mapping to the LCS Project phases Execution / Completed).
Idempotent: skips stages that already exist.
"""

import frappe

NEW = [
	{
		"stage": "Ausführung", "entity_group": "Projekt", "funnel_index": 8,
		"description": "Projekt in Ausführung — Umsetzung läuft (ERPNext-Projekt).",
		"criteria": "Projekt gestartet\nMontageteam eingeplant",
		"fields_to_fill": "expected_start_date",
	},
	{
		"stage": "Abgeschlossen", "entity_group": "Projekt", "funnel_index": 9,
		"description": "Projekt abgeschlossen — Abnahme erfolgt.",
		"criteria": "Abnahme erfolgt\nSchlussrechnung gestellt",
		"fields_to_fill": "",
	},
]


def execute():
	if not frappe.db.exists("DocType", "LCS Funnel Phase"):
		return
	for p in NEW:
		if frappe.db.exists("LCS Funnel Phase", p["stage"]):
			continue
		frappe.new_doc("LCS Funnel Phase").update(p).insert(ignore_permissions=True)
	frappe.clear_cache()
	frappe.db.commit()
