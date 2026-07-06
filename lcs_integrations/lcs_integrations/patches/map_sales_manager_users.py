"""Resolve the market-split sales-manager codes (JFA / PKO / CLU / DRO) to
real User accounts and write them onto every LCS Sales Territory.

The market-split seed only stores the three-letter staff codes. Auto-assign
and the assignment dashboard need an actual User to attribute leads / deals /
projects to, so this patch:

  1. ensures a User exists for every code (creating a demo account when the
     mapped e-mail is missing), and
  2. sets `sales_manager` / `deputy_sales_manager` on each territory from its
     code, without ever clobbering a User link that is already set.

Idempotent. Source: `Marktaufteilung-2026_R03.xlsx`.
"""

from __future__ import annotations

import frappe

# code -> (email, full name). PKO / DRO already exist as demo users; JFA / CLU
# are created here following the same lcs-test.local convention.
CODE_TO_USER: dict[str, tuple[str, str]] = {
    "JFA": ("jfa@lcs-test.local", "JFA"),
    "PKO": ("patrick.koch@lcs-test.local", "Patrick Koch"),
    "CLU": ("clu@lcs-test.local", "CLU"),
    "DRO": ("daniel.rohrer@lcs-test.local", "Daniel Rohrer"),
}


def _ensure_user(email: str, full_name: str) -> str:
    if frappe.db.exists("User", email):
        # Backfill a readable display name when the existing demo account
        # was created without one (so the dashboard shows "Patrick Koch",
        # not the raw e-mail).
        current = frappe.db.get_value("User", email, "full_name")
        if not current or current == email.split("@")[0]:
            first, _, last = full_name.partition(" ")
            frappe.db.set_value("User", email, {
                "first_name": first or full_name,
                "last_name": last or None,
                "full_name": full_name,
            })
        return email
    first, _, last = full_name.partition(" ")
    user = frappe.new_doc("User")
    user.email = email
    user.first_name = first or full_name
    user.last_name = last or None
    user.full_name = full_name
    user.enabled = 1
    user.user_type = "System User"
    user.send_welcome_email = 0
    user.insert(ignore_permissions=True)
    for role in ("Sales User", "Sales Manager"):
        if frappe.db.exists("Role", role):
            user.add_roles(role)
    return email


def execute() -> None:
    code_email = {
        code: _ensure_user(email, name)
        for code, (email, name) in CODE_TO_USER.items()
    }

    for name in frappe.get_all("LCS Sales Territory", pluck="name"):
        doc = frappe.get_doc("LCS Sales Territory", name)
        changed = False

        if not doc.sales_manager and doc.sales_manager_code in code_email:
            doc.sales_manager = code_email[doc.sales_manager_code]
            changed = True
        if not doc.deputy_sales_manager and doc.deputy_sales_manager_code in code_email:
            doc.deputy_sales_manager = code_email[doc.deputy_sales_manager_code]
            changed = True

        if changed:
            doc.save(ignore_permissions=True)

    frappe.cache().delete_key("lcs_country_territory_map")
    frappe.db.commit()
