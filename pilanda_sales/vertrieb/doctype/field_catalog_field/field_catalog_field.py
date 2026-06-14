"""Field Catalog Field — eine Felddefinition im Feldkatalog (02 §2.4, Dossier 10).

Companion-Mechanik (exklusiv): `other` (zusaetzliche Radio-Option "Other:" + Freitext)
ODER `specify` (Freitext aktiv wenn Wert == Trigger, Default "Yes"). Companions werden
disabled, nicht versteckt.
"""

from __future__ import annotations

from frappe.model.document import Document


class FieldCatalogField(Document):
    pass
