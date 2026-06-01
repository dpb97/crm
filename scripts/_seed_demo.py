"""Seed LCS Cable Cranes demo data. Run via bench console.
Flat-style — no top-level functions, so IPython's REPL doesn't
lose closures over module-level constants.

Run:
    bench --site lcs.local console < /tmp/_seed.py
"""
import frappe
from datetime import datetime, timedelta

# ----------------------------------------------------------------
# Pre-seed lookups
# ----------------------------------------------------------------
COMPANY = frappe.db.get_value("Company", {"is_group": 0}, "name") or frappe.db.get_value("Company", {}, "name")
DEFAULT_ITEM_GROUP = frappe.db.get_value("Item Group", {"is_group": 0}, "name") or "Products"
PARENT_TERR = frappe.db.get_value("Territory", {"is_group": 1}, "name") or "All Territories"
CUSTOMER_GROUP = frappe.db.get_value("Customer Group", {"is_group": 0}, "name") or "All Customer Groups"
SUPPLIER_GROUP = frappe.db.get_value("Supplier Group", {"is_group": 0}, "name") or "All Supplier Groups"
print("Using company: %s" % COMPANY)

# ----------------------------------------------------------------
# Customers (inline)
# ----------------------------------------------------------------
print("Seeding customers ...")
customers = []
for name, territory in [
    ("Vinci Construction Grands Projets", "Frankreich"),
    ("Hochtief AG",                       "Deutschland"),
    ("STRABAG SE",                        "Oesterreich"),
    ("Implenia Schweiz AG",               "Schweiz"),
    ("Skanska AB",                        "Skandinavien"),
]:
    if not frappe.db.exists("Territory", territory):
        frappe.get_doc({"doctype": "Territory", "territory_name": territory, "parent_territory": PARENT_TERR, "is_group": 0}).insert(ignore_permissions=True)
    if frappe.db.exists("Customer", name):
        customers.append(name); continue
    d = frappe.get_doc({"doctype": "Customer", "customer_name": name, "customer_type": "Company", "customer_group": CUSTOMER_GROUP, "territory": territory}).insert(ignore_permissions=True)
    customers.append(d.name)
print("  -> %d customers" % len(customers))

# ----------------------------------------------------------------
# Suppliers
# ----------------------------------------------------------------
print("Seeding suppliers ...")
suppliers = []
for name in ["Pfeifer Drako GmbH", "Brugg Lifting AG", "Siemens AG", "WTW Antriebstechnik GmbH"]:
    if frappe.db.exists("Supplier", name):
        suppliers.append(name); continue
    d = frappe.get_doc({"doctype": "Supplier", "supplier_name": name, "supplier_type": "Company", "supplier_group": SUPPLIER_GROUP}).insert(ignore_permissions=True)
    suppliers.append(d.name)
print("  -> %d suppliers" % len(suppliers))

# ----------------------------------------------------------------
# Items
# ----------------------------------------------------------------
print("Seeding items ...")
items = []
for code, desc, uom in [
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
]:
    if not frappe.db.exists("UOM", uom):
        frappe.get_doc({"doctype": "UOM", "uom_name": uom}).insert(ignore_permissions=True)
    if frappe.db.exists("Item", code):
        items.append(code); continue
    d = frappe.get_doc({"doctype": "Item", "item_code": code, "item_name": desc, "description": desc, "item_group": DEFAULT_ITEM_GROUP, "stock_uom": uom, "is_stock_item": 1}).insert(ignore_permissions=True)
    items.append(d.name)
print("  -> %d items" % len(items))

# ----------------------------------------------------------------
# Project Type
# ----------------------------------------------------------------
if not frappe.db.exists("Project Type", "External"):
    frappe.get_doc({"doctype": "Project Type", "project_type_name": "External"}).insert(ignore_permissions=True)

# ----------------------------------------------------------------
# Projects + Tasks
# ----------------------------------------------------------------
print("Seeding projects + tasks ...")
today = datetime.utcnow().date()
TASKS = [
    "Konstruktion", "Fertigung Mechanik", "Fertigung Elektrik",
    "Lieferung Baustelle", "Vor-Montage", "Endmontage",
    "Inbetriebnahme", "Werksabnahme", "Bauabnahme",
]
projects = []
for pn, cust, off, dur, kind in [
    ("Staudamm Engadin Materialseilbahn",       "Implenia Schweiz AG",              -60, 180, "Materialseilbahn"),
    ("Pylon-Montage Stelvio",                   "STRABAG SE",                       -30,  90, "Pylon-Montage"),
    ("Brueckenbau Loetschberg Sued",            "Vinci Construction Grands Projets", 10, 220, "Brueckenbau"),
    ("Talsperre Norge - Materialseilbahn",      "Skanska AB",                        20, 240, "Materialseilbahn"),
    ("Tunnel Gotthard Versorgung",              "Hochtief AG",                       45, 150, "Versorgung"),
    ("Wasserkraftwerk Wallis Hauptkran",        "Implenia Schweiz AG",               80, 270, "Krananlage"),
]:
    if frappe.db.exists("Project", {"project_name": pn}):
        projects.append(pn); continue
    s = today + timedelta(days=off)
    e = s + timedelta(days=dur)
    doc = frappe.get_doc({
        "doctype":           "Project",
        "project_name":      pn,
        "project_type":      "External",
        "customer":          cust,
        "expected_start_date": s.isoformat(),
        "expected_end_date":   e.isoformat(),
        "status":            "Open",
        "company":           COMPANY,
    }).insert(ignore_permissions=True)
    slice_d = max(1, dur // len(TASKS))
    for idx, t in enumerate(TASKS):
        ts = s + timedelta(days=idx * slice_d)
        te = ts + timedelta(days=slice_d - 1)
        frappe.get_doc({
            "doctype":  "Task",
            "subject":  "%s - %s" % (t, kind),
            "project":  doc.name,
            "exp_start_date": ts.isoformat(),
            "exp_end_date":   te.isoformat(),
            "status":   "Open",
        }).insert(ignore_permissions=True)
    projects.append(doc.name)
print("  -> %d projects, %d tasks" % (len(projects), frappe.db.count("Task")))

# ----------------------------------------------------------------
# Pilanda News
# ----------------------------------------------------------------
print("Seeding news ...")
news = []
if frappe.db.table_exists("Pilanda News"):
    for title, cat, pinned, summary, body in [
        ("Pilanda v1.0 ausgerollt", "Release", 1,
         "Die einheitliche Navigation fuer den LCS-ERP-Stack ist freigegeben.",
         "<p>Mit v1.0 laeuft die Pilanda-Navigation als eigene Vue-3-App ueber Frappe Desk, Frappe CRM, Helpdesk, LMS und Builder mit derselben Brand und Sub-Modulen, einem 'Zur Uebersicht'-Link unten links.</p>"),
        ("Fruehwarnungs-Modul live", "Produkt", 0,
         "PLS unterstuetzt Eskalationspfade mit Schwellwerten je Projekt-Typ.",
         "<p>Die LCS-Fruehwarnung erfasst Termin-, Budget- und Qualitaetskonflikte direkt am Projekt - mit Verantwortlichem und Verlauf.</p>"),
        ("Onboarding-Workshop am 12.06.", "Veranstaltung", 0,
         "Vertrieb + Projektmanagement lernen die neue Pilanda-Navigation kennen.",
         "<p>Anmeldung beim Pilanda-Projektteam. Dauer ca. 90 min, online via Teams.</p>"),
        ("Demo-Daten neu eingespielt", "Unternehmen", 0,
         "Sechs typische LCS-Projekte vom Staudamm bis zum Tunnel als Sandbox-Daten.",
         "<p>Reset der Sandbox: 5 Kunden, 4 Lieferanten, 12 Artikel, 6 Cable-Crane-Installationen mit jeweils 9 Tasks.</p>"),
        ("Vertrieb laeuft im CRM (Frappe)", "Release", 0,
         "Der Pilanda-Eintrag 'Vertrieb' fuehrt direkt in /crm.",
         "<p>Brand-Logo und Titel der Frappe-CRM-SPA sind auf 'Vertrieb' + Pilanda-Mark gesetzt - visuell ein Pilanda-Modul, technisch die volle Frappe-CRM-Funktionalitaet.</p>"),
    ]:
        if frappe.db.exists("Pilanda News", {"title": title}):
            news.append(title); continue
        d = frappe.get_doc({
            "doctype":      "Pilanda News",
            "title":        title,
            "category":     cat,
            "is_pinned":    pinned,
            "is_published": 1,
            "summary":      summary,
            "body":         body,
        }).insert(ignore_permissions=True)
        news.append(d.name)
print("  -> %d news" % len(news))

frappe.db.commit()
print("\nDone.")
