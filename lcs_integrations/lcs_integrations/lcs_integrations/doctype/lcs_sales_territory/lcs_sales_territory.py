import frappe
from frappe.model.document import Document


class LCSSalesTerritory(Document):
    def on_update(self):
        # The auto-assign lookup caches a Country -> Territory map.
        # Drop it whenever the territory definition changes so the next
        # lead/deal/project insert sees fresh ownership.
        frappe.cache().delete_key("lcs_country_territory_map")

    def on_trash(self):
        frappe.cache().delete_key("lcs_country_territory_map")
