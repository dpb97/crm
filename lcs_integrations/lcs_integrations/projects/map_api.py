"""Whitelisted backend for the LCS Projects map page.

Returns one record per LCS Project, joined with its country centroid so
the SPA can plot it on a Leaflet map. Country coordinates come from a
static lookup table below — Frappe's `Country` DocType carries no
lat/lng, and geocoding every customer address is overkill for a
"where are our projects" overview.

If a project's country is missing from the table the record is still
returned, but `lat`/`lng` are None and the frontend will list it under
"unmapped". Add coordinates here when new countries enter the
market-split.
"""

from __future__ import annotations

import frappe


# (lat, lng) centroid per Frappe `Country.name`. Approximate — geographic
# centre or capital, whichever gives a more useful "this is roughly
# where the work is". Source: well-known geo references; values rounded
# to 1 decimal so the table is auditable by eye.
COUNTRY_CENTROIDS: dict[str, tuple[float, float]] = {
    # Europe
    "Germany": (51.2, 10.4),
    "Austria": (47.5, 14.5),
    "Switzerland": (46.8, 8.2),
    "France": (46.2, 2.2),
    "Italy": (41.9, 12.6),
    "Spain": (40.4, -3.7),
    "Portugal": (39.5, -8.0),
    "Belgium": (50.5, 4.5),
    "Netherlands": (52.1, 5.3),
    "Luxembourg": (49.8, 6.1),
    "Liechtenstein": (47.2, 9.5),
    "Monaco": (43.7, 7.4),
    "United Kingdom": (55.0, -2.0),
    "Ireland": (53.1, -7.7),
    "Norway": (60.5, 8.5),
    "Sweden": (60.1, 18.6),
    "Finland": (61.9, 25.7),
    "Denmark": (56.2, 9.5),
    "Iceland": (64.9, -19.0),
    "Estonia": (58.6, 25.0),
    "Latvia": (56.9, 24.6),
    "Lithuania": (55.2, 23.9),
    "Greece": (39.1, 21.8),
    "Croatia": (45.1, 15.2),
    "Slovenia": (46.2, 14.8),
    "Serbia": (44.0, 21.0),
    "Bosnia and Herzegovina": (43.9, 17.7),
    "Montenegro": (42.7, 19.4),
    "Albania": (41.2, 20.2),
    "North Macedonia": (41.6, 21.7),
    "Malta": (35.9, 14.4),
    "Poland": (51.9, 19.1),
    "Czech Republic": (49.8, 15.5),
    "Slovakia": (48.7, 19.7),
    "Hungary": (47.2, 19.5),
    "Romania": (45.9, 24.9),
    "Bulgaria": (42.7, 25.5),
    "Moldova": (47.4, 28.4),
    "Belarus": (53.7, 27.9),
    "Ukraine": (48.4, 31.2),
    "Russia": (61.5, 105.3),
    # Americas
    "United States": (39.8, -100.0),
    "Canada": (56.1, -106.3),
    "Mexico": (23.6, -102.5),
    "Belize": (17.2, -88.5),
    "Costa Rica": (9.7, -83.7),
    "El Salvador": (13.8, -88.9),
    "Guatemala": (15.8, -90.2),
    "Honduras": (15.2, -86.2),
    "Nicaragua": (12.9, -85.2),
    "Panama": (8.5, -80.8),
    "Cuba": (21.5, -77.8),
    "Jamaica": (18.1, -77.3),
    "Haiti": (18.9, -72.3),
    "Dominican Republic": (18.7, -70.2),
    "Bahamas": (25.0, -77.4),
    "Barbados": (13.2, -59.5),
    "Trinidad and Tobago": (10.7, -61.2),
    "Brazil": (-14.2, -51.9),
    "Argentina": (-38.4, -63.6),
    "Chile": (-35.7, -71.5),
    "Peru": (-9.2, -75.0),
    "Colombia": (4.6, -74.3),
    "Venezuela": (6.4, -66.6),
    "Ecuador": (-1.8, -78.2),
    "Bolivia": (-16.3, -63.6),
    "Paraguay": (-23.4, -58.4),
    "Uruguay": (-32.5, -55.8),
    "Guyana": (4.9, -58.9),
    "Suriname": (3.9, -56.0),
    # Africa
    "Egypt": (26.8, 30.8),
    "Algeria": (28.0, 1.7),
    "Morocco": (31.8, -7.1),
    "Tunisia": (33.9, 9.5),
    "Libya": (26.3, 17.2),
    "Sudan": (12.9, 30.2),
    "Nigeria": (9.1, 8.7),
    "Ghana": (7.9, -1.0),
    "Senegal": (14.5, -14.5),
    "Ivory Coast": (7.5, -5.5),
    "Mali": (17.6, -3.9),
    "Burkina Faso": (12.2, -1.6),
    "Niger": (17.6, 8.1),
    "Kenya": (-0.0, 37.9),
    "Tanzania": (-6.4, 34.9),
    "Uganda": (1.4, 32.3),
    "Ethiopia": (9.1, 40.5),
    "Somalia": (5.2, 46.2),
    "Rwanda": (-1.9, 29.9),
    "Burundi": (-3.4, 29.9),
    "South Africa": (-30.6, 22.9),
    "Namibia": (-22.9, 18.5),
    "Botswana": (-22.3, 24.7),
    "Lesotho": (-29.6, 28.2),
    "Eswatini": (-26.5, 31.5),
    "Zimbabwe": (-19.0, 29.2),
    "Zambia": (-13.1, 27.8),
    "Mozambique": (-18.7, 35.5),
    "Malawi": (-13.3, 34.3),
    # Oceania
    "Australia": (-25.3, 133.8),
    "New Zealand": (-40.9, 174.9),
    "Papua New Guinea": (-6.3, 143.9),
    "Fiji": (-17.7, 178.1),
    # Asia — South Asia
    "India": (20.6, 78.9),
    "Bhutan": (27.5, 90.4),
    "Nepal": (28.4, 84.1),
    "Pakistan": (30.4, 69.3),
    "Bangladesh": (23.7, 90.4),
    "Sri Lanka": (7.9, 80.8),
    "Maldives": (3.2, 73.2),
    # Asia — Middle East
    "Saudi Arabia": (23.9, 45.1),
    "Oman": (21.5, 55.9),
    "United Arab Emirates": (23.4, 53.8),
    "Qatar": (25.4, 51.2),
    "Kuwait": (29.3, 47.5),
    "Bahrain": (26.0, 50.6),
    "Israel": (31.0, 34.9),
    "Jordan": (30.6, 36.2),
    "Iraq": (33.2, 43.7),
    "Iran": (32.4, 53.7),
    "Lebanon": (33.9, 35.9),
    "Syria": (34.8, 38.0),
    "Yemen": (15.6, 48.5),
    # Asia — East Asia
    "China": (35.9, 104.2),
    "Japan": (36.2, 138.3),
    "South Korea": (35.9, 127.8),
    "North Korea": (40.3, 127.5),
    "Mongolia": (46.9, 103.8),
    "Taiwan": (23.7, 121.0),
    # Asia — Central Asia
    "Kazakhstan": (48.0, 66.9),
    "Kyrgyzstan": (41.2, 74.8),
    "Tajikistan": (38.9, 71.3),
    "Uzbekistan": (41.4, 64.6),
    "Turkmenistan": (38.97, 59.6),
}


@frappe.whitelist()
def get_projects_for_map() -> dict:
    """Return project data shaped for a Leaflet view.

    Output:
      {
        "centroids": {"Germany": [51.2, 10.4], ...},
        "projects": [
          {"name": "LCS-PROJ-...", "project_name": "...", "country": "...",
           "lat": 51.2, "lng": 10.4, "phase": "Offer",
           "sales_manager": "...", "organization": "...",
           "estimated_value": 0.0, "probability": 0.0},
          ...
        ],
        "unmapped_countries": ["..."]  // countries used by a project but
                                       // missing from COUNTRY_CENTROIDS
      }
    """
    rows = frappe.get_all(
        "LCS Project",
        fields=[
            "name",
            "project_name",
            "country",
            "phase",
            "status",
            "sales_manager",
            "salesperson",
            "organization",
            "estimated_value",
            "probability",
        ],
        order_by="modified desc",
        limit_page_length=5000,
    )

    unmapped: set[str] = set()
    out: list[dict] = []
    for r in rows:
        country = r.get("country")
        coord = COUNTRY_CENTROIDS.get(country) if country else None
        if country and not coord:
            unmapped.add(country)
        # latitude/longitude match the field names the existing
        # ProjectMap.vue component expects (see ProjectDashboard.vue).
        out.append(
            {
                **r,
                "latitude": coord[0] if coord else None,
                "longitude": coord[1] if coord else None,
            }
        )

    return {
        "projects": out,
        "unmapped_countries": sorted(unmapped),
    }
