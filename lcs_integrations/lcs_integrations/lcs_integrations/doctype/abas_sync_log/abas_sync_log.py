"""Controller for the ABAS Sync Log DocType.

Append-only audit trail. Writing is restricted to the `abas` service layer —
the controller rejects direct UI edits.
"""

from __future__ import annotations

import frappe
from frappe.model.document import Document


class ABASSyncLog(Document):
    def before_insert(self) -> None:
        # Truncate huge payloads so one bad request does not blow up the table.
        for field in ("request_payload", "response_payload", "error_message"):
            value = self.get(field)
            if value and len(value) > 64 * 1024:
                self.set(field, value[: 64 * 1024] + "\n…[truncated]")

    def on_update(self) -> None:  # pragma: no cover — guard only
        if not frappe.flags.in_abas_sync:
            frappe.throw("ABAS Sync Log records are append-only.")
