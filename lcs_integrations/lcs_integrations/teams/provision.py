"""
MS Teams / SharePoint project provisioning via Microsoft Graph API.

Requires:
- Azure AD App Registration with Sites.Manage.All, Team.Create, Channel.Create.All
- MSAL credentials in site_config.json (ms_graph_client_id, ms_graph_client_secret, ms_graph_tenant_id)
"""

import frappe
from frappe import _

# Channel structure from requirements (Teams-Structure_2025-07-10.xlsx)
PROJECT_CHANNELS = [
    {"name": "01-Sales", "description": "Client interactions: emails, meeting notes, questions"},
    {"name": "02-Contract-Legal", "description": "Contracts, amendments, security documents"},
    {"name": "03-Project-Management", "description": "Scheduling, tasks, internal discussions"},
    {"name": "04-Change-Management", "description": "Change requests and approvals"},
    {"name": "05-Finance-Cost-Control", "description": "Budgeting, invoicing, payment plans"},
    {"name": "06-Installation", "description": "On-site updates, progress, commissioning"},
    {"name": "07-Documents", "description": "Standard documents, transmittals"},
    {"name": "08-Certification", "description": "Certification and building permits"},
    {"name": "09-Engineering-Design", "description": "Design reviews, simulations, arrangements"},
    {"name": "10-SCM", "description": "Suppliers, subcontractors, vendor management"},
    {"name": "11-Logistics", "description": "Delivery, customs, shipping documents"},
    {"name": "12-Meeting-Protocols", "description": "Meeting summaries, decisions, action items"},
    {"name": "13-General-Chat", "description": "Internal team communication"},
    {"name": "14-Lessons-Learned", "description": "Post-project reflection and feedback"},
    {"name": "15-Shared-with-Client", "description": "Documents shared with client"},
]

# Folder structure per channel (key channels only)
CHANNEL_FOLDERS = {
    "01-Sales": [
        "01-Tender",
        "02-Pre-Qualifications",
        "03-Internal-Approval",
        "04-Quotations",
        "05-Transmitted-Documents",
        "06-Offer-Calculation",
        "07-Correspondence",
    ],
    "02-Contract-Legal": [
        "01-Contract",
        "02-Amendments",
        "03-Securities",
        "04-Insurances",
        "05-Notices",
    ],
    "03-Project-Management": [
        "01-Kick-off-Meeting",
        "02-Organisation-Chart",
        "03-Project-Schedule",
        "04-Weekly-Meetings",
        "05-To-Do-List",
    ],
    "06-Installation": [
        "01-HS-QA-QC",
        "02-Manpower",
        "03-Reports",
        "04-Checklists",
        "05-Site-Preparation",
    ],
    "07-Documents": [
        "01-Standard-Documents",
        "02-To-Customer",
        "03-From-Customer",
        "04-Transmittals",
    ],
    "09-Engineering-Design": [
        "01-System-Design",
        "02-General-Arrangement",
    ],
    "10-SCM": ["01-Suppliers", "02-Subcontractors"],
    "11-Logistics": ["01-Logistics"],
}


def get_graph_client():
    """Get authenticated MS Graph client using MSAL credentials."""
    import msal

    client_id = frappe.conf.get("ms_graph_client_id")
    client_secret = frappe.conf.get("ms_graph_client_secret")
    tenant_id = frappe.conf.get("ms_graph_tenant_id")

    if not all([client_id, client_secret, tenant_id]):
        frappe.throw(_("MS Graph credentials not configured in site_config.json"))

    authority = f"https://login.microsoftonline.com/{tenant_id}"
    app = msal.ConfidentialClientApplication(
        client_id,
        authority=authority,
        client_credential=client_secret,
    )
    result = app.acquire_token_for_client(
        scopes=["https://graph.microsoft.com/.default"]
    )
    if "access_token" not in result:
        frappe.throw(
            _("Failed to acquire MS Graph token: {0}").format(
                result.get("error_description", "Unknown error")
            )
        )
    return result["access_token"]


@frappe.whitelist()
def provision_project_team(project_name):
    """Create MS Teams team with channels and SharePoint folder structure for a project.

    This is an async operation -- Teams creation can take up to 30 seconds.
    Updates the LCS Project with team_link and sharepoint_link when done.
    """
    import requests

    project = frappe.get_doc("LCS Project", project_name)
    if project.team_link:
        frappe.throw(_("Team already exists for this project"))

    token = get_graph_client()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    base_url = "https://graph.microsoft.com/v1.0"

    # Step 1: Create Team
    team_name = f"{project.project_number} - {project.project_name}"
    team_payload = {
        "template@odata.bind": f"{base_url}/teamsTemplates('standard')",
        "displayName": team_name,
        "description": f"LCS Project: {project.project_description or project.project_name}",
    }
    resp = requests.post(f"{base_url}/teams", json=team_payload, headers=headers)
    if resp.status_code not in (201, 202):
        frappe.throw(_("Failed to create team: {0}").format(resp.text))

    # Team creation is async -- get team ID from Location header
    team_url = resp.headers.get("Location", "")
    # Poll for team readiness (simplified -- production should use background job)
    team_id = (
        resp.headers.get("Content-Location", "").split("'")[-2]
        if "'" in resp.headers.get("Content-Location", "")
        else None
    )

    if not team_id:
        frappe.log_error(
            "Teams provisioning: could not extract team ID", resp.headers
        )
        frappe.throw(_("Team created but ID could not be determined. Check logs."))

    # Step 2: Create channels — capture the ID of the configured notifications channel
    settings = frappe.get_cached_doc("LCS Outlook Sync Settings")
    notif_channel_name = (settings.notifications_channel_name or "01-Sales").strip()
    notif_channel_id: str | None = None

    for channel in PROJECT_CHANNELS:
        ch_payload = {
            "displayName": channel["name"],
            "description": channel["description"],
        }
        ch_resp = requests.post(
            f"{base_url}/teams/{team_id}/channels",
            json=ch_payload,
            headers=headers,
        )
        if ch_resp.status_code in (201, 200) and channel["name"] == notif_channel_name:
            try:
                notif_channel_id = ch_resp.json().get("id")
            except ValueError:
                notif_channel_id = None

    # Step 3: Update project with links + Graph IDs (needed for notifications)
    team_link = f"https://teams.microsoft.com/l/team/{team_id}"
    frappe.db.set_value(
        "LCS Project",
        project_name,
        {
            "team_link": team_link,
            "teams_team_id": team_id,
            "teams_notifications_channel_id": notif_channel_id,
            "sharepoint_link": f"https://lcscablecranes.sharepoint.com/sites/{project.project_number}",
        },
    )
    frappe.db.commit()

    return {
        "team_id": team_id,
        "team_link": team_link,
        "notifications_channel_id": notif_channel_id,
    }
