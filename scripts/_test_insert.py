import frappe
from frappe.utils import now
print("CONNECTED to:", frappe.local.site)
print("Before:", frappe.db.count("Customer"))
try:
    frappe.db.sql(
        "INSERT IGNORE INTO `tabCustomer` "
        "(name, owner, creation, modified, modified_by, docstatus, idx, customer_name, customer_type, disabled, language) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
        ("TEST AG", "Administrator", now(), now(), "Administrator", 0, 0, "TEST AG", "Company", 0, "en")
    )
    frappe.db.commit()
    print("After insert:", frappe.db.count("Customer"))
except Exception as e:
    print("ERROR:", type(e).__name__, e)
