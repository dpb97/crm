"""K Item (K-Artikel) — Kalkulationsartikel mit eigenen Regeln (E-22/E-17).

Nicht dispofaehig (kein Einkauf/keine Fertigung). K-Nummer via naming_series.
Preis ergibt sich aus Baugruppen (Item/K Item) + Zuschlaegen. Kann spaeter in den
echten Artikelstamm zurueckgeschrieben werden (`target_item`).
"""

from __future__ import annotations

from frappe.model.document import Document


class KItem(Document):
    pass
