"""Public lead intake — guest endpoint for website / external forms.

POST /api/method/lcs_integrations.leads.intake.create_lead
  first_name (required), last_name, email (required), organization,
  mobile_no, message, source, website — plus a honeypot field `company_url`
  that must stay empty (bots fill it; we answer OK without creating).

Guarded by a per-IP rate limit (10/hour) and basic e-mail validation.
Territory/sales-manager auto-assign hooks run as usual on insert.
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import validate_email_address

RATE_LIMIT = 10  # requests per IP per hour


def _rate_limited() -> bool:
    ip = getattr(frappe.local, "request_ip", None) or "unknown"
    key = f"lcs_lead_intake:{ip}"
    count = frappe.cache().get_value(key) or 0
    if int(count) >= RATE_LIMIT:
        return True
    frappe.cache().set_value(key, int(count) + 1, expires_in_sec=3600)
    return False


@frappe.whitelist(allow_guest=True, methods=["POST"])
def create_lead(
    first_name: str | None = None,
    last_name: str | None = None,
    email: str | None = None,
    organization: str | None = None,
    mobile_no: str | None = None,
    message: str | None = None,
    source: str | None = None,
    website: str | None = None,
    company_url: str | None = None,  # honeypot
):
    # Honeypot filled -> pretend success, create nothing.
    if company_url:
        return {"ok": True}

    if _rate_limited():
        frappe.throw(_("Too many requests, please try again later."), frappe.TooManyRequestsError)

    first_name = (first_name or "").strip()
    email = (email or "").strip().lower()
    if not first_name or not email:
        frappe.throw(_("first_name and email are required."))
    validate_email_address(email, throw=True)

    # Duplicate guard: an open lead with the same address is reused.
    existing = frappe.db.get_value("CRM Lead", {"email": email, "converted": 0}, "name")
    if existing:
        if message:
            frappe.get_doc("CRM Lead", existing).add_comment(
                "Comment", text=frappe.utils.strip_html(message)[:2000]
            )
        return {"ok": True, "lead": existing, "duplicate": True}

    lead = frappe.new_doc("CRM Lead")
    lead.first_name = first_name[:140]
    lead.last_name = (last_name or "").strip()[:140]
    lead.email = email
    lead.organization = (organization or "").strip()[:140]
    lead.mobile_no = (mobile_no or "").strip()[:30]
    lead.website = (website or "").strip()[:140]
    if source and frappe.db.exists("CRM Lead Source", source):
        lead.source = source
    elif frappe.db.exists("CRM Lead Source", "Website"):
        lead.source = "Website"
    lead.insert(ignore_permissions=True)

    if message:
        lead.add_comment("Comment", text=frappe.utils.strip_html(message)[:2000])

    frappe.db.commit()
    return {"ok": True, "lead": lead.name}
