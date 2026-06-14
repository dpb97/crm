"""Versionierte Custom Fields von pilanda_sales am ERPNext-`Project`.

Project-Objekt-SSOT (pilanda/docs/conventions/project-object-ssot.md):
- `Project` = ERPNext-Standard; Erweiterung NUR per Custom Field als Code.
- Namespace `custom_sales_`; genau EIN Eigentuemer-Repo je Feld.
- ERPNext-Standardfelder werden zuerst genutzt und NICHT dupliziert (02 §2.1):
  customer, project_name, status, currency, expected_start_date/expected_end_date,
  company, project_type(Link). Hier nur genuin neue, kaufmaennische Felder.
- `crm_deal`-Verknuepfung gehoert der CRM-Domaene (pilanda_sales · CRM, Owner
  Dominik) und wird dort definiert — bewusst NICHT hier (ein Eigentuemer je Feld).

Idempotent via `after_migrate` (hooks.py).
"""

from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

CUSTOM_FIELDS = {
    "Project": [
        {
            "fieldname": "custom_sales_customer_short",
            "label": "Customer (Short)",
            "fieldtype": "Data",
            "insert_after": "customer",
            "description": "Kurzname des Kunden (geht in den Angebots-Dateinamen).",
        },
        {
            "fieldname": "custom_sales_short_name",
            "label": "Project Short Name",
            "fieldtype": "Data",
            "insert_after": "project_name",
        },
        {
            "fieldname": "custom_sales_site_location",
            "label": "Site Location",
            "fieldtype": "Data",
            "insert_after": "custom_sales_short_name",
        },
        {
            "fieldname": "custom_sales_project_class",
            "label": "Project Class",
            "fieldtype": "Select",
            "options": "\nstandard\nbigproject",
            "insert_after": "status",
            "description": "standard | bigproject (bigproject vorerst deferred).",
        },
        {
            "fieldname": "custom_sales_fx_rate_to_eur",
            "label": "FX Rate to EUR",
            "fieldtype": "Float",
            "precision": "6",
            "insert_after": "currency",
            "description": (
                "1 Einheit Projektwaehrung in EUR. Intern ist EUR Master (E-8); "
                "die Angebotsversion friert den Kurs ein."
            ),
        },
        {
            "fieldname": "custom_sales_duration_months",
            "label": "Duration (Months)",
            "fieldtype": "Int",
            "insert_after": "expected_end_date",
            "description": (
                "Projektdauer in Monaten (treibt Miet-/PMT-Logik). Kommt kuenftig "
                "aus pilanda_pm [OFFEN F-7]."
            ),
        },
        {
            "fieldname": "custom_sales_validity_until",
            "label": "Validity Until",
            "fieldtype": "Date",
            "insert_after": "custom_sales_duration_months",
        },
        {
            "fieldname": "custom_sales_provenance_sb",
            "label": "Angebots-Provenienz (LCS)",
            "fieldtype": "Section Break",
            "insert_after": "custom_sales_validity_until",
            "collapsible": 1,
        },
        {
            "fieldname": "custom_sales_reviewed_by",
            "label": "Reviewed By",
            "fieldtype": "Link",
            "options": "User",
            "insert_after": "custom_sales_provenance_sb",
        },
        {
            "fieldname": "custom_sales_approved_by",
            "label": "Approved By",
            "fieldtype": "Link",
            "options": "User",
            "insert_after": "custom_sales_reviewed_by",
        },
        {
            "fieldname": "custom_sales_signee_1",
            "label": "Signee 1",
            "fieldtype": "Link",
            "options": "User",
            "insert_after": "custom_sales_approved_by",
        },
        {
            "fieldname": "custom_sales_signee_2",
            "label": "Signee 2",
            "fieldtype": "Link",
            "options": "User",
            "insert_after": "custom_sales_signee_1",
        },
    ],
}


def ensure_custom_fields() -> None:
    """Idempotent: legt fehlende Felder an / aktualisiert vorhandene (after_migrate)."""
    create_custom_fields(CUSTOM_FIELDS, ignore_validate=True)
