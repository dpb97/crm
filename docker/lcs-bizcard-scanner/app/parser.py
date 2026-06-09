"""Heuristic business-card field extraction from raw OCR text.

Pure regex + small ordered rules. No ML, deterministic, fast.
The downstream `polish_with_llm` step optionally refines the result
when an Ollama-backed model is configured.
"""

from __future__ import annotations

import re
from typing import Optional

EMAIL_RE = re.compile(r"[\w\.\-+]+@[\w\.\-]+\.[A-Za-z]{2,}")
URL_RE = re.compile(r"(?:https?://|www\.)\S+", re.IGNORECASE)
PHONE_RE = re.compile(r"[+\d][\d\s\-/\(\)\.]{7,}\d")

DESIGNATION_KEYWORDS = (
    "manager", "director", "engineer", "developer", "architect",
    "ceo", "cto", "cfo", "coo", "founder", "owner", "partner",
    "sales", "marketing", "account", "vp ", "vice president",
    "head of", "chief", "lead", "consultant",
    # German
    "vertrieb", "leiter", "geschäftsführer", "geschaeftsfuehrer",
    "prokurist", "ingenieur",
)


def _first(pattern: re.Pattern, text: str) -> Optional[str]:
    m = pattern.search(text)
    return m.group(0).strip() if m else None


def _looks_mobile(digits: str) -> bool:
    # German / Austrian / Swiss mobile prefixes after normalization.
    return any(digits.startswith(p) for p in (
        "491", "151", "152", "157", "159",
        "160", "162", "163",
        "170", "171", "172", "173", "174", "175", "176", "177", "178", "179",
        "4367", "4368", "4369", "417", "418", "419",
    ))


def _normalise_phone(num: str) -> str:
    return re.sub(r"\D", "", num)


def parse_card_text(text: str) -> dict:
    out: dict = {
        "first_name": "",
        "last_name": "",
        "company_name": "",
        "designation": "",
        "email_id": "",
        "mobile_no": "",
        "phone": "",
        "website": "",
        "address": "",
    }

    if not text or not text.strip():
        return out

    out["email_id"] = _first(EMAIL_RE, text) or ""
    out["website"] = _first(URL_RE, text) or ""

    phones = PHONE_RE.findall(text)
    mobile, landline = None, None
    for p in phones:
        digits = _normalise_phone(p)
        if not mobile and _looks_mobile(digits):
            mobile = p.strip()
        elif not landline:
            landline = p.strip()
    out["mobile_no"] = mobile or ""
    out["phone"] = landline or ""

    # Strip noisy lines so the name/company guesses don't fight matches.
    clean: list[str] = []
    for raw in text.splitlines():
        ln = raw.strip()
        if not ln:
            continue
        if EMAIL_RE.search(ln) or URL_RE.search(ln) or PHONE_RE.search(ln):
            continue
        # Filter address-like lines for the address bucket
        if re.search(r"\b\d{4,5}\b", ln):
            out["address"] = (out["address"] + " " + ln).strip()
            continue
        clean.append(ln)

    # Name: first line with 2–4 capitalised tokens
    for idx, ln in enumerate(clean):
        tokens = ln.split()
        if 2 <= len(tokens) <= 4 and all(
            (t[:1].isupper() or t[:1] in {"D", "v", "z"})  # German particles
            for t in tokens if t
        ):
            out["first_name"] = tokens[0]
            out["last_name"] = " ".join(tokens[1:])
            clean.pop(idx)
            break

    # Designation: first remaining line that contains a known keyword
    for idx, ln in enumerate(clean):
        low = ln.lower()
        if any(k in low for k in DESIGNATION_KEYWORDS):
            out["designation"] = ln
            clean.pop(idx)
            break

    # Company: first remaining line, but ignore the address.
    for ln in clean:
        if ln.strip().startswith(out["address"][:8] if out["address"] else "\0"):
            continue
        out["company_name"] = ln.strip()
        break

    return out
