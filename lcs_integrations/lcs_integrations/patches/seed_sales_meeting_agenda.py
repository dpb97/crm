"""Seed a small demo agenda for the weekly sales meeting so the committee view
is demonstrable out of the box.

Creates three open agenda points for the most recent meeting date, each tied to
a real open CRM Deal when one exists. Idempotent: skips entirely once any agenda
item exists, so it never duplicates and never overwrites the user's own points.
"""

import frappe


def execute():
    if frappe.db.count("LCS Sales Meeting Agenda"):
        return

    deals = frappe.get_all(
        "CRM Deal",
        filters={"status": ["not in", ["Won", "Lost"]]},
        fields=["name", "organization"],
        order_by="annual_revenue desc",
        limit=3,
    )
    templates = [
        ("Preisfreigabe Richtpreisangebot", "Freigabe des Richtpreises vor Versand?"),
        ("Nachfassen offener Lead", "Termin fixieren und Verantwortlichen bestimmen."),
        ("Ressourcen fuer Projektstart", "Montageteam und Termin fuer den Baubeginn klaeren."),
    ]

    today = frappe.utils.today()
    for i, (topic, _hint) in enumerate(templates):
        deal = deals[i] if i < len(deals) else None
        frappe.get_doc({
            "doctype": "LCS Sales Meeting Agenda",
            "meeting_date": today,
            "sort_index": i,
            "topic": topic,
            "reference_object": (deal.organization or deal.name) if deal else "",
            "reference_doctype": "CRM Deal" if deal else None,
            "reference_name": deal.name if deal else None,
            "responsible": "Administrator",
            "status": "Open",
        }).insert(ignore_permissions=True)
