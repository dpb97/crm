"""Delete existing internal->internal e-mails that are not shared.

Per the user: mail from @lcs-group.com to @lcs-group.com must never appear
unless a project number/name is in the subject or crm@lcs-group.com is in the
CC. Those relevant ones carry lcs_shared=1 and are KEPT; the rest (lcs_internal=1
AND lcs_shared=0) are pure internal noise and are removed, together with their
timeline links. New such mail is already dropped at import (delta_service).

Idempotent — after the first run nothing matches (the import filter keeps it out).

Caveat: CC was not stored on older imports, so an old internal mail that ONLY
CC'd crm@lcs-group.com (never in To) cannot be told apart from noise and is
removed too. New mail records the CC and is kept correctly.
"""

from __future__ import annotations

import frappe

BATCH = 1000


def execute():
    if not frappe.db.has_column("Communication", "lcs_internal"):
        return
    names = frappe.get_all(
        "Communication",
        filters={"communication_medium": "Email", "lcs_internal": 1, "lcs_shared": 0},
        pluck="name",
    )
    if not names:
        return

    for i in range(0, len(names), BATCH):
        batch = names[i : i + BATCH]
        # Timeline links first (Communication is their parent), then the mails.
        frappe.db.delete("Communication Link", {"parent": ["in", batch]})
        frappe.db.delete("Communication", {"name": ["in", batch]})
        frappe.db.commit()

    frappe.logger().info(f"purge_internal_internal_mail: removed {len(names)} internal mails")
