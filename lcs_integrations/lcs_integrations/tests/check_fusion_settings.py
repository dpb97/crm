import frappe


def run():
    meta = frappe.get_meta("LCS Fusion Manage Settings")
    fields = [(f.fieldname, f.fieldtype) for f in meta.fields
              if f.fieldtype not in ("Section Break", "Column Break")]
    print(f"Total fields: {len(fields)}")
    for fn, ft in fields:
        print(f"  {fn}: {ft}")

    # Also show current settings values (no secrets)
    s = frappe.get_single("LCS Fusion Manage Settings")
    print(f"\nenabled: {s.enabled}")
    print(f"tenant: {s.tenant}")
    print(f"default_workspace: {s.default_workspace}")
    print(f"redirect_uri: {s.redirect_uri}")
    print(f"client_id set: {bool(s.client_id)}")
    print(f"access_token present: {bool(s.access_token)}")
