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
            # Vertriebsphase = Übergabe-Mechanik Vertrieb/Innendienst ↔ Projektierung
            # (Entscheid Marco 03.07.2026, mit Vertrieb abgestimmt; Ablauf-SSOT:
            # pilanda_projectengineering/Entwicklungsplan.md §Ablauf). Schleifen
            # sind erlaubt (Budget-/Richtpreis-/Final-Angebotsrunden) — deshalb
            # bewusst Select statt starrem Einbahn-Workflow. Review: Dominik.
            "fieldname": "custom_sales_phase",
            "label": "Vertriebsphase",
            "fieldtype": "Select",
            "options": "\nLead\nProjektierung\nKalkulation\nAngebot\nVerhandlung\nEntscheidung Kunde",
            "insert_after": "status",
            "in_list_view": 1,
            "in_standard_filter": 1,
            "description": "Übergabe an die Projektierung = Phase „Projektierung“; Rückgabe = „Kalkulation“. Mehrere Runden möglich.",
        },
        {
            "fieldname": "custom_sales_project_class",
            "label": "Project Class",
            "fieldtype": "Select",
            "options": "\nstandard\nbigproject",
            "insert_after": "custom_sales_phase",
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
    "Item": [
        {
            "fieldname": "custom_sales_calc_sb",
            "label": "Pilanda Vertrieb — Kalkulation",
            "fieldtype": "Section Break",
            "insert_after": "item_group",
            "collapsible": 1,
        },
        {
            "fieldname": "custom_sales_cn",
            "label": "CN (Controlling-Nummer)",
            "fieldtype": "Data",
            "insert_after": "custom_sales_calc_sb",
            "description": "Passives Attribut beim Import (B-4: keine Vergabe-Automatik in v1).",
        },
        {
            "fieldname": "custom_sales_board_category",
            "label": "Board-Kategorie",
            "fieldtype": "Select",
            "options": "\nmanpower_onsite\nmanpower_offsite\nequipment\ntransport_manpower\nconsumables\ntransports\ngeneral\nsubcontractor_works",
            "insert_after": "custom_sales_cn",
        },
        {
            "fieldname": "custom_sales_hk_source",
            "label": "HK-Quelle (N/E/A/S)",
            "fieldtype": "Select",
            "options": "\nneu\nestp\nangeb\nschaetz",
            "insert_after": "custom_sales_board_category",
            "description": "N=Neuentwicklung, E=letzter Einstandspreis (estp), A=Angebot, S=Schätzung. Historisierung der Werte je Quelle = [OFFEN F-5], hier vorerst nur Quellen-Markierung.",
        },
        {
            "fieldname": "custom_sales_invest_class",
            "label": "Investitionsklasse",
            "fieldtype": "Select",
            "options": "\n1\n2\n3",
            "insert_after": "custom_sales_hk_source",
            "description": "1=Verbrauch, 2=Standard/wiederverwendbar, 3=Projektspezifisch.",
        },
        {
            "fieldname": "custom_sales_afa_category",
            "label": "AfA-Kategorie",
            "fieldtype": "Data",
            "insert_after": "custom_sales_invest_class",
            "description": "Vorerst Data → später Link auf Stammdaten 'AfA Category' (Phase 1.3/2).",
        },
        {
            "fieldname": "custom_sales_cb_rates",
            "fieldtype": "Column Break",
            "insert_after": "custom_sales_afa_category",
        },
        {
            "fieldname": "custom_sales_daily_cost_local",
            "label": "Tageskosten lokal",
            "fieldtype": "Currency",
            "insert_after": "custom_sales_cb_rates",
            "description": "HK/Tag lokal (Zweitwährung × fx).",
        },
        {
            "fieldname": "custom_sales_daily_rate_local",
            "label": "Tagessatz lokal",
            "fieldtype": "Currency",
            "insert_after": "custom_sales_daily_cost_local",
        },
        {
            "fieldname": "custom_sales_daily_cost_expat",
            "label": "Tageskosten Expat",
            "fieldtype": "Currency",
            "insert_after": "custom_sales_daily_rate_local",
            "description": "HK/Tag Expat (EUR).",
        },
        {
            "fieldname": "custom_sales_daily_rate_expat",
            "label": "Tagessatz Expat",
            "fieldtype": "Currency",
            "insert_after": "custom_sales_daily_cost_expat",
        },
        {
            "fieldname": "custom_sales_flags_sb",
            "label": "Flags",
            "fieldtype": "Section Break",
            "insert_after": "custom_sales_daily_rate_expat",
        },
        {
            "fieldname": "custom_sales_flag_expat",
            "label": "Expat",
            "fieldtype": "Check",
            "insert_after": "custom_sales_flags_sb",
        },
        {
            "fieldname": "custom_sales_flag_import_duty",
            "label": "Einfuhrzoll",
            "fieldtype": "Check",
            "insert_after": "custom_sales_flag_expat",
        },
        {
            "fieldname": "custom_sales_flag_ppe",
            "label": "PPE",
            "fieldtype": "Check",
            "insert_after": "custom_sales_flag_import_duty",
        },
        {
            "fieldname": "custom_sales_flag_visa",
            "label": "Visa",
            "fieldtype": "Check",
            "insert_after": "custom_sales_flag_ppe",
        },
        {
            "fieldname": "custom_sales_flag_default",
            "label": "Default-Vorbelegung",
            "fieldtype": "Check",
            "insert_after": "custom_sales_flag_visa",
        },
    ],
}


def ensure_custom_fields() -> None:
    """Idempotent: legt fehlende Felder an / aktualisiert vorhandene (after_migrate)."""
    create_custom_fields(CUSTOM_FIELDS, ignore_validate=True)
