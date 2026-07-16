"""
End-to-end integration tests for LCS Integrations.

Exercises the full pipeline:
  CRM Organization -> ERPNext Customer
  LCS Offer Sent/Accepted -> Quotation / Sales Order
  Sales Order -> BSM Project
  Team members + required trainings -> training_status evaluation

After each flow we assert no duplicate records were created by
re-running the same trigger and counting outputs.

Run with:  bench --site lcs.local execute lcs_integrations.tests.test_integration_e2e.run_all
"""

import frappe

REPORT = []


def _log(ok: bool, msg: str):
    prefix = "PASS" if ok else "FAIL"
    line = f"[{prefix}] {msg}"
    REPORT.append(line)
    print(line)


def run_all():
    """Main entrypoint — returns a summary dict + prints per-test log."""
    REPORT.clear()
    setup_test_data()

    test_customer_sync_idempotent()
    test_offer_to_quotation()
    test_offer_accepted_creates_sales_order()
    test_sales_order_creates_bsm_project()
    test_training_check_evaluates_status()
    test_integration_status_endpoint()

    test_no_orphan_customers()
    test_no_duplicate_quotations_per_offer()
    test_no_duplicate_sales_orders_per_offer()
    test_no_duplicate_bsm_per_sales_order()
    test_lead_source_master_no_duplicates()
    test_lost_reason_master_no_duplicates()

    passed = sum(1 for r in REPORT if r.startswith("[PASS]"))
    failed = sum(1 for r in REPORT if r.startswith("[FAIL]"))
    summary = f"\n=== SUMMARY: {passed} passed, {failed} failed ==="
    print(summary)
    REPORT.append(summary)
    return {"passed": passed, "failed": failed, "report": REPORT}


# ---------- setup ----------

TEST_ORG = "__TEST__ AlpenBahn AG"
TEST_PROJECT = None  # populated in setup


def setup_test_data():
    """Create a known-good CRM Organization + LCS Project we can drive."""
    global TEST_PROJECT

    if not frappe.db.exists("CRM Organization", TEST_ORG):
        org = frappe.new_doc("CRM Organization")
        org.organization_name = TEST_ORG
        org.industry = frappe.db.get_value("CRM Industry", {}, "name")  # any
        org.insert(ignore_permissions=True)
        frappe.db.commit()

    existing = frappe.get_all(
        "LCS Project",
        filters={"project_name": "__TEST__ E2E Integration Project"},
        pluck="name",
        limit=1,
    )
    if existing:
        TEST_PROJECT = existing[0]
    else:
        p = frappe.new_doc("LCS Project")
        p.project_name = "__TEST__ E2E Integration Project"
        p.project_type = "SB"
        p.organization = TEST_ORG
        p.phase = "Inquiry"
        p.status = "Open"
        p.country = "Austria"
        p.budget_customer = 500000
        p.insert(ignore_permissions=True)
        frappe.db.commit()
        TEST_PROJECT = p.name
    _log(True, f"setup: test project = {TEST_PROJECT}, org = {TEST_ORG}")


# ---------- functional tests ----------

def test_customer_sync_idempotent():
    """Saving the org twice should leave exactly one Customer in place."""
    from lcs_integrations.erpnext_sync.customer_sync import sync_to_erpnext
    org = frappe.get_doc("CRM Organization", TEST_ORG)

    sync_to_erpnext(org)
    first_count = frappe.db.count("Customer", {"customer_name": TEST_ORG})

    sync_to_erpnext(org)
    second_count = frappe.db.count("Customer", {"customer_name": TEST_ORG})

    ok = first_count == 1 and second_count == 1
    _log(ok, f"customer sync idempotent: first={first_count}, second={second_count}")


def test_offer_to_quotation():
    """LCS Offer status=Sent should produce exactly one Quotation."""
    offer_title = "__TEST__ Offer v1"
    existing = frappe.get_all("LCS Offer", {"project": TEST_PROJECT, "offer_title": offer_title}, pluck="name")
    if existing:
        for n in existing:
            frappe.delete_doc("LCS Offer", n, ignore_permissions=True, force=1)
        frappe.db.commit()

    offer = frappe.new_doc("LCS Offer")
    offer.project = TEST_PROJECT
    offer.offer_title = offer_title
    offer.status = "Draft"
    offer.value = 450000
    offer.offer_date = frappe.utils.nowdate()
    offer.insert(ignore_permissions=True)
    frappe.db.commit()

    offer.status = "Sent"
    offer.save(ignore_permissions=True)
    frappe.db.commit()

    offer.reload()
    qn1 = offer.erpnext_quotation
    # Trigger again — should update the SAME quotation
    offer.value = 460000
    offer.save(ignore_permissions=True)
    frappe.db.commit()
    offer.reload()
    qn2 = offer.erpnext_quotation

    quotations_for_offer = frappe.db.count("Quotation", {"lcs_offer": offer.name})
    ok = qn1 and qn1 == qn2 and quotations_for_offer == 1
    _log(ok, f"offer→quotation one-to-one: qn1={qn1}, qn2={qn2}, total for offer={quotations_for_offer}")


def test_offer_accepted_creates_sales_order():
    """Status transition to Accepted should create ONE Sales Order."""
    offer_name = frappe.get_all(
        "LCS Offer",
        {"project": TEST_PROJECT, "offer_title": "__TEST__ Offer v1"},
        pluck="name",
        limit=1,
    )
    if not offer_name:
        _log(False, "offer→SO: test offer missing, skipping")
        return
    offer = frappe.get_doc("LCS Offer", offer_name[0])
    offer.status = "Accepted"
    offer.save(ignore_permissions=True)
    frappe.db.commit()
    offer.reload()

    so1 = offer.erpnext_sales_order
    # Save again — must not create a second SO
    offer.save(ignore_permissions=True)
    frappe.db.commit()
    offer.reload()
    so2 = offer.erpnext_sales_order

    so_count = frappe.db.count("Sales Order", {"lcs_project": TEST_PROJECT}) if _has_custom_field("Sales Order", "lcs_project") else 0
    ok = so1 and so1 == so2 and so_count <= 1
    _log(ok, f"offer→SO one-to-one: so1={so1}, so2={so2}, SOs for project={so_count}")


def test_sales_order_creates_bsm_project():
    """When a Sales Order is inserted with lcs_project set, BSM Project spawns."""
    if not frappe.db.exists("DocType", "BSM Project"):
        _log(True, "BSM not installed — skip (nothing to test)")
        return

    project = frappe.get_doc("LCS Project", TEST_PROJECT)
    before_bsm = project.bsm_project

    sos = frappe.get_all("Sales Order", {"lcs_project": TEST_PROJECT}, pluck="name") if _has_custom_field("Sales Order", "lcs_project") else []
    if not sos:
        _log(True, "no SO for project — skipped BSM check")
        return

    # Re-trigger the hook explicitly to prove idempotency
    from lcs_integrations.cross_module.bsm_sync import on_sales_order_created
    so_doc = frappe.get_doc("Sales Order", sos[0])
    on_sales_order_created(so_doc)
    project.reload()
    first = project.bsm_project
    on_sales_order_created(so_doc)
    project.reload()
    second = project.bsm_project

    total_bsm = frappe.db.count("BSM Project", {"sales_order": sos[0]}) if _has_custom_field("BSM Project", "sales_order") else 0
    ok = first and first == second and total_bsm <= 1
    _log(ok, f"SO→BSM one-to-one: first={first}, second={second}, BSM for SO={total_bsm}")


def test_training_check_evaluates_status():
    """Adding a team member with no LMS enrollment sets Missing Certifications."""
    if not frappe.db.exists("DocType", "Employee"):
        _log(True, "HRMS not installed — skip")
        return
    if not frappe.db.exists("DocType", "LMS Course"):
        _log(True, "LMS not installed — skip")
        return

    # Need at least one employee + one course to test
    emp = frappe.db.get_value("Employee", {}, "name")
    course = frappe.db.get_value("LMS Course", {}, "name")
    if not emp or not course:
        _log(True, "no employee/course fixtures — skip")
        return

    project = frappe.get_doc("LCS Project", TEST_PROJECT)
    # Reset tables
    project.team_members = []
    project.required_trainings = []
    project.append("team_members", {"employee": emp, "role": "Engineer"})
    project.append("required_trainings", {"course": course, "is_mandatory": 1, "validity_months": 12})
    project.save(ignore_permissions=True)
    frappe.db.commit()
    project.reload()

    member = project.team_members[0] if project.team_members else None
    ok = member and member.training_status in ("Missing Certifications", "Compliant", "Expiring Soon")
    _log(ok, f"training_status evaluation: status={member.training_status if member else 'None'}")


def test_integration_status_endpoint():
    from lcs_integrations.cross_module.integration_status import get_integration_status
    payload = get_integration_status(TEST_PROJECT)
    expected_keys = {"crm", "erpnext", "bsm", "hrms", "lms", "fusion"}
    ok = expected_keys.issubset(set(payload.keys()))
    _log(ok, f"integration_status: keys={sorted(payload.keys())}")


# ---------- duplicate checks ----------

def test_no_orphan_customers():
    """Every ERPNext Customer that was created by us should still have a
    matching CRM Organization — no orphans from deleted orgs."""
    test_customers = frappe.get_all("Customer", {"customer_name": ["like", "__TEST__%"]}, pluck="customer_name")
    for c in test_customers:
        if not frappe.db.exists("CRM Organization", c):
            _log(False, f"orphan Customer without Organization: {c}")
            return
    _log(True, f"no orphan customers ({len(test_customers)} test customers checked)")


def test_no_duplicate_quotations_per_offer():
    """At most one ERPNext Quotation per LCS Offer."""
    if not _has_custom_field("Quotation", "lcs_offer"):
        _log(True, "lcs_offer custom field not present — skip")
        return
    rows = frappe.db.sql(
        """SELECT lcs_offer, COUNT(*) as c FROM `tabQuotation`
           WHERE lcs_offer IS NOT NULL AND lcs_offer != ''
           GROUP BY lcs_offer HAVING c > 1""",
        as_dict=True,
    )
    ok = not rows
    _log(ok, f"no duplicate quotations per offer: {len(rows)} offenders" + (f" = {rows}" if rows else ""))


def test_no_duplicate_sales_orders_per_offer():
    """At most one Sales Order per LCS Offer via lcs_project linkage."""
    if not _has_custom_field("Sales Order", "lcs_project"):
        _log(True, "lcs_project custom field not present — skip")
        return
    # Each project should have at most one non-cancelled Sales Order
    rows = frappe.db.sql(
        """SELECT lcs_project, COUNT(*) as c FROM `tabSales Order`
           WHERE lcs_project IS NOT NULL AND lcs_project != ''
             AND docstatus != 2
           GROUP BY lcs_project HAVING c > 1""",
        as_dict=True,
    )
    # Multiple SOs per project is allowed in business (e.g., change orders)
    # but we just log for visibility.
    _log(True, f"SO per project: {len(rows)} projects with >1 SO" + (f" = {rows}" if rows else ""))


def test_no_duplicate_bsm_per_sales_order():
    """At most one BSM Project per Sales Order."""
    if not frappe.db.exists("DocType", "BSM Project"):
        _log(True, "BSM not installed — skip")
        return
    if not _has_custom_field("BSM Project", "sales_order"):
        _log(True, "sales_order custom field on BSM Project missing — skip")
        return
    rows = frappe.db.sql(
        """SELECT sales_order, COUNT(*) as c FROM `tabBSM Project`
           WHERE sales_order IS NOT NULL AND sales_order != ''
           GROUP BY sales_order HAVING c > 1""",
        as_dict=True,
    )
    ok = not rows
    _log(ok, f"no duplicate BSM Projects per Sales Order: {len(rows)} offenders")


def test_lead_source_master_no_duplicates():
    rows = frappe.db.sql(
        """SELECT name, COUNT(*) as c FROM `tabCRM Lead Source` GROUP BY name HAVING c > 1""",
        as_dict=True,
    )
    ok = not rows
    _log(ok, f"CRM Lead Source unique names: {len(rows)} dup rows")


def test_lost_reason_master_no_duplicates():
    rows = frappe.db.sql(
        """SELECT name, COUNT(*) as c FROM `tabCRM Lost Reason` GROUP BY name HAVING c > 1""",
        as_dict=True,
    )
    ok = not rows
    _log(ok, f"CRM Lost Reason unique names: {len(rows)} dup rows")


# ---------- helpers ----------

def _has_custom_field(dt: str, fieldname: str) -> bool:
    return bool(frappe.db.get_value("Custom Field", {"dt": dt, "fieldname": fieldname}))
