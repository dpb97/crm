"""Force the Pilanda brand colour to LCS teal (#008b8b).

The Pilanda Theme Settings shipped with a stale navy primary_color (#0B3A6F),
which the theme's after_request hook injects as `--pp-brand-primary` inline in
<head> — overriding the teal CSS files (and any CRM override) so active pills,
buttons and accents rendered dark blue instead of the brand turquoise.

Pin the brand to teal. Idempotent: only writes when the value is not already the
teal hex, and is a no-op when the pilanda_theme app / doctype is absent.
"""

import frappe

TEAL = "#008b8b"
TEAL_D = "#0a6f6f"


def execute():
	if not frappe.db.exists("DocType", "Pilanda Theme Settings"):
		return
	current = frappe.db.get_single_value("Pilanda Theme Settings", "primary_color")
	if (current or "").lower() == TEAL:
		return
	try:
		doc = frappe.get_single("Pilanda Theme Settings")
		doc.primary_color = TEAL
		doc.primary_color_dark = TEAL_D
		doc.save(ignore_permissions=True)
		frappe.clear_cache()
	except Exception:
		frappe.log_error(title="set_pilanda_brand_teal failed")
