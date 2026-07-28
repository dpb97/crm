import frappe

# Demo-data cleanup: the projects imported from deals carried meaningless
# numbers/names (LCS-Other-2026-00x / CRM-DEAL-2026-000xx). Give them a logical
# number {TYPE}-{CUSTOMER}-{NR} (TYPE = SB Seilbahn · SK Seilkran · WI Winde) and
# a readable name, and set project_type so the map draws the right symbol.
# Idempotent: keyed by the OLD project_number; once renamed the old key is gone,
# so a re-run is a no-op. Keyed by data, so it silently skips on other sites.
_RENAME = {
    "LCS-Other-2026-005": ("SK", "SK-BBW-001", "Seilkran Vinci Statik"),
    "LCS-Other-2026-007": ("SB", "SB-BBW-002", "Seilbahn Bergbahnen Wallis"),
    "LCS-Other-2026-006": ("WI", "WI-DBC-001", "Winde DynaBCS Vorschub"),
    "LCS-Other-2026-004": ("SB", "SB-BBD-001", "Seilbahn Bergbahn Demo Nord"),
    "LCS-Other-2026-003": ("SK", "SK-BBD-002", "Seilkran Bergbahn Demo Sued"),
    "LCS-Other-2026-002": ("WI", "WI-BBD-003", "Winde Bergbahn Demo Vorschub"),
    "LCS-Other-2026-001": ("SB", "SB-BBD-004", "Seilbahn Bergbahn Demo West"),
}


def execute():
    for old_no, (typ, new_no, name) in _RENAME.items():
        pname = frappe.db.get_value("LCS Project", {"project_number": old_no}, "name")
        if not pname:
            continue
        frappe.db.set_value(
            "LCS Project",
            pname,
            {"project_number": new_no, "project_name": name, "project_type": typ},
            update_modified=False,
        )
