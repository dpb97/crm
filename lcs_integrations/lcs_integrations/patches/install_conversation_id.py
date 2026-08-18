"""Store the Graph conversationId on synced mail so the reader can group an
exact conversation thread (even when the subject changes). Idempotent."""

from __future__ import annotations

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    create_custom_fields({
        "Communication": [
            {
                "fieldname": "lcs_conversation_id",
                "label": "Conversation ID (Graph)",
                "fieldtype": "Data",
                "read_only": 1,
                "no_copy": 1,
                "insert_after": "message_id",
            },
        ],
    }, update=True)
    frappe.db.add_index("Communication", ["lcs_conversation_id"])
