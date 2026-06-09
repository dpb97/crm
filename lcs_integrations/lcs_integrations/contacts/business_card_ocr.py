"""Business-card OCR (PR-06).

Upload a phone photo of a business card, return a parsed contact draft
the SPA can pre-fill the Contact form with. The user reviews/edits
and saves — never auto-create the Contact, because OCR errors land in
the customer master otherwise.

Provider is Azure AI Vision Read 3.2 by default. MS Graph also exposes
an OCR endpoint for Microsoft 365 tenants — kept as a fallback hook.
"""

from __future__ import annotations

import base64
import io
import re
from typing import Optional

import frappe
import requests
from frappe import _


PHONE_RE = re.compile(r"[+\d][\d\s\-/\(\)\.]{7,}\d")
EMAIL_RE = re.compile(r"[\w\.\-+]+@[\w\.\-]+\.[A-Za-z]{2,}")
URL_RE = re.compile(r"(?:https?://|www\.)\S+", re.IGNORECASE)


@frappe.whitelist()
def parse_card(image_b64: str, mime_type: str = "image/jpeg") -> dict:
    """Parse a base64-encoded business-card photo.

    Returns a dict shaped like:
      {
        "first_name": "...",
        "last_name": "...",
        "company_name": "...",
        "designation": "...",
        "email_id": "...",
        "mobile_no": "...",
        "phone": "...",
        "website": "...",
        "raw_text": "..."
      }
    Fields are best-effort — the SPA shows them as editable suggestions.
    """
    settings = frappe.get_single("LCS Business Card OCR Settings")
    if not settings.is_enabled:
        frappe.throw(_("Business-card OCR is disabled."))

    try:
        image_bytes = base64.b64decode(image_b64)
    except Exception:
        frappe.throw(_("Invalid base64 image payload."))

    if settings.provider == "Azure AI Vision":
        raw_text = _ocr_azure(image_bytes, settings, mime_type)
    else:
        frappe.throw(_("OCR provider {0} not implemented yet.").format(settings.provider))

    return _parse_text(raw_text)


def _ocr_azure(image_bytes: bytes, settings, mime_type: str) -> str:
    endpoint = (settings.azure_endpoint or "").rstrip("/")
    if not endpoint:
        frappe.throw(_("Azure endpoint missing in LCS Business Card OCR Settings."))
    key = settings.get_password("azure_api_key")
    if not key:
        frappe.throw(_("Azure API key missing in LCS Business Card OCR Settings."))

    # Azure AI Vision Image Analysis 4.0 — synchronous, returns full text.
    url = f"{endpoint}/computervision/imageanalysis:analyze?api-version=2024-02-01&features=read"
    headers = {
        "Ocp-Apim-Subscription-Key": key,
        "Content-Type": mime_type,
    }
    r = requests.post(url, headers=headers, data=image_bytes, timeout=30)
    r.raise_for_status()
    payload = r.json()
    read = payload.get("readResult") or {}
    blocks = read.get("blocks") or []
    lines: list[str] = []
    for block in blocks:
        for line in block.get("lines", []):
            text = line.get("text")
            if text:
                lines.append(text)
    return "\n".join(lines)


def _parse_text(text: str) -> dict:
    """Heuristic extraction. Quality is good enough for a draft Contact
    that the user reviews — we deliberately do NOT try to be clever
    beyond a few well-known patterns."""
    if not text:
        return {"raw_text": ""}

    email = _first(EMAIL_RE, text)
    url = _first(URL_RE, text)

    phones = PHONE_RE.findall(text)
    mobile = next((p for p in phones if _looks_mobile(p)), None)
    phone = next((p for p in phones if p != mobile), None)

    # Strip noisy tokens so name/company guesses don't fight them.
    clean_lines = [
        ln.strip()
        for ln in text.splitlines()
        if ln.strip()
        and not EMAIL_RE.search(ln)
        and not URL_RE.search(ln)
        and not PHONE_RE.search(ln)
    ]

    first_name = ""
    last_name = ""
    company_name = ""
    designation = ""

    if clean_lines:
        # Heuristic: first non-noisy line with two capitalised tokens => name
        for idx, ln in enumerate(clean_lines):
            tokens = ln.split()
            if (
                2 <= len(tokens) <= 4
                and all(t[:1].isupper() for t in tokens if t)
            ):
                first_name = tokens[0]
                last_name = " ".join(tokens[1:])
                clean_lines.pop(idx)
                break

        # Designation often contains a known keyword
        for idx, ln in enumerate(clean_lines):
            low = ln.lower()
            if any(k in low for k in (
                "manager", "director", "engineer", "ceo", "cto", "owner",
                "sales", "vertrieb", "leiter", "head of"
            )):
                designation = ln
                clean_lines.pop(idx)
                break

        if clean_lines:
            # First remaining line is the safest company-name guess
            company_name = clean_lines[0]

    return {
        "first_name": first_name,
        "last_name": last_name,
        "company_name": company_name,
        "designation": designation,
        "email_id": email or "",
        "mobile_no": mobile or "",
        "phone": phone or "",
        "website": url or "",
        "raw_text": text,
    }


def _first(pattern: re.Pattern, text: str) -> Optional[str]:
    m = pattern.search(text)
    return m.group(0) if m else None


def _looks_mobile(num: str) -> bool:
    digits = re.sub(r"\D", "", num)
    if len(digits) < 9:
        return False
    # German / Austrian / Swiss mobile prefixes — heuristic only.
    return any(
        digits.startswith(p)
        for p in ("491", "151", "152", "157", "159", "160", "162", "163",
                  "170", "171", "172", "173", "174", "175", "176", "177", "178", "179",
                  "4367", "4368", "417")
    )
