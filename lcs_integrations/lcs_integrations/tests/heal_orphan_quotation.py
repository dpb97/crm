import frappe


def run():
    rows = frappe.db.sql(
        """SELECT q.name, q.lcs_offer FROM `tabQuotation` q
           WHERE q.lcs_offer IS NOT NULL AND q.lcs_offer != ''
             AND NOT EXISTS (SELECT 1 FROM `tabLCS Offer` o WHERE o.name = q.lcs_offer)""",
        as_dict=True,
    )
    for r in rows:
        frappe.db.set_value("Quotation", r.name, "lcs_offer", None)
        print(f"cleared lcs_offer on {r.name}")
    frappe.db.commit()
    print(f"total healed: {len(rows)}")
