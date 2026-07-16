"""Seed LCS Cable Cranes demo data using raw SQL INSERTs so
installed apps' doc_events (next_pms, fusion_manage, bsm) that
reference now-removed custom_* fields don't crash the run.

Run via bench console:
    bench --site lcs.local console < /tmp/_seed.py
"""
import frappe
from datetime import datetime, timedelta

NOW = frappe.utils.now()
ADMIN = "Administrator"

# ---------------------------------------------------------------
# SQL insert helper — adds the standard Frappe meta columns.
# ---------------------------------------------------------------
def sql_insert(doctype, name, **vals):
    full = {
        "name":        name,
        "owner":       ADMIN,
        "creation":    NOW,
        "modified":    NOW,
        "modified_by": ADMIN,
        "docstatus":   0,
        "idx":         0,
        **vals,
    }
    cols = ", ".join("`%s`" % k for k in full.keys())
    placeholders = ", ".join(["%s"] * len(full))
    table = "tab" + doctype
    frappe.db.sql(
        "INSERT IGNORE INTO `%s` (%s) VALUES (%s)" % (table, cols, placeholders),
        list(full.values()),
    )
    return name

# ---------------------------------------------------------------
# Lookups
# ---------------------------------------------------------------
COMPANY        = frappe.db.get_value("Company", {}, "name")
ITEM_GROUP     = frappe.db.get_value("Item Group", {"is_group": 0}, "name") or "Products"
PARENT_TERR    = frappe.db.get_value("Territory", {"is_group": 1}, "name") or "All Territories"
CUSTOMER_GROUP = frappe.db.get_value("Customer Group", {"is_group": 0}, "name") or "All Customer Groups"
SUPPLIER_GROUP = frappe.db.get_value("Supplier Group", {"is_group": 0}, "name") or "All Supplier Groups"
print("Using company: %s" % COMPANY)

# ---------------------------------------------------------------
# Territories
# ---------------------------------------------------------------
for terr in ["Frankreich", "Deutschland", "Oesterreich", "Schweiz", "Skandinavien"]:
    if not frappe.db.exists("Territory", terr):
        sql_insert("Territory", terr,
            territory_name=terr, parent_territory=PARENT_TERR, is_group=0, lft=0, rgt=0)

# ---------------------------------------------------------------
# Customers
# ---------------------------------------------------------------
CUSTOMERS = [
    ("Vinci Construction Grands Projets", "Frankreich"),
    ("Hochtief AG",                       "Deutschland"),
    ("STRABAG SE",                        "Oesterreich"),
    ("Implenia Schweiz AG",               "Schweiz"),
    ("Skanska AB",                        "Skandinavien"),
]
for cname, terr in CUSTOMERS:
    if frappe.db.exists("Customer", cname):
        continue
    sql_insert("Customer", cname,
        customer_name=cname, customer_type="Company",
        customer_group=CUSTOMER_GROUP, territory=terr,
        is_internal_customer=0, disabled=0, is_frozen=0,
        language="en")
print("Customers   : %d" % frappe.db.count("Customer"))

# ---------------------------------------------------------------
# Suppliers
# ---------------------------------------------------------------
SUPPLIERS = ["Pfeifer Drako GmbH", "Brugg Lifting AG", "Siemens AG", "WTW Antriebstechnik GmbH"]
for sname in SUPPLIERS:
    if frappe.db.exists("Supplier", sname):
        continue
    sql_insert("Supplier", sname,
        supplier_name=sname, supplier_type="Company",
        supplier_group=SUPPLIER_GROUP, disabled=0, language="en")
print("Suppliers   : %d" % frappe.db.count("Supplier"))

# ---------------------------------------------------------------
# UOM
# ---------------------------------------------------------------
for u in ["Meter", "Nos"]:
    if not frappe.db.exists("UOM", u):
        sql_insert("UOM", u, uom_name=u, enabled=1)

# ---------------------------------------------------------------
# Items
# ---------------------------------------------------------------
ITEMS = [
    ("SEIL-32",   "Stahlseil 32 mm",      "Meter"),
    ("SEIL-40",   "Stahlseil 40 mm",      "Meter"),
    ("SEIL-48",   "Stahlseil 48 mm",      "Meter"),
    ("TROM-1500", "Trommel 1500 kg",      "Nos"),
    ("TROM-3000", "Trommel 3000 kg",      "Nos"),
    ("TROM-5000", "Trommel 5000 kg",      "Nos"),
    ("ANTR-90",   "Antrieb 90 kW",        "Nos"),
    ("ANTR-160",  "Antrieb 160 kW",       "Nos"),
    ("STG-HMI",   "Steuerung HMI Panel",  "Nos"),
    ("PYL-STD",   "Pylon Standard Modul", "Nos"),
    ("WAGEN-A",   "Laufwagen Typ A",      "Nos"),
    ("FB-STD",    "Fangbremse Standard",  "Nos"),
]
for code, desc, uom in ITEMS:
    if frappe.db.exists("Item", code):
        continue
    sql_insert("Item", code,
        item_code=code, item_name=desc, description=desc,
        item_group=ITEM_GROUP, stock_uom=uom, is_stock_item=1,
        disabled=0, has_variants=0, is_sales_item=1, is_purchase_item=1,
        include_item_in_manufacturing=0, allow_alternative_item=0,
        valuation_method="", standard_rate=0)
print("Items       : %d" % frappe.db.count("Item"))

# ---------------------------------------------------------------
# Project Type
# ---------------------------------------------------------------
if not frappe.db.exists("Project Type", "External"):
    sql_insert("Project Type", "External", project_type_name="External")

# ---------------------------------------------------------------
# Projects + Tasks
# ---------------------------------------------------------------
today = datetime.utcnow().date()
TASKS = [
    "Konstruktion", "Fertigung Mechanik", "Fertigung Elektrik",
    "Lieferung Baustelle", "Vor-Montage", "Endmontage",
    "Inbetriebnahme", "Werksabnahme", "Bauabnahme",
]
PROJECTS = [
    ("Staudamm Engadin Materialseilbahn",       "Implenia Schweiz AG",              -60, 180, "Materialseilbahn"),
    ("Pylon-Montage Stelvio",                   "STRABAG SE",                       -30,  90, "Pylon-Montage"),
    ("Brueckenbau Loetschberg Sued",            "Vinci Construction Grands Projets", 10, 220, "Brueckenbau"),
    ("Talsperre Norge - Materialseilbahn",      "Skanska AB",                        20, 240, "Materialseilbahn"),
    ("Tunnel Gotthard Versorgung",              "Hochtief AG",                       45, 150, "Versorgung"),
    ("Wasserkraftwerk Wallis Hauptkran",        "Implenia Schweiz AG",               80, 270, "Krananlage"),
]
proj_count = 0
task_count = 0
for idx, (pn, cust, off, dur, kind) in enumerate(PROJECTS, 1):
    if frappe.db.exists("Project", {"project_name": pn}):
        continue
    s = today + timedelta(days=off)
    e = s + timedelta(days=dur)
    pname = "PROJ-%05d" % idx
    sql_insert("Project", pname,
        project_name=pn, project_type="External", customer=cust,
        expected_start_date=s.isoformat(), expected_end_date=e.isoformat(),
        status="Open", company=COMPANY, percent_complete=0,
        is_active="Yes", priority="Medium")
    proj_count += 1
    slice_d = max(1, dur // len(TASKS))
    for tidx, tname in enumerate(TASKS):
        ts = s + timedelta(days=tidx * slice_d)
        te = ts + timedelta(days=slice_d - 1)
        tn = "TASK-%05d-%02d" % (idx, tidx + 1)
        sql_insert("Task", tn,
            subject="%s - %s" % (tname, kind),
            project=pname,
            exp_start_date=ts.isoformat(),
            exp_end_date=te.isoformat(),
            status="Open", priority="Medium",
            progress=0, is_group=0, is_template=0,
            is_milestone=0)
        task_count += 1
print("Projects    : %d (+%d)" % (frappe.db.count("Project"), proj_count))
print("Tasks       : %d (+%d)" % (frappe.db.count("Task"), task_count))

# ---------------------------------------------------------------
# Pilanda News
# ---------------------------------------------------------------
news_count = 0
if frappe.db.table_exists("Pilanda News"):
    NEWS = [
        ("PN-0001", "Pilanda v1.0 ausgerollt",       "Release",      1,
         "Die einheitliche Navigation fuer den LCS-ERP-Stack ist freigegeben.",
         "<p>Mit v1.0 laeuft die Pilanda-Navigation als eigene Vue-3-App ueber Frappe Desk, Frappe CRM, Helpdesk, LMS und Builder.</p>"),
        ("PN-0002", "Fruehwarnungs-Modul live",      "Produkt",      0,
         "PLS unterstuetzt Eskalationspfade mit Schwellwerten je Projekt-Typ.",
         "<p>Die LCS-Fruehwarnung erfasst Termin-, Budget- und Qualitaetskonflikte direkt am Projekt.</p>"),
        ("PN-0003", "Onboarding-Workshop am 12.06.", "Veranstaltung", 0,
         "Vertrieb + Projektmanagement lernen die neue Pilanda-Navigation kennen.",
         "<p>Anmeldung beim Pilanda-Projektteam. Dauer ca. 90 min, online via Teams.</p>"),
        ("PN-0004", "Demo-Daten neu eingespielt",    "Unternehmen",   0,
         "Sechs typische LCS-Projekte vom Staudamm bis zum Tunnel als Sandbox-Daten.",
         "<p>Reset der Sandbox: 5 Kunden, 4 Lieferanten, 12 Artikel, 6 Cable-Crane-Installationen mit jeweils 9 Tasks.</p>"),
        ("PN-0005", "Vertrieb laeuft im CRM (Frappe)", "Release",     0,
         "Der Pilanda-Eintrag 'Vertrieb' fuehrt direkt in /crm.",
         "<p>Brand-Logo und Titel der Frappe-CRM-SPA sind auf 'Vertrieb' + Pilanda-Mark gesetzt.</p>"),
    ]
    for n, title, cat, pinned, summary, body in NEWS:
        if frappe.db.exists("Pilanda News", n):
            continue
        sql_insert("Pilanda News", n,
            title=title, category=cat, is_pinned=pinned,
            is_published=1, summary=summary, body=body,
            author=ADMIN, published_on=NOW)
        news_count += 1
print("Pilanda News: %d (+%d)" % (frappe.db.count("Pilanda News"), news_count))

frappe.db.commit()
print("\nDone.")
