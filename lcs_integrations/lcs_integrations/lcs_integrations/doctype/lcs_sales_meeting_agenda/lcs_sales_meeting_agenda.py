# Copyright (c) 2026, LCS Cable Cranes and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime


class LCSSalesMeetingAgenda(Document):
	def before_save(self):
		# Stamp the decision timestamp the moment a point leaves the "Open" state,
		# and clear it again if the point is re-opened.
		if self.status in ("Decided", "Archived"):
			if not self.decided_on:
				self.decided_on = now_datetime()
		else:
			self.decided_on = None
