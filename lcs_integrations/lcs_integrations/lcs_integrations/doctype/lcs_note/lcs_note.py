"""LCS Note — a note (typed or dictated) that can be linked to several CRM
entities at once (LCS Project, CRM Lead, LCS Chance, Contact, CRM Organization)
via the standard Dynamic Link child table."""

from __future__ import annotations

import frappe
from frappe.model.document import Document


class LCSNote(Document):
	def validate(self):
		# Drop empty / duplicate links.
		seen = set()
		kept = []
		for row in self.links or []:
			if not row.link_doctype or not row.link_name:
				continue
			key = (row.link_doctype, row.link_name)
			if key in seen:
				continue
			seen.add(key)
			kept.append(row)
		self.links = kept
