"""Whitelisted backend for the LCS Projects map page.

Returns one record per LCS Project, joined with its country centroid so
the SPA can plot it on a Leaflet map. Country coordinates come from the
shared static table in `country_coords.py` — Frappe's `Country` DocType
carries no lat/lng, and geocoding every customer address is overkill for
a "where are our projects" overview.

If a project's country is missing from the table the record is still
returned, but `latitude`/`longitude` are None and the frontend will list
it under "unmapped". Add coordinates in `country_coords.py` when new
countries enter the market-split.
"""

from __future__ import annotations

import frappe

from lcs_integrations.projects.country_coords import get_coords


@frappe.whitelist()
def get_projects_for_map() -> dict:
    """Return project data shaped for a Leaflet view.

    Output:
      {
        "projects": [
          {"name": "LCS-PROJ-...", "project_name": "...", "country": "...",
           "latitude": 51.2, "longitude": 10.4, "phase": "Offer",
           "sales_manager": "...", "organization": "...",
           "estimated_value": 0.0, "probability": 0.0},
          ...
        ],
        "unmapped_countries": ["..."]  // countries used by a project but
                                       // missing from country_coords.py
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
        coord = get_coords(country)
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
