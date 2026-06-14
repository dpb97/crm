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

# Custom-Field-Namensraum dieser App = custom_sales_* — wird über
# pilanda_sales.custom_fields.ensure_custom_fields versioniert angelegt
# (Project-Objekt-SSOT), sobald die ersten Felder definiert sind (Phase 1.1):
# after_migrate = ["pilanda_sales.custom_fields.ensure_custom_fields"]
