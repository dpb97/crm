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
    # Only run if old column still exists — Frappe migrate drops it otherwise
    try:
        offers = frappe.db.sql(
            """SELECT name, status, won_lost_reason
               FROM `tabLCS Offer`
               WHERE won_lost_reason IS NOT NULL AND won_lost_reason != ''""",
            as_dict=True,
        )
    except Exception:
        return  # Column already gone — nothing to migrate

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
            except Exception:
                continue
        frappe.db.set_value("LCS Offer", o.name, "lost_reason", reason_text)
    frappe.db.commit()
