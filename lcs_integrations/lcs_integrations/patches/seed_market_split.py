"""Seed the LCS market-split data model (R03, 2026-03-11).

Idempotent. Re-running this patch overwrites the territory / segment
ownership data; user-side `sales_manager` (User) links are preserved
when already set so the User mapping survives subsequent runs.

Source: `Marktaufteilung-2026_R03.xlsx`, sheet *Overview*.
"""

from __future__ import annotations

import frappe


# 11 product / business segments as listed in the market-split sheet.
SEGMENTS: list[str] = [
    "Mining",
    "Hydropower / Civil Construction",
    "Pipeline (Oil and Gas)",
    "Mountain Construction Sites",
    "Bridge Construction / Infrastructure",
    "Ropeway Installation and Civil Construction",
    "QX / Safety Systems",
    "Seilkrananlagen 6 - 25to",
    "Dualsystem",
    "QXcranes",
    "TK - Kabelkrananlagen",
]


# Segment responsibility matrix from the lower block of the sheet.
# (segment, lead_code, deputy_code)
SEGMENT_RESPONSIBILITY: list[tuple[str, str, str]] = [
    ("Mining", "JFA & PKO", "CLU"),
    ("Hydropower / Civil Construction", "CLU", "JFA"),
    ("Pipeline (Oil and Gas)", "CLU", "JFA"),
    ("Mountain Construction Sites", "JFA (CLU)", "CLU"),
    ("Bridge Construction / Infrastructure", "JFA (CLU)", "CLU"),
    ("Ropeway Installation and Civil Construction", "CLU", "JFA"),
    ("QX / Safety Systems", "PKO", "JFA"),
]


# Territories from sheet *Overview* (rows 1.x .. 5.x).
# Tuple format:
#   (territory_name, region, sub_region, sm_code, deputy_code,
#    agent_name, priority, country_list, active_segments_list)
#
# `country_list` uses Frappe's standard Country names. A territory that
# represents a region (LATAM, Middle East, …) has an empty country
# list — auto-assign only kicks in once a country mapping is provided
# manually for that region.
_S = SEGMENTS  # alias for brevity
_ALL_SEG = _S
_NO_TK = [s for s in _S if s != "TK - Kabelkrananlagen"]

TERRITORIES: list[tuple] = [
    # Amerika
    ("LATAM", "Amerika", "Südamerika", "JFA", "", "Servinge", "Go",
     ["Argentina", "Chile", "Peru", "Colombia", "Venezuela", "Ecuador",
      "Bolivia", "Paraguay", "Uruguay", "Guyana", "Suriname"], _ALL_SEG),
    ("Brazil", "Amerika", "Südamerika", "JFA", "", "LCS-Brazil & Servinge", "Go",
     ["Brazil"], _ALL_SEG),
    ("Mittelamerika", "Amerika", "Mittelamerika", "JFA", "", "Servinge", "Go",
     ["Mexico", "Belize", "Costa Rica", "El Salvador", "Guatemala", "Honduras",
      "Nicaragua", "Panama"], _ALL_SEG),
    ("Karibik", "Amerika", "Mittelamerika", "JFA", "", "Servinge", "Go",
     ["Cuba", "Jamaica", "Haiti", "Dominican Republic", "Bahamas", "Barbados",
      "Trinidad and Tobago"],
     ["Hydropower / Civil Construction", "Mountain Construction Sites",
      "Bridge Construction / Infrastructure",
      "Ropeway Installation and Civil Construction",
      "Seilkrananlagen 6 - 25to"]),
    ("USA", "Amerika", "Nordamerika", "JFA", "", "", "Go",
     ["United States"], _NO_TK),
    ("Canada", "Amerika", "Nordamerika", "JFA", "", "Semir", "Go",
     ["Canada"], _NO_TK),
    # Europa
    ("Europa", "Europa", "", "PKO", "", "", "Go",
     ["Germany", "Austria", "Switzerland", "France", "Italy", "Spain",
      "Portugal", "Belgium", "Netherlands", "Luxembourg", "Liechtenstein",
      "Monaco", "United Kingdom", "Ireland", "Norway", "Sweden", "Finland",
      "Denmark", "Iceland", "Estonia", "Latvia", "Lithuania", "Greece",
      "Croatia", "Slovenia", "Serbia", "Bosnia and Herzegovina", "Montenegro",
      "Albania", "North Macedonia", "Malta", "Poland", "Czech Republic",
      "Slovakia", "Hungary", "Romania", "Bulgaria", "Moldova"],
     ["Mining", "Hydropower / Civil Construction", "Pipeline (Oil and Gas)",
      "Mountain Construction Sites", "Bridge Construction / Infrastructure",
      "Ropeway Installation and Civil Construction", "Seilkrananlagen 6 - 25to"]),
    ("GUS", "Europa", "Osteuropa", "PKO", "", "STEF UG - Consultant", "Go",
     ["Belarus", "Ukraine", "Russia"], _NO_TK),
    # Afrika
    ("East&South Africa", "Afrika", "", "JFA", "", "", "Maintain",
     ["Kenya", "Tanzania", "Uganda", "Ethiopia", "Somalia", "Rwanda",
      "Burundi", "South Africa", "Namibia", "Botswana", "Lesotho", "Eswatini",
      "Zimbabwe", "Zambia", "Mozambique", "Malawi"], _NO_TK),
    ("West/North Africa", "Afrika", "", "JFA", "", "", "Maintain",
     ["Egypt", "Algeria", "Morocco", "Tunisia", "Libya", "Sudan", "Nigeria",
      "Ghana", "Senegal", "Ivory Coast", "Mali", "Burkina Faso", "Niger"],
     _NO_TK),
    # Ozeanien
    ("Australia", "Ozeanien", "", "DRO", "CLU", "NACAP", "Go",
     ["Australia"], _NO_TK),
    ("New Zealand", "Ozeanien", "", "CLU", "DRO", "", "Go",
     ["New Zealand"], _NO_TK),
    ("Papua New Guinea", "Ozeanien", "", "CLU", "DRO", "NACAP", "Go",
     ["Papua New Guinea"], _NO_TK),
    # Asien
    ("India", "Asien", "Südasien", "CLU", "", "VASU Chemicals", "Go",
     ["India"], _NO_TK),
    ("Bhutan", "Asien", "Südasien", "CLU", "", "Amoda Enterprise", "Maintain",
     ["Bhutan"],
     ["Hydropower / Civil Construction", "Pipeline (Oil and Gas)",
      "Seilkrananlagen 6 - 25to"]),
    ("Nepal", "Asien", "Südasien", "CLU", "", "Sanket Lamichhane", "Go",
     ["Nepal"],
     ["Mining", "Hydropower / Civil Construction", "Pipeline (Oil and Gas)",
      "Mountain Construction Sites", "Bridge Construction / Infrastructure",
      "Ropeway Installation and Civil Construction", "Seilkrananlagen 6 - 25to"]),
    ("Middle East", "Asien", "Westasien", "CLU", "", "", "Go",
     [], _NO_TK),
    ("Oman", "Asien", "Westasien", "CLU", "", "KHIMJI", "Go",
     ["Oman"], _NO_TK),
    ("United Arab Emirates", "Asien", "Westasien", "CLU", "", "Stefan Brändle", "Go",
     ["United Arab Emirates"], _NO_TK),
    ("Saudi Arabia", "Asien", "Westasien", "CLU", "", "Stefan Brändle", "Go",
     ["Saudi Arabia"], _NO_TK),
    ("Japan", "Asien", "Ostasien", "CLU", "", "Nippon Cable", "Go",
     ["Japan"], _NO_TK),
    ("Central Asia", "Asien", "Zentralasien", "PKO", "", "STEF UG - Consultant", "Go",
     ["Kazakhstan", "Kyrgyzstan", "Tajikistan", "Uzbekistan", "Turkmenistan"],
     _NO_TK),
]


def _upsert_segments() -> None:
    for name in SEGMENTS:
        if frappe.db.exists("LCS Segment", name):
            continue
        frappe.get_doc({
            "doctype": "LCS Segment",
            "segment_name": name,
            "is_active": 1,
        }).insert(ignore_permissions=True)


def _upsert_responsibility() -> None:
    for segment, lead_code, deputy_code in SEGMENT_RESPONSIBILITY:
        if frappe.db.exists("LCS Segment Responsibility", segment):
            doc = frappe.get_doc("LCS Segment Responsibility", segment)
            doc.lead_code = lead_code
            doc.deputy_code = deputy_code
            doc.save(ignore_permissions=True)
        else:
            frappe.get_doc({
                "doctype": "LCS Segment Responsibility",
                "segment": segment,
                "lead_code": lead_code,
                "deputy_code": deputy_code,
            }).insert(ignore_permissions=True)


def _country_exists(name: str) -> bool:
    return bool(frappe.db.exists("Country", name))


def _upsert_territories() -> None:
    for (territory_name, region, sub_region, sm_code, deputy_code,
         agent_name, priority, countries, segments) in TERRITORIES:

        valid_countries = [c for c in countries if _country_exists(c)]
        if len(valid_countries) != len(countries):
            missing = sorted(set(countries) - set(valid_countries))
            frappe.log_error(
                title="LCS market-split seed: missing countries",
                message=f"Territory '{territory_name}': {missing}",
            )

        valid_segments = [s for s in segments if frappe.db.exists("LCS Segment", s)]

        if frappe.db.exists("LCS Sales Territory", territory_name):
            doc = frappe.get_doc("LCS Sales Territory", territory_name)
            # Preserve manually-set User links across re-seeds.
            preserved_user = doc.sales_manager
            preserved_deputy_user = doc.deputy_sales_manager
        else:
            doc = frappe.new_doc("LCS Sales Territory")
            doc.territory_name = territory_name
            preserved_user = None
            preserved_deputy_user = None

        doc.region = region
        doc.sub_region = sub_region or None
        doc.sales_manager_code = sm_code
        doc.deputy_sales_manager_code = deputy_code or None
        if preserved_user:
            doc.sales_manager = preserved_user
        if preserved_deputy_user:
            doc.deputy_sales_manager = preserved_deputy_user
        doc.agent_name = agent_name or None
        doc.priority = priority
        doc.is_active = 1

        doc.set("countries", [])
        for c in valid_countries:
            doc.append("countries", {"country": c})

        doc.set("segments", [])
        for s in valid_segments:
            doc.append("segments", {"segment": s, "is_active": 1})

        doc.save(ignore_permissions=True)


def execute() -> None:
    _upsert_segments()
    _upsert_responsibility()
    _upsert_territories()
    frappe.cache().delete_key("lcs_country_territory_map")
    frappe.db.commit()
