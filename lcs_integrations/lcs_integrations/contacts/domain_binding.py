"""Bind contacts and emails to a customer by mail domain.

This is the canonical resolver for "given an email domain, which customer
(CRM Organization) and which active project does it belong to?". Both the
shared-mailbox contact sync and the inbound/outbound mail autolink hook
build on the helpers here.

Binding rules (LCS minimum feature set):
- A Contact whose primary email shares an organization's `email_domain`
  gets a Dynamic Link to that CRM Organization (idempotent).
- The organization's most recent non-closed LCS Project is treated as the
  "active" project — emails route there and the contact is added to the
  project's contact table.

Personal mail domains are never bound — they don't identify a customer.
"""

from __future__ import annotations

from typing import Any

import frappe

PERSONAL_DOMAINS = frozenset({
    "gmail.com", "googlemail.com", "yahoo.com", "outlook.com", "hotmail.com",
    "gmx.de", "gmx.at", "gmx.net", "web.de", "t-online.de", "icloud.com",
})

# Phases that mean the project is no longer actively worked.
_CLOSED_PHASES = ("Completed", "Lost")


def domain_of(address: str | None) -> str | None:
    """Lower-cased domain part of an email address, or None."""
    if not address or "@" not in address:
        return None
    domain = address.rsplit("@", 1)[-1].lower().strip()
    return domain or None


def is_bindable_domain(domain: str | None) -> bool:
    return bool(domain) and domain not in PERSONAL_DOMAINS


def org_for_domain(domain: str) -> str | None:
    """Resolve a CRM Organization name from a mail domain.

    Primary match: the explicit `email_domain` custom field. Fallback:
    the domain appears in the organization's website URL.
    """
    if not is_bindable_domain(domain):
        return None

    name = frappe.db.get_value("CRM Organization", {"email_domain": domain}, "name")
    if name:
        return name

    # Fallback — derive from website (e.g. https://www.kunde.de).
    row = frappe.db.sql(
        """SELECT name FROM `tabCRM Organization`
           WHERE website LIKE %(p1)s OR website LIKE %(p2)s
           ORDER BY modified DESC LIMIT 1""",
        {"p1": f"%//{domain}%", "p2": f"%.{domain}%"},
        as_dict=True,
    )
    if row:
        return row[0]["name"]

    # Last resort — match the domain's main label against an organization name
    # (many customers have neither email_domain nor website filled). Conservative:
    # the label must be ≥6 chars and be contained in the normalized org name.
    return _org_by_name_label(domain)


def _norm(text: str) -> str:
    return "".join(ch for ch in str(text or "").lower() if ch.isalnum())


def _org_by_name_label(domain: str) -> str | None:
    import re

    label = domain.split(".")[0]
    label = re.sub(r"(^|[-_])(www|mail|demo|test|kontakt|office|info)([-_]|$)", "", label)
    label = _norm(label)
    if len(label) < 6:
        return None
    for o in frappe.get_all("CRM Organization", fields=["name", "organization_name"], limit=0):
        norm = _norm(o.organization_name or o.name)
        if label in norm or norm[: len(label)] == label:
            return o.name
    return None


def active_project_for_org(org: str) -> str | None:
    """Most recently modified non-closed LCS Project of an organization."""
    rows = frappe.get_all(
        "LCS Project",
        filters={"organization": org, "phase": ["not in", _CLOSED_PHASES]},
        fields=["name"],
        order_by="modified desc",
        limit=1,
    )
    return rows[0]["name"] if rows else None


def resolve_project_for_domain(domain: str | None) -> dict[str, str | None]:
    """One-shot resolver used by the mail autolink hook."""
    org = org_for_domain(domain) if domain else None
    project = active_project_for_org(org) if org else None
    return {"organization": org, "project": project}


# --------------------------------------------------------------- Binding

def _has_org_link(contact, org: str) -> bool:
    return any(
        l.link_doctype == "CRM Organization" and l.link_name == org
        for l in (contact.get("links") or [])
    )


def bind_contact_to_org(contact_name: str, org: str, *, add_to_project: bool = True) -> bool:
    """Link a Contact to a CRM Organization and (optionally) its active
    project. Idempotent — returns True only when something changed.

    Also fills the VISIBLE `company_name` field (never overriding a manual one)
    so the contact actually shows its customer — the Dynamic Link alone left the
    company field blank in the UI.
    """
    contact = frappe.get_doc("Contact", contact_name)
    changed = False
    org_label = frappe.db.get_value("CRM Organization", org, "organization_name") or org

    need_link = not _has_org_link(contact, org)
    need_company = not (contact.company_name or "").strip()
    if need_link or need_company:
        if need_link:
            contact.append("links", {"link_doctype": "CRM Organization", "link_name": org})
        if need_company:
            contact.company_name = org_label
        # Skip the Outlook push echo for a pure link/company change.
        setattr(contact, "_lcs_skip_push", True)
        contact.save(ignore_permissions=True)
        changed = True

    if add_to_project:
        project = active_project_for_org(org)
        if project and _add_contact_to_project(project, contact_name):
            changed = True

    return changed


def _add_contact_to_project(project: str, contact_name: str) -> bool:
    """Append the contact to the LCS Project's contact table if missing."""
    doc = frappe.get_doc("LCS Project", project)
    if any(row.contact == contact_name for row in (doc.get("contacts") or [])):
        return False
    doc.append("contacts", {"contact": contact_name})
    doc.save(ignore_permissions=True)
    return True


def bind_contact_by_domain(contact_name: str, *, add_to_project: bool = True) -> str | None:
    """Derive the contact's domain from its primary email and bind it.

    Returns the matched organization name, or None when nothing matched.
    """
    primary = frappe.db.get_value(
        "Contact Email", {"parent": contact_name, "is_primary": 1}, "email_id"
    ) or frappe.db.get_value("Contact Email", {"parent": contact_name}, "email_id")

    org = org_for_domain(domain_of(primary)) if primary else None
    if not org:
        return None
    bind_contact_to_org(contact_name, org, add_to_project=add_to_project)
    return org


# --------------------------------------------------------------- Hooks

def on_contact_change(doc: Any, method: str | None = None) -> None:
    """Contact after_insert / on_update hook: bind by mail domain.

    Idempotent and cheap — a no-op when the domain doesn't match a customer
    or the link already exists.
    """
    try:
        bind_contact_by_domain(doc.name)
    except Exception as exc:  # noqa: BLE001 — never block a Contact save
        frappe.log_error(title="domain_binding", message=f"{doc.name}: {exc}")


def backfill_all() -> dict[str, int]:
    """Bind EVERY existing Contact to its customer by mail domain (fills the
    visible company_name + the Dynamic Link). Idempotent — safe to re-run."""
    names = frappe.get_all("Contact", pluck="name")
    bound = 0
    for name in names:
        try:
            if bind_contact_by_domain(name):
                bound += 1
        except Exception as exc:  # noqa: BLE001 — log, keep going
            frappe.log_error(title="domain_binding backfill", message=f"{name}: {exc}")
    frappe.db.commit()
    return {"contacts": len(names), "bound": bound}


# ----------------------------------------------------------- Reconcile

def reconcile_all() -> dict[str, int]:
    """Scheduler entry: bind every shared-mailbox contact to its customer.

    Walks each CRM Organization that has an `email_domain` and links every
    Contact whose primary email matches. Cheap and idempotent — safe to run
    daily. Gated by the directory-import setting so it stays opt-in.
    """
    settings = frappe.get_cached_doc("LCS Outlook Sync Settings")
    if not settings.get("enable_directory_domain_import"):
        return {"organizations": 0, "bound": 0}

    orgs = frappe.get_all(
        "CRM Organization",
        filters={"email_domain": ["is", "set"]},
        fields=["name", "email_domain"],
    )

    bound = 0
    for org in orgs:
        domain = (org.email_domain or "").lower().strip()
        if not is_bindable_domain(domain):
            continue
        contacts = frappe.db.sql(
            """SELECT DISTINCT parent FROM `tabContact Email`
               WHERE email_id LIKE %(pattern)s""",
            {"pattern": f"%@{domain}"},
            as_dict=True,
        )
        for row in contacts:
            try:
                if bind_contact_to_org(row["parent"], org.name):
                    bound += 1
            except Exception as exc:  # noqa: BLE001 — log, keep reconciling
                frappe.log_error(title="domain_binding", message=f"{row['parent']}: {exc}")

    frappe.db.commit()
    return {"organizations": len(orgs), "bound": bound}
