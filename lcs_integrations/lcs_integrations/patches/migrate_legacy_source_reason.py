"""
Migration for Project.source and Offer.won_lost_reason to linked master data.

Runs after seed_lookup_data — renames any legacy Select values to matching
CRM Lead Source / CRM Lost Reason records. Also copies the old free-text
won_lost_reason into the new lost_reason field when status='Rejected'.

Idempotent.
"""

import frappe


def execute():
    # Source values already match seed_lookup_data entries, so the Select→Link
    # migration only needs to ensure the value exists as a record. Frappe's
    # own DocType migration already handles the column type.
    migrate_source()
    migrate_lost_reason()


def migrate_source():
    """If an LCS Project has an old Select value like 'Direct' and the CRM
    Lead Source doesn't contain a record named 'Direct', create it so the
    Link field validates."""
    projects = frappe.get_all("LCS Project", fields=["name", "source"], filters={"source": ["is", "set"]})
    for p in projects:
        if p.source and not frappe.db.exists("CRM Lead Source", p.source):
            try:
                doc = frappe.new_doc("CRM Lead Source")
                doc.source_name = p.source
                doc.insert(ignore_permissions=True, ignore_if_duplicate=True)
            except Exception as e:
                frappe.log_error(f"Could not create CRM Lead Source '{p.source}': {e}")
    frappe.db.commit()


def migrate_lost_reason():
    """Old schema had a single `won_lost_reason` Small Text field. Copy its
    value into the new `lost_reason` Link field when status='Rejected',
    creating the CRM Lost Reason record if it's missing."""
    # Only run if old column still exists — Frappe migrate drops it otherwise.
    # Check via the ORM-safe meta lookup rather than swallowing SQL errors
    # (previously this hid every DB-layer failure, not just "column gone").
    if not _has_column("tabLCS Offer", "won_lost_reason"):
        return

    try:
        offers = frappe.db.sql(
            """SELECT name, status, won_lost_reason
               FROM `tabLCS Offer`
               WHERE won_lost_reason IS NOT NULL AND won_lost_reason != ''""",
            as_dict=True,
        )
    except Exception as e:
        # Column existed per the meta check but query still failed — this is
        # a real error the operator needs to see.
        frappe.log_error(
            f"Unexpected error reading legacy won_lost_reason column: {e}",
            "migrate_legacy_source_reason",
        )
        return

    for o in offers:
        if o.status != "Rejected":
            continue
        reason_text = (o.won_lost_reason or "").strip()
        if not reason_text:
            continue
        # Create master record if missing
        if not frappe.db.exists("CRM Lost Reason", reason_text):
            try:
                doc = frappe.new_doc("CRM Lost Reason")
                doc.lost_reason = reason_text
                doc.insert(ignore_permissions=True, ignore_if_duplicate=True)
            except Exception as e:
                # Surface the per-row failure so partial migration is visible
                frappe.log_error(
                    f"Could not create CRM Lost Reason '{reason_text}' for offer {o.name}: {e}",
                    "migrate_legacy_source_reason",
                )
                continue
        frappe.db.set_value("LCS Offer", o.name, "lost_reason", reason_text)
    frappe.db.commit()


def _has_column(table: str, column: str) -> bool:
    """True if the given column currently exists on the given table.
    Uses information_schema so we don't rely on catching SQL errors."""
    rows = frappe.db.sql(
        """SELECT 1 FROM information_schema.columns
           WHERE table_schema = DATABASE()
             AND table_name = %s AND column_name = %s LIMIT 1""",
        (table, column),
    )
    return bool(rows)
