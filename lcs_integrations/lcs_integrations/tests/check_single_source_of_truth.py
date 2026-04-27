"""
Single-source-of-truth audit across the full LCS stack.

Checks that LCS Project is the canonical pivot for every integrated
system and that the cross-module link graph has no orphans, no forks
(one-to-many where it should be one-to-one), and no contradictions.

Read-only — safe against production data.
"""

import frappe


REPORT = []


def _ok(msg):
    REPORT.append(("ok", msg))
    print(f"[ OK  ] {msg}")


def _warn(msg, detail=None):
    REPORT.append(("warn", msg))
    print(f"[WARN ] {msg}")
    if detail:
        for d in detail[:5]:
            print(f"          {d}")


def _fail(msg, detail=None):
    REPORT.append(("fail", msg))
    print(f"[FAIL ] {msg}")
    if detail:
        for d in detail[:5]:
            print(f"          {d}")


def run():
    REPORT.clear()
    print("\n=== Single-Source-of-Truth Audit ===\n")

    print("─── Identity ───")
    _check_project_identity()

    print("\n─── CRM (Lead → Deal → Project) ───")
    _check_crm_chain()

    print("\n─── ERPNext (Customer / Quotation / Sales Order) ───")
    _check_erpnext_chain()

    print("\n─── BSM (Construction Site) ───")
    _check_bsm_chain()

    print("\n─── HRMS (Employee, Project Manager, Team) ───")
    _check_hrms_chain()

    print("\n─── LMS (Required Trainings) ───")
    _check_lms_chain()

    print("\n─── Fusion Manage (PLM) ───")
    _check_fusion_chain()

    # Tally
    counts = {"ok": 0, "warn": 0, "fail": 0}
    for level, _ in REPORT:
        counts[level] += 1
    print("\n" + "=" * 60)
    print(f"  ✓ {counts['ok']} OK   ⚠ {counts['warn']} warnings   ✗ {counts['fail']} failures")
    print("=" * 60)

    return {
        "total": len(REPORT),
        "ok": counts["ok"],
        "warn": counts["warn"],
        "fail": counts["fail"],
        "is_canonical": counts["fail"] == 0,
    }


# ---- checks ----------------------------------------------------------------


def _check_project_identity():
    total = frappe.db.count("LCS Project")
    _ok(f"{total} LCS Projects total")

    # Project numbers must be unique
    dups = frappe.db.sql(
        """SELECT project_number, COUNT(*) c FROM `tabLCS Project`
           WHERE project_number IS NOT NULL AND project_number != ''
           GROUP BY project_number HAVING c > 1""",
        as_dict=True,
    )
    if dups:
        _fail(f"{len(dups)} duplicate project_numbers", [f"{d.project_number} ({d.c}×)" for d in dups])
    else:
        _ok("project_number unique across all projects")


def _check_crm_chain():
    # Every project should have a deal (per the user's spec)
    no_deal = frappe.db.count("LCS Project", {"deal": ["is", "not set"]})
    if no_deal:
        _warn(f"{no_deal} LCS Projects have no Deal linked",
              frappe.get_all("LCS Project", {"deal": ["is", "not set"]},
                             ["name", "project_name"], limit=5))
    else:
        _ok("Every LCS Project links to a CRM Deal")

    # No project should claim a non-existent deal
    bad = frappe.db.sql(
        """SELECT p.name, p.deal FROM `tabLCS Project` p
           WHERE p.deal IS NOT NULL AND p.deal != ''
             AND NOT EXISTS (SELECT 1 FROM `tabCRM Deal` d WHERE d.name = p.deal)""",
        as_dict=True,
    )
    if bad:
        _fail(f"{len(bad)} projects link to a deleted CRM Deal", [f"{r.name} → {r.deal}" for r in bad])
    else:
        _ok("All deal back-links resolve to existing CRM Deals")

    # Two projects can't share the same deal — that's a fork
    deal_dups = frappe.db.sql(
        """SELECT deal, COUNT(*) c FROM `tabLCS Project`
           WHERE deal IS NOT NULL AND deal != ''
           GROUP BY deal HAVING c > 1""",
        as_dict=True,
    )
    if deal_dups:
        _fail(f"{len(deal_dups)} CRM Deals are linked to MULTIPLE LCS Projects",
              [f"{r.deal} → {r.c} projects" for r in deal_dups])
    else:
        _ok("Each CRM Deal points at exactly one LCS Project (1:1)")

    # Every Deal should have a Lead
    deal_meta = frappe.get_meta("CRM Deal")
    if any(f.fieldname == "lead" for f in deal_meta.fields):
        no_lead = frappe.db.count("CRM Deal", {"lead": ["is", "not set"]})
        total = frappe.db.count("CRM Deal")
        if no_lead == 0:
            _ok(f"All {total} CRM Deals have a Lead origin")
        else:
            _warn(f"{no_lead}/{total} CRM Deals have no Lead linked")


def _check_erpnext_chain():
    # CRM Organization → ERPNext Customer
    if frappe.db.exists("DocType", "Customer"):
        org_cf = frappe.db.get_value("Custom Field", {"dt": "CRM Organization", "fieldname": "erpnext_customer"})
        if org_cf:
            mismatched = frappe.db.sql(
                """SELECT o.name, o.erpnext_customer FROM `tabCRM Organization` o
                   WHERE o.erpnext_customer IS NOT NULL AND o.erpnext_customer != ''
                     AND NOT EXISTS (SELECT 1 FROM `tabCustomer` c WHERE c.name = o.erpnext_customer)""",
                as_dict=True,
            )
            if mismatched:
                _fail(f"{len(mismatched)} CRM Orgs reference deleted Customers", mismatched)
            else:
                _ok("All erpnext_customer back-links resolve")

    # LCS Offer → Quotation
    bad_q = frappe.db.sql(
        """SELECT o.name, o.erpnext_quotation FROM `tabLCS Offer` o
           WHERE o.erpnext_quotation IS NOT NULL AND o.erpnext_quotation != ''
             AND NOT EXISTS (SELECT 1 FROM `tabQuotation` q WHERE q.name = o.erpnext_quotation)""",
        as_dict=True,
    )
    if bad_q:
        _fail(f"{len(bad_q)} LCS Offers point at deleted Quotations", bad_q)
    else:
        _ok("LCS Offer → Quotation links all valid")

    # Each LCS Offer in 'Sent/Accepted/In Review' state should have a Quotation
    missing_q = frappe.get_all(
        "LCS Offer",
        filters={
            "status": ["in", ["Sent", "In Review", "Accepted"]],
            "erpnext_quotation": ["in", ["", None]],
        },
        fields=["name", "status"],
    )
    if missing_q:
        _warn(f"{len(missing_q)} active LCS Offers have no Quotation",
              [f"{o.name} ({o.status})" for o in missing_q])
    else:
        _ok("All Sent/InReview/Accepted offers have a Quotation in ERPNext")

    # Sales Order → LCS Project back-link consistency
    cf_so = frappe.db.get_value("Custom Field", {"dt": "Sales Order", "fieldname": "lcs_project"})
    if cf_so:
        orphan_so = frappe.db.sql(
            """SELECT s.name, s.lcs_project FROM `tabSales Order` s
               WHERE s.lcs_project IS NOT NULL AND s.lcs_project != ''
                 AND NOT EXISTS (SELECT 1 FROM `tabLCS Project` p WHERE p.name = s.lcs_project)""",
            as_dict=True,
        )
        if orphan_so:
            _fail(f"{len(orphan_so)} Sales Orders reference deleted LCS Projects", orphan_so)
        else:
            _ok("Sales Order.lcs_project back-links resolve")

    # No project should have multiple active Sales Orders (fork detection)
    if cf_so:
        multi_so = frappe.db.sql(
            """SELECT lcs_project, COUNT(*) c FROM `tabSales Order`
               WHERE lcs_project IS NOT NULL AND lcs_project != ''
                 AND docstatus != 2
               GROUP BY lcs_project HAVING c > 1""",
            as_dict=True,
        )
        if multi_so:
            _warn(f"{len(multi_so)} LCS Projects have >1 active Sales Order",
                  [f"{r.lcs_project} → {r.c} SOs" for r in multi_so])
        else:
            _ok("Every LCS Project ↔ Sales Order is 1:1 (or 1:0)")


def _check_bsm_chain():
    if not frappe.db.exists("DocType", "BSM Project"):
        _warn("BSM Project DocType not installed")
        return

    # LCS Project.bsm_project must resolve
    bad_bsm = frappe.db.sql(
        """SELECT p.name, p.bsm_project FROM `tabLCS Project` p
           WHERE p.bsm_project IS NOT NULL AND p.bsm_project != ''
             AND NOT EXISTS (SELECT 1 FROM `tabBSM Project` b WHERE b.name = p.bsm_project)""",
        as_dict=True,
    )
    if bad_bsm:
        _fail(f"{len(bad_bsm)} LCS Projects link to deleted BSM Projects", bad_bsm)
    else:
        _ok("LCS Project.bsm_project links all resolve")

    # Symmetry: BSM.lcs_project → LCS Project must resolve
    has_cf = frappe.db.get_value("Custom Field", {"dt": "BSM Project", "fieldname": "lcs_project"})
    if has_cf:
        bad_back = frappe.db.sql(
            """SELECT b.name, b.lcs_project FROM `tabBSM Project` b
               WHERE b.lcs_project IS NOT NULL AND b.lcs_project != ''
                 AND NOT EXISTS (SELECT 1 FROM `tabLCS Project` p WHERE p.name = b.lcs_project)""",
            as_dict=True,
        )
        if bad_back:
            _fail(f"{len(bad_back)} BSM Projects link to deleted LCS Projects", bad_back)
        else:
            _ok("BSM Project.lcs_project links all resolve")

        # Bidirectional consistency: if A→B then B→A
        asymmetric = frappe.db.sql(
            """SELECT p.name AS lcs, p.bsm_project AS expected_bsm, b.lcs_project AS actual_lcs
               FROM `tabLCS Project` p
               JOIN `tabBSM Project` b ON b.name = p.bsm_project
               WHERE p.bsm_project IS NOT NULL AND p.bsm_project != ''
                 AND (b.lcs_project IS NULL OR b.lcs_project != p.name)""",
            as_dict=True,
        )
        if asymmetric:
            _warn(f"{len(asymmetric)} LCS↔BSM links are not bidirectional",
                  [f"{r.lcs} ←→ {r.expected_bsm} (BSM points at {r.actual_lcs or 'nothing'})" for r in asymmetric])
        else:
            _ok("Every LCS ↔ BSM project link is symmetric")

    # No BSM project should claim TWO different LCS Projects
    if has_cf:
        forks = frappe.db.sql(
            """SELECT lcs_project, COUNT(*) c FROM `tabBSM Project`
               WHERE lcs_project IS NOT NULL AND lcs_project != ''
               GROUP BY lcs_project HAVING c > 1""",
            as_dict=True,
        )
        if forks:
            _fail(f"{len(forks)} LCS Projects have multiple BSM mirrors",
                  [f"{r.lcs_project} → {r.c} BSM" for r in forks])
        else:
            _ok("Each LCS Project ↔ BSM Project is 1:1 (or 1:0)")


def _check_hrms_chain():
    if not frappe.db.exists("DocType", "Employee"):
        _warn("HRMS Employee DocType not installed")
        return

    # Project Manager links must resolve
    bad_pm = frappe.db.sql(
        """SELECT p.name, p.project_manager FROM `tabLCS Project` p
           WHERE p.project_manager IS NOT NULL AND p.project_manager != ''
             AND NOT EXISTS (SELECT 1 FROM `tabEmployee` e WHERE e.name = p.project_manager)""",
        as_dict=True,
    )
    if bad_pm:
        _fail(f"{len(bad_pm)} LCS Projects have a deleted project_manager", bad_pm)
    else:
        _ok("project_manager links to existing Employees")

    # Team member links must resolve
    bad_tm = frappe.db.sql(
        """SELECT t.parent AS project, t.employee FROM `tabLCS Project Team Member` t
           WHERE t.employee IS NOT NULL AND t.employee != ''
             AND NOT EXISTS (SELECT 1 FROM `tabEmployee` e WHERE e.name = t.employee)""",
        as_dict=True,
    )
    if bad_tm:
        _fail(f"{len(bad_tm)} team-member rows reference deleted Employees", bad_tm)
    else:
        _ok("Team Members all resolve to existing Employees")

    # PM should also be a team member ideally — soft check
    pm_not_in_team = frappe.db.sql(
        """SELECT p.name, p.project_manager FROM `tabLCS Project` p
           WHERE p.project_manager IS NOT NULL AND p.project_manager != ''
             AND NOT EXISTS (
               SELECT 1 FROM `tabLCS Project Team Member` t
               WHERE t.parent = p.name AND t.employee = p.project_manager
             )""",
        as_dict=True,
    )
    if pm_not_in_team:
        _warn(f"{len(pm_not_in_team)} project managers are not also in their team table",
              [f"{r.name} (PM: {r.project_manager})" for r in pm_not_in_team])
    else:
        _ok("Every Project Manager appears in their project's team")


def _check_lms_chain():
    if not frappe.db.exists("DocType", "LMS Course"):
        _warn("LMS Course DocType not installed — LMS chain skipped")
        return

    # Required course links must resolve
    bad_courses = frappe.db.sql(
        """SELECT t.parent AS project, t.course FROM `tabLCS Project Required Training` t
           WHERE t.course IS NOT NULL AND t.course != ''
             AND NOT EXISTS (SELECT 1 FROM `tabLMS Course` c WHERE c.name = t.course)""",
        as_dict=True,
    )
    if bad_courses:
        _fail(f"{len(bad_courses)} required-training rows reference deleted LMS Courses", bad_courses)
    else:
        _ok("All required_trainings.course links resolve")

    total_proj = frappe.db.count("LCS Project")
    with_training = frappe.db.sql(
        "SELECT COUNT(DISTINCT parent) FROM `tabLCS Project Required Training`"
    )[0][0]
    _ok(f"{with_training}/{total_proj} projects have at least one required training defined")


def _check_fusion_chain():
    # Fusion is read-only — link integrity but no FK to a Frappe DocType
    with_fusion = frappe.db.count("LCS Project", {"fusion_item_id": ["is", "set"]})
    if with_fusion:
        _ok(f"{with_fusion} projects linked to Fusion Manage items")
    else:
        _warn("No projects linked to Fusion Manage items yet (integration not configured)")
