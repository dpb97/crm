"""Controller for the Lead Scoring Rule DocType."""

from __future__ import annotations

from frappe.model.document import Document


class LeadScoringRule(Document):
    def validate(self) -> None:
        # Normalise operator casing for the engine.
        if self.operator:
            self.operator = self.operator.lower().strip()
