"""Project Variant (Projektvariante) — eine angebotene Anlagen-Alternative je Projekt.

Verweist per Link auf das ERPNext-`Project` (SSOT, 02 §2.2). Eine Variante =
eine Kran-/Payload-Alternative (Prototyp: calc.units "Line 1/2").
"""

from __future__ import annotations

from frappe.model.document import Document


class ProjectVariant(Document):
    pass
