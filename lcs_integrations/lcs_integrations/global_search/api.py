"""Ctrl/Cmd+K global search across the CRM's core doctypes.

One round trip returns grouped hits; permissions apply per doctype via
frappe.get_list. Each config entry declares which fields are searched
and what the SPA shows as label / sub-line.
"""

from __future__ import annotations

import frappe

# doctype -> (search fields, label field, sub-line fields)
SEARCH_CONFIG = [
    {
        "doctype": "CRM Lead",
        "search": ["lead_name", "first_name", "last_name", "organization", "email"],
        "label": "lead_name",
        "sub": ["organization", "status"],
    },
    {
        "doctype": "CRM Deal",
        "search": ["organization", "deal_name", "email"],
        "label": "organization",
        "sub": ["status", "deal_owner"],
    },
    {
        "doctype": "Contact",
        "search": ["full_name", "email_id", "company_name", "mobile_no"],
        "label": "full_name",
        "sub": ["company_name", "email_id"],
    },
    {
        "doctype": "CRM Organization",
        "search": ["organization_name", "website"],
        "label": "organization_name",
        "sub": ["website"],
    },
    {
        "doctype": "LCS Project",
        "search": ["project_name", "project_number", "organization", "country"],
        "label": "project_name",
        "sub": ["project_number", "phase"],
    },
]


@frappe.whitelist()
def global_search(txt: str, limit: int = 5):
    """Grouped substring search; returns [{doctype, results: [...]}, ...]."""
    txt = (txt or "").strip()
    if len(txt) < 2:
        return []
    limit = max(1, min(int(limit or 5), 10))
    like = f"%{txt}%"

    groups = []
    for cfg in SEARCH_CONFIG:
        dt = cfg["doctype"]
        if not frappe.db.exists("DocType", dt) or not frappe.has_permission(dt, "read"):
            continue
        meta = frappe.get_meta(dt)
        search_fields = [f for f in cfg["search"] if meta.get_field(f)]
        if not search_fields:
            continue
        fields = ["name"] + [
            f for f in {cfg["label"], *cfg["sub"]} if meta.get_field(f)
        ]
        try:
            rows = frappe.get_list(
                dt,
                or_filters=[[dt, f, "like", like] for f in search_fields],
                fields=fields,
                limit_page_length=limit,
                order_by="modified desc",
            )
        except Exception:
            continue
        if not rows:
            continue
        results = []
        for r in rows:
            sub = " · ".join(str(r.get(f)) for f in cfg["sub"] if r.get(f))
            results.append({
                "name": r["name"],
                "label": r.get(cfg["label"]) or r["name"],
                "sub": sub,
            })
        groups.append({"doctype": dt, "results": results})
    return groups
