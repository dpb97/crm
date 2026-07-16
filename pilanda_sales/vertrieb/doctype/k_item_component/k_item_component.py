"""K Item Component — Baugruppen-Zeile eines K-Artikels (Child Table).

Referenziert per Dynamic Link entweder ein echtes `Item` oder ein anderes `K Item`.
"""

from __future__ import annotations

from frappe.model.document import Document


class KItemComponent(Document):
    pass
