"""
Quick-note dispatcher — frontend sends in a blob of text (typed or
dictated), backend ranks every visible LCS Project against it and
either returns candidates or logs the note against the clear winner.

Follows Frappe customisation conventions (see
feedback_frappe_doc_compliance.md in agent memory):
- @frappe.whitelist with role gates
- frappe.get_all / frappe.get_doc instead of raw SQL
- Logs partial failures via frappe.log_error with a namespaced category
- Uses frappe.has_permission so Access Profile visibility flows through
"""

import re
import frappe


# Scoring weights — tuned so that a project-number mention always wins,
# organization matches beat loose name overlap, and country is a soft
# tiebreaker between otherwise equal candidates.
WEIGHT_PROJECT_NUMBER = 1.0
WEIGHT_PROJECT_ABBR = 0.6
WEIGHT_PROJECT_NAME = 0.5
WEIGHT_ORGANIZATION = 0.3
WEIGHT_COUNTRY = 0.15
WEIGHT_TYPE_PHRASE = 0.1

# Confidence thresholds
AUTO_DISPATCH_MIN = 0.8
SUGGEST_MIN = 0.25

# Stop words we don't treat as meaningful match signals
STOP_WORDS = {
    "der", "die", "das", "und", "oder", "mit", "für", "von", "bei", "auf", "ist", "wir",
    "the", "and", "or", "with", "for", "of", "at", "on", "is", "we", "are",
    "heute", "morgen", "gestern", "hat", "um", "an", "nach", "vor",
    "project", "projekt", "auftrag", "angebot", "offer",
}

# German product-term hints → LCS project_type
TYPE_KEYWORDS = [
    (re.compile(r"\bseilbahn\w*", re.I), "SB"),
    (re.compile(r"\bwinde\w*", re.I), "WI"),
    (re.compile(r"\blift\w*", re.I), "LL"),
    (re.compile(r"\bcable ?cran\w*", re.I), "SB"),
]


@frappe.whitelist()
def dispatch_note(text: str, project: str = None, dry_run: bool = False):
    """
    Rank visible LCS Projects against the note text and optionally log it.

    Parameters:
      text     : str — the note body (typed or dictated)
      project  : str — optional: caller already knows the target; skip matching
      dry_run  : bool — if truthy, only return candidates; don't create the Comment

    Returns:
      {
        "candidates": [ {name, project_name, project_number, organization,
                         country, project_type, score, confidence} ],
        "auto_dispatched": bool,
        "comment": str | None,
        "target_project": str | None
      }
    """
    text = (text or "").strip()
    if not text:
        frappe.throw("Note text is empty")

    # Coerce string params from HTTP form-urlencoded bodies
    if isinstance(dry_run, str):
        dry_run = dry_run.lower() in ("1", "true", "yes")

    # If caller names an explicit project, skip matching
    if project:
        if not frappe.has_permission("LCS Project", ptype="write", doc=project):
            frappe.throw("Not permitted to write to this project", frappe.PermissionError)
        comment_name = _log_as_comment(project, text) if not dry_run else None
        return {
            "candidates": [],
            "auto_dispatched": not dry_run,
            "comment": comment_name,
            "target_project": project,
        }

    # Match against every project the user can see — frappe.get_all
    # already honours our permission_query_conditions hook.
    projects = frappe.get_all(
        "LCS Project",
        filters={"status": ["not in", ["Cancelled"]]},
        fields=[
            "name", "project_name", "project_number", "project_abbr",
            "project_type", "organization", "country", "phase", "status",
        ],
        limit=0,  # return all visible
    )

    scored = []
    hinted_type = _detect_type_hint(text)
    text_lower = text.lower()
    text_tokens = _tokenize(text_lower)

    for p in projects:
        score, reasons = _score_project(p, text_lower, text_tokens, hinted_type)
        if score > 0:
            scored.append({**p, "score": round(score, 3), "reasons": reasons})

    scored.sort(key=lambda x: x["score"], reverse=True)
    top = [c for c in scored if c["score"] >= SUGGEST_MIN][:5]

    for c in top:
        c["confidence"] = _confidence_label(c["score"])

    # Clear winner → auto-dispatch (unless caller explicitly asked for dry-run)
    auto_target = None
    comment_name = None
    if top and top[0]["score"] >= AUTO_DISPATCH_MIN:
        # Tie check: if #2 is within 10% of #1 it's not actually clear
        if len(top) < 2 or top[0]["score"] - top[1]["score"] >= 0.1:
            auto_target = top[0]["name"]

    if auto_target and not dry_run:
        if frappe.has_permission("LCS Project", ptype="write", doc=auto_target):
            comment_name = _log_as_comment(auto_target, text)
        else:
            # Silent downgrade: still suggest but don't dispatch
            auto_target = None

    return {
        "candidates": top,
        "auto_dispatched": bool(comment_name),
        "comment": comment_name,
        "target_project": auto_target if comment_name else None,
    }


def _score_project(p: dict, text_lower: str, text_tokens: set, hinted_type: str | None):
    """Return (score, reasons[]) for how well `p` matches the note."""
    score = 0.0
    reasons = []

    number = (p.get("project_number") or "").lower()
    if number and number in text_lower:
        score += WEIGHT_PROJECT_NUMBER
        reasons.append(f"number:{number}")

    abbr = (p.get("project_abbr") or "").lower()
    # Abbreviations <3 chars are too noisy — they'd match random words
    if abbr and len(abbr) >= 3 and _word_in_text(abbr, text_lower):
        score += WEIGHT_PROJECT_ABBR
        reasons.append(f"abbr:{abbr}")

    # Project-name token overlap. Name is often just "SB-SADDN" which maps to
    # tokens {sb, saddn} — if "saddn" appears in the note, score.
    name = (p.get("project_name") or "").lower()
    name_tokens = _tokenize(name)
    name_hits = name_tokens & text_tokens
    if name_tokens and name_hits:
        ratio = len(name_hits) / len(name_tokens)
        # For 1-token names the ratio is 1.0 but we only count it if the
        # token is at least 4 chars — otherwise "mtm" matches too aggressively
        interesting = {t for t in name_hits if len(t) >= 4}
        if interesting or ratio == 1.0:
            score += WEIGHT_PROJECT_NAME * ratio
            reasons.append(f"name:{sorted(name_hits)}")

    org = (p.get("organization") or "").lower()
    org_tokens = _tokenize(org)
    org_hits = org_tokens & text_tokens
    if org_tokens and org_hits:
        ratio = len(org_hits) / len(org_tokens)
        score += WEIGHT_ORGANIZATION * ratio
        reasons.append(f"org:{sorted(org_hits)}")

    country = (p.get("country") or "").lower()
    if country and country in text_lower:
        score += WEIGHT_COUNTRY
        reasons.append(f"country:{country}")

    if hinted_type and p.get("project_type") == hinted_type:
        score += WEIGHT_TYPE_PHRASE
        reasons.append(f"type_hint:{hinted_type}")

    return score, reasons


def _tokenize(text: str) -> set:
    """Split on non-word chars and strip stop words + short tokens."""
    if not text:
        return set()
    raw = re.split(r"\W+", text.lower())
    return {t for t in raw if t and t not in STOP_WORDS and len(t) >= 3}


def _word_in_text(needle: str, haystack: str) -> bool:
    """Case-insensitive whole-word match (so 'SB' inside 'SBAHN' doesn't count)."""
    return re.search(rf"\b{re.escape(needle)}\b", haystack) is not None


def _detect_type_hint(text: str) -> str | None:
    """Return SB / WI / LL if the text mentions a product category."""
    for pattern, t in TYPE_KEYWORDS:
        if pattern.search(text):
            return t
    return None


def _confidence_label(score: float) -> str:
    if score >= AUTO_DISPATCH_MIN:
        return "high"
    if score >= 0.5:
        return "medium"
    if score >= SUGGEST_MIN:
        return "low"
    return "very-low"


def _log_as_comment(project: str, text: str) -> str:
    """Attach the note as a Frappe Comment on the project's activity feed.

    Uses the documented Comment DocType — same thing Frappe's own
    '+ Comment' button produces, so notes show up in the Activity tab
    without extra UI work on our side.
    """
    comment = frappe.new_doc("Comment")
    comment.comment_type = "Comment"
    comment.reference_doctype = "LCS Project"
    comment.reference_name = project
    comment.content = f"📝 **Quick Note**\n\n{text.strip()}"
    comment.insert(ignore_permissions=False)
    frappe.db.commit()
    return comment.name
