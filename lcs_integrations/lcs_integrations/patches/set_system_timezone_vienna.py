import frappe


def execute():
    """Pin the site to Europe/Vienna.

    An empty System Settings `time_zone` makes Frappe fall back to its default
    (Asia/Kolkata, +5:30), which shifted EVERY timestamp — including synced
    Outlook mail — by +3:30 versus the actual Austrian local time. Idempotent:
    only writes when the timezone is unset or still on the Kolkata default, so a
    deliberate later change is never overwritten.
    """
    current = frappe.db.get_single_value("System Settings", "time_zone")
    if not current or current == "Asia/Kolkata":
        frappe.db.set_single_value("System Settings", "time_zone", "Europe/Vienna")
        frappe.db.commit()
