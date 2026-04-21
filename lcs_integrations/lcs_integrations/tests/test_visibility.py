"""
Exercises the visibility service:
- Creates a test access profile restricting to Austria + SB only
- Creates two test projects (Austria/SB, Italy/WI)
- Binds a test user to the profile
- Verifies get_permission_query_conditions returns the right SQL
- Verifies has_permission allows / denies correctly
- Verifies get_user_preferences returns merged prefs + profile
"""

import frappe

REPORT = []


def _log(ok, msg):
    REPORT.append(f"[{'PASS' if ok else 'FAIL'}] {msg}")
    print(REPORT[-1])


def run():
    REPORT.clear()
    _ensure_test_user()
    _ensure_test_profile()
    _ensure_test_projects()
    _bind_user_to_profile()

    _test_query_conditions()
    _test_has_permission_allowed()
    _test_has_permission_denied_country()
    _test_has_permission_denied_type()
    _test_get_user_preferences()
    _test_system_manager_bypasses()

    passed = sum(1 for r in REPORT if r.startswith("[PASS]"))
    failed = sum(1 for r in REPORT if r.startswith("[FAIL]"))
    summary = f"\n=== {passed} passed, {failed} failed ==="
    print(summary)
    return {"passed": passed, "failed": failed, "report": REPORT}


TEST_USER = "visibility_tester@lcs.test"
TEST_PROFILE = "__TEST__ Austria SB Only"


def _ensure_test_user():
    if not frappe.db.exists("User", TEST_USER):
        u = frappe.new_doc("User")
        u.email = TEST_USER
        u.first_name = "Visibility"
        u.last_name = "Tester"
        u.send_welcome_email = 0
        u.user_type = "System User"
        u.append("roles", {"role": "Sales User"})
        u.insert(ignore_permissions=True)
        frappe.db.commit()


def _ensure_test_profile():
    if frappe.db.exists("LCS Access Profile", TEST_PROFILE):
        frappe.delete_doc("LCS Access Profile", TEST_PROFILE, force=1, ignore_permissions=True)
    p = frappe.new_doc("LCS Access Profile")
    p.profile_name = TEST_PROFILE
    p.description = "Test profile — Austria + SB only"
    p.is_active = 1
    p.append("scope_countries", {"country": "Austria"})
    p.append("scope_project_types", {"project_type": "SB"})
    p.hide_pricing = 1
    p.hide_forecasting = 1
    p.insert(ignore_permissions=True)
    frappe.db.commit()


def _ensure_test_projects():
    for data in [
        {"project_name": "__TEST_VIS__ Austria SB", "country": "Austria", "project_type": "SB"},
        {"project_name": "__TEST_VIS__ Italy WI", "country": "Italy", "project_type": "WI"},
    ]:
        existing = frappe.get_all("LCS Project", {"project_name": data["project_name"]}, pluck="name")
        for n in existing:
            frappe.delete_doc("LCS Project", n, force=1, ignore_permissions=True)
        p = frappe.new_doc("LCS Project")
        p.update(data)
        p.phase = "Inquiry"
        p.status = "Open"
        p.insert(ignore_permissions=True)
    frappe.db.commit()


def _bind_user_to_profile():
    name = TEST_USER
    if frappe.db.exists("LCS User Preferences", name):
        frappe.delete_doc("LCS User Preferences", name, force=1, ignore_permissions=True)
    prefs = frappe.new_doc("LCS User Preferences")
    prefs.user = name
    prefs.access_profile = TEST_PROFILE
    prefs.insert(ignore_permissions=True)
    frappe.db.commit()
    # Bust cache
    frappe.cache().hdel("lcs_access_profile_cache", name)


def _test_query_conditions():
    from lcs_integrations.visibility.service import get_permission_query_conditions
    cond = get_permission_query_conditions(user=TEST_USER)
    ok = "Austria" in cond and "SB" in cond and "`tabLCS Project`.country" in cond
    _log(ok, f"query_conditions contains country+type filters: {cond[:120]}...")


def _test_has_permission_allowed():
    from lcs_integrations.visibility.service import has_permission
    doc = frappe.get_doc("LCS Project", {"project_name": "__TEST_VIS__ Austria SB"})
    ok = has_permission(doc, "read", user=TEST_USER) is True
    _log(ok, f"Austria/SB project allowed for user")


def _test_has_permission_denied_country():
    from lcs_integrations.visibility.service import has_permission
    doc = frappe.get_doc("LCS Project", {"project_name": "__TEST_VIS__ Italy WI"})
    ok = has_permission(doc, "read", user=TEST_USER) is False
    _log(ok, f"Italy/WI project denied for user (country mismatch)")


def _test_has_permission_denied_type():
    from lcs_integrations.visibility.service import has_permission
    # Create an Austria+WI project — country OK, type blocked
    existing = frappe.get_all("LCS Project", {"project_name": "__TEST_VIS__ Austria WI"}, pluck="name")
    for n in existing:
        frappe.delete_doc("LCS Project", n, force=1, ignore_permissions=True)
    p = frappe.new_doc("LCS Project")
    p.project_name = "__TEST_VIS__ Austria WI"
    p.country = "Austria"
    p.project_type = "WI"
    p.phase = "Inquiry"
    p.status = "Open"
    p.insert(ignore_permissions=True)
    frappe.db.commit()

    ok = has_permission(p, "read", user=TEST_USER) is False
    _log(ok, f"Austria/WI project denied (type mismatch)")


def _test_get_user_preferences():
    from lcs_integrations.visibility.service import get_user_preferences
    payload = get_user_preferences(user=TEST_USER)
    profile = payload.get("access_profile")
    ok = (
        profile is not None
        and profile["countries"] == ["Austria"]
        and profile["project_types"] == ["SB"]
        and profile["hide_pricing"] is True
        and profile["hide_forecasting"] is True
    )
    _log(ok, f"get_user_preferences returns profile: countries={profile['countries'] if profile else None}")


def _test_system_manager_bypasses():
    from lcs_integrations.visibility.service import get_permission_query_conditions, has_permission
    cond = get_permission_query_conditions(user="Administrator")
    doc = frappe.get_doc("LCS Project", {"project_name": "__TEST_VIS__ Italy WI"})
    ok = cond == "" and has_permission(doc, "read", user="Administrator") is True
    _log(ok, f"Administrator bypasses all restrictions (cond='{cond}')")


def cleanup():
    """Remove test artefacts."""
    for name in frappe.get_all("LCS Project", {"project_name": ["like", "__TEST_VIS__%"]}, pluck="name"):
        frappe.delete_doc("LCS Project", name, force=1, ignore_permissions=True)
    if frappe.db.exists("LCS User Preferences", TEST_USER):
        frappe.delete_doc("LCS User Preferences", TEST_USER, force=1, ignore_permissions=True)
    if frappe.db.exists("LCS Access Profile", TEST_PROFILE):
        frappe.delete_doc("LCS Access Profile", TEST_PROFILE, force=1, ignore_permissions=True)
    if frappe.db.exists("User", TEST_USER):
        frappe.delete_doc("User", TEST_USER, force=1, ignore_permissions=True)
    frappe.cache().hdel("lcs_access_profile_cache", TEST_USER)
    frappe.db.commit()
    print("visibility test cleanup done")
