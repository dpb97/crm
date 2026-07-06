import frappe
import json
print("STEP 1: set overrides")
doc = frappe.get_single("Pilanda Theme Settings")
doc.set("module_icons", json.dumps({"vertrieb": "briefcase", "einkauf": "shopping-bag"}))
doc.flags.ignore_validate = True
doc.save(ignore_permissions=True)
frappe.cache().delete_value("pilanda_theme_tokens")
frappe.db.commit()

print("STEP 2: read raw value")
print(repr(frappe.db.get_single_value("Pilanda Theme Settings", "module_icons")))

print("STEP 3: get_module_icon_overrides()")
from pilanda_theme.api import get_module_icon_overrides
overrides = get_module_icon_overrides()
print(overrides)

print("STEP 4: simulate www/pilanda.get_context")
from pilanda.modules_data import MODULES
ver = [m for m in MODULES if m["slug"] == "vertrieb"][0]
print("Vertrieb default icon:", ver["icon"])
m2 = dict(ver)
if m2["slug"] in overrides:
    m2["icon"] = overrides[m2["slug"]]
print("Vertrieb after override:", m2["icon"])
