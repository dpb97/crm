"""One-shot data filler: map sales-manager codes -> User emails on
LCS Sales Territory. Idempotent. Skips already-filled rows. Logs every
change. Designed to be re-run safely after additional code -> email
mappings are added below.

Run via:
  bench --site lcs.local execute lcs_integrations.scripts.fill_territory_users.run

When new mappings come in (e.g. JFA, CLU), append them to CODE_TO_USER
and re-run.
"""

from __future__ import annotations

import frappe


# Add new mappings here when codes are resolved to real Users.
CODE_TO_USER: dict[str, str] = {
    "PKO": "patrick.koch@lcs-test.local",
    "DRO": "daniel.rohrer@lcs-test.local",
    # "JFA": "<missing — please provide>",
    # "CLU": "<missing — please provide>",
}


def run() -> None:
    # Verify the candidate users exist; bail loudly if not so we don't
    # silently leave the field empty.
    for code, email in CODE_TO_USER.items():
        if not frappe.db.exists("User", email):
            print(f"SKIP {code}: User {email!r} does not exist on this site")
    valid = {c: e for c, e in CODE_TO_USER.items() if frappe.db.exists("User", e)}

    territories = frappe.get_all(
        "LCS Sales Territory",
        fields=["name", "sales_manager_code", "sales_manager"],
    )

    updated = 0
    skipped_filled = 0
    skipped_unknown_code = 0

    for t in territories:
        if t["sales_manager"]:
            skipped_filled += 1
            continue
        code = (t["sales_manager_code"] or "").strip()
        user = valid.get(code)
        if not user:
            skipped_unknown_code += 1
            continue
        frappe.db.set_value("LCS Sales Territory", t["name"], "sales_manager", user)
        updated += 1
        print(f"  {t['name']:<30s} {code} -> {user}")

    frappe.db.commit()
    # Drop the cached country -> territory map so the next auto-assign
    # picks up the new ownership immediately.
    frappe.cache().delete_key("lcs_country_territory_map")

    print()
    print(f"Updated:               {updated}")
    print(f"Skipped (already set): {skipped_filled}")
    print(f"Skipped (unknown code):{skipped_unknown_code}")
