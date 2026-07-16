"""Pilanda Vertrieb — Questionnaire/Lastenheft, Kalkulation, Angebot (LCS)."""

app_name = "pilanda_sales"
app_title = "Pilanda Vertrieb"
app_publisher = "LCS Group"
app_description = "Vertrieb/Angebotswesen (Questionnaire, Kalkulation, Angebot) für den Pilanda-Stack auf ERPNext."
app_email = "it@lcs-group.com"
app_license = "proprietary"

# Liest ERPNext Project/Task/Item + die freigegebene Anlagenkonfiguration aus
# pilanda_projectengineering und Phasen aus pilanda_pm. Kopplung an andere
# Pilanda-Apps nur über geteilte ERPNext-Daten (siehe ARCHITEKTUR-PILANDA.md §4).
required_apps = ["erpnext", "pilanda_theme"]

# Custom-Field-Namensraum dieser App = custom_sales_* — versioniert via
# pilanda_sales.custom_fields.ensure_custom_fields (Project-Objekt-SSOT), idempotent.
# Die CRM-Domaene (crm_deal-Link am Project) haengt separat dran — eigener
# Bereich, eigener Eigentuemer (siehe pilanda_sales/crm/custom_fields.py).
after_migrate = [
    "pilanda_sales.custom_fields.ensure_custom_fields",
    "pilanda_sales.crm.custom_fields.ensure_crm_custom_fields",
]
