"""Migrate legacy LCS Project.phase values to the CRM 12.05.2026
pipeline vocabulary.

  Inquiry  -> Qualified
  Order    -> Won
  others   -> unchanged

Idempotent: only rows still carrying a legacy value are rewritten.
"""

from __future__ import annotations

import frappe


PHASE_MAP: dict[str, str] = {
    "Inquiry": "Qualified",
    "Order": "Won",
}


def execute() -> None:
    for old, new in PHASE_MAP.items():
        if not frappe.db.has_column("LCS Project", "phase"):
            return
        affected = frappe.db.sql(
            """
            UPDATE `tabLCS Project`
            SET    phase = %s
            WHERE  phase = %s
            """,
            (new, old),
        )
        if affected:
            print(f"migrate_project_phase: {old} -> {new} on {affected} row(s)")
    frappe.db.commit()
