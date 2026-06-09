"""Whitelisted API for the bizcard scanner.

Two endpoints the embedded page calls:
  - `scan_card(image_base64)`       → forwards to the local OCR
                                       microservice, returns the
                                       parsed contact draft
  - `create_contact_from_scan(...)` → upserts a Frappe Contact from
                                       the user-reviewed draft

The microservice URL comes from `site_config.bizcard_scanner_url`
(default http://host.docker.internal:8089). A shared token can be
added via `site_config.bizcard_shared_token` — the microservice
honours it via the `X-LCS-Token` header.
"""

from __future__ import annotations

from typing import Optional

import frappe
import httpx
from frappe import _


def _scanner_url() -> str:
    return (
        frappe.local.conf.get("bizcard_scanner_url")
        or "http://host.docker.internal:8089"
    ).rstrip("/")


def _headers() -> dict:
    h = {"Content-Type": "application/json"}
    token = frappe.local.conf.get("bizcard_shared_token")
    if token:
        h["X-LCS-Token"] = token
    return h


@frappe.whitelist()
def health() -> dict:
    """Liveness probe — proxies to the scanner's /healthz so the UI
    can flag a misconfigured / offline microservice clearly."""
    url = _scanner_url() + "/healthz"
    try:
        with httpx.Client(timeout=3.0) as client:
            r = client.get(url)
            r.raise_for_status()
            return {"ok": True, "scanner": r.json(), "scanner_url": _scanner_url()}
    except Exception as e:
        return {"ok": False, "error": str(e), "scanner_url": _scanner_url()}


@frappe.whitelist()
def scan_card(image_base64: str, mime_type: str = "image/jpeg") -> dict:
    """Send a base64 image to the scanner, return the parsed draft."""
    if not image_base64:
        frappe.throw(_("Missing image data"))

    url = _scanner_url() + "/scan-base64"
    try:
        with httpx.Client(timeout=30.0) as client:
            r = client.post(
                url,
                json={"image_base64": image_base64, "mime_type": mime_type},
                headers=_headers(),
            )
            r.raise_for_status()
            return r.json()
    except httpx.HTTPStatusError as e:
        frappe.log_error(
            title="lcs_bizcard scan failed",
            message=f"{url} -> {e.response.status_code}\n\n{e.response.text}",
        )
        frappe.throw(_("Scanner returned {0}").format(e.response.status_code))
    except Exception as e:
        frappe.log_error(title="lcs_bizcard scan exception", message=str(e))
        frappe.throw(_("Scanner unreachable: {0}").format(str(e)))


@frappe.whitelist()
def create_contact_from_scan(
    first_name: str = "",
    last_name: str = "",
    company_name: str = "",
    designation: str = "",
    email_id: str = "",
    mobile_no: str = "",
    phone: str = "",
    website: Optional[str] = None,
    address: Optional[str] = None,
) -> dict:
    """Create a Frappe Contact from the user-reviewed draft.

    Conservative: never overwrites an existing Contact found by email.
    Returns the canonical Contact name so the iframe parent can
    open / link it.
    """
    first_name = (first_name or "").strip()
    last_name = (last_name or "").strip()
    if not (first_name or last_name or company_name):
        frappe.throw(_("Need at least a name or company to create a contact."))

    # Try to dedupe by email_id — the most reliable identity on a card.
    existing = None
    if email_id:
        rows = frappe.get_all(
            "Contact Email",
            filters={"email_id": email_id.strip().lower()},
            fields=["parent"],
            limit=1,
        )
        if rows:
            existing = rows[0]["parent"]

    if existing:
        return {
            "name": existing,
            "created": False,
            "message": _("Contact with this email already exists."),
        }

    doc = frappe.new_doc("Contact")
    doc.first_name = first_name or (company_name or "Unknown")
    if last_name:
        doc.last_name = last_name
    if designation:
        doc.designation = designation
    if company_name:
        doc.company_name = company_name

    if email_id:
        doc.append("email_ids", {"email_id": email_id.strip().lower(), "is_primary": 1})
    if mobile_no:
        doc.append("phone_nos", {"phone": mobile_no, "is_primary_mobile_no": 1})
    if phone and phone != mobile_no:
        doc.append("phone_nos", {"phone": phone})

    notes = []
    if website:
        notes.append(f"Website: {website}")
    if address:
        notes.append(f"Address: {address}")
    if notes:
        doc.unsubscribed = 0  # noop guard against Contact validation quirks
        doc.set("notes", "\n".join(notes))

    doc.insert(ignore_permissions=False)
    return {"name": doc.name, "created": True}
