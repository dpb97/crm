import frappe
from frappe import _


@frappe.whitelist()
def get_project_list(filters=None, order_by="modified desc", limit=20, start=0):
    """Get paginated project list for CRM frontend."""
    return frappe.get_list(
        "LCS Project",
        filters=filters,
        fields=[
            "name",
            "project_name",
            "project_number",
            "project_type",
            "project_abbr",
            "country",
            "phase",
            "status",
            "salesperson",
            "organization",
            "probability",
            "estimated_value",
            "modified",
        ],
        order_by=order_by,
        start=int(start),
        page_length=int(limit),
    )


@frappe.whitelist()
def get_project_summary():
    """Dashboard summary data."""
    phases = frappe.get_all(
        "LCS Project",
        fields=["phase", "count(name) as count", "sum(estimated_value) as value"],
        group_by="phase",
    )
    types = frappe.get_all(
        "LCS Project",
        fields=["project_type", "count(name) as count"],
        group_by="project_type",
    )
    countries = frappe.get_all(
        "LCS Project",
        fields=["country", "count(name) as count", "sum(estimated_value) as value"],
        group_by="country",
    )
    return {"phases": phases, "types": types, "countries": countries}


@frappe.whitelist()
def get_project_map_data():
    """Get project data with coordinates for map display."""
    projects = frappe.get_all(
        "LCS Project",
        filters={"status": ["!=", "Cancelled"]},
        fields=[
            "name",
            "project_name",
            "project_number",
            "project_type",
            "country",
            "phase",
            "status",
            "salesperson",
            "estimated_value",
            "probability",
        ],
    )
    # Enrich with country coordinates
    for p in projects:
        if p.country:
            coords = frappe.db.get_value(
                "Country", p.country, ["latitude", "longitude"]
            )
            if coords:
                p["latitude"], p["longitude"] = coords
            else:
                p["latitude"], p["longitude"] = None, None
    return [p for p in projects if p.get("latitude")]


@frappe.whitelist()
def get_opportunity_matrix(project):
    """Get opportunity matrix entries for a project."""
    return frappe.get_all(
        "LCS Opportunity Matrix",
        filters={"project": project},
        fields="*",
    )


@frappe.whitelist()
def create_project_from_deal(deal_name):
    """Create an LCS Project from a CRM Deal."""
    deal = frappe.get_doc("CRM Deal", deal_name)
    project = frappe.new_doc("LCS Project")
    project.project_name = deal.deal_name or deal.lead_name or deal.name
    project.organization = deal.organization
    project.deal = deal_name
    project.salesperson = deal.deal_owner
    project.estimated_value = deal.annual_revenue
    project.phase = "Inquiry"
    project.status = "Open"
    project.insert(ignore_permissions=True)
    frappe.db.commit()
    return project.name
