"""
Link existing LCS Projects back to their originating CRM Deals.

The BSM back-fill created LCS Projects from construction-site records
that predate the CRM rollout — those projects have no deal linked.
This module tries to find the deal each project should have been
spawned from, using multiple signals.

Matching signals (highest wins):

1. Same organization + similar deal/project name (fuzzy)
2. Same organization + overlapping date range (deal close → project start)
3. Same organization (fallback — only linked if exactly one open deal)

Idempotent: projects that already have `deal` set are skipped.
Deals linked to a different project are never stolen.

Run:
  bench --site lcs.local execute lcs_integrations.cross_module.link_deals.run \
      --kwargs "{'dry_run': True}"
  bench --site lcs.local execute lcs_integrations.cross_module.link_deals.run
"""

import re
import difflib
import frappe


@frappe.whitelist()
def api_link(dry_run: bool = False, create_missing: bool = True) -> dict:
    """Whitelisted wrapper — Admin-triggered back-fill from the UI."""
    frappe.only_for(["System Manager", "Sales Manager"])
    if isinstance(dry_run, str):
        dry_run = dry_run.lower() in ("1", "true", "yes")
    if isinstance(create_missing, str):
        create_missing = create_missing.lower() in ("1", "true", "yes")
    return run(dry_run=dry_run, create_missing=create_missing)


@frappe.whitelist()
def api_backfill_leads(dry_run: bool = False) -> dict:
    """Create retrospective CRM Leads for every Deal that doesn't have one
    yet, back-linking deal.lead so the Lead → Deal → Project chain has
    records at every step."""
    frappe.only_for(["System Manager", "Sales Manager"])
    if isinstance(dry_run, str):
        dry_run = dry_run.lower() in ("1", "true", "yes")
    return backfill_leads(dry_run=dry_run)


def backfill_leads(dry_run: bool = False) -> dict:
    if not frappe.db.exists("DocType", "CRM Lead") or not frappe.db.exists("DocType", "CRM Deal"):
        return {"error": "CRM Lead or CRM Deal not installed"}

    deal_meta = frappe.get_meta("CRM Deal")
    available = {f.fieldname for f in deal_meta.fields}
    has_lead_field = "lead" in available

    # Build the field list dynamically so we don't request columns that don't
    # exist in this Frappe/CRM version (e.g. deal_name is absent in some schemas).
    wanted = ["name", "organization", "status"]
    if "deal_name" in available:
        wanted.append("deal_name")

    deals = frappe.get_all(
        "CRM Deal",
        filters={"organization": ["is", "set"]},
        fields=wanted,
    )

    summary = {
        "deals_checked": len(deals),
        "leads_created": 0,
        "already_had_lead": 0,
        "reused_existing_lead": 0,
        "dry_run": bool(dry_run),
        "changes": [],
    }

    for d in deals:
        # Skip deals that already have a lead linked
        if has_lead_field:
            existing_link = frappe.db.get_value("CRM Deal", d["name"], "lead")
            if existing_link:
                summary["already_had_lead"] += 1
                continue

        # Is there already a Lead for this organization we can reuse?
        existing_lead = frappe.db.get_value(
            "CRM Lead",
            {"organization": d["organization"]},
            "name",
        )

        if existing_lead:
            action = "reused"
            lead_name = existing_lead
            summary["reused_existing_lead"] += 1
        else:
            action = "would-create" if dry_run else "created"
            lead_name = None
            if not dry_run:
                lead_name = _create_retro_lead(d)
                if lead_name:
                    summary["leads_created"] += 1

        summary["changes"].append({
            "deal": d["name"],
            "deal_name": d.get("deal_name") or d["name"],
            "organization": d["organization"],
            "lead": lead_name,
            "action": action,
        })

        # Back-link the lead onto the deal so the pipeline shows Lead → Deal
        if lead_name and has_lead_field and not dry_run:
            frappe.db.set_value("CRM Deal", d["name"], "lead", lead_name, update_modified=False)

    if not dry_run:
        frappe.db.commit()

    prefix = "[DRY-RUN] " if dry_run else ""
    print(f"\n{prefix}=== Lead back-fill summary ===")
    print(f"  Deals checked:         {summary['deals_checked']}")
    print(f"  Leads created:         {summary['leads_created']}")
    print(f"  Reused existing lead:  {summary['reused_existing_lead']}")
    print(f"  Already had lead:      {summary['already_had_lead']}")
    for c in summary["changes"][:40]:
        a = c["action"]
        marker = {"created": "+", "would-create": "?", "reused": "="}.get(a, "?")
        lname = (c.get("lead") or "(none)")[:30]
        dname = (c.get("deal_name") or c["deal"])[:32]
        print(f"  [{marker}] {dname:<34}  ← {lname}")
    return summary


def _create_retro_lead(deal: dict) -> str | None:
    """Create a minimal CRM Lead for the given deal's organization."""
    try:
        lead = frappe.new_doc("CRM Lead")
        meta = frappe.get_meta("CRM Lead")
        fields = {f.fieldname for f in meta.fields}

        org_name = deal["organization"]
        lead_name_text = deal.get("deal_name") or org_name

        if "lead_name" in fields:
            lead.lead_name = lead_name_text
        if "first_name" in fields:
            # frappe/crm requires first_name — fall back to org name
            lead.first_name = (org_name or "Unknown").split(" ")[0]
        if "organization" in fields:
            lead.organization = org_name
        if "no_of_employees" in fields:
            # Some CRM installs require this — give a harmless default
            lead.no_of_employees = "1-10"

        # Seed a Retro-Import source if the app supports it
        retro_source = "Retro-Import"
        if frappe.db.exists("DocType", "CRM Lead Source"):
            if not frappe.db.exists("CRM Lead Source", retro_source):
                try:
                    src = frappe.new_doc("CRM Lead Source")
                    src.source_name = retro_source
                    src.insert(ignore_permissions=True, ignore_if_duplicate=True)
                except Exception:
                    pass
            if "source" in fields and frappe.db.exists("CRM Lead Source", retro_source):
                lead.source = retro_source

        lead.insert(ignore_permissions=True)
        return lead.name
    except Exception as e:
        frappe.log_error(
            f"Could not create retro lead for deal {deal['name']}: {e}",
            "link_deals.retro_lead",
        )
        return None


def run(dry_run: bool = False, create_missing: bool = True) -> dict:
    if not frappe.db.exists("DocType", "CRM Deal"):
        return {"error": "CRM Deal not installed"}

    # frappe/crm uses a default communication_status="Open" but doesn't
    # seed the row — every retro deal insert fails silently without it.
    # Ensure it exists before we run.
    if create_missing:
        _ensure_communication_status("Open")

    projects = frappe.get_all(
        "LCS Project",
        filters={"deal": ["is", "not set"], "organization": ["is", "set"]},
        fields=["name", "project_name", "organization", "country",
                "expected_close_date", "modified"],
    )

    deal_cache = _build_deal_cache()

    summary = {
        "projects_checked": len(projects),
        "linked": 0,
        "created": 0,
        "no_match": 0,
        "skipped_ambiguous": 0,
        "dry_run": bool(dry_run),
        "changes": [],
    }

    for p in projects:
        deals = deal_cache.get(p.organization, [])
        # Skip deals that are already linked to some other LCS Project
        deals = [d for d in deals if d["name"] not in _already_linked_deals()]

        if not deals:
            if create_missing:
                # Every LCS Project was a Deal at some point — create the
                # missing commercial record so reports + forecasting have
                # a consistent shape.
                action = "would-create" if dry_run else "created"
                summary["changes"].append({
                    "project": p.name, "project_name": p.project_name,
                    "organization": p.organization, "action": action,
                })
                if not dry_run:
                    deal_name = _create_retro_deal(p)
                    if deal_name:
                        frappe.db.set_value("LCS Project", p.name, "deal", deal_name)
                        summary["created"] += 1
                        summary["changes"][-1]["deal"] = deal_name
            else:
                summary["no_match"] += 1
                summary["changes"].append({
                    "project": p.name, "project_name": p.project_name,
                    "organization": p.organization, "action": "no-candidates",
                })
            continue

        # Score each deal for this project
        scored = [(d, _score(p, d)) for d in deals]
        scored.sort(key=lambda x: x[1], reverse=True)
        best_deal, best_score = scored[0]

        # Clear winner: score ≥ 0.4, and ≥ 0.15 ahead of runner-up
        second_score = scored[1][1] if len(scored) > 1 else 0
        clear = best_score >= 0.4 and (best_score - second_score) >= 0.15

        # Fallback: if the organization has exactly one open deal, trust it
        if not clear and len(deals) == 1 and best_score > 0:
            clear = True

        if not clear:
            summary["skipped_ambiguous"] += 1
            summary["changes"].append({
                "project": p.name, "project_name": p.project_name,
                "organization": p.organization, "action": "ambiguous",
                "top": best_deal["name"], "score": round(best_score, 2),
                "candidates": len(deals),
            })
            continue

        summary["changes"].append({
            "project": p.name, "project_name": p.project_name,
            "organization": p.organization, "action": "would-link" if dry_run else "linked",
            "deal": best_deal["name"], "deal_name": best_deal.get("deal_name") or best_deal["name"],
            "score": round(best_score, 2),
        })
        if not dry_run:
            frappe.db.set_value("LCS Project", p.name, "deal", best_deal["name"])
            summary["linked"] += 1

    if not dry_run:
        frappe.db.commit()

    _print_summary(summary)
    return summary


# -- scoring --

def _score(project: dict, deal: dict) -> float:
    """Return a [0..1] confidence that this project came from this deal."""
    score = 0.0

    # Name similarity (fuzzy — deal names often contain the product info)
    proj_name = _clean(project.get("project_name") or "")
    deal_name = _clean(deal.get("deal_name") or deal.get("name") or "")
    if proj_name and deal_name:
        ratio = difflib.SequenceMatcher(None, proj_name, deal_name).ratio()
        score += 0.5 * ratio

    # Country alignment
    if project.get("country") and deal.get("country") and \
            project["country"] == deal["country"]:
        score += 0.2

    # Expected-close proximity — if the project has an expected close
    # that's within 180 days of the deal's close, that's a strong signal
    p_close = project.get("expected_close_date")
    d_close = deal.get("close_date")
    if p_close and d_close:
        try:
            from datetime import date
            if isinstance(p_close, str):
                p_close = date.fromisoformat(p_close)
            if isinstance(d_close, str):
                d_close = date.fromisoformat(d_close)
            delta = abs((p_close - d_close).days)
            if delta <= 30:
                score += 0.3
            elif delta <= 180:
                score += 0.15
        except (ValueError, TypeError):
            pass

    return min(score, 1.0)


def _ensure_communication_status(name: str) -> None:
    """Make sure the CRM Communication Status row exists — CRM Deal's
    default `communication_status` field points to it."""
    if not frappe.db.exists("DocType", "CRM Communication Status"):
        return
    if frappe.db.exists("CRM Communication Status", name):
        return
    try:
        doc = frappe.new_doc("CRM Communication Status")
        # Field name varies; try the common candidates
        for fn in ("status", "name", "communication_status"):
            if hasattr(doc, fn):
                setattr(doc, fn, name)
        doc.insert(ignore_permissions=True, ignore_if_duplicate=True)
        frappe.db.commit()
    except Exception as e:
        frappe.log_error(
            f"Could not seed Communication Status '{name}': {e}",
            "link_deals.seed",
        )


def _create_retro_deal(project: dict) -> str | None:
    """Create a CRM Deal for an LCS Project that predates the CRM.

    Populates the bare minimum so the deal is valid — the user can flesh
    it out later. Status is NOT set explicitly because frappe/crm deals
    have a `communication_status` default that fights user-set values;
    letting Frappe pick the default is the cleanest path.
    """
    try:
        # Look up an existing 'Won' CRM Deal Status if available, otherwise
        # leave status unset — Frappe will use the DocType default.
        won_status = frappe.db.get_value("CRM Deal Status", "Won", "name") \
            if frappe.db.exists("DocType", "CRM Deal Status") else None

        doc = frappe.new_doc("CRM Deal")
        meta = frappe.get_meta("CRM Deal")
        fields = {f.fieldname for f in meta.fields}

        if "organization" in fields:
            doc.organization = project["organization"]
        if "deal_name" in fields:
            doc.deal_name = project.get("project_name") or project["name"]
        # Only set status if we found a valid record
        if won_status and "status" in fields:
            doc.status = won_status
        if "probability" in fields:
            doc.probability = 100
        if "close_date" in fields and project.get("expected_close_date"):
            doc.close_date = project["expected_close_date"]
        # Most frappe/crm installs require communication_status; use Frappe default
        doc.insert(ignore_permissions=True)
        return doc.name
    except Exception as e:
        frappe.log_error(
            f"Could not create retro deal for project {project['name']}: {e}",
            "link_deals",
        )
        return None


def _clean(s: str) -> str:
    """Strip prefixes like 'SB-', 'AS_', punctuation — so 'SB-SADDN' and
    'Saddn Cable Crane' compare meaningfully."""
    s = s.lower()
    s = re.sub(r"^(sb|wi|ll|sk|as)[-_]", "", s)
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return s.strip()


# -- caches --

_DEAL_CACHE = None
_LINKED_DEALS = None


def _build_deal_cache():
    """Group every CRM Deal by organization for O(1) lookup per project."""
    global _DEAL_CACHE
    if _DEAL_CACHE is not None:
        return _DEAL_CACHE

    # Fields vary between Frappe CRM versions — pick what's available
    meta = frappe.get_meta("CRM Deal")
    fieldnames = [f.fieldname for f in meta.fields]
    wanted = ["name", "organization", "deal_name", "status", "close_date"]
    available = [f for f in wanted if f == "name" or f in fieldnames]

    all_deals = frappe.get_all(
        "CRM Deal",
        filters={"organization": ["is", "set"]},
        fields=available,
        limit=0,
    )
    cache = {}
    for d in all_deals:
        cache.setdefault(d.organization, []).append(d)
    _DEAL_CACHE = cache
    return cache


def _already_linked_deals():
    global _LINKED_DEALS
    if _LINKED_DEALS is not None:
        return _LINKED_DEALS
    rows = frappe.get_all(
        "LCS Project",
        filters={"deal": ["is", "set"]},
        fields=["deal"],
        pluck="deal",
    )
    _LINKED_DEALS = set(rows)
    return _LINKED_DEALS


def _print_summary(summary: dict) -> None:
    prefix = "[DRY-RUN] " if summary["dry_run"] else ""
    print(f"\n{prefix}=== Deal linking summary ===")
    print(f"  Projects checked:   {summary['projects_checked']}")
    print(f"  Linked to existing: {summary['linked']}")
    print(f"  Retro deals created:{summary.get('created', 0)}")
    print(f"  No candidates:      {summary['no_match']}")
    print(f"  Ambiguous (manual): {summary['skipped_ambiguous']}")
    print()
    for c in summary["changes"][:30]:
        action = c.get("action", "?")
        pname = (c.get("project_name") or "?")[:32]
        org = (c.get("organization") or "-")[:25]
        if action in ("linked", "would-link"):
            print(f"  [+] {pname:<34} ← {c.get('deal_name') or c.get('deal'):<20}  (score {c.get('score', 0):.2f})")
        elif action in ("created", "would-create"):
            marker = "+" if action == "created" else "?"
            print(f"  [{marker}] {pname:<34} + new Deal {(c.get('deal') or '(dry-run)'):<22}")
        elif action == "ambiguous":
            print(f"  [?] {pname:<34} {org:<25}  ({c.get('candidates', 0)} candidates, top {c.get('score', 0):.2f})")
        else:
            print(f"  [-] {pname:<34} {org:<25}  no candidates")
