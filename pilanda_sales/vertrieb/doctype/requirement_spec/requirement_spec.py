"""Requirement Spec (Lastenheft) — Questionnaire-Instanz je Projekt (02 §3.1).

Antworten zum Feldkatalog + Ableitung ins ERPNext-Project. Ableitungsregel
(Prototyp _derive_header_from_questionnaire, Dossier 10 §4): **leere Werte
ueberschreiben nie** — nur nicht-leere Antworten werden uebernommen.
"""

from __future__ import annotations

import frappe
from frappe.model.document import Document

# Antwort-Feld-ID -> Ziel-Feld am Project (nur einfache Header-Ableitungen).
# Kran-Ableitungen (payload/horizontal_length -> Project Variant) folgen mit der
# Varianten-Auswahl (spaeter); Customer (Link) wird manuell gesetzt.
PROJECT_TEXT_MAP = {
    "project_name": "project_name",
    "company": "custom_sales_customer_short",
    "location": "custom_sales_site_location",
}


class RequirementSpec(Document):
    def get_answer(self, field_id: str) -> str:
        for row in self.answers:
            if row.field_id == field_id:
                return (row.value or "").strip()
        return ""

    @frappe.whitelist()
    def derive_to_project(self) -> list[str]:
        """Uebertraegt nicht-leere Antworten ins Project. Gibt geaenderte Felder zurueck."""
        if not self.project:
            frappe.throw("Kein Project verknuepft.")
        proj = frappe.get_doc("Project", self.project)
        changed: list[str] = []

        for fid, target in PROJECT_TEXT_MAP.items():
            val = self.get_answer(fid)
            if val:  # leer ueberschreibt nie
                if (proj.get(target) or "") != val:
                    proj.set(target, val)
                    changed.append(target)

        dm = self.get_answer("duration_months")
        if dm:
            try:
                months = int(float(dm))
                if proj.get("custom_sales_duration_months") != months:
                    proj.custom_sales_duration_months = months
                    changed.append("custom_sales_duration_months")
            except ValueError:
                pass

        if changed:
            proj.save()
        return changed
