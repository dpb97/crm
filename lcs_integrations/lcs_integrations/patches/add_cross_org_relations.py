import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    """Cross-organization / person relationships (einpflegbar):
      · CRM Organization → Partner & Zulieferer (LCS Org Relation)
      · Contact → Arbeitgeber-Historie (LCS Contact Employment) + Beziehungen/
        Freunde (LCS Contact Relation)
    Added as custom Table fields so the upstream doctypes stay untouched.
    Idempotent (create_custom_fields updates in place)."""
    create_custom_fields(
        {
            "CRM Organization": [
                {
                    "fieldname": "lcs_relations",
                    "fieldtype": "Table",
                    "options": "LCS Org Relation",
                    "label": "Partner & suppliers",
                    "insert_after": "website",
                },
            ],
            "Contact": [
                {
                    "fieldname": "lcs_employment",
                    "fieldtype": "Table",
                    "options": "LCS Contact Employment",
                    "label": "Employment history",
                    "insert_after": "company_name",
                },
                {
                    "fieldname": "lcs_relations",
                    "fieldtype": "Table",
                    "options": "LCS Contact Relation",
                    "label": "Relations",
                    "insert_after": "lcs_employment",
                },
            ],
        },
        ignore_validate=True,
    )
