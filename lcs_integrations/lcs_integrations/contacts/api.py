"""
Contact phone helper — the CRM's `Contact.mobile_no` is read-only and derived
from the `phone_nos` child table (Contact Phone) on validate, so it cannot be
written directly. This upserts the PRIMARY mobile number into `phone_nos` so a
single-field phone editor (LcsPhoneInput) can persist a number the normal way.

Follows Frappe customisation conventions (see feedback_frappe_doc_compliance.md
in agent memory): whitelisted, permission-gated, uses the document API (no raw
SQL / no manual DDL), lives in lcs_integrations (never touches upstream crm/).
"""

import frappe
from frappe import _


@frappe.whitelist()
def set_primary_phone(contact: str, value: str):
	"""Set/replace the primary mobile number of a Contact.

	`value` is the full number (e.g. "+43664123456"). An empty value removes the
	primary mobile row. Returns the recomputed mobile_no after save.
	"""
	if not frappe.has_permission("Contact", "write", contact):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	doc = frappe.get_doc("Contact", contact)
	value = (value or "").strip()

	# Locate the current primary mobile row (fall back to the first row so we edit
	# in place instead of piling up duplicates when nothing is flagged primary).
	primary = next((p for p in doc.phone_nos if p.is_primary_mobile_no), None)
	if primary is None and doc.phone_nos:
		primary = doc.phone_nos[0]

	if not value:
		if primary is not None:
			doc.remove(primary)
	elif primary is not None:
		primary.phone = value
		primary.is_primary_mobile_no = 1
	else:
		doc.append("phone_nos", {"phone": value, "is_primary_mobile_no": 1})

	doc.save()
	# Contact.set_primary() recomputes mobile_no from the flagged row on validate.
	return {"mobile_no": doc.mobile_no}
