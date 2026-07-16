"""Einmalige, idempotente Übernahme ERPNext → Frappe-CRM (Marco 16.07.2026).

Dominiks CRM ist eine eigene Datenwelt und startet leer; der ERPNext-Bestand
(Customer/Lead) war deshalb in den CRM-Sub-Pages des Moduls Vertrieb
unsichtbar. Diese Übernahme spiegelt die Stammdaten EINMALIG ins CRM:

  Customer  → CRM Organization  (Upsert per Name; Rück-Sync von Dominik ist
                                 selbst ein Upsert per Name — keine Duplikate)
  Lead      → CRM Lead          (Idempotenz über E-Mail bzw. Vor-/Nachname+Firma)

Bewusst NICHT übernommen: Opportunity → CRM Deal (Dominiks Funnel-Phasen-
Semantik + Deal→LCS-Project-Automatik; Mapping gehört zu ihm bzw. E3).

Lauf:  bench --site lcs.local execute pilanda_sales.crm.backfill.execute
"""

import frappe


def execute() -> dict:
    stats = {
        "organizations_neu": 0, "organizations_vorhanden": 0,
        "leads_neu": 0, "leads_vorhanden": 0, "fehler": [],
    }

    default_status = frappe.db.get_value(
        "CRM Lead Status", {}, "name", order_by="position asc"
    )
    if not default_status:
        frappe.throw("Keine CRM Lead Status vorhanden — erst crm.install.after_install() ausführen.")

    for c in frappe.get_all(
        "Customer",
        fields=["name", "customer_name", "website", "industry", "territory"],
    ):
        if not c.customer_name or c.customer_name.startswith("_Test"):
            continue
        if frappe.db.exists("CRM Organization", c.customer_name):
            stats["organizations_vorhanden"] += 1
            continue
        try:
            org = frappe.new_doc("CRM Organization")
            org.organization_name = c.customer_name
            if c.website:
                org.website = c.website
            if c.industry and frappe.db.exists("CRM Industry", c.industry):
                org.industry = c.industry
            if c.territory and frappe.db.exists("CRM Territory", c.territory):
                org.territory = c.territory
            org.insert(ignore_permissions=True)
            stats["organizations_neu"] += 1
        except Exception as e:
            stats["fehler"].append(f"Customer {c.name}: {e}")

    lead_meta = frappe.get_meta("Lead")
    lead_fields = ["name", "lead_name", "first_name", "last_name",
                   "company_name", "email_id", "mobile_no", "phone"]
    for opt in ("website", "source"):
        if lead_meta.has_field(opt):
            lead_fields.append(opt)

    for lead in frappe.get_all("Lead", fields=lead_fields):
        exists = None
        if lead.email_id:
            exists = frappe.db.exists("CRM Lead", {"email": lead.email_id})
        if not exists and lead.first_name:
            exists = frappe.db.exists(
                "CRM Lead",
                {
                    "first_name": lead.first_name,
                    "last_name": lead.last_name or "",
                    "organization": lead.company_name or "",
                },
            )
        if exists:
            stats["leads_vorhanden"] += 1
            continue
        try:
            doc = frappe.new_doc("CRM Lead")
            doc.first_name = lead.first_name or (lead.lead_name or lead.name).split(" ")[0]
            doc.last_name = lead.last_name or ""
            doc.organization = lead.company_name or ""
            doc.email = lead.email_id or ""
            doc.mobile_no = lead.mobile_no or lead.phone or ""
            doc.website = lead.get("website") or ""
            doc.status = default_status
            if lead.get("source") and frappe.db.exists("CRM Lead Source", lead.source):
                doc.source = lead.source
            doc.insert(ignore_permissions=True)
            stats["leads_neu"] += 1
        except Exception as e:
            stats["fehler"].append(f"Lead {lead.name}: {e}")

    stats.update(backfill_opportunities())

    frappe.db.commit()
    # Fail-loud: Fehler nicht verschlucken, aber die restlichen Datensätze
    # trotzdem übernehmen — am Ende vollständige Bilanz ausgeben.
    print("BACKFILL:", stats)
    return stats


# ERPNext-Opportunity-Status → CRM-Deal-Status (Dominiks Funnel).
_OPP_STATUS_MAP = {
    "Open": "Qualification",
    "Quotation": "Proposal/Quotation",
    "Replied": "Negotiation",
    "Converted": "Won",
    "Lost": "Lost",
    "Closed": "Won",
}


def backfill_opportunities() -> dict:
    """Opportunity → CRM Deal (Migration in die EINE CRM-Datenwelt).

    Der after_insert-Hook von lcs_integrations legt je Deal automatisch das
    LCS Project an (Deal=Projekt) — Vertriebsprojekte füllen sich mit.
    Idempotenz: pro Organisation+Status wird kein zweiter Deal angelegt.
    """
    stats = {"deals_neu": 0, "deals_vorhanden": 0, "deal_fehler": []}
    fallback_status = frappe.db.get_value(
        "CRM Deal Status", {}, "name", order_by="position asc"
    )

    for opp in frappe.get_all(
        "Opportunity",
        fields=["name", "customer_name", "title", "status",
                "opportunity_amount", "currency", "probability", "territory"],
    ):
        org = opp.customer_name or opp.title
        if not org:
            continue
        status = _OPP_STATUS_MAP.get(opp.status, fallback_status)
        if frappe.db.exists("CRM Deal", {"organization": org, "status": status}):
            stats["deals_vorhanden"] += 1
            continue
        try:
            deal = frappe.new_doc("CRM Deal")
            if frappe.db.exists("CRM Organization", org):
                deal.organization = org
            deal.status = status
            if opp.opportunity_amount:
                deal.annual_revenue = opp.opportunity_amount
            if opp.currency and hasattr(deal, "currency"):
                deal.currency = opp.currency
            if opp.probability:
                deal.probability = opp.probability
            if opp.territory and frappe.db.exists("CRM Territory", opp.territory):
                deal.territory = opp.territory
            if status == "Lost":
                # Pflichtfeld im CRM; Altbestand kennt den Grund nicht —
                # ehrlich kennzeichnen statt raten.
                reason = (frappe.db.exists("CRM Lost Reason", "Other")
                          or frappe.db.get_value("CRM Lost Reason", {}, "name"))
                if reason:
                    deal.lost_reason = reason
                deal.lost_notes = f"Migriert aus ERPNext-Altbestand ({opp.name}); ursprünglicher Verlustgrund nicht erfasst."
            deal.insert(ignore_permissions=True)
            stats["deals_neu"] += 1
        except Exception as e:
            stats["deal_fehler"].append(f"Opportunity {opp.name}: {e}")

    return stats
