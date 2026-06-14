"""Seed der Pilanda-Vertriebs-/Projektierungs-Rollen — Phase 1.6 (Grundgeruest).

Domaenen-Rollen aus 02 §6.5: Verkaeufer, Projektant, Vertriebsleitung,
Technik-Stammdaten. PM nutzt die bestehende ERPNext-Rolle "Projects Manager".
Detaillierte Objekt-Rechte werden je Objekt/Workflow (Phase 3-6) gesetzt; hier nur
die Rollen selbst (Grundgeruest). Idempotent.

Aufruf:  bench --site <site> execute pilanda_sales.seed.roles.seed_roles
"""

from __future__ import annotations

import frappe

# Rolle -> kurze Zweckbeschreibung (Rechte-Matrix s. Entwicklungsplan §1.6)
ROLES = {
    "Verkäufer": "CRM, Lastenheft, Vorauswahl, Kalkulation, Angebot",
    "Projektant": "Anlagenkonfiguration + Technik-Freigabe (Submit)",
    "Vertriebsleitung": "Freigabe verbindlicher Angebote ab Schwelle (E-19)",
    "Technik-Stammdaten": "Pflege Artikel/Seil-Matrix/Maschinen-Konfigs/Feldkatalog",
}


def seed_roles() -> None:
    """Idempotent: legt fehlende Domaenen-Rollen an (desk_access)."""
    created = []
    for role in ROLES:
        if not frappe.db.exists("Role", role):
            frappe.get_doc({
                "doctype": "Role",
                "role_name": role,
                "desk_access": 1,
            }).insert()
            created.append(role)
    frappe.db.commit()
    print(f"Rollen angelegt: {created or '(alle bereits vorhanden)'}")
