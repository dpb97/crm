"""REST surface for Proxess DMS."""

from __future__ import annotations

import frappe

from .service import list_documents, upload_document


@frappe.whitelist(methods=["POST"])
def upload(reference_doctype: str, reference_name: str, title: str) -> dict:
    files = frappe.request.files
    if not files or "file" not in files:
        frappe.throw("file multipart part is required")
    upload_file = files["file"]
    link_name = upload_document(
        reference_doctype=reference_doctype,
        reference_name=reference_name,
        title=title,
        content_type=upload_file.mimetype,
        data=upload_file.read(),
    )
    return {"name": link_name}


@frappe.whitelist(methods=["GET"])
def list_for(reference_doctype: str, reference_name: str) -> list[dict]:
    return list_documents(reference_doctype, reference_name)
