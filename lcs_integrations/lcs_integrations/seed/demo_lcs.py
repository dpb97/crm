"""Idempotent demo data for the LCS adaptations.

Creates a small, realistic dataset that exercises the LCS-specific
features so they can be demoed end to end:

- CRM Organizations with an `email_domain` (drives domain-binding).
- Contacts on those domains — most released, a few left private to a
  sales user to show the owner-only-until-release rule.
- LCS Projects per organization, with project contacts.
- Email Communications linked to the projects (in + out) so the project
  mail feed (MailActivityWidget) has content.

Safe to run repeatedly — every record is keyed and skipped if present.
Run:  bench --site lcs.local execute lcs_integrations.seed.demo_lcs.seed_demo
"""

from __future__ import annotations

import frappe
from frappe.utils import add_to_date, now_datetime, add_days, nowdate

# (org_name, domain, website, country)
ORGS = [
    ("Doppelmayr Seilbahnen", "doppelmayr.com", "https://www.doppelmayr.com", "Austria"),
    ("LEITNER ropeways", "leitner.com", "https://www.leitner.com", "Italy"),
    ("ROSEN Group", "rosen-group.com", "https://www.rosen-group.com", "Germany"),
    ("Bartholet Maschinenbau", "bmf.ch", "https://www.bartholet.swiss", "Switzerland"),
    ("Tata Projects", "tataprojects.com", "https://www.tataprojects.com", "India"),
]

# (org_domain, first, last, designation, released, owner)
PRIVATE_OWNER = "vertrieb1@lcs-group.com"
CONTACTS = [
    ("doppelmayr.com", "Markus", "Huber", "Head of Procurement", True, None),
    ("doppelmayr.com", "Sabine", "Wagner", "Project Engineer", True, None),
    ("leitner.com", "Luca", "Rossi", "Technical Buyer", True, None),
    ("leitner.com", "Anna", "Gruber", "Site Manager", False, PRIVATE_OWNER),
    ("rosen-group.com", "Thomas", "Berg", "Operations Lead", True, None),
    ("rosen-group.com", "Petra", "Klein", "Procurement", False, PRIVATE_OWNER),
    ("bmf.ch", "Reto", "Meier", "Managing Director", True, None),
    ("tataprojects.com", "Arjun", "Patel", "Senior Engineer", True, None),
    ("tataprojects.com", "Neha", "Sharma", "Contracts Manager", False, PRIVATE_OWNER),
]

# (project_name, org_domain, phase, status, value, project_type)
PROJECTS = [
    ("Material Ropeway Andermatt", "doppelmayr.com", "Offer", "Active", 1850000, "SB"),
    ("Cable Crane Brenner Tunnel", "leitner.com", "Negotiation", "Active", 3200000, "LL"),
    ("Pipeline Inspection Hoist", "rosen-group.com", "Qualified", "Open", 740000, "WI"),
    ("Ski Lift Drive Upgrade", "bmf.ch", "Richtpreis", "Active", 1250000, "SK"),
    ("Bridge Erection Crane", "tataprojects.com", "Offer", "Active", 2600000, "LL"),
]


def _org_name_for(domain: str) -> str | None:
    return frappe.db.get_value("CRM Organization", {"email_domain": domain}, "name")


def _seed_orgs() -> int:
    made = 0
    for name, domain, website, _country in ORGS:
        if frappe.db.exists("CRM Organization", {"organization_name": name}):
            # ensure the domain is set on a pre-existing org
            existing = frappe.db.get_value("CRM Organization", {"organization_name": name}, "name")
            if not frappe.db.get_value("CRM Organization", existing, "email_domain"):
                frappe.db.set_value("CRM Organization", existing, "email_domain", domain)
            continue
        doc = frappe.new_doc("CRM Organization")
        doc.organization_name = name
        doc.website = website
        doc.email_domain = domain
        doc.insert(ignore_permissions=True)
        made += 1
    return made


def _seed_contacts() -> int:
    made = 0
    for domain, first, last, role, released, owner in CONTACTS:
        email = f"{first.lower()}.{last.lower()}@{domain}"
        if frappe.db.exists("Contact Email", {"email_id": email}):
            continue
        org = _org_name_for(domain)
        c = frappe.new_doc("Contact")
        c.first_name = first
        c.last_name = last
        c.company_name = next((o[0] for o in ORGS if o[1] == domain), "")
        c.designation = role
        c.lcs_released = 1 if released else 0
        c.append("email_ids", {"email_id": email, "is_primary": 1})
        if org:
            c.append("links", {"link_doctype": "CRM Organization", "link_name": org})
        c.flags.ignore_mandatory = True
        c.insert(ignore_permissions=True)
        # Private contacts belong to a sales rep so the owner-only rule shows.
        if owner and frappe.db.exists("User", owner):
            frappe.db.set_value("Contact", c.name, "owner", owner)
        made += 1
    return made


def _seed_projects() -> int:
    made = 0
    salesperson = PRIVATE_OWNER if frappe.db.exists("User", PRIVATE_OWNER) else None
    for pname, domain, phase, status, value, ptype in PROJECTS:
        if frappe.db.exists("LCS Project", {"project_name": pname}):
            continue
        org = _org_name_for(domain)
        country = next((o[3] for o in ORGS if o[1] == domain), None)
        p = frappe.new_doc("LCS Project")
        p.project_name = pname
        if org:
            p.organization = org
        p.phase = phase
        p.status = status
        p.estimated_value = value
        p.project_type = ptype
        p.probability = 50
        if salesperson:
            p.salesperson = salesperson
        if country and frappe.db.exists("Country", country):
            p.country = country
        # attach the org's contacts to the project
        for domain2, first, last, *_rest in CONTACTS:
            if domain2 != domain:
                continue
            cname = frappe.db.get_value(
                "Contact Email", {"email_id": f"{first.lower()}.{last.lower()}@{domain}"}, "parent"
            )
            if cname:
                p.append("contacts", {"contact": cname})
        try:
            p.insert(ignore_permissions=True)
            made += 1
        except Exception as exc:  # noqa: BLE001 — keep seeding the rest
            frappe.log_error(title="demo_lcs", message=f"{pname}: {exc}")
    return made


def _seed_communications() -> int:
    made = 0
    for pname, domain, *_rest in PROJECTS:
        project = frappe.db.get_value("LCS Project", {"project_name": pname}, "name")
        if not project:
            continue
        contact = next((c for c in CONTACTS if c[0] == domain), None)
        if not contact:
            continue
        peer = f"{contact[1].lower()}.{contact[2].lower()}@{domain}"
        me = "vertrieb@lcs-group.com"
        thread = [
            ("Received", peer, me, f"Anfrage: {pname}",
             f"Guten Tag, wir interessieren uns für Ihr Angebot zu '{pname}'. Bitte um Rückmeldung."),
            ("Sent", me, peer, f"AW: Anfrage: {pname}",
             "Vielen Dank für Ihre Anfrage — anbei unser Richtpreis. Gerne besprechen wir die Details."),
            ("Received", peer, me, f"AW: {pname} — Termin",
             "Passt, lassen Sie uns nächste Woche einen Call machen."),
        ]
        for i, (direction, sender, recipients, subject, body) in enumerate(thread):
            if frappe.db.exists(
                "Communication",
                {"reference_doctype": "LCS Project", "reference_name": project, "subject": subject},
            ):
                continue
            comm = frappe.new_doc("Communication")
            comm.communication_type = "Communication"
            comm.communication_medium = "Email"
            comm.sent_or_received = direction
            comm.subject = subject
            comm.content = f"<p>{body}</p>"
            comm.sender = sender
            comm.recipients = recipients
            comm.reference_doctype = "LCS Project"
            comm.reference_name = project
            comm.communication_date = add_to_date(now_datetime(), days=-(len(thread) - i) * 2)
            comm.flags.ignore_mandatory = True
            comm.insert(ignore_permissions=True)
            made += 1
    return made


_FIRST = [
    "Felix", "Laura", "Jonas", "Mia", "Paul", "Emma", "Lukas", "Sophie",
    "David", "Hannah", "Tobias", "Lena", "Stefan", "Julia", "Martin", "Nina",
    "Andreas", "Carmen", "Florian", "Katrin", "Simon", "Theresa", "Daniel", "Eva",
]
_LAST = [
    "Berger", "Fischer", "Wolf", "Keller", "Brandl", "Sommer", "Hofer", "Egger",
    "Mayer", "Reiter", "Steiner", "Lang", "Moser", "Bauer", "Pichler", "Wimmer",
    "Lechner", "Aigner", "Holzer", "Url", "Kainz", "Ebner", "Hasler", "Strobl",
]
_ROLES = [
    "Buyer", "Project Manager", "Engineer", "CFO", "Site Supervisor",
    "Procurement Lead", "Technical Director", "Operations Manager", "QA Lead",
]


def seed_test_contacts(per_org: int = 5) -> dict:
    """Bulk test contacts across the demo organizations.

    `per_org` contacts per organization, deterministic names (so re-runs
    are idempotent). Every 3rd contact is left private (lcs_released=0,
    owned by the sales rep) to exercise the owner-only rule.
    """
    made = 0
    private = 0
    n = 0
    for _name, domain, _website, _country in ORGS:
        org = _org_name_for(domain)
        company = next((o[0] for o in ORGS if o[1] == domain), "")
        for i in range(per_org):
            first = _FIRST[n % len(_FIRST)]
            last = _LAST[(n * 7 + i) % len(_LAST)]
            n += 1
            email = f"{first.lower()}.{last.lower()}@{domain}"
            if frappe.db.exists("Contact Email", {"email_id": email}):
                continue
            is_private = (n % 3 == 0)
            c = frappe.new_doc("Contact")
            c.first_name = first
            c.last_name = last
            c.company_name = company
            c.designation = _ROLES[n % len(_ROLES)]
            c.lcs_released = 0 if is_private else 1
            c.append("email_ids", {"email_id": email, "is_primary": 1})
            c.append("phone_nos", {"phone": f"+49 89 {1000000 + n}", "is_primary_mobile_no": 1})
            if org:
                c.append("links", {"link_doctype": "CRM Organization", "link_name": org})
            c.flags.ignore_mandatory = True
            try:
                c.insert(ignore_permissions=True)
            except Exception as exc:  # noqa: BLE001 — keep going
                frappe.log_error(title="demo_lcs", message=f"{email}: {exc}")
                continue
            if is_private and frappe.db.exists("User", PRIVATE_OWNER):
                frappe.db.set_value("Contact", c.name, "owner", PRIVATE_OWNER)
                private += 1
            made += 1
    frappe.db.commit()
    return {"created": made, "private": private}


# Full pipeline showcase: (project_name, org_domain, phase, status, value, probability, ptype)
SHOWCASE_PROJECTS = [
    ("Ropeway Tender Chile", "doppelmayr.com", "Qualified", "Open", 900000, 20, "SB"),
    ("Mine Hoist Budget — Zambia", "rosen-group.com", "Budget", "Open", 1400000, 30, "WI"),
    ("Richtpreis Funicular AT", "leitner.com", "Richtpreis", "Active", 2100000, 45, "SK"),
    ("Cable Crane Offer — Nepal", "tataprojects.com", "Offer", "Active", 2750000, 55, "LL"),
    ("Negotiation Dam Crane CH", "bmf.ch", "Negotiation", "Active", 3300000, 70, "LL"),
    ("Won — Material Ropeway IT", "leitner.com", "Won", "Active", 1950000, 100, "SB"),
    ("Execution Bridge Crane IN", "tataprojects.com", "Execution", "Active", 2600000, 100, "LL"),
    ("Completed Ski Lift CH", "bmf.ch", "Completed", "Completed", 1180000, 100, "SK"),
    ("Lost — Pipeline Hoist US", "rosen-group.com", "Lost", "Cancelled", 820000, 0, "WI"),
]

TRIP_REPORTS = [
    ("Geschäftsreise USA — Q2 Mining Tour", "United States",
     "Kundenbesuche bei Mining-Betreibern an der Westküste; 3 Projekte angebahnt.",
     "Hohe Nachfrage nach QX-Safety-Systemen.", "Angebote für 2 Standorte bis KW+3."),
    ("Geschäftsreise Indien — Infrastructure", "India",
     "Tata Projects + lokale EPCs besucht; Brückenbau-Pipeline stark.",
     "Preissensibel, aber Volumen hoch.", "Richtpreis für Bridge Crane nachreichen."),
]


def _seed_showcase_projects() -> int:
    made = 0
    sales = PRIVATE_OWNER if frappe.db.exists("User", PRIVATE_OWNER) else None
    for pname, domain, phase, status, value, prob, ptype in SHOWCASE_PROJECTS:
        if frappe.db.exists("LCS Project", {"project_name": pname}):
            continue
        try:
            p = frappe.new_doc("LCS Project")
            p.project_name = pname
            org = _org_name_for(domain)
            if org:
                p.organization = org
            p.phase = phase
            p.status = status
            p.estimated_value = value
            p.probability = prob
            p.project_type = ptype
            country = next((o[3] for o in ORGS if o[1] == domain), None)
            if country and frappe.db.exists("Country", country):
                p.country = country
            if sales:
                p.salesperson = sales
            p.insert(ignore_permissions=True)
            made += 1
        except Exception as exc:  # noqa: BLE001
            frappe.log_error(title="demo_lcs.showcase", message=f"{pname}: {exc}")
    frappe.db.commit()
    return made


def _seed_offers() -> int:
    """1–2 Offer revisions per active project; the Lost one gets a reason."""
    made = 0
    projects = frappe.get_all(
        "LCS Project",
        filters={"phase": ["in", ["Richtpreis", "Offer", "Negotiation", "Won", "Lost"]]},
        fields=["name", "project_name", "phase", "estimated_value"],
    )
    for pr in projects:
        existing = frappe.db.count("LCS Offer", {"project": pr.name})
        if existing:
            continue
        revisions = 2 if pr.phase in ("Negotiation", "Won") else 1
        for v in range(1, revisions + 1):
            try:
                o = frappe.new_doc("LCS Offer")
                o.project = pr.name
                o.offer_title = f"{pr.project_name} — Angebot V{v}"
                o.version = v
                o.value = (pr.estimated_value or 0) * (1.0 + 0.03 * (v - 1))
                o.currency = "EUR"
                o.offer_date = frappe.utils.nowdate()
                o.valid_until = frappe.utils.add_days(frappe.utils.nowdate(), 30)
                if pr.phase == "Lost":
                    o.status = "Rejected"
                    o.lost_reason = "Preis zu hoch — Wettbewerber günstiger"
                elif pr.phase == "Won":
                    o.status = "Accepted"
                    o.won_notes = "Zuschlag erhalten."
                else:
                    o.status = "Sent" if v == 1 else "Revised"
                o.insert(ignore_permissions=True)
                made += 1
            except Exception as exc:  # noqa: BLE001
                frappe.log_error(title="demo_lcs.offers", message=f"{pr.name} v{v}: {exc}")
    frappe.db.commit()
    return made


def _seed_followups() -> int:
    """Wiedervorlagen on released contacts, due overdue/today/upcoming."""
    owner = PRIVATE_OWNER if frappe.db.exists("User", PRIVATE_OWNER) else "Administrator"
    contacts = frappe.get_all(
        "Contact", filters={"lcs_released": 1}, fields=["name"], limit=6
    )
    presets = [(-2, "Messebekanntschaft — nachfassen"), (0, "Heute anrufen"),
               (7, "Projekt pausiert — in 1 Woche prüfen"), (30, "Quartals-Check"),
               (3, "Angebot nachfassen"), (14, "Richtpreis besprechen")]
    made = 0
    for i, c in enumerate(contacts):
        days, reason = presets[i % len(presets)]
        due = frappe.utils.add_days(frappe.utils.nowdate(), days)
        if frappe.db.exists("ToDo", {"reference_name": c.name, "lcs_kind": "Follow-up", "date": due}):
            continue
        try:
            frappe.get_doc({
                "doctype": "ToDo",
                "allocated_to": owner,
                "description": f"Contact: {c.name}\n{reason}",
                "date": due,
                "reference_type": "Contact",
                "reference_name": c.name,
                "priority": "Medium",
                "lcs_kind": "Follow-up",
                "lcs_reason": reason,
                "lcs_visible_to_manager": 1,
            }).insert(ignore_permissions=True)
            made += 1
        except Exception as exc:  # noqa: BLE001
            frappe.log_error(title="demo_lcs.followups", message=f"{c.name}: {exc}")
    frappe.db.commit()
    return made


def _seed_trip_reports() -> int:
    owner = PRIVATE_OWNER if frappe.db.exists("User", PRIVATE_OWNER) else "Administrator"
    made = 0
    for title, country, summary, findings, nxt in TRIP_REPORTS:
        if frappe.db.exists("LCS Trip Report", {"title": title}):
            continue
        try:
            t = frappe.new_doc("LCS Trip Report")
            t.title = title
            t.trip_country = country if frappe.db.exists("Country", country) else None
            t.trip_from = frappe.utils.add_days(frappe.utils.nowdate(), -20)
            t.trip_to = frappe.utils.add_days(frappe.utils.nowdate(), -14)
            t.salesperson = owner
            t.summary = summary
            t.key_findings = findings
            t.next_steps = nxt
            t.flags.ignore_mandatory = True
            t.insert(ignore_permissions=True)
            made += 1
        except Exception as exc:  # noqa: BLE001
            frappe.log_error(title="demo_lcs.trips", message=f"{title}: {exc}")
    frappe.db.commit()
    return made


def enable_speech() -> dict:
    """Turn on voice input (Web Speech API — browser-native, no Azure keys)."""
    s = frappe.get_single("LCS Speech Settings")
    s.enabled = 1
    s.backend = "Web Speech API"
    if not s.custom_phrases:
        s.custom_phrases = "Seilkran\nRichtpreis\nKabelkran\nDoppelmayr\nLEITNER\nRopeway"
    s.save(ignore_permissions=True)
    frappe.db.commit()
    return {"enabled": 1, "backend": s.backend}


def _seed_opportunity_matrix() -> int:
    made = 0
    projects = frappe.get_all(
        "LCS Project",
        filters={"phase": ["in", ["Offer", "Negotiation", "Won"]]},
        fields=["name", "organization"],
        limit=4,
    )
    scores = [(4, 5, 4, 3, 5), (3, 4, 5, 2, 4), (5, 3, 4, 4, 3)]
    for i, pr in enumerate(projects):
        if frappe.db.exists("LCS Opportunity Matrix", {"project": pr.name}):
            continue
        tf, cf, rs, cl, si = scores[i % len(scores)]
        try:
            m = frappe.new_doc("LCS Opportunity Matrix")
            m.project = pr.name
            if pr.organization:
                m.organization = pr.organization
            m.technical_fit = tf
            m.commercial_fit = cf
            m.relationship_strength = rs
            m.competition_level = cl
            m.strategic_importance = si
            m.flags.ignore_mandatory = True
            m.insert(ignore_permissions=True)
            made += 1
        except Exception as exc:  # noqa: BLE001
            frappe.log_error(title="demo_lcs.matrix", message=f"{pr.name}: {exc}")
    frappe.db.commit()
    return made


def _seed_tasks_notes() -> dict:
    owner = PRIVATE_OWNER if frappe.db.exists("User", PRIVATE_OWNER) else "Administrator"
    leads = frappe.get_all("CRM Lead", fields=["name", "lead_name"], limit=5)
    tasks = notes = 0
    task_titles = ["Erstkontakt anrufen", "Unterlagen senden", "Technik-Call planen",
                   "Angebot nachfassen", "Referenzen teilen"]
    note_texts = ["Auf Messe kennengelernt, hohes Interesse.",
                  "Budget noch offen, Entscheidung Q3.",
                  "Technische Anforderungen geklärt.",
                  "Wettbewerb im Spiel — Preis kritisch.",
                  "Bestandskunde, Folgeprojekt möglich."]
    for i, ld in enumerate(leads):
        try:
            if not frappe.db.exists("CRM Task", {"reference_docname": ld.name, "title": task_titles[i % len(task_titles)]}):
                t = frappe.new_doc("CRM Task")
                t.title = task_titles[i % len(task_titles)]
                t.reference_doctype = "CRM Lead"
                t.reference_docname = ld.name
                t.assigned_to = owner
                t.date = frappe.utils.add_days(frappe.utils.nowdate(), i + 1)
                t.flags.ignore_mandatory = True
                t.insert(ignore_permissions=True)
                tasks += 1
        except Exception as exc:  # noqa: BLE001
            frappe.log_error(title="demo_lcs.tasks", message=f"{ld.name}: {exc}")
        try:
            if not frappe.db.exists("FCRM Note", {"reference_docname": ld.name, "title": "Gesprächsnotiz"}):
                n = frappe.new_doc("FCRM Note")
                n.title = "Gesprächsnotiz"
                n.content = note_texts[i % len(note_texts)]
                n.reference_doctype = "CRM Lead"
                n.reference_docname = ld.name
                n.flags.ignore_mandatory = True
                n.insert(ignore_permissions=True)
                notes += 1
        except Exception as exc:  # noqa: BLE001
            frappe.log_error(title="demo_lcs.notes", message=f"{ld.name}: {exc}")
    frappe.db.commit()
    return {"tasks": tasks, "notes": notes}


def seed_showcase() -> dict:
    """Full demo showcase + voice input enabled."""
    return {
        "projects": _seed_showcase_projects(),
        "offers": _seed_offers(),
        "followups": _seed_followups(),
        "trip_reports": _seed_trip_reports(),
        "opportunity_matrix": _seed_opportunity_matrix(),
        "tasks_notes": _seed_tasks_notes(),
        "speech": enable_speech(),
    }


def seed_demo() -> dict:
    """Entry point — seeds orgs, contacts, projects, project emails."""
    result = {
        "organizations": _seed_orgs(),
        "contacts": _seed_contacts(),
        "projects": _seed_projects(),
        "communications": _seed_communications(),
    }
    frappe.db.commit()
    return result


FLAGSHIP_NAME = "Showcase — Seilkran Zugspitze"


def seed_flagship() -> dict:
    """One fully-populated demo project: pricing, contacts, two offers,
    follow-up tasks and a small mail thread. Idempotent."""
    existing = frappe.db.get_value("LCS Project", {"project_name": FLAGSHIP_NAME}, "name")
    if existing:
        return {"status": "exists", "project": existing}

    org = frappe.db.get_value(
        "CRM Organization", {"organization_name": ["like", "%Doppelmayr%"]}, "name"
    )
    cf = next(
        (f.fieldname for f in frappe.get_meta("LCS Project Contact").fields
         if f.fieldtype == "Link" and f.options == "Contact"),
        "contact",
    )
    type_field = frappe.get_meta("LCS Project").get_field("project_type")
    ptype = (type_field.options or "").split("\n")[0].strip() if type_field and type_field.options else None
    contacts = frappe.get_all(
        "Contact",
        filters=[["name", "not in", ["salesmgr", "vertrieb1", "vertrieb2", "Administrator", "Guest"]]],
        limit=3,
        pluck="name",
    )

    p = frappe.new_doc("LCS Project")
    p.project_name = FLAGSHIP_NAME
    if ptype:
        p.project_type = ptype
    p.country = "Austria"
    p.is_gu = 1
    p.phase = "Negotiation"
    p.status = "Active"
    if org:
        p.organization = org
    p.salesperson = "vertrieb1@lcs-group.com"
    p.sales_manager = "salesmgr@lcs-group.com"
    p.budget_customer = 2500000
    p.richtpreis = 2750000
    p.angebot_total = 2690000
    p.estimated_value = 2690000
    p.probability = 70
    p.notes = (
        "Materialseilkran 60t für den Ausbau der Bergstation.\n"
        "Kunde wünscht Liefertermin Q3. Wettbewerb: 1 Mitbewerber – "
        "preislich knapp, technisch führend."
    )
    p.team_link = "https://teams.microsoft.com/l/channel/showcase"
    p.sharepoint_link = "https://lcsgroup.sharepoint.com/sites/Zugspitze"
    for c in contacts:
        p.append("contacts", {cf: c})
    p.insert(ignore_permissions=True)
    pj = p.name

    for ver, (st, val) in enumerate([("Sent", 2750000), ("In Review", 2690000)], start=1):
        o = frappe.new_doc("LCS Offer")
        o.project = pj
        o.offer_title = f"{FLAGSHIP_NAME} – v{ver}"
        o.version = ver
        o.status = st
        o.value = val
        o.currency = "EUR"
        o.probability = 70
        o.offer_date = frappe.utils.add_days(frappe.utils.nowdate(), -20 + ver * 5)
        o.valid_until = frappe.utils.add_days(frappe.utils.nowdate(), 30)
        o.insert(ignore_permissions=True)

    tasks = [
        ("Technische Rückfrage Bergstation klären", "High", 2),
        ("Angebot v2 nachfassen", "Medium", 5),
        ("Referenzliste senden", "Low", -3),
    ]
    for title, prio, off in tasks:
        frappe.get_doc({
            "doctype": "CRM Task", "title": title, "status": "Todo", "priority": prio,
            "date": frappe.utils.add_days(frappe.utils.nowdate(), off),
            "reference_doctype": "LCS Project", "reference_docname": pj,
        }).insert(ignore_permissions=True)

    mails = [
        ("Received", "kunde@doppelmayr.com", "Anfrage Materialseilkran Zugspitze", "Bitte um Angebot inkl. Montage.", -18),
        ("Sent", "vertrieb1@lcs-group.com", "AW: Angebot Materialseilkran Zugspitze", "Anbei unser Angebot v1.", -13),
        ("Received", "kunde@doppelmayr.com", "Rückfrage zur Tragfähigkeit", "Können Sie 60t bestätigen?", -6),
        ("Sent", "vertrieb1@lcs-group.com", "AW: aktualisiertes Angebot v2", "Tragfähigkeit bestätigt, v2 anbei.", -2),
    ]
    for sor, sender, subj, body, off in mails:
        c = frappe.new_doc("Communication")
        c.communication_type = "Communication"
        c.communication_medium = "Email"
        c.sent_or_received = sor
        c.sender = sender
        c.subject = subj
        c.content = body
        c.reference_doctype = "LCS Project"
        c.reference_name = pj
        c.communication_date = add_to_date(now_datetime(), days=off)
        c.status = "Linked"
        c.insert(ignore_permissions=True)

    frappe.db.commit()
    return {
        "status": "created", "project": pj, "type": ptype, "org": org,
        "contacts": len(contacts), "offers": 2, "tasks": len(tasks), "mails": len(mails),
    }


def seed_contact_demo() -> dict:
    """Link Tata Projects contacts to projects and add per-contact mail
    activity, so the contact detail tabs (Projekte / Aktivität) aren't empty."""
    org = frappe.db.get_value("CRM Organization", {"organization_name": "Tata Projects"}, "name")
    projects = (
        frappe.get_all("LCS Project", filters={"organization": org}, pluck="name") if org else []
    )
    if not projects:
        return {"status": "no_tata_projects"}
    cf = next(
        (f.fieldname for f in frappe.get_meta("LCS Project Contact").fields
         if f.fieldtype == "Link" and f.options == "Contact"),
        "contact",
    )
    contacts = frappe.get_all(
        "Contact", filters={"company_name": org}, fields=["name", "email_id"]
    )
    if not contacts:
        contacts = frappe.get_all(
            "Contact", filters=[["email_id", "like", "%tataprojects%"]],
            fields=["name", "email_id"],
        )
    linked = mails = 0
    for idx, c in enumerate(contacts[:4]):
        target = projects[idx % len(projects)]
        if not frappe.get_all("LCS Project Contact", filters={"parent": target, cf: c.name}, limit=1):
            p = frappe.get_doc("LCS Project", target)
            p.append("contacts", {cf: c.name})
            p.save(ignore_permissions=True)
            linked += 1
        email = c.email_id or f"{c.name.lower().replace(' ', '.')}@tataprojects.com"
        if not frappe.db.exists("Communication", {"sender": email}):
            thread = [
                ("Received", email, f"Anfrage {target}", "Bitte um Angebot und Zeitplan.", -12),
                ("Sent", "vertrieb1@lcs-group.com", f"AW: Anfrage {target}", "Anbei unser Angebot, Rückfragen jederzeit.", -9),
                ("Received", email, "Rückfrage Kommerzielles", "Können wir die Zahlungsbedingungen anpassen?", -4),
            ]
            for sor, sender, subj, body, off in thread:
                m = frappe.new_doc("Communication")
                m.communication_type = "Communication"
                m.communication_medium = "Email"
                m.sent_or_received = sor
                m.sender = sender
                m.recipients = "vertrieb1@lcs-group.com" if sor == "Received" else email
                m.subject = subj
                m.content = body
                m.reference_doctype = "LCS Project"
                m.reference_name = target
                m.communication_date = add_to_date(now_datetime(), days=off)
                m.status = "Linked"
                m.insert(ignore_permissions=True)
                mails += 1
    frappe.db.commit()
    return {"status": "ok", "contacts": len(contacts), "linked": linked, "mails": mails}


def seed_avatars(overwrite: int = 0) -> dict:
    """Give demo contacts a face from pravatar.cc (deterministic per email).
    Written via db.set_value so the Graph photo-push hook does not fire."""
    made = 0
    for c in frappe.get_all("Contact", fields=["name", "email_id", "image"]):
        if c.image and not overwrite:
            continue
        seed = (c.email_id or c.name).strip().lower()
        url = f"https://i.pravatar.cc/300?u={frappe.utils.quote(seed)}"
        frappe.db.set_value("Contact", c.name, "image", url, update_modified=False)
        made += 1
    frappe.db.commit()
    return {"updated": made}


def seed_leads() -> dict:
    """Wipe existing CRM Leads and create ones that match the demo orgs —
    the top of the Lead -> Angebot -> Projekt funnel."""
    for n in frappe.get_all("CRM Lead", pluck="name"):
        frappe.delete_doc("CRM Lead", n, force=1, ignore_permissions=True)

    LEADS = [
        ("Stefan", "Huber", "Doppelmayr Seilbahnen", "Qualified", 1800000),
        ("Marco", "Bianchi", "LEITNER ropeways", "Contacted", 2400000),
        ("Arjun", "Nair", "Tata Projects", "Nurture", 2600000),
        ("Anna", "Berg", "ROSEN Group", "New", 1400000),
        ("Luca", "Moser", "Bartholet Maschinenbau", "Qualified", 1250000),
        ("Felix", "Wagner", "ACME Anlagenbau GmbH", "Contacted", 945000),
        ("Ingrid", "Solberg", "Construct Norge AS", "New", 1310000),
        ("Thomas", "Bergmann", "Bergblick Seilbahn AG", "Nurture", 188500),
    ]
    made = 0
    for fn, ln, org, status, value in LEADS:
        d = frappe.new_doc("CRM Lead")
        d.first_name = fn
        d.last_name = ln
        d.lead_name = f"{fn} {ln}"
        d.organization = org
        d.status = status
        d.email = f"{fn.lower()}.{ln.lower()}@{org.split()[0].lower()}.com"
        d.annual_revenue = value
        d.lead_owner = "vertrieb1@lcs-group.com"
        d.insert(ignore_permissions=True)
        made += 1
    frappe.db.commit()
    return {"created": made}


def seed_activity_types() -> dict:
    """Add non-email activity types (call, meeting, demo) for Neha Sharma so
    the contact activity tab shows a realistic mix, not only emails."""
    email = "neha.sharma@tataprojects.com"
    target = frappe.db.get_value("LCS Project", {"project_name": "Bridge Erection Crane"}, "name")
    if not target:
        return {"status": "no_project"}
    valid = set((frappe.get_meta("Communication").get_field("communication_medium").options or "").split("\n"))

    def med(*candidates):
        for c in candidates:
            if c in valid:
                return c
        return "Other"

    acts = [
        ("Received", med("Phone"), "Telefonat: Projektabstimmung Bergstation", "Zeitplan besprochen, Kunde will Liefertermin Q3.", -7),
        ("Sent", med("Meeting", "Event", "Visit"), "Vor-Ort-Termin Baustelle", "Begehung der Baustelle vereinbart.", -3),
        ("Received", med("Event", "Meeting", "Other"), "Web-Demo Steuerungssystem", "Online-Demo des Steuerungssystems durchgeführt.", -1),
    ]
    made = 0
    for sor, medium, subj, body, off in acts:
        if frappe.db.exists("Communication", {"subject": subj}):
            continue
        m = frappe.new_doc("Communication")
        m.communication_type = "Communication"
        m.communication_medium = medium
        m.sent_or_received = sor
        m.sender = email if sor == "Received" else "vertrieb1@lcs-group.com"
        m.recipients = "vertrieb1@lcs-group.com" if sor == "Received" else email
        m.subject = subj
        m.content = body
        m.reference_doctype = "LCS Project"
        m.reference_name = target
        m.communication_date = add_to_date(now_datetime(), days=off)
        m.status = "Linked"
        m.insert(ignore_permissions=True)
        made += 1
    frappe.db.commit()
    return {"status": "ok", "created": made, "mediums": sorted(valid)}


def seed_career_history() -> dict:
    """Give a few contacts a former employer (one of the other demo orgs) so
    the network graph shows career moves between companies."""
    orgs = set(frappe.get_all("CRM Organization", pluck="name"))
    ring = [o for o in [
        "Doppelmayr Seilbahnen", "LEITNER ropeways", "Bartholet Maschinenbau",
        "Tata Projects", "ROSEN Group", "Bergblick Seilbahn AG",
    ] if o in orgs]
    if len(ring) < 2:
        return {"status": "not_enough_orgs"}
    contacts = frappe.get_all(
        "Contact", filters={"company_name": ["in", ring]},
        fields=["name", "company_name", "previous_companies"],
    )
    made = 0
    for i, org in enumerate(ring):
        prev = ring[(i + 1) % len(ring)]
        cand = [c for c in contacts if c.company_name == org and not (c.previous_companies or "").strip()]
        if cand:
            frappe.db.set_value("Contact", cand[0].name, "previous_companies", prev, update_modified=False)
            made += 1
    frappe.db.commit()
    return {"status": "ok", "links": made}


def seed_all() -> dict:
    """One-shot demo seeding: runs every seeder (idempotent) and tops up
    open follow-up tasks (with due dates) + a recent comment per active
    project, so Sales-Meeting / Forecast / activity views are all populated."""
    report = {}
    for fn in ("seed_showcase", "seed_flagship", "seed_demo", "_seed_offers",
               "seed_contact_demo", "seed_activity_types", "seed_leads", "seed_avatars",
               "seed_career_history"):
        f = globals().get(fn)
        if not f:
            continue
        try:
            report[fn] = f()
        except Exception as e:  # one seeder failing must not abort the rest
            report[fn] = "ERR " + repr(e)[:120]

    ACTIVE = ["Qualified", "Budget", "Richtpreis", "Offer", "Negotiation"]
    ACTIONS = ["Angebot nachfassen", "Technische Klärung mit Kunde",
               "Richtpreis abstimmen", "Liefertermin bestätigen", "Vertrag final prüfen"]
    projs = frappe.get_all("LCS Project", filters={"phase": ["in", ACTIVE]}, fields=["name"])
    tasks = comments = 0
    for i, p in enumerate(projs):
        if not frappe.get_all("CRM Task", filters={
            "reference_doctype": "LCS Project", "reference_docname": p.name,
            "status": ["in", ["Todo", "Backlog", "In Progress"]],
        }, limit=1):
            t = frappe.new_doc("CRM Task")
            t.title = ACTIONS[i % len(ACTIONS)]
            t.status = "Todo"
            t.priority = "Medium"
            t.due_date = add_days(nowdate(), (i % 10) - 2)
            t.reference_doctype = "LCS Project"
            t.reference_docname = p.name
            t.insert(ignore_permissions=True)
            tasks += 1
        if not frappe.get_all("Comment", filters={
            "reference_doctype": "LCS Project", "reference_name": p.name, "comment_type": "Comment",
        }, limit=1):
            c = frappe.new_doc("Comment")
            c.comment_type = "Comment"
            c.reference_doctype = "LCS Project"
            c.reference_name = p.name
            c.content = "Letzter Stand: " + ACTIONS[i % len(ACTIONS)] + "."
            c.insert(ignore_permissions=True)
            comments += 1
    frappe.db.commit()
    report["open_tasks"] = tasks
    report["comments"] = comments
    return report
