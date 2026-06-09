"""One-shot: stamp `module = LCS Integrations` on every Custom Field
that should belong to our app but has module=NULL."""

import frappe


TARGETS = [
    ("CRM Organization", "erpnext_customer"),
    ("CRM Deal", "erpnext_customer"),
    ("CRM Deal", "sales_manager"),
    ("CRM Lead", "erpnext_customer"),
    ("CRM Lead", "sales_manager"),
    ("CRM Lead", "lcs_score"),
    ("Sales Order", "lcs_project"),
    ("Quotation", "lcs_offer"),
    ("BSM Project", "lcs_project"),
    ("BSM Project", "sales_order"),
]


def run():
    healed = 0
    skipped = 0
    for dt, fn in TARGETS:
        row = frappe.db.get_value(
            "Custom Field",
            {"dt": dt, "fieldname": fn},
            ["name", "module"],
            as_dict=True,
        )
        if not row:
            print(f"  [-] {dt}.{fn}: no Custom Field row (skipped)")
            skipped += 1
            continue
        if row.module == "LCS Integrations":
            print(f"  [=] {dt}.{fn}: already stamped")
            continue
        frappe.db.set_value("Custom Field", row.name, "module", "LCS Integrations")
        print(f"  [+] {dt}.{fn}: stamped (was {row.module or 'NULL'})")
        healed += 1
    frappe.db.commit()
    print(f"\nDone — {healed} field(s) stamped, {skipped} missing")
    return {"healed": healed, "skipped": skipped}
