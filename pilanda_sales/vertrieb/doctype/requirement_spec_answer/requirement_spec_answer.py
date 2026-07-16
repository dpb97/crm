"""Requirement Spec Answer — eine Antwort im Lastenheft (Child Table).

value als Text (JSON-faehig fuer multi/array; radio->String, bool->'1'/'0').
"""

from __future__ import annotations

from frappe.model.document import Document


class RequirementSpecAnswer(Document):
    pass
