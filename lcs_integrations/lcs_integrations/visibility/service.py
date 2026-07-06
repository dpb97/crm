"""
Visibility service — resolves a user's LCS Access Profile and enforces it
at two layers:

1. permission_query_conditions hook (row-level) — filters LCS Project rows
   the user is allowed to see in lists, reports, list APIs.
2. has_permission hook (document-level) — decides whether a single
   document is readable by the current user.
3. get_user_preferences whitelisted method — the frontend queries this
   on boot to decide which panels/tabs to render for the current user.

System Managers bypass everything.
"""

import frappe
from frappe.utils import cint


def _profile_for(user: str) -> dict | None:
    """Returns the effective access profile for a user, or None.

    Lookup order:
      1. LCS User Preferences.access_profile (per-user override)
      2. None — user has no profile, unrestricted at this layer
    """
    if not user or user == "Administrator":
        return None
    if "System Manager" in frappe.get_roles(user):
        return None

    cache_key = f"lcs_profile:{user}"
    cached = frappe.cache().hget("lcs_access_profile_cache", user)
    if cached is not None:
        return cached if cached else None

    profile_name = frappe.db.get_value("LCS User Preferences", user, "access_profile")
    if not profile_name or not frappe.db.exists("LCS Access Profile", profile_name):
        frappe.cache().hset("lcs_access_profile_cache", user, {})
        return None

    profile = frappe.get_doc("LCS Access Profile", profile_name)
    if not profile.is_active:
        frappe.cache().hset("lcs_access_profile_cache", user, {})
        return None

    payload = {
        "profile_name": profile.profile_name,
        "countries": [c.country for c in (profile.scope_countries or [])],
        "project_types": [t.project_type for t in (profile.scope_project_types or [])],
        "own_only": bool(profile.scope_own_only),
        "team_members": [t.user for t in (profile.scope_team_members or [])],
        "hide_pricing": bool(profile.hide_pricing),
        "hide_team": bool(profile.hide_team),
        "hide_fusion": bool(profile.hide_fusion),
        "hide_bsm": bool(profile.hide_bsm),
        "hide_forecasting": bool(profile.hide_forecasting),
        "hide_opportunity_matrix": bool(profile.hide_opportunity_matrix),
        "can_export": bool(profile.can_export),
        "can_create_projects": bool(profile.can_create_projects),
        "can_delete_projects": bool(profile.can_delete_projects),
        "can_accept_offers": bool(profile.can_accept_offers),
        "can_edit_phase": bool(profile.can_edit_phase),
    }
    frappe.cache().hset("lcs_access_profile_cache", user, payload)
    return payload


def get_permission_query_conditions(user: str = None) -> str:
    """Frappe hook — returns SQL conditions appended to list queries for LCS Project.

    The string is concatenated with existing WHERE clauses via AND.
    """
    user = user or frappe.session.user
    profile = _profile_for(user)
    if not profile:
        return ""

    clauses: list[str] = []

    # Country restriction
    if profile["countries"]:
        quoted = ", ".join([f"'{frappe.db.escape(c)[1:-1]}'" for c in profile["countries"]])
        clauses.append(f"`tabLCS Project`.country IN ({quoted})")

    # Project type restriction
    if profile["project_types"]:
        quoted = ", ".join([f"'{frappe.db.escape(t)[1:-1]}'" for t in profile["project_types"]])
        clauses.append(f"`tabLCS Project`.project_type IN ({quoted})")

    # Own / team restriction
    if profile["own_only"]:
        allowed_users = [user] + (profile["team_members"] or [])
        quoted = ", ".join([f"'{frappe.db.escape(u)[1:-1]}'" for u in allowed_users])
        clauses.append(f"`tabLCS Project`.salesperson IN ({quoted})")

    return " AND ".join(clauses)


def has_permission(doc, ptype: str = None, user: str = None) -> bool:
    """Document-level permission check for LCS Project.

    Covers every CRUD ptype Frappe can pass: read, write, create, delete,
    submit, amend, cancel, print, email, export, share. Defaults to
    allowing unknown ptypes so future Frappe additions don't break
    existing access — the base role check still applies on top.
    """
    user = user or frappe.session.user
    profile = _profile_for(user)
    if not profile:
        return True

    # Row-scope first — if the project is outside the user's scope they
    # can't do anything with it regardless of ptype.
    if profile["countries"] and doc.get("country") not in profile["countries"]:
        return False
    if profile["project_types"] and doc.get("project_type") not in profile["project_types"]:
        return False
    if profile["own_only"]:
        allowed_users = [user] + (profile["team_members"] or [])
        if doc.get("salesperson") not in allowed_users:
            return False

    # Action-level gates. 'read' and 'print'/'email'/'export'/'share' pass
    # through once the row scope allows the doc — those are handled by
    # access profile's can_export for bulk export instead.
    if ptype == "delete" and not profile["can_delete_projects"]:
        return False
    if ptype == "create" and not profile["can_create_projects"]:
        return False
    # 'write' / 'submit' / 'amend' / 'cancel': use phase-edit gate as a
    # reasonable default — if a user can't change phase they're effectively
    # read-only on the project.
    if ptype in ("write", "submit", "amend", "cancel") and not profile["can_edit_phase"]:
        return False
    if ptype == "export" and not profile["can_export"]:
        return False

    return True


def get_offer_query_conditions(user: str = None) -> str:
    """Filter LCS Offer lists to offers of projects the user can see."""
    user = user or frappe.session.user
    profile = _profile_for(user)
    if not profile:
        return ""

    project_conditions = get_permission_query_conditions(user)
    if not project_conditions:
        return ""

    # Translate the project-side conditions onto tabLCS Offer.project via
    # a subquery. Using a subquery keeps the hook signature (returns a
    # single SQL fragment) while still leveraging the existing logic.
    project_conditions_for_subquery = project_conditions.replace(
        "`tabLCS Project`.", "p."
    )
    return (
        f"`tabLCS Offer`.project IN ("
        f"SELECT p.name FROM `tabLCS Project` p "
        f"WHERE {project_conditions_for_subquery}"
        f")"
    )


def has_offer_permission(doc, ptype: str = None, user: str = None) -> bool:
    """Offer visibility + mutation follows its parent project's rules."""
    user = user or frappe.session.user
    profile = _profile_for(user)
    if not profile:
        return True
    if not doc.get("project"):
        # Orphan offer — defer to base role perms
        return True
    try:
        project = frappe.get_cached_doc("LCS Project", doc.get("project"))
    except frappe.DoesNotExistError:
        return False

    if not has_permission(project, "read", user=user):
        return False

    # Status transitions that actually change commercial state — gate via
    # can_accept_offers so junior sales can't self-confirm deals.
    if ptype == "write" and doc.get("status") == "Accepted" and not profile.get("can_accept_offers"):
        return False

    return True


@frappe.whitelist()
def get_user_preferences(user: str = None) -> dict:
    """Entry point for the frontend on boot — returns the user's display prefs
    merged with their access profile so the SPA knows which UI elements to
    render and which fields to hide."""
    user = user or frappe.session.user

    # Per-user preferences (created lazily if missing)
    prefs = None
    if frappe.db.exists("LCS User Preferences", user):
        prefs = frappe.get_doc("LCS User Preferences", user).as_dict()

    profile = _profile_for(user)

    return {
        "user": user,
        "preferences": prefs or _default_prefs(),
        "access_profile": profile,
        "is_system_manager": "System Manager" in frappe.get_roles(user),
    }


@frappe.whitelist()
def save_user_preferences(preferences: dict) -> dict:
    """Upsert the current user's preferences. Used by the settings dialog."""
    user = frappe.session.user
    import json
    if isinstance(preferences, str):
        preferences = json.loads(preferences)

    # Users can only write their own prefs (enforced by if_owner role perm
    # on the DocType, but we double-check here for safety).
    preferences["user"] = user

    if frappe.db.exists("LCS User Preferences", user):
        doc = frappe.get_doc("LCS User Preferences", user)
        for k, v in preferences.items():
            if k in ("user", "access_profile"):
                # Normal users can't change their own access profile —
                # only System Manager can assign one.
                if k == "access_profile" and "System Manager" not in frappe.get_roles(user):
                    continue
            if hasattr(doc, k):
                setattr(doc, k, v)
        doc.save(ignore_permissions=True)
    else:
        # Strip access_profile for non-sysmgr users
        if "System Manager" not in frappe.get_roles(user):
            preferences.pop("access_profile", None)
        doc = frappe.get_doc({"doctype": "LCS User Preferences", **preferences})
        doc.insert(ignore_permissions=True)

    frappe.db.commit()
    # Bust cache so next request sees the new prefs
    frappe.cache().hdel("lcs_access_profile_cache", user)
    return {"ok": True, "name": doc.name}


def _default_prefs() -> dict:
    """Safe defaults for a user who hasn't set any preferences yet."""
    return {
        "list_columns": "{}",
        "show_forecasting": 1,
        "show_integration_panel": 1,
        "show_team_section": 1,
        "show_fusion_section": 1,
        "show_bsm_section": 1,
        "show_training_section": 1,
        "show_opportunity_matrix": 1,
        "show_pricing_details": 1,
        "default_list_view": "Table",
        "default_show_only_mine": 0,
        "default_period_forecasting": "month",
        "compact_mode": 0,
        "confirm_phase_changes": 1,
        "voice_input_language": "de-DE",
    }
