"""Idempotent mock data for the LCS demo surface.

Run from the bench:

    bench --site lcs.local execute lcs_integrations.seed.mock_mail.seed_all

DEV ONLY. The function refuses to run unless `developer_mode=1` so it
can't be called against a live tenant by accident.

What gets seeded:
- 3 demo Users (vertrieb1/2/salesmgr)
- 3 CRM Organizations (DE, CH, NO)
- 3 primary Contacts (with phones / emails)
- 3 Outlook Mailbox Bindings — one per demo user
- ~8 free-floating email threads (Communications)
- 6 LCS Projects across phases / countries / project types — each with:
    · Richtpreis (internal estimate), Budget (customer indication),
      Angebot (quoted total)
    · 1–2 LCS Offers with versioning
    · 1 LCS Opportunity Matrix (5-factor scoring)
    · 2–4 project-scoped Communications (linked via reference_doctype)
- 3 LCS WhatsApp Messages
- All seeded rows carry the marker `[lcs-seed]` in their content / body /
  notes so they're easy to find / clean up via `purge_all`.
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta
from typing import Any

import frappe
from frappe.utils import add_to_date, now_datetime

SEED_MARKER = "[lcs-seed]"


# ---------------------------------------------------------------- Guards


def _refuse_in_production() -> None:
    if not frappe.conf.get("developer_mode"):
        frappe.throw(
            "mock_mail.seed_all: refusing to run because developer_mode is not enabled. "
            "Set developer_mode=1 in site_config.json on dev sites only."
        )


# ----------------------------------------------------------- Test fixtures

DEMO_ORGS: list[dict[str, Any]] = [
    {
        "name": "ACME Anlagenbau GmbH",
        # Industries are mapped to values that ship with frappe/crm by
        # default — avoids the seed needing master-data prep.
        "industry": "Manufacturing",
        "website": "https://acme-anlagen.example.com",
        "country": "Germany",
    },
    {
        "name": "Bergblick Seilbahn AG",
        "industry": "Transportation",
        "website": "https://bergblick.example.ch",
        "country": "Switzerland",
    },
    {
        "name": "Construct Norge AS",
        "industry": "Real Estate",
        "website": "https://construct.example.no",
        "country": "Norway",
    },
]

DEMO_CONTACTS: list[dict[str, Any]] = [
    {
        "first_name": "Erika",
        "last_name": "Mustermann",
        "designation": "Head of Procurement",
        "email": "erika.mustermann@acme-anlagen.example.com",
        "phone_business": "+49 89 1234 5678",
        "phone_mobile": "+49 170 9988 776",
        "company": "ACME Anlagenbau GmbH",
    },
    {
        "first_name": "Hans",
        "last_name": "Brunner",
        "designation": "CTO",
        "email": "h.brunner@bergblick.example.ch",
        "phone_business": "+41 81 555 4422",
        "phone_mobile": "+41 79 333 11 22",
        "company": "Bergblick Seilbahn AG",
    },
    {
        "first_name": "Astrid",
        "last_name": "Lindqvist",
        "designation": "Project Engineer",
        "email": "astrid@construct.example.no",
        "phone_business": "+47 22 11 22 33",
        "phone_mobile": "+47 900 11 222",
        "company": "Construct Norge AS",
    },
]

DEMO_USERS: list[str] = [
    "vertrieb1@lcs-group.com",
    "vertrieb2@lcs-group.com",
    "salesmgr@lcs-group.com",
]

EMAIL_THREADS: list[dict[str, Any]] = [
    {
        "subject": "Anfrage Seilkran für Tunnelbau",
        "messages": [
            ("Received", "erika.mustermann@acme-anlagen.example.com", "Guten Tag, wir haben eine Ausschreibung für einen 60-t-Seilkran. Können Sie ein erstes Richtpreis-Angebot zusenden?"),
            ("Sent", None, "Sehr geehrte Frau Mustermann, vielen Dank für Ihre Anfrage. Wir bereiten ein Richtpreis-Angebot vor und melden uns innerhalb von 5 Werktagen."),
            ("Received", "erika.mustermann@acme-anlagen.example.com", "Vielen Dank, Termin notiert. Anbei das Lastenheft."),
        ],
    },
    {
        "subject": "Wartungsvertrag Bergblick — Verlängerung 2026",
        "messages": [
            ("Sent", None, "Hallo Hans, anbei der Vertragsentwurf für die Verlängerung 2026. Kannst du bitte über die Konditionen schauen?"),
            ("Received", "h.brunner@bergblick.example.ch", "Sieht passend aus. Ich gebe das ans Legal-Team weiter."),
        ],
    },
    {
        "subject": "Offer Q-2026-0042 — clarification",
        "messages": [
            ("Received", "astrid@construct.example.no", "Hi, two clarification questions on the latest quote — see attached PDF."),
            ("Sent", None, "Hi Astrid, replies inline below. Let me know if you need a call."),
            ("Received", "astrid@construct.example.no", "Thanks, that resolves it. We'll come back next week with the PO decision."),
        ],
    },
]

WHATSAPP_MESSAGES: list[dict[str, Any]] = [
    {
        "direction": "Outbound",
        "phone_number": "491709988776",
        "contact_email": "erika.mustermann@acme-anlagen.example.com",
        "body": "Hallo Frau Mustermann, kurze Erinnerung zum Angebot Q-2026-0017 — Rückmeldung bis Ende der Woche möglich? Viele Grüße",
        "status": "delivered",
    },
    {
        "direction": "Inbound",
        "phone_number": "491709988776",
        "contact_email": "erika.mustermann@acme-anlagen.example.com",
        "body": "Danke für die Erinnerung — Rückmeldung kommt heute Nachmittag.",
        "status": "received",
    },
    {
        "direction": "Inbound",
        "phone_number": "4179333112",
        "contact_email": "h.brunner@bergblick.example.ch",
        "body": "Servus, könnt ihr morgen zur Vor-Ort-Besichtigung anrücken?",
        "status": "received",
    },
]


# Each project carries: phase, country, project_type, GU flag, pricing
# stages (budget / richtpreis / angebot) in EUR, an opportunity-matrix
# scoring profile, an offer history, and 2–4 project-scoped emails.
DEMO_PROJECTS: list[dict[str, Any]] = [
    {
        "key": "tunnelbau-acme",
        "name": "Tunnelbau Seilkran 60t — ACME",
        "abbr": "TUN-ACME",
        "type": "SB",
        "country": "Germany",
        "is_gu": 1,
        "phase": "Offer",
        "status": "Active",
        "organization": "ACME Anlagenbau GmbH",
        "primary_contact_email": "erika.mustermann@acme-anlagen.example.com",
        "salesperson": "vertrieb1@lcs-group.com",
        "sales_manager": "salesmgr@lcs-group.com",
        "expected_close_offset_days": 45,
        "probability": 60,
        "budget_customer": 850_000,
        "richtpreis": 920_000,
        "angebot_total": 945_000,
        "matrix": {"technical": 80, "commercial": 65, "relationship": 70, "competition": 50, "strategic": 75},
        "offers": [
            {"title": "Richtpreis Angebot Tunnelbau 60t", "version": 1, "status": "Sent", "value": 920_000, "offset_days": 14},
            {"title": "Verbindliches Angebot Tunnelbau 60t", "version": 2, "status": "In Review", "value": 945_000, "offset_days": 3},
        ],
        "emails": [
            ("Received", "erika.mustermann@acme-anlagen.example.com", "Anfrage Richtpreis 60-t-Seilkran",
             "Guten Tag, anbei das Lastenheft für den Tunnelvortrieb. Bitte um Richtpreis-Angebot bis Monatsende."),
            ("Sent", None, "Re: Anfrage Richtpreis 60-t-Seilkran",
             "Sehr geehrte Frau Mustermann, gerne — wir senden das Richtpreis-Angebot bis Freitag."),
            ("Sent", None, "Richtpreis-Angebot Tunnelbau 60t",
             "Anbei das Richtpreis-Angebot über 920.000 EUR. Detaillierte Aufstellung im PDF."),
            ("Received", "erika.mustermann@acme-anlagen.example.com", "Re: Richtpreis-Angebot Tunnelbau 60t",
             "Danke. Können wir die Lieferzeit auf 14 Wochen verkürzen? Falls ja, wären wir an einer Verbindlichen interessiert."),
        ],
    },
    {
        "key": "bergblick-wartung",
        "name": "Bergblick Wartungsvertrag 2026",
        "abbr": "BBW-2026",
        "type": "WI",
        "country": "Switzerland",
        "is_gu": 0,
        "phase": "Negotiation",
        "status": "Active",
        "organization": "Bergblick Seilbahn AG",
        "primary_contact_email": "h.brunner@bergblick.example.ch",
        "salesperson": "vertrieb2@lcs-group.com",
        "sales_manager": "salesmgr@lcs-group.com",
        "expected_close_offset_days": 21,
        "probability": 80,
        "budget_customer": 180_000,
        "richtpreis": 195_000,
        "angebot_total": 188_500,
        "matrix": {"technical": 85, "commercial": 75, "relationship": 95, "competition": 30, "strategic": 60},
        "offers": [
            {"title": "Wartungsvertrag Bergblick 2026 — Verlängerung", "version": 1, "status": "In Review", "value": 188_500, "offset_days": 7},
        ],
        "emails": [
            ("Sent", None, "Wartungsvertrag 2026 — Entwurf",
             "Hallo Hans, anbei der Entwurf für den Wartungsvertrag 2026. Konditionen wie besprochen."),
            ("Received", "h.brunner@bergblick.example.ch", "Re: Wartungsvertrag 2026 — Entwurf",
             "Servus — sieht gut aus. Eine Frage zu §7.2: Reaktionszeit auf 4h statt 8h?"),
            ("Sent", None, "Re: Wartungsvertrag 2026 — Entwurf",
             "Hallo Hans, 4h Reaktionszeit kostet uns 8.500 EUR p.a. mehr. Anbei angepasstes Angebot."),
        ],
    },
    {
        "key": "construct-staudamm",
        "name": "Staudamm Norge — Materialseilbahn",
        "abbr": "STDM-NO",
        "type": "LL",
        "country": "Norway",
        "is_gu": 1,
        "phase": "Order",
        "status": "Active",
        "organization": "Construct Norge AS",
        "primary_contact_email": "astrid@construct.example.no",
        "salesperson": "vertrieb1@lcs-group.com",
        "sales_manager": "salesmgr@lcs-group.com",
        "expected_close_offset_days": -5,  # already won
        "probability": 100,
        "budget_customer": 2_400_000,
        "richtpreis": 2_550_000,
        "angebot_total": 2_485_000,
        "matrix": {"technical": 90, "commercial": 80, "relationship": 70, "competition": 60, "strategic": 90},
        "offers": [
            {"title": "Materialseilbahn Staudamm — Richtpreis", "version": 1, "status": "Sent", "value": 2_550_000, "offset_days": 60},
            {"title": "Materialseilbahn Staudamm — Verhandelt", "version": 2, "status": "Accepted", "value": 2_485_000, "offset_days": 10},
        ],
        "emails": [
            ("Received", "astrid@construct.example.no", "Tender STDM-2026-007 — Material ropeway",
             "Hi LCS team, please find the ITT for the dam construction ropeway. Submission by 30 April."),
            ("Sent", None, "Re: Tender STDM-2026-007",
             "Hi Astrid, confirmed — we'll submit by 30 April. Pre-bid clarification call next Tuesday?"),
            ("Sent", None, "Final offer — Material ropeway STDM-2026-007",
             "Final offer attached, EUR 2.485M. Includes commissioning + 12 months warranty."),
            ("Received", "astrid@construct.example.no", "PO STDM-2026-007 — letter of intent",
             "Congratulations — we award the contract. PO will follow this week."),
        ],
    },
    {
        "key": "acme-skischaukel",
        "name": "Ski-Schaukel Erweiterung Phase II",
        "abbr": "SSE-II",
        "type": "SK",
        "country": "Austria",
        "is_gu": 0,
        "phase": "Inquiry",
        "status": "Open",
        "organization": "ACME Anlagenbau GmbH",
        "primary_contact_email": "erika.mustermann@acme-anlagen.example.com",
        "salesperson": "vertrieb2@lcs-group.com",
        "sales_manager": "salesmgr@lcs-group.com",
        "expected_close_offset_days": 90,
        "probability": 25,
        "budget_customer": 0,
        "richtpreis": 0,
        "angebot_total": 0,
        "matrix": {"technical": 65, "commercial": 50, "relationship": 70, "competition": 70, "strategic": 55},
        "offers": [],
        "emails": [
            ("Received", "erika.mustermann@acme-anlagen.example.com", "Konzeptanfrage Ski-Schaukel Phase II",
             "Hallo, wir prüfen eine Erweiterung. Können Sie unverbindlich Konzeptvorschläge zusenden?"),
            ("Sent", None, "Re: Konzeptanfrage Ski-Schaukel Phase II",
             "Sehr geehrte Frau Mustermann, gerne — wir bereiten 2-3 Varianten vor. Lieferzeit 2 Wochen."),
        ],
    },
    {
        "key": "bergblick-revision",
        "name": "Bergblick Revision Hauptseil 2026",
        "abbr": "BBR-26",
        "type": "WI",
        "country": "Switzerland",
        "is_gu": 0,
        "phase": "Completed",
        "status": "Completed",
        "organization": "Bergblick Seilbahn AG",
        "primary_contact_email": "h.brunner@bergblick.example.ch",
        "salesperson": "vertrieb2@lcs-group.com",
        "sales_manager": "salesmgr@lcs-group.com",
        "expected_close_offset_days": -120,
        "probability": 100,
        "budget_customer": 95_000,
        "richtpreis": 102_000,
        "angebot_total": 99_800,
        "matrix": {"technical": 85, "commercial": 70, "relationship": 95, "competition": 20, "strategic": 50},
        "offers": [
            {"title": "Hauptseil-Revision 2026", "version": 1, "status": "Accepted", "value": 99_800, "offset_days": 150},
        ],
        "emails": [
            ("Received", "h.brunner@bergblick.example.ch", "Revision Hauptseil — Auftrag",
             "Servus, wir vergeben den Auftrag wie besprochen. Kick-off nächste Woche?"),
            ("Sent", None, "Re: Revision Hauptseil — Auftrag",
             "Vielen Dank. Kick-off Mo 9:00 vor Ort, Team steht bereit."),
            ("Sent", None, "Revision Hauptseil — Abnahmeprotokoll",
             "Anbei das unterschriebene Abnahmeprotokoll. Anlage ist wieder im Vollbetrieb."),
        ],
    },
    {
        "key": "construct-bergung",
        "name": "Norwegen Bergung — Lost Tender",
        "abbr": "NBT",
        "type": "Other",
        "country": "Norway",
        "is_gu": 1,
        "phase": "Lost",
        "status": "Cancelled",
        "organization": "Construct Norge AS",
        "primary_contact_email": "astrid@construct.example.no",
        "salesperson": "vertrieb1@lcs-group.com",
        "sales_manager": "salesmgr@lcs-group.com",
        "expected_close_offset_days": -40,
        "probability": 0,
        "budget_customer": 1_200_000,
        "richtpreis": 1_350_000,
        "angebot_total": 1_310_000,
        "matrix": {"technical": 75, "commercial": 50, "relationship": 60, "competition": 90, "strategic": 40},
        "offers": [
            {"title": "Bergungs-Kran Norwegen — Final", "version": 1, "status": "Rejected", "value": 1_310_000, "offset_days": 50},
        ],
        "emails": [
            ("Received", "astrid@construct.example.no", "Tender result — Bergung",
             "Hi LCS, thanks for the bid. Unfortunately we awarded the contract to a competitor (price-driven decision)."),
            ("Sent", None, "Re: Tender result — Bergung",
             "Hi Astrid, thanks for the heads up. Looking forward to the next opportunity."),
        ],
    },
]


# --------------------------------------------------------------- Builders


def _ensure_user(email: str) -> str:
    if frappe.db.exists("User", email):
        return email
    user = frappe.get_doc(
        {
            "doctype": "User",
            "email": email,
            "first_name": email.split("@")[0],
            "send_welcome_email": 0,
            "user_type": "System User",
        }
    )
    user.insert(ignore_permissions=True)
    return email


def _ensure_industry(name: str | None) -> str | None:
    """CRM Industry is a Link target — auto-create if missing so the seed
    works on a fresh bench without manual master-data prep."""
    if not name:
        return None
    if frappe.db.exists("CRM Industry", name):
        return name
    doc = frappe.get_doc({"doctype": "CRM Industry", "industry": name})
    doc.insert(ignore_permissions=True)
    return name


def _ensure_organization(spec: dict[str, Any]) -> str:
    name = spec["name"]
    if frappe.db.exists("CRM Organization", name):
        return name
    doc = frappe.get_doc(
        {
            "doctype": "CRM Organization",
            "organization_name": name,
            "industry": _ensure_industry(spec.get("industry")),
            "website": spec.get("website"),
            "country": spec.get("country"),
        }
    )
    doc.insert(ignore_permissions=True)
    return name


def _ensure_contact(spec: dict[str, Any]) -> str:
    """Find by primary email (the natural CRM key) and reuse if present."""
    existing = frappe.db.sql(
        """SELECT parent FROM `tabContact Email` WHERE email_id=%s LIMIT 1""",
        (spec["email"],),
        as_dict=True,
    )
    if existing:
        return existing[0]["parent"]

    contact = frappe.new_doc("Contact")
    contact.first_name = spec["first_name"]
    contact.last_name = spec["last_name"]
    contact.full_name = f"{spec['first_name']} {spec['last_name']}"
    contact.designation = spec.get("designation")
    contact.company_name = spec.get("company")

    contact.append("email_ids", {"email_id": spec["email"], "is_primary": 1})
    if spec.get("phone_business"):
        contact.append("phone_nos", {"phone": spec["phone_business"], "is_primary_phone": 1})
    if spec.get("phone_mobile"):
        contact.append("phone_nos", {"phone": spec["phone_mobile"], "is_primary_mobile_no": 1})

    contact.insert(ignore_permissions=True)
    return contact.name


def _ensure_mailbox_binding(user: str) -> str:
    name = frappe.db.get_value("Outlook Mailbox Binding", {"user": user}, "name")
    if name:
        return name
    doc = frappe.get_doc(
        {
            "doctype": "Outlook Mailbox Binding",
            "user": user,
            "graph_mailbox": user,  # mock: same UPN
            "is_active": 1,
            "delta_token": "mock-delta-token-mail-0001",
            "calendar_delta_token": "mock-delta-token-cal-0001",
            "last_sync": now_datetime(),
            "last_calendar_sync": now_datetime(),
        }
    )
    doc.insert(ignore_permissions=True)
    return doc.name


def _seed_email_thread(thread: dict[str, Any], demo_user: str, base_offset_days: int) -> int:
    """Insert one free-floating email thread (no project link)."""
    created = 0
    base_dt: datetime = add_to_date(now_datetime(), days=-base_offset_days)
    for index, (sent_or_received, sender, body) in enumerate(thread["messages"]):
        ts = base_dt + timedelta(hours=index * 6)
        marker = f"{SEED_MARKER}::{thread['subject']}::{index}"
        if frappe.db.exists("Communication", {"content": ["like", f"%{marker}%"]}):
            continue
        comm = frappe.get_doc(
            {
                "doctype": "Communication",
                "communication_medium": "Email",
                "communication_type": "Communication",
                "sent_or_received": sent_or_received,
                "sender": sender or demo_user,
                "recipients": demo_user if sent_or_received == "Received" else (sender or ""),
                "subject": thread["subject"],
                "content": f"<p>{body}</p><p style=\"color:#888\">{marker}</p>",
                "user": demo_user,
                "communication_date": ts,
                "creation": ts,
            }
        )
        comm.insert(ignore_permissions=True)
        created += 1
    return created


def _seed_whatsapp_messages() -> int:
    created = 0
    for spec in WHATSAPP_MESSAGES:
        marker = f"{SEED_MARKER}::wa::{spec['phone_number']}::{spec['direction']}::{spec['body'][:40]}"
        if frappe.db.exists("LCS WhatsApp Message", {"body": ["like", f"%{marker}%"]}):
            continue
        contact_name = None
        rows = frappe.db.sql(
            """SELECT parent FROM `tabContact Email` WHERE email_id=%s LIMIT 1""",
            (spec["contact_email"],),
            as_dict=True,
        )
        if rows:
            contact_name = rows[0]["parent"]
        doc = frappe.get_doc(
            {
                "doctype": "LCS WhatsApp Message",
                "direction": spec["direction"],
                "phone_number": spec["phone_number"],
                "contact": contact_name,
                "wa_message_id": f"wamid.MOCK_{random.randint(100000, 999999)}",
                "status": spec["status"],
                "received_at": now_datetime() if spec["direction"] == "Inbound" else None,
                "message_type": "text",
                "body": f"{spec['body']}\n\n{marker}",
            }
        )
        doc.insert(ignore_permissions=True)
        created += 1
    return created


# ----------------------------------------------------------- Project seed


def _contact_name_by_email(email: str) -> str | None:
    rows = frappe.db.sql(
        """SELECT parent FROM `tabContact Email` WHERE email_id=%s LIMIT 1""",
        (email,),
        as_dict=True,
    )
    return rows[0]["parent"] if rows else None


def _seed_one_project(spec: dict[str, Any]) -> tuple[str | None, bool]:
    """Insert one LCS Project. Returns (name, was_created)."""
    notes_marker = f"{SEED_MARKER}::project::{spec['key']}"
    existing = frappe.db.get_value("LCS Project", {"notes": ["like", f"%{notes_marker}%"]}, "name")
    if existing:
        return existing, False

    contact_name = _contact_name_by_email(spec["primary_contact_email"])
    expected_close = add_to_date(now_datetime(), days=spec["expected_close_offset_days"])

    proj = frappe.get_doc(
        {
            "doctype": "LCS Project",
            "project_name": spec["name"],
            "project_abbr": spec["abbr"],
            "project_type": spec["type"],
            "project_description": f"Demo project — {spec['name']}",
            "country": spec["country"],
            "is_gu": spec["is_gu"],
            "salesperson": spec["salesperson"],
            "sales_manager": spec["sales_manager"],
            "phase": spec["phase"],
            "status": spec["status"],
            "organization": spec["organization"],
            "primary_contact": contact_name,
            "source": None,
            "expected_close_date": expected_close,
            "probability": spec["probability"],
            "budget_customer": spec["budget_customer"],
            "richtpreis": spec["richtpreis"],
            "angebot_total": spec["angebot_total"],
            "estimated_value": spec["angebot_total"] or spec["richtpreis"] or spec["budget_customer"],
            "notes": f"<p>Demo project for the LCS sales surface.</p><p style=\"color:#888\">{notes_marker}</p>",
        }
    )
    proj.insert(ignore_permissions=True)
    return proj.name, True


def _seed_project_offers(project_name: str, spec: dict[str, Any]) -> int:
    created = 0
    for offer_spec in spec.get("offers") or []:
        offer_marker = f"{SEED_MARKER}::offer::{spec['key']}::v{offer_spec['version']}"
        if frappe.db.exists("LCS Offer", {"notes": ["like", f"%{offer_marker}%"]}):
            continue
        offer_date = add_to_date(now_datetime(), days=-offer_spec["offset_days"])
        valid_until = add_to_date(offer_date, days=30)
        offer = frappe.get_doc(
            {
                "doctype": "LCS Offer",
                "project": project_name,
                "offer_title": offer_spec["title"],
                "version": offer_spec["version"],
                "status": offer_spec["status"],
                "offer_date": offer_date,
                "valid_until": valid_until,
                "value": offer_spec["value"],
                "currency": "EUR",
                "probability": spec["probability"],
                "notes": f"<p>{offer_spec['title']} v{offer_spec['version']}</p><p style=\"color:#888\">{offer_marker}</p>",
            }
        )
        offer.insert(ignore_permissions=True)
        created += 1
    return created


def _seed_project_matrix(project_name: str, spec: dict[str, Any]) -> bool:
    matrix_marker = f"{SEED_MARKER}::matrix::{spec['key']}"
    # LCS Opportunity Matrix has no `notes` field — dedupe by project+marker
    # via project link is enough since one matrix per demo project is the
    # convention here.
    existing = frappe.db.exists("LCS Opportunity Matrix", {"project": project_name})
    if existing:
        return False

    m = spec["matrix"]
    doc = frappe.get_doc(
        {
            "doctype": "LCS Opportunity Matrix",
            "project": project_name,
            "organization": spec["organization"],
            "technical_fit": m["technical"],
            "commercial_fit": m["commercial"],
            "relationship_strength": m["relationship"],
            "competition_level": m["competition"],
            "strategic_importance": m["strategic"],
        }
    )
    # Trigger matrix calculation if a controller exists; otherwise the
    # Frappe doc.insert path will use whatever logic is configured.
    doc.insert(ignore_permissions=True)
    # Stash the marker in a comment so purge_all can find it (matrix has
    # no free-text fields).
    frappe.get_doc(
        {
            "doctype": "Comment",
            "comment_type": "Comment",
            "reference_doctype": "LCS Opportunity Matrix",
            "reference_name": doc.name,
            "content": matrix_marker,
        }
    ).insert(ignore_permissions=True)
    return True


def _seed_project_emails(project_name: str, spec: dict[str, Any], salesperson: str) -> int:
    """Insert project-scoped Communications, linked via reference_doctype."""
    created = 0
    base_offset = abs(spec["expected_close_offset_days"]) + 5
    base_dt: datetime = add_to_date(now_datetime(), days=-base_offset)

    for index, (sent_or_received, sender, subject, body) in enumerate(spec.get("emails") or []):
        marker = f"{SEED_MARKER}::pemail::{spec['key']}::{index}"
        if frappe.db.exists("Communication", {"content": ["like", f"%{marker}%"]}):
            continue
        ts = base_dt + timedelta(days=index, hours=random.randint(0, 8))
        comm = frappe.get_doc(
            {
                "doctype": "Communication",
                "communication_medium": "Email",
                "communication_type": "Communication",
                "sent_or_received": sent_or_received,
                "sender": sender or salesperson,
                "recipients": salesperson if sent_or_received == "Received" else (sender or ""),
                "subject": subject,
                "content": f"<p>{body}</p><p style=\"color:#888\">{marker}</p>",
                "user": salesperson,
                "reference_doctype": "LCS Project",
                "reference_name": project_name,
                "communication_date": ts,
                "creation": ts,
            }
        )
        comm.insert(ignore_permissions=True)
        created += 1
    return created


def _seed_projects() -> dict[str, int]:
    counts = {"projects": 0, "offers": 0, "matrices": 0, "project_emails": 0}
    for spec in DEMO_PROJECTS:
        proj_name, _was_new = _seed_one_project(spec)
        if not proj_name:
            continue
        counts["projects"] += 1
        counts["offers"] += _seed_project_offers(proj_name, spec)
        if _seed_project_matrix(proj_name, spec):
            counts["matrices"] += 1
        counts["project_emails"] += _seed_project_emails(proj_name, spec, spec["salesperson"])
    return counts


# ---------------------------------------------------------------- Driver


def seed_all() -> dict[str, int]:
    """Populate all mock surfaces. Returns counts per layer.

    Idempotent — safe to call repeatedly.
    """
    _refuse_in_production()

    counts: dict[str, int] = {
        "users": 0,
        "organizations": 0,
        "contacts": 0,
        "mailbox_bindings": 0,
        "communications": 0,
        "whatsapp_messages": 0,
        "projects": 0,
        "offers": 0,
        "matrices": 0,
        "project_emails": 0,
    }

    for email in DEMO_USERS:
        _ensure_user(email)
        counts["users"] += 1

    for org in DEMO_ORGS:
        _ensure_organization(org)
        counts["organizations"] += 1

    for c in DEMO_CONTACTS:
        _ensure_contact(c)
        counts["contacts"] += 1

    for email in DEMO_USERS:
        _ensure_mailbox_binding(email)
        counts["mailbox_bindings"] += 1

    for offset, thread in enumerate(EMAIL_THREADS):
        demo_user = DEMO_USERS[offset % len(DEMO_USERS)]
        counts["communications"] += _seed_email_thread(thread, demo_user, base_offset_days=offset * 3 + 1)

    counts["whatsapp_messages"] += _seed_whatsapp_messages()

    project_counts = _seed_projects()
    counts.update(project_counts)

    frappe.db.commit()
    return counts


def purge_all() -> dict[str, int]:
    """Delete every row that carries the seed marker.

    Mirrors `seed_all` — same scope, no surprise side-effects. Order
    matters: child rows (offers, matrices, project-emails) before
    projects, since LCS Offer + Communication carry hard FKs to the
    project.
    """
    _refuse_in_production()
    counts = {
        "communications": 0,
        "whatsapp_messages": 0,
        "offers": 0,
        "matrices": 0,
        "projects": 0,
    }

    # 1. project-scoped + free-floating emails
    comms = frappe.get_all(
        "Communication",
        filters={"content": ["like", f"%{SEED_MARKER}%"]},
        pluck="name",
    )
    for name in comms:
        frappe.delete_doc("Communication", name, ignore_permissions=True, force=True)
        counts["communications"] += 1

    # 2. WhatsApp messages
    waps = frappe.get_all(
        "LCS WhatsApp Message",
        filters={"body": ["like", f"%{SEED_MARKER}%"]},
        pluck="name",
    )
    for name in waps:
        frappe.delete_doc("LCS WhatsApp Message", name, ignore_permissions=True, force=True)
        counts["whatsapp_messages"] += 1

    # 3. Offers (notes carry the marker)
    offers = frappe.get_all(
        "LCS Offer",
        filters={"notes": ["like", f"%{SEED_MARKER}%"]},
        pluck="name",
    )
    for name in offers:
        frappe.delete_doc("LCS Offer", name, ignore_permissions=True, force=True)
        counts["offers"] += 1

    # 4. Opportunity matrices (marker stored in Comment)
    matrix_names = frappe.get_all(
        "Comment",
        filters={
            "reference_doctype": "LCS Opportunity Matrix",
            "content": ["like", f"%{SEED_MARKER}::matrix::%"],
        },
        pluck="reference_name",
    )
    for name in set(matrix_names):
        if frappe.db.exists("LCS Opportunity Matrix", name):
            frappe.delete_doc("LCS Opportunity Matrix", name, ignore_permissions=True, force=True)
            counts["matrices"] += 1

    # 5. Projects (notes carry the marker) — last, after everything that
    #    referenced them
    projects = frappe.get_all(
        "LCS Project",
        filters={"notes": ["like", f"%{SEED_MARKER}%"]},
        pluck="name",
    )
    for name in projects:
        frappe.delete_doc("LCS Project", name, ignore_permissions=True, force=True)
        counts["projects"] += 1

    frappe.db.commit()
    return counts
