"""Owner-only visibility + internal-noise suppression for synced e-mails.

Rules (from the user, 2026-08-20):
  * Everyone sees only mail from THEIR OWN mailbox (Communication.user == me) and
    can release it so the team sees it.
  * Internal -> internal mail (sender @lcs-group.com AND every recipient
    @lcs-group.com) must NEVER appear.
  * Both rules have the SAME exception `P`: a project number/name is in the
    subject, OR crm@lcs-group.com is in the CC. `P` makes a mail team-visible
    (shared) and lets internal mail through.

Effective flags stored on each Communication:
  * lcs_shared   = P (auto) OR manually released → visible to everyone
  * lcs_internal = internal-to-internal

Visibility:  lcs_shared == 1  OR  (user == me AND lcs_internal == 0)
Import skip:  lcs_internal AND NOT lcs_shared  → do not import at all
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _

# Company mail domains that count as "internal".
OWN_DOMAINS = {"lcs-group.com", "lcscable.onmicrosoft.com"}
# CC this address to file an internal mail into the CRM regardless of anything else.
CRM_CC = "crm@lcs-group.com"


# --- helpers ---------------------------------------------------------------
def _addr_domain(addr: str) -> str:
    a = (addr or "").strip().lower()
    return a.rsplit("@", 1)[-1] if "@" in a else ""


def _is_internal_addr(addr: str) -> bool:
    return _addr_domain(addr) in OWN_DOMAINS


def _split(addresses: str | None) -> list[str]:
    return [a.strip() for a in (addresses or "").replace(";", ",").split(",") if a.strip()]


def project_refs() -> list[str]:
    """Uppercased project numbers + names to scan subjects for (cached 1h)."""
    refs = frappe.cache().get_value("lcs_email_project_refs")
    if refs is None:
        refs = set()
        for r in frappe.get_all("LCS Project", fields=["project_number", "project_name"]):
            for val in (r.get("project_number"), r.get("project_name")):
                v = (val or "").strip().upper()
                if len(v) >= 4:
                    refs.add(v)
                    # projects carry a V_ sales prefix — also match the bare code
                    if v.startswith("V_") and len(v) >= 6:
                        refs.add(v[2:])
        refs = list(refs)
        frappe.cache().set_value("lcs_email_project_refs", refs, expires_in_sec=3600)
    return refs


def subject_has_project(subject: str | None) -> bool:
    s = (subject or "").upper()
    if not s:
        return False
    return any(ref in s for ref in project_refs())


def crm_in_cc(cc: str | None, recipients: str | None = None) -> bool:
    """crm@lcs-group.com among the CC (also accept To — being addressed at all
    is a stronger signal than being CC'd)."""
    pool = " ".join([cc or "", recipients or ""]).lower()
    return CRM_CC in pool


def is_internal_internal(sender: str, recipients: str | None, cc: str | None) -> bool:
    """Sender internal AND at least one recipient, all recipients internal."""
    if not _is_internal_addr(sender):
        return False
    parties = _split(recipients) + _split(cc)
    if not parties:
        return False
    return all(_is_internal_addr(a) for a in parties)


def compute_flags(sender: str, subject: str | None, recipients: str | None, cc: str | None) -> dict:
    """Return {'lcs_internal', 'lcs_shared', 'skip'} for a message."""
    shared = subject_has_project(subject) or crm_in_cc(cc, recipients)
    internal = is_internal_internal(sender, recipients, cc)
    return {
        "lcs_internal": 1 if internal else 0,
        "lcs_shared": 1 if shared else 0,
        "skip": bool(internal and not shared),
    }


# --- permission layer (desk / get_all) -------------------------------------
def get_permission_query_conditions(user: str | None = None) -> str:
    user = user or frappe.session.user
    if user == "Administrator":
        return ""
    esc = frappe.db.escape(user)
    # shared to everyone, OR my own non-internal mail. Non-Email communications
    # (no medium filter here) are unaffected: they have lcs_internal=0 and, if
    # not mailbox-owned, are treated as shared by the backfill.
    return (
        "(`tabCommunication`.lcs_shared = 1 "
        f"or (`tabCommunication`.user = {esc} and `tabCommunication`.lcs_internal = 0))"
    )


def sql_visibility(alias: str = "c", user: str | None = None) -> str:
    """WHERE-clause fragment for the raw-SQL email-list APIs (which bypass
    permission_query_conditions). Shared to all, or my own non-internal mail."""
    user = user or frappe.session.user
    if user == "Administrator":
        return "1=1"
    esc = frappe.db.escape(user)
    return f"({alias}.lcs_shared = 1 or ({alias}.user = {esc} and {alias}.lcs_internal = 0))"


def has_permission(doc: Any, ptype: str = "read", user: str | None = None) -> bool | None:
    if ptype not in ("read", "select"):
        return None
    user = user or frappe.session.user
    if user == "Administrator":
        return None
    if getattr(doc, "lcs_shared", 0):
        return None
    if getattr(doc, "user", None) == user and not getattr(doc, "lcs_internal", 0):
        return None
    return False


# --- release actions -------------------------------------------------------
def _recompute_shared(doc) -> int:
    return 1 if (subject_has_project(doc.subject) or crm_in_cc(doc.get("cc"), doc.recipients)) else 0


@frappe.whitelist()
def release_email(name: str) -> dict:
    """Release one of MY e-mails so the team can see it. Owner (or admin) only."""
    doc = frappe.get_doc("Communication", name)
    if doc.user != frappe.session.user and frappe.session.user != "Administrator":
        frappe.throw(_("Nur der Postfach-Eigentümer kann diese Mail freigeben."), frappe.PermissionError)
    doc.db_set("lcs_shared", 1, update_modified=False)
    return {"ok": True, "shared": True}


@frappe.whitelist()
def unrelease_email(name: str) -> dict:
    """Take back a manual release. Falls back to the automatic P rule, so a mail
    that is structurally shared (project ref / crm CC) stays shared."""
    doc = frappe.get_doc("Communication", name)
    if doc.user != frappe.session.user and frappe.session.user != "Administrator":
        frappe.throw(_("Nur der Postfach-Eigentümer kann die Freigabe zurücknehmen."), frappe.PermissionError)
    doc.db_set("lcs_shared", _recompute_shared(doc), update_modified=False)
    return {"ok": True, "shared": bool(doc.lcs_shared)}
