"""
Contact phone helper — the CRM's `Contact.mobile_no` / `Contact.phone` fields are
read-only and derived from the `phone_nos` child table (Contact Phone) on
validate, so they cannot be written directly. This upserts the PRIMARY mobile
OR landline number into `phone_nos` so a single-field phone editor
(LcsPhoneInput) can persist a number the normal way.

Follows Frappe customisation conventions (see feedback_frappe_doc_compliance.md
in agent memory): whitelisted, permission-gated, uses the document API (no raw
SQL / no manual DDL), lives in lcs_integrations (never touches upstream crm/).
"""

import frappe
from frappe import _

# kind -> the Contact Phone child flag that makes a row the primary of that kind.
FLAGS = {"mobile": "is_primary_mobile_no", "phone": "is_primary_phone"}


@frappe.whitelist()
def set_primary_phone(contact: str, value: str, kind: str = "mobile"):
	"""Set/replace the primary mobile OR landline number of a Contact.

	`kind` is "mobile" (→ Contact.mobile_no) or "phone" (→ Contact.phone).
	`value` is the full number (e.g. "+43664123456"). An empty value clears that
	kind. Returns the recomputed mobile_no + phone after save.
	"""
	flag = FLAGS.get(kind)
	if not flag:
		frappe.throw(_("Invalid phone kind"))
	if not frappe.has_permission("Contact", "write", contact):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	other = FLAGS["phone" if kind == "mobile" else "mobile"]
	doc = frappe.get_doc("Contact", contact)
	value = (value or "").strip()

	primary = next((p for p in doc.phone_nos if p.get(flag)), None)

	if not value:
		if primary is not None:
			# The row may also serve the other kind (one number, both flags) —
			# only drop this kind's flag then, otherwise remove the row entirely.
			if primary.get(other):
				primary.set(flag, 0)
			else:
				doc.remove(primary)
	else:
		if primary is None:
			# Reuse a row that already holds this exact number (don't pile up
			# duplicates); never steal the row flagged as the OTHER kind.
			primary = next(
				(p for p in doc.phone_nos if (p.phone or "").strip() == value and not p.get(other)),
				None,
			)
		if primary is None:
			primary = doc.append("phone_nos", {})
		primary.phone = value
		primary.set(flag, 1)

	doc.save()
	# Contact.set_primary() recomputes mobile_no / phone from the flagged rows.
	return {"mobile_no": doc.mobile_no, "phone": doc.phone}
