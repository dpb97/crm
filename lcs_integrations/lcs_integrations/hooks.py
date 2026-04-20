"""Frappe app hooks for lcs_integrations.

Only wiring lives here. Business logic must stay in the sub-packages.
"""

app_name = "lcs_integrations"
app_title = "LCS Integrations"
app_publisher = "LCS Group"
app_description = "LCS-specific integrations: abas ERP, Proxess DMS, Outlook, MSAL SSO, lead scoring."
app_email = "it@lcs-group.com"
app_license = "proprietary"

# Fixtures — Custom fields for upstream CRM DocTypes.
fixtures = [
    {
        "doctype": "Custom Field",
        "filters": [["module", "=", "LCS Integrations"]],
    },
    {
        "doctype": "Social Login Key",
        "filters": [["name", "=", "entra"]],
    },
]

# Document events — keep the list minimal; each handler is a thin adapter
# that delegates to a service.
#
# Target stack: ERPNext (Lead / Customer / Quotation / Sales Order). The
# frappe/crm DocTypes (CRM Lead / CRM Deal) are not installed on the LCS
# bench — see docs/adr/0004-erpnext-over-frappe-crm.md.
doc_events = {
    "Lead": {
        "on_update": "lcs_integrations.lead_scoring.hooks.recompute_score",
    },
    "Customer": {
        "after_insert": "lcs_integrations.abas.hooks.on_customer_created",
        "on_update": "lcs_integrations.abas.hooks.on_customer_updated",
    },
    "Contact": {
        "on_update": "lcs_integrations.abas.hooks.on_contact_updated",
    },
    "Communication": {
        "after_insert": "lcs_integrations.email_domain_autolink.hooks.auto_link",
    },
    "LCS Project": {
        "validate": "lcs_integrations.projects.notifications.on_project_phase_change",
    },
    "LCS Opportunity Matrix": {
        "validate": "lcs_integrations.projects.notifications.on_high_probability",
    },
}

# Scheduled tasks.
scheduler_events = {
    "cron": {
        # Outlook delta sync every 5 minutes per user.
        "*/5 * * * *": ["lcs_integrations.outlook_sync.delta_service.sync_all_bindings"],
    },
    "daily": [
        "lcs_integrations.abas.service.reconcile_delta",
    ],
}

# Whitelisted API methods — defined explicitly per module so the surface area
# stays auditable. Do NOT use wildcard imports.
# (Frappe derives the whitelist from @frappe.whitelist decorators at runtime;
#  this comment is informational.)

# Override workspaces to hide Campaign/Marketing menus (LCS scope decision).
override_whitelisted_methods: dict[str, str] = {}

# Website routes — none for now.
website_route_rules: list[dict[str, str]] = []
