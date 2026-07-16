"""Business logic for Proxess DMS."""

from __future__ import annotations

from typing import Any

import frappe

from .client import ProxessClient


def upload_document(reference_doctype: str, reference_name: str, *,
                     title: str, content_type: str, data: bytes) -> str:
    """Upload a file to Proxess and persist a Proxess Document Link."""
    meta = {
        "ref_doctype": reference_doctype,
        "ref_name": reference_name,
        "uploaded_by": frappe.session.user,
    }
    with ProxessClient() as client:
        result = client.upload(title, content_type, data, meta=meta)
    doc = frappe.get_doc({
        "doctype": "Proxess Document Link",
        "reference_doctype": reference_doctype,
        "reference_name": reference_name,
        "proxess_id": result["id"],
        "title": title,
        "content_type": content_type,
        "uploaded_by": frappe.session.user,
        "uploaded_on": frappe.utils.now_datetime(),
    }).insert(ignore_permissions=True)
    return doc.name


def list_documents(reference_doctype: str, reference_name: str) -> list[dict[str, Any]]:
    # Prefer Frappe's own cache over the DMS when links are already known.
    links = frappe.get_all(
        "Proxess Document Link",
        filters={"reference_doctype": reference_doctype, "reference_name": reference_name},
        fields=["name", "proxess_id", "title", "content_type", "uploaded_on"],
        order_by="uploaded_on desc",
    )
    return links
