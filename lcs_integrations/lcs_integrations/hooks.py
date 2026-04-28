"""Frappe app hooks for lcs_integrations.

Only wiring lives here. Business logic must stay in the sub-packages.
"""

app_name = "lcs_integrations"
app_title = "LCS Integrations"
app_publisher = "LCS Group"
app_description = (
    "LCS-specific integrations: ERPNext (Customer, Quotation, Sales Order), "
    "Fusion Manage PLM, Proxess DMS, Outlook, MSAL SSO, lead scoring."
)
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
# Target ERP is ERPNext (installed alongside frappe/crm on the LCS bench).
# Fusion Manage is the PLM of record for product data.
# Row-level and document-level permission filters — driven by LCS Access Profile.
# LCS Offer inherits the project's access restriction because offer visibility
# without its project's context would leak pricing/commercial data.
permission_query_conditions = {
    "LCS Project": "lcs_integrations.visibility.service.get_permission_query_conditions",
    "LCS Offer": "lcs_integrations.visibility.service.get_offer_query_conditions",
}

has_permission = {
    "LCS Project": "lcs_integrations.visibility.service.has_permission",
    "LCS Offer": "lcs_integrations.visibility.service.has_offer_permission",
}

doc_events = {
    "CRM Lead": {
        "on_update": "lcs_integrations.lead_scoring.hooks.recompute_score",
    },
    "CRM Organization": {
        "after_insert": "lcs_integrations.erpnext_sync.customer_sync.on_organization_created",
        "on_update": "lcs_integrations.erpnext_sync.customer_sync.on_organization_updated",
    },
    "CRM Deal": {
        # Close the Lead → Deal → LCS Project loop: when a deal is won,
        # auto-create the project so Ops doesn't have to click anything.
        "on_update": "lcs_integrations.cross_module.deal_to_project.on_deal_update",
    },
    "Communication": {
        "after_insert": "lcs_integrations.email_domain_autolink.hooks.auto_link",
    },
    "LCS Project": {
        "validate": [
            "lcs_integrations.projects.notifications.on_project_phase_change",
            "lcs_integrations.cross_module.training_check.on_project_validate",
            # LCS Project is the single source of truth for sales_manager —
            # every change propagates down to the linked Deal + Lead.
            "lcs_integrations.cross_module.sales_manager_sync.on_project_validate",
        ],
        # Spawn an ERPNext Project as soon as the project enters Order/
        # Execution so resource planning has somewhere to live during the
        # active phase, not just after closure.
        "on_update": "lcs_integrations.cross_module.erpnext_project_sync.on_lcs_project_update",
    },
    "LCS Opportunity Matrix": {
        "validate": "lcs_integrations.projects.notifications.on_high_probability",
    },
    "LCS Offer": {
        "on_update": "lcs_integrations.erpnext_sync.quotation_sync.on_offer_updated",
    },
    "Sales Order": {
        "after_insert": "lcs_integrations.cross_module.bsm_sync.on_sales_order_created",
    },
}

# Scheduled tasks.
scheduler_events = {
    "cron": {
        # Outlook delta sync every 5 minutes per user.
        "*/5 * * * *": ["lcs_integrations.outlook_sync.delta_service.sync_all_bindings"],
    },
    "hourly": [
        # Pull PLM changes for linked projects
        "lcs_integrations.fusion_manage.service.sync_linked_projects",
    ],
}

# Whitelisted API methods — defined explicitly per module so the surface area
# stays auditable.

# No workspace overrides for now.
override_whitelisted_methods: dict[str, str] = {}

# Website routes — none for now.
website_route_rules: list[dict[str, str]] = []
