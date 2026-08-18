"""Salesbot → LCS Chance ingestion.

Pulls scored tenders from the Hermes Salesbot Postgres (read-only) and upserts
them into the LCS Chance doctype (source = "Pilot-Scout"), so scouted tenders
land in the sales opportunity funnel. Idempotent: matched by external_id =
"<source>:<tender external_id>". Scout-owned fields are refreshed on every run;
sales-owned fields (status, responsible, sales_note, crm_lead, title) are set on
first insert only and never overwritten.

Connection config lives in the site's site_config.json (NOT in code — it holds a
password). Add one of:

    "salesbot_db": {
        "host": "lcs-salesbot.westeurope.cloudapp.azure.com",
        "port": 5432,
        "dbname": "salesbot",
        "user": "salesbot_ro",
        "password": "…",
        "sslmode": "require"
    }

or a full DSN string in "salesbot_db_dsn". Optional tuning:
    "salesbot_sync_relevance": ["high", "medium"]   (default)
    "salesbot_sync_days": 0    (0 = no age limit; else only tenders created in
                                the last N days)
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import getdate, today, add_days

# Salesbot relevance enum (lowercase) → LCS Chance "Relevance" select options.
_RELEVANCE_MAP = {"high": "hoch", "medium": "mittel", "low": "niedrig"}
_DEFAULT_RELEVANCE = ["high", "medium"]

# Scout-owned fields: refreshed on every sync (the salesbot is the source of
# truth for these). Sales-owned fields are handled separately on insert only.
_SCOUT_FIELDS = (
    "source_detail", "client", "company", "country", "cpv_codes",
    "order_value", "published_on", "deadline", "source_url",
    "score", "relevance", "category", "reasoning", "summary_de",
    "description_original", "latitude", "longitude", "geo_confidence",
    "last_synced",
)


def _conn_params():
    """Read the salesbot Postgres connection from site_config. Returns kwargs for
    psycopg2.connect, or a {'dsn': …} dict, or None when unconfigured."""
    dsn = frappe.conf.get("salesbot_db_dsn")
    if dsn:
        return {"dsn": dsn}
    cfg = frappe.conf.get("salesbot_db")
    if not cfg or not cfg.get("host"):
        return None
    return {
        "host": cfg.get("host"),
        "port": cfg.get("port", 5432),
        "dbname": cfg.get("dbname", "salesbot"),
        "user": cfg.get("user"),
        "password": cfg.get("password"),
        "sslmode": cfg.get("sslmode", "require"),
        "connect_timeout": cfg.get("connect_timeout", 10),
    }


def _as_list(v):
    """JSON columns come back parsed by psycopg2, but tolerate a raw string too."""
    if isinstance(v, (list, tuple)):
        return list(v)
    if isinstance(v, str) and v.strip():
        import json
        try:
            parsed = json.loads(v)
            return parsed if isinstance(parsed, list) else [str(parsed)]
        except ValueError:
            return [v]
    return []


def _fetch_tenders(rels, since):
    """Read scored tenders from the salesbot Postgres (read-only)."""
    import psycopg2
    import psycopg2.extras

    params = _conn_params()
    if params is None:
        frappe.throw(_(
            "Salesbot database is not configured. Add 'salesbot_db' to the "
            "site's site_config.json."
        ))

    sql = """
        SELECT t.id, t.source, t.external_id, t.title, t.description, t.country,
               t.buyer, t.url, t.cpv_codes, t.value_eur, t.published_at,
               t.deadline_at, t.latitude, t.longitude, t.geo_source,
               s.relevance, s.score, s.reasoning, s.summary_de, s.title_de,
               s.detected_categories
          FROM tenders t
          JOIN scores s ON s.tender_id = t.id
         WHERE lower(s.relevance) = ANY(%(rels)s)
           AND (%(since)s IS NULL OR t.created_at >= %(since)s)
         ORDER BY t.created_at DESC
         LIMIT 2000
    """
    conn = psycopg2.connect(**params)
    try:
        conn.set_session(readonly=True, autocommit=True)
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, {"rels": [r.lower() for r in rels], "since": since})
            return cur.fetchall()
    finally:
        conn.close()


def _scout_values(t):
    """Map one salesbot tender row to the LCS Chance scout-owned field values."""
    cpv = ", ".join(str(c) for c in _as_list(t.get("cpv_codes")))[:140]
    cats = ", ".join(str(c) for c in _as_list(t.get("detected_categories")))[:140]
    rel = (t.get("relevance") or "").lower()
    score = t.get("score")
    buyer = (t.get("buyer") or "")[:140]
    return {
        "source_detail": (t.get("source") or "")[:140],
        "client": buyer,
        "company": buyer,
        "country": (t.get("country") or "")[:140],
        "cpv_codes": cpv,
        "order_value": float(t.get("value_eur") or 0),
        "published_on": getdate(t["published_at"]) if t.get("published_at") else None,
        "deadline": getdate(t["deadline_at"]) if t.get("deadline_at") else None,
        "source_url": (t.get("url") or "")[:500],
        "score": int(round(score)) if score is not None else 0,
        "relevance": _RELEVANCE_MAP.get(rel, ""),
        "category": cats,
        "reasoning": t.get("reasoning") or "",
        "summary_de": t.get("summary_de") or "",
        "description_original": t.get("description") or "",
        "latitude": t.get("latitude"),
        "longitude": t.get("longitude"),
        "geo_confidence": t.get("geo_source") or "",
        "last_synced": today(),
    }


@frappe.whitelist()
def sync_salesbot_tenders():
    """Pull scored tenders from the salesbot and upsert them as LCS Chances.

    Returns a summary {created, updated, total}. Manual trigger + daily job."""
    rels = frappe.conf.get("salesbot_sync_relevance") or _DEFAULT_RELEVANCE
    days = int(frappe.conf.get("salesbot_sync_days") or 0)
    since = add_days(today(), -days) if days > 0 else None

    rows = _fetch_tenders(rels, since)

    # Seed the CH-### counter once (avoid an O(n) scan per insert).
    top = 99
    for no in frappe.get_all("LCS Chance", pluck="chance_no"):
        if no and no.startswith("CH-"):
            try:
                top = max(top, int(no[3:]))
            except (ValueError, TypeError):
                pass

    created = updated = 0
    for t in rows:
        key = f"{t.get('source') or ''}:{t.get('external_id') or t.get('id')}"
        vals = _scout_values(t)
        name = frappe.db.get_value("LCS Chance", {"external_id": key}, "name")
        if name:
            frappe.db.set_value("LCS Chance", name, vals, update_modified=True)
            updated += 1
        else:
            top += 1
            doc = frappe.new_doc("LCS Chance")
            doc.chance_no = f"CH-{top}"
            doc.external_id = key
            doc.source = "Pilot-Scout"
            doc.status = "Neu"
            doc.title = (t.get("title_de") or t.get("title") or key)[:140]
            for f, v in vals.items():
                doc.set(f, v)
            doc.insert(ignore_permissions=True)
            created += 1

    frappe.db.commit()
    return {"created": created, "updated": updated, "total": len(rows)}


def scheduled_sync():
    """Daily scheduler entry point — never raises (logs instead)."""
    if _conn_params() is None:
        return  # not configured on this site; stay quiet
    try:
        result = sync_salesbot_tenders()
        frappe.logger("salesbot").info(f"salesbot sync: {result}")
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Salesbot tender sync failed")
