"""
Outlook Add-in backend — endpoints called by the taskpane running inside
Outlook's iframe. Every entry point is idempotent and read-only OR uses
an explicit create intent, so an accidental double-click from the pane
cannot corrupt CRM state.

CORS: these endpoints are whitelisted and served over https so the
Office.js sandbox can call them cross-origin.
"""

import frappe


@frappe.whitelist()
def lookup_email_context(sender_email: str, subject: str = ""):
    """
    Entry point for the taskpane when an email is opened.

    Returns contact / organization / open project matches for the sender's
    email address so the taskpane can show "You are corresponding with X
    about project Y" before the user does anything.
    """
    if not sender_email:
        return {"matched": False, "contacts": [], "organizations": [], "projects": [], "offers": []}

    domain = sender_email.split("@")[-1].lower() if "@" in sender_email else None

    # Contacts matching by email
    contacts = frappe.db.sql(
        """SELECT DISTINCT c.name, c.full_name, c.designation, c.company_name
           FROM `tabContact` c
           JOIN `tabContact Email` e ON e.parent = c.name
           WHERE LOWER(e.email_id) = LOWER(%s)
           LIMIT 5""",
        (sender_email,),
        as_dict=True,
    )

    # Organizations matching by domain (if we have web_url or email_domain)
    organizations = []
    if domain:
        organizations = frappe.db.sql(
            """SELECT DISTINCT name, organization_name, industry
               FROM `tabCRM Organization`
               WHERE website LIKE %s OR website LIKE %s
               LIMIT 5""",
            (f"%{domain}%", f"%//{domain}%"),
            as_dict=True,
        )

    # LCS Projects via matching organizations
    org_names = [o["name"] for o in organizations]
    projects = []
    if org_names:
        projects = frappe.get_all(
            "LCS Project",
            filters={
                "organization": ["in", org_names],
                "status": ["not in", ["Completed", "Cancelled"]],
            },
            fields=["name", "project_name", "project_number", "phase", "estimated_value", "probability"],
            order_by="modified desc",
            limit=10,
        )

    # Recent offers for those projects
    offers = []
    if projects:
        project_names = [p["name"] for p in projects]
        offers = frappe.get_all(
            "LCS Offer",
            filters={
                "project": ["in", project_names],
                "status": ["in", ["Draft", "Sent", "In Review"]],
            },
            fields=["name", "project", "offer_title", "version", "status", "value", "valid_until"],
            order_by="modified desc",
            limit=10,
        )

    return {
        "matched": bool(contacts or organizations or projects),
        "sender": sender_email,
        "domain": domain,
        "contacts": contacts,
        "organizations": organizations,
        "projects": projects,
        "offers": offers,
    }


@frappe.whitelist()
def log_email_to_project(project: str, subject: str, body: str, sender: str, received_at: str = None):
    """
    Attach an email as a Comment on the LCS Project's activity feed.
    Used by the "Log to CRM" ribbon action.
    """
    if not frappe.db.exists("LCS Project", project):
        frappe.throw(f"LCS Project {project} not found")

    comment = frappe.new_doc("Comment")
    comment.comment_type = "Comment"
    comment.reference_doctype = "LCS Project"
    comment.reference_name = project
    comment.subject = subject or "Email"
    # Strip HTML for storage; keep plain text for searchability
    import re
    plain = re.sub(r"<[^>]+>", "", body or "").strip()
    comment.content = f"📧 **Email from {sender}**\n\n{plain[:2000]}"
    comment.insert(ignore_permissions=True)
    frappe.db.commit()

    return {"ok": True, "comment": comment.name, "project": project}


@frappe.whitelist()
def create_lead_from_email(sender: str, sender_name: str = "", subject: str = "", body: str = ""):
    """
    Create a new CRM Lead from an email. Used when the sender domain
    doesn't match any existing organization.
    """
    if frappe.db.exists("CRM Lead", {"email": sender}):
        lead_name = frappe.db.get_value("CRM Lead", {"email": sender}, "name")
        return {"ok": True, "lead": lead_name, "created": False}

    lead = frappe.new_doc("CRM Lead")
    lead.lead_name = sender_name or sender.split("@")[0]
    lead.email = sender
    if hasattr(lead, "status"):
        lead.status = "New"
    lead.insert(ignore_permissions=True)
    frappe.db.commit()
    return {"ok": True, "lead": lead.name, "created": True}


@frappe.whitelist()
def search_projects(query: str, limit: int = 20):
    """Autocomplete endpoint for the 'Link to Project' picker."""
    return frappe.get_all(
        "LCS Project",
        or_filters={
            "project_name": ["like", f"%{query}%"],
            "project_number": ["like", f"%{query}%"],
        },
        fields=["name", "project_name", "project_number", "phase", "organization"],
        order_by="modified desc",
        limit=int(limit),
    )
