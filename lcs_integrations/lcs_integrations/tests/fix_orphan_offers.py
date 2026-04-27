"""Re-trigger the ERPNext-quotation sync for offers that pre-date the hook."""

import frappe


def run():
    """Call the upsert_quotation service directly for offers where the
    hook didn't fire (created before the integration was wired)."""
    from lcs_integrations.erpnext_sync.quotation_sync import upsert_quotation, create_sales_order

    offers = frappe.get_all(
        "LCS Offer",
        filters={
            "status": ["in", ["Sent", "In Review", "Accepted"]],
            "erpnext_quotation": ["in", ["", None]],
        },
        pluck="name",
    )
    for n in offers:
        try:
            offer = frappe.get_doc("LCS Offer", n)
            upsert_quotation(offer)
            offer.reload()
            if offer.status == "Accepted" and offer.erpnext_quotation:
                create_sales_order(offer)
                offer.reload()
            print(f"  {n} ({offer.status}) → quote={offer.erpnext_quotation or '(none)'}, "
                  f"so={offer.erpnext_sales_order or '(none)'}")
        except Exception as e:
            print(f"  [FAIL] {n}: {e}")
            frappe.log_error(f"fix_orphan_offers {n}: {e}", "fix_orphan_offers")
    frappe.db.commit()
    print(f"Done — processed {len(offers)} offer(s)")
