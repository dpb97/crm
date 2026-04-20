"""Document event handlers that bridge Frappe → abas service layer.

Controllers stay thin: queue background jobs and hand off. Target stack is
ERPNext: `Customer` is the canonical record that gets pushed to abas once
created; Leads / Opportunities / Quotations stay CRM-only until conversion.
"""

from __future__ import annotations

from typing import Any

import frappe


def on_contact_updated(doc: Any, method: str | None = None) -> None:
    if not doc.get("abas_contact_id"):
        return
    frappe.enqueue(
        "lcs_integrations.abas.service.push_customer",
        queue="short",
        crm_doctype="Contact",
        crm_name=doc.name,
    )


def on_customer_created(doc: Any, method: str | None = None) -> None:
    # Skip disabled customers — they are test rows or tombstones.
    if doc.get("disabled"):
        return
    frappe.enqueue(
        "lcs_integrations.abas.service.push_customer",
        queue="short",
        crm_doctype="Customer",
        crm_name=doc.name,
    )


def on_customer_updated(doc: Any, method: str | None = None) -> None:
    on_customer_created(doc, method)
