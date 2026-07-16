"""Field Catalog (Feldkatalog) — versionierter Katalog-Kopf (02 §2.4, E-16).

Eine Quelle fuer Portal-Wizard UND ausfuellbares PDF (gleiche Feld-IDs). Lebt als
Datensaetze in der DB (kein JS/Excel eingebunden). Sprache kundenseitig immer EN (E-12).
"""

from __future__ import annotations

from frappe.model.document import Document


class FieldCatalog(Document):
    pass
