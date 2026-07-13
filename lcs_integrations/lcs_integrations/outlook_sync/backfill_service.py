"""Historical mail backfill.

The delta driver (`delta_service`) only walks the Inbox delta forward from a
stored token, so it never sees mail that predates the token or lives in other
folders. This module pages through the ENTIRE mailbox (all folders) once, on
demand, and imports every message whose sender resolves to a known CRM
contact/company — reusing the delta path's persist logic so filtering, dedup
(by Graph message id) and org auto-linking behave identically.

It deliberately does NOT touch `delta_token`: the forward delta stream keeps
running untouched; backfill only fills the gap behind it.
"""

from __future__ import annotations

import frappe

from .delta_service import _persist_message
from .graph_client import GraphClient, GraphClientError


def backfill_one(binding_name: str, *, since: str | None = None, max_messages: int = 2000) -> dict:
    """Import historical mail for one binding. `since` is an optional date/
    datetime lower bound (e.g. '2024-01-01'); None means as far back as the
    mailbox allows, capped at `max_messages`. Returns {seen, created}."""
    binding = frappe.get_doc("Outlook Mailbox Binding", binding_name)
    only_known = bool(binding.get("import_only_known_domains"))

    since_iso = None
    if since:
        since_iso = frappe.utils.get_datetime(since).strftime("%Y-%m-%dT%H:%M:%SZ")

    client = GraphClient()
    seen = created = 0
    page_url: str | None = None
    try:
        while True:
            page = client.messages_list(binding.graph_mailbox, since_iso=since_iso, page_url=page_url)
            for message in page.get("value", []):
                seen += 1
                frappe.db.savepoint("bf_msg")
                try:
                    if _persist_message(binding.user, message, only_known=only_known):
                        created += 1
                except Exception:  # noqa: BLE001 — one bad message must not abort the run
                    frappe.db.rollback(save_point="bf_msg")
                    frappe.log_error(title="outlook backfill skipped a message")
            page_url = page.get("@odata.nextLink")
            if not page_url or seen >= max_messages:
                break
    finally:
        client.close()

    frappe.db.commit()
    return {"seen": seen, "created": created}


@frappe.whitelist()
def backfill_mailbox(user: str | None = None, binding: str | None = None,
                     since: str | None = None, max_messages: int = 2000) -> dict:
    """UI/bench entry point. Restricted to managers. Resolve by binding name or
    by the salesperson's user id."""
    frappe.only_for(["System Manager", "Sales Manager"])
    if not binding:
        rows = frappe.get_all("Outlook Mailbox Binding", filters={"user": user}, limit=1)
        if not rows:
            frappe.throw(f"No mailbox binding for {user}")
        binding = rows[0].name
    return backfill_one(binding, since=since, max_messages=int(max_messages))


@frappe.whitelist()
def enqueue_backfill(user: str | None = None, binding: str | None = None,
                     since: str | None = None) -> dict:
    """Queue a historical backfill in the background — large mailboxes take
    minutes, so this must not run inside the web request. Managers only."""
    frappe.only_for(["System Manager", "Sales Manager"])
    if not binding:
        rows = frappe.get_all("Outlook Mailbox Binding", filters={"user": user}, limit=1)
        if not rows:
            frappe.throw(f"No mailbox binding for {user}")
        binding = rows[0].name
    frappe.enqueue(
        "lcs_integrations.outlook_sync.backfill_service.backfill_one",
        queue="long",
        timeout=3600,
        binding_name=binding,
        since=since or None,
        max_messages=100000,
    )
    return {"started": True, "binding": binding}


def backfill_all_active_full() -> dict:
    """One-shot full history backfill for every active binding — bench-executable,
    no kwargs. Effectively uncapped: paging stops when the mailbox is exhausted."""
    return backfill_all_active(since=None, max_messages=100000)


def backfill_all_active(since: str | None = None, max_messages: int = 2000) -> dict:
    """Backfill every active binding (bench-executable, no kwargs needed)."""
    import traceback

    results = {}
    for b in frappe.get_all("Outlook Mailbox Binding", filters={"is_active": 1}, fields=["name", "user"]):
        try:
            results[b.user] = backfill_one(b.name, since=since, max_messages=max_messages)
        except Exception as exc:  # noqa: BLE001 — surface the real error, don't let bench mask it
            results[b.user] = {"error": repr(exc), "tb": traceback.format_exc()}
    print(results)
    return results
