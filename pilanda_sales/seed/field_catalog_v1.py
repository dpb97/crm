"""Seed des Feldkatalogs Version 1 (106 Felder) — Phase 1.4 (b).

Quelle der Wahrheit: `ImportzuPILANDA/10_DOSSIER_QUESTIONNAIRE.md` §2 (GESICHERT-
Extraktion aus `static/questionnaire_catalog.js`, App-Version). E-16: der Katalog
lebt als DB-Datensaetze; KEIN JS/Excel eingebunden.

Aufbau: 9 Kunden-Sektionen (86 Felder) + 12 Companion-Felder + 1 Pseudo-Sektion
`lcs_internal` (8 nur-interne Felder) = 106 Field-Records.

Companion-Mechanik (exklusiv, Dossier 10 §2.12): der PARENT traegt
companion_mode (other|specify) + companion_id; das Companion-Freitextfeld ist ein
eigener Record (Typ text). Companion-Labels sind generisch abgeleitet (die
autoritativen Labels stehen in catalog.js) — bei Bedarf nachziehen.

Idempotent: legt Katalog "1" nur an, wenn er noch nicht existiert.

Aufruf:  bench --site <site> execute pilanda_sales.seed.field_catalog_v1.seed_v1
"""

from __future__ import annotations

import frappe

CATALOG_VERSION = "1"
CATALOG_NAME = f"FieldCatalog-{CATALOG_VERSION}"

# (section_id, title_en, sort_order)
SECTIONS: list[tuple[str, str, int]] = [
    ("contact", "Contact Information", 1),
    ("project", "Project Information", 2),
    ("material", "Material Handled", 3),
    ("personnel", "Personnel Transport", 4),
    ("operating", "Operating Data", 5),
    ("geometry", "Installation Data / Geometry", 6),
    ("energy", "Energy Supply (Drive Station)", 7),
    ("environmental", "Site Conditions & Environmental Aspects", 8),
    ("standards", "Standards, Regulations & Additional", 9),
    ("lcs_internal", "LCS (intern)", 99),
]

# Kompakte Felddefinition: (section, field_id, label_en, field_type, options,
#   companion_mode, companion_id, internal_only)
# options = Liste von Strings (value == label). "" = keine.
T = "text"; N = "number"; TA = "textarea"; R = "radio"; M = "multi"
_F = []  # (section, fid, label, type, options, comp_mode, comp_id, internal)

def _f(section, fid, label, ftype, options=None, comp_mode="", comp_id="", internal=0):
    _F.append((section, fid, label, ftype, options or [], comp_mode, comp_id, internal))

# --- 1 contact ---
_f("contact", "company", "Company", T)
_f("contact", "street", "Street", T)
_f("contact", "street_number", "No.", T)
_f("contact", "zip", "ZIP / Postal Code", T)
_f("contact", "city", "City", T)
_f("contact", "state", "State", T)
_f("contact", "province", "Province / Region", T)
_f("contact", "country_customer", "Country", T)
_f("contact", "contact_person", "Contact Person", T)
_f("contact", "email", "E-Mail", "email")
_f("contact", "office_phone", "Office Phone", "tel")
_f("contact", "mobile_phone", "Mobile Phone", "tel")
_f("contact", "customer_role", "Customer role (please select one)", R,
   ["Owner", "Contractor", "Consultant", "Other"], "other", "customer_role_other")
_f("contact", "customer_role_other", "Other (please specify)", T)

# --- 2 project ---
_f("project", "project_name", "Project name", T)
_f("project", "sector", "Sector", R,
   ["Hydropower", "Oil&Gas", "Mountain Construction", "Bridge Construction", "Mining", "Other"],
   "other", "sector_other")
_f("project", "sector_other", "Other (please specify)", T)
_f("project", "country_project", "Country (Project)", T)
_f("project", "location", "Location / Region", T)
_f("project", "start_date", "Expected project start date", "month")
_f("project", "duration_months", "Expected duration (months)", N)
_f("project", "description", "Project description (scope, cable-crane use)", TA)
_f("project", "project_files", "Project documents (PDF, images, sketches; multi)", "file")

# --- 3 material ---
_f("material", "material_bulk", "Bulk material", T)
_f("material", "material_unit_loads", "Unit loads", T)
_f("material", "material_others", "Others", T)
_f("material", "bulk_density_max", "Bulk density max (kg/m3)", N)
_f("material", "bulk_density_min", "Bulk density min (kg/m3)", N)
_f("material", "weight_per_load_max", "Weight per single load max (kg/pcs)", N)
_f("material", "weight_per_load_min", "Weight per single load min (kg/pcs)", N)
_f("material", "dimensions", "Overall dimension (L x W x H) m", T)
_f("material", "weather_protection", "Protection against weather", R, ["Yes", "No"],
   "specify", "weather_protection_reason")
_f("material", "weather_protection_reason", "Please specify", T)
_f("material", "other_characteristics", "Other characteristics", TA)

# --- 4 personnel ---
_f("personnel", "personnel_required", "Personnel transport required?", R, ["Yes", "No"],
   "specify", "personnel_reason")
_f("personnel", "personnel_reason", "Please specify", T)
_f("personnel", "personnel_capacity_value", "Capacity", N)
_f("personnel", "personnel_capacity_unit", "Unit", R, ["Persons / Trip", "Persons / Day"])

# --- 5 operating (keine Companions) ---
_f("operating", "payload", "Requested PAYLOAD (metric tonnes)", N)
_f("operating", "direction", "Direction of transport", R, ["in one direction", "in both directions"])
_f("operating", "direction_loads", "If both directions - kind of loads", T)
_f("operating", "capacity_value", "Requested capacity", N)
_f("operating", "capacity_unit", "Capacity unit", R, ["Metric tonnes / h", "Pcs. / h"])
_f("operating", "operation_period_value", "Estimated operation period", N)
_f("operating", "operation_period_unit", "Period unit", R, ["months", "years"])
_f("operating", "operation_amount_value", "Estimated operation time per unit", N)
_f("operating", "operation_amount_unit", "Unit", R,
   ["hours per day", "days per week", "weeks per month", "months per year"])
_f("operating", "operating_shifts", "Operating shifts (multiple)", M,
   ["Morning shift", "Afternoon shift", "Night shift"])
_f("operating", "commissioning_date", "Preferred commissioning date", "month")
_f("operating", "third_party_cert", "Third party certification required?", R, ["Yes", "No"])

# --- 6 geometry ---
_f("geometry", "horizontal_length", "Horizontal transport length (m)", N)
_f("geometry", "altitude_bottom", "Altitude of bottom station (m.a.s.l.)", N)
_f("geometry", "altitude_top", "Altitude of top station (m.a.s.l.)", N)
_f("geometry", "altitude_bottom_gps", "Bottom station GPS", T)
_f("geometry", "altitude_bottom_utm", "Bottom station UTM", T)
_f("geometry", "altitude_top_gps", "Top station GPS", T)
_f("geometry", "altitude_top_utm", "Top station UTM", T)
_f("geometry", "unloading_areas", "Unloading areas", R,
   ["Along the track", "Only at unloading station (Top/Bottom)", "Other"], "other", "unloading_other")
_f("geometry", "unloading_other", "Other (please specify)", T)
_f("geometry", "drive_location", "Preferred location of drive system", R,
   ["Top station", "Bottom station", "Other"], "other", "drive_location_other")
_f("geometry", "drive_location_other", "Other (please specify)", T)
_f("geometry", "accessibility", "Accessibility of site", TA)
_f("geometry", "contour_map_attached", "Contour map with longitudinal profile attached?", R, ["Yes", "No"])
_f("geometry", "pictures_attached", "Pictures / sketches attached?", R, ["Yes", "No"])
_f("geometry", "attachment_link", "Link to attachments", T)
_f("geometry", "geometry_files", "Geometry attachments (multi)", "file")

# --- 7 energy ---
_f("energy", "power_source", "Available source of power", R,
   ["Electricity", "Diesel Power Generator", "None", "Other"], "other", "power_source_other")
_f("energy", "power_source_other", "Other (please specify)", T)
_f("energy", "power_capacity_value", "Available power capacity", N)
_f("energy", "power_capacity_unit", "Capacity unit", R, ["kW", "kVA"])
_f("energy", "power_comments", "Comments", TA)

# --- 8 environmental ---
_f("environmental", "temp_min", "Ambient temperature min (C)", N)
_f("environmental", "temp_max", "Ambient temperature max (C)", N)
_f("environmental", "humidity_value", "Average humidity", N)
_f("environmental", "humidity_unit", "Humidity unit", R, ["g/m3", "%", "mmHg"])
_f("environmental", "corrosive", "Corrosive media", TA)
_f("environmental", "wind_speed", "Wind speed out of operation (m/s)", N)
_f("environmental", "wind_pressure", "Wind pressure out of operation (N/m2)", N)
_f("environmental", "snow_pressure", "Snow pressure (kN/m2)", N)
_f("environmental", "snow_creep", "Snow pack, snow creep", TA)
_f("environmental", "ice_load", "Ice load", TA)
_f("environmental", "avalanche", "Avalanche", TA)
_f("environmental", "rockfall", "Rockfall", TA)
_f("environmental", "seismic", "Seismic", TA)
_f("environmental", "vegetation", "Vegetation (e.g. tree height)", TA)
_f("environmental", "row_meters", "Available ROW (right of way) (m)", N)
_f("environmental", "interferences", "Interferences with infrastructure along the track?", R,
   ["Yes", "No"], "specify", "interferences_text")
_f("environmental", "interferences_text", "Please specify", TA)
_f("environmental", "air_traffic", "Air traffic control requirements?", R, ["Yes", "No"],
   "specify", "air_traffic_text")
_f("environmental", "air_traffic_text", "Please specify", TA)
_f("environmental", "residential", "Affects residential areas or nature reserves?", R,
   ["Yes", "No"], "specify", "residential_text")
_f("environmental", "residential_text", "Please specify", TA)

# --- 9 standards ---
_f("standards", "specific_standards", "Specific standards to be considered?", R, ["Yes", "No"],
   "specify", "specific_standards_text")
_f("standards", "specific_standards_text", "Please specify", TA)
_f("standards", "specific_regulations", "Specific regulations to be considered?", R, ["Yes", "No"],
   "specify", "specific_regulations_text")
_f("standards", "specific_regulations_text", "Please specify", TA)
_f("standards", "additional_info", "Additional information", TA)
_f("standards", "links", "Links (URLs, document references)", TA)

# --- LCS-intern (8, nur Editor) ---
_f("lcs_internal", "customer_short", "Customer (short)", T, internal=1)
_f("lcs_internal", "project_short_name", "Project short name", T, internal=1)
_f("lcs_internal", "project_no", "LCS project no.", T, internal=1)
_f("lcs_internal", "template_type", "Document type", R, ["rental", "sale"], internal=1)
_f("lcs_internal", "project_type", "Project type", R, ["standard", "bigproject"], internal=1)
_f("lcs_internal", "parts_condition", "Parts condition", R, ["used", "new"], internal=1)
_f("lcs_internal", "proposal_purpose", "Proposal purpose", "select_master",
   ["Commercial proposal", "Pre-bid evaluation", "Evaluation only", "Technical proposal",
    "Budgetary Proposal", "Rental Proposal", "Purchase Proposal"], internal=1)
_f("lcs_internal", "purchase_option_included", "Purchase option included", "bool", internal=1)


def seed_v1() -> None:
    """Idempotent: legt Feldkatalog Version 1 mit 106 Feldern an (falls noch nicht da)."""
    if frappe.db.exists("Field Catalog", CATALOG_NAME):
        print(f"Field Catalog {CATALOG_NAME} existiert bereits — uebersprungen.")
        return

    frappe.get_doc({
        "doctype": "Field Catalog",
        "catalog_version": CATALOG_VERSION,
        "title": "LCS Sales Questionnaire (App v1)",
        "language": "en",
        "is_active": 1,
    }).insert()

    for section_id, title_en, order in SECTIONS:
        frappe.get_doc({
            "doctype": "Field Catalog Section",
            "catalog": CATALOG_NAME,
            "section_id": section_id,
            "title_en": title_en,
            "sort_order": order,
        }).insert()

    n = 0
    for section, fid, label, ftype, options, comp_mode, comp_id, internal in _F:
        doc = {
            "doctype": "Field Catalog Field",
            "catalog": CATALOG_NAME,
            "section": f"{CATALOG_NAME}::{section}",
            "field_id": fid,
            "label_en": label,
            "field_type": ftype,
            "layout_weight": 1,
            "internal_only": internal,
            "companion_mode": comp_mode,
            "companion_id": comp_id,
            "companion_trigger": "Yes" if comp_mode == "specify" else "",
            "options": [{"value": o, "option_label": o} for o in options],
        }
        frappe.get_doc(doc).insert()
        n += 1

    frappe.db.commit()
    print(f"Feldkatalog {CATALOG_NAME}: {len(SECTIONS)} Sektionen, {n} Felder angelegt.")
