import frappe
print("--- Raw module_icons value ---")
raw = frappe.db.get_single_value("Pilanda Theme Settings", "module_icons")
print(repr(raw))
print()
print("--- get_module_icon_overrides() result ---")
from pilanda_theme.api import get_module_icon_overrides
print(get_module_icon_overrides())
print()
print("--- _resolve cached ---")
from pilanda_theme.api import _resolve
frappe.cache().delete_value("pilanda_theme_tokens")
d = _resolve()
print("module_icons in _resolve:", repr(d.get("module_icons", "MISSING")))
