__version__ = "0.1.0"

# Compat shim: upstream crm develop imports "_add" from assign_to (the
# frappe develop line split "add" into public "add" + internal "_add").
# The frappe v16 release line this bench is pinned to only has "add",
# whose signature (args=None, *, ignore_permissions=False) matches the
# way crm calls it. Alias it here — this module is imported when hooks
# load, i.e. before any crm doctype controller.
from frappe.desk.form import assign_to as _assign_to

if not hasattr(_assign_to, "_add"):
    _assign_to._add = _assign_to.add
