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
import difflib
import frappe
from frappe import _


# Scoring weights — tuned so that a project-number mention always wins,
# organization matches beat loose name overlap, and country is a soft
# tiebreaker between otherwise equal candidates.
WEIGHT_PROJECT_NUMBER = 1.0
WEIGHT_PROJECT_ABBR = 0.6
# An EXACT, complete project-name token (e.g. "CAPU" for SB-CAPU) is a strong,
# unambiguous mention → it must clear AUTO_DISPATCH_MIN (0.8) on its own so the
# note auto-links to every project named in the text. Fuzzy name matches carry a
# 0.8 penalty (→ 0.68) and stay below the auto threshold (suggestion only).
WEIGHT_PROJECT_NAME = 0.85
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
def search_projects(query: str, limit: int = 20):
    """
    Simple OR search across project_name + project_number for the manual
    picker on the Quick Note page. Respects the current user's access
    profile because frappe.get_all honours permission_query_conditions.
    """
    query = (query or "").strip()
    if len(query) < 2:
        return []
    try:
        limit = max(1, min(int(limit), 50))
    except (TypeError, ValueError):
        limit = 20
    like = f"%{query}%"
    return frappe.get_all(
        "LCS Project",
        or_filters={
            "project_name": ["like", like],
            "project_number": ["like", like],
            "project_abbr": ["like", like],
            "organization": ["like", like],
        },
        fields=["name", "project_name", "project_number", "project_type",
                "organization", "phase", "country"],
        order_by="modified desc",
        limit_page_length=limit,
    )


# Entities a note may be linked to (multi-link via the Dynamic Link child).
ALLOWED_LINK_DOCTYPES = ("LCS Project", "CRM Lead", "LCS Chance", "Contact", "CRM Organization")


def _rank_projects(text: str):
    """Return (top_candidates, strong_project_names) for a note text. Strong =
    score >= AUTO_DISPATCH_MIN and the user may write the project."""
    projects = frappe.get_all(
        "LCS Project",
        filters={"status": ["not in", ["Cancelled"]]},
        fields=[
            "name", "project_name", "project_number", "project_abbr",
            "project_type", "organization", "country", "phase", "status",
        ],
        limit=0,  # all visible (permission_query_conditions applies)
    )
    hinted_type = _detect_type_hint(text)
    text_lower = text.lower()
    text_tokens = _tokenize(text_lower)
    scored = []
    for p in projects:
        score, reasons = _score_project(p, text_lower, text_tokens, hinted_type)
        if score > 0:
            scored.append({**p, "score": round(score, 3), "reasons": reasons})
    scored.sort(key=lambda x: x["score"], reverse=True)
    top = [c for c in scored if c["score"] >= SUGGEST_MIN][:5]
    for c in top:
        c["confidence"] = _confidence_label(c["score"])
    strong = [
        c["name"] for c in top
        if c["score"] >= AUTO_DISPATCH_MIN
        and frappe.has_permission("LCS Project", ptype="write", doc=c["name"])
    ]
    return top, strong


def _parse_links(links):
    import json
    if not links:
        return []
    if isinstance(links, str):
        try:
            links = json.loads(links)
        except Exception:
            return []
    return links if isinstance(links, list) else []


@frappe.whitelist()
def dispatch_note(text: str, project: str = None, dry_run: bool = False,
                  audio_file_url: str = None, links=None, note_type: str = None):
    """Rank visible LCS Projects against the note text and (unless dry_run) file
    the note as ONE `LCS Note`, auto-linked to EVERY strongly-matched project
    plus any explicit `project` / `links`. Returns the candidates for the picker.
    """
    text = (text or "").strip()
    if not text:
        frappe.throw("Note text is empty")
    if isinstance(dry_run, str):
        dry_run = dry_run.lower() in ("1", "true", "yes")

    top, strong = _rank_projects(text)
    if dry_run:
        return {"candidates": top, "auto_dispatched": False, "note": None, "target_projects": []}

    # Assemble the link set: explicit project + explicit links + auto strong projects.
    seen = set()
    link_rows = []

    def _add(dt, dn):
        if dt in ALLOWED_LINK_DOCTYPES and dn and (dt, dn) not in seen:
            seen.add((dt, dn))
            link_rows.append({"link_doctype": dt, "link_name": dn})

    if project:
        _add("LCS Project", project)
    for l in _parse_links(links):
        _add(l.get("link_doctype"), l.get("link_name"))
    for name in strong:
        _add("LCS Project", name)

    note = frappe.new_doc("LCS Note")
    note.content = text
    note.note_type = note_type or ("voice" if audio_file_url else "text")
    if audio_file_url:
        note.audio_file = audio_file_url
    for l in link_rows:
        note.append("links", l)
    note.insert()
    frappe.db.commit()

    target_projects = [l["link_name"] for l in link_rows if l["link_doctype"] == "LCS Project"]
    return {
        "candidates": top,
        "auto_dispatched": bool(link_rows),
        "note": note.name,
        "target_projects": target_projects,
        "target_project": target_projects[0] if target_projects else None,  # back-compat
        "comments": [note.name] if link_rows else [],  # back-compat for the composer
    }


# --------------------------------------------------------------------------- #
#  Note CRUD + link management                                                 #
# --------------------------------------------------------------------------- #
def _assert_note_perm(name: str, ptype: str = "write"):
    if not frappe.has_permission("LCS Note", ptype=ptype, doc=name):
        frappe.throw(_("Not permitted"), frappe.PermissionError)


_TITLE_FIELD = {
    "LCS Project": "project_name", "CRM Lead": "lead_name", "LCS Chance": "title",
    "Contact": "full_name", "CRM Organization": "organization_name",
}


def _link_row(l):
    title = frappe.db.get_value(l.link_doctype, l.link_name, _TITLE_FIELD.get(l.link_doctype, "name"))
    return {"link_doctype": l.link_doctype, "link_name": l.link_name, "title": title or l.link_name}


@frappe.whitelist()
def get_note(name: str):
    _assert_note_perm(name, "read")
    doc = frappe.get_doc("LCS Note", name)
    return {
        "name": doc.name, "content": doc.content, "note_type": doc.note_type,
        "audio_file": doc.audio_file, "owner": doc.owner, "creation": str(doc.creation),
        "links": [_link_row(l) for l in doc.links],
    }


@frappe.whitelist()
def update_note(name: str, text: str):
    """Edit a note's text and UNION-in any newly mentioned projects (existing
    links are kept — removing a link is an explicit action)."""
    _assert_note_perm(name, "write")
    doc = frappe.get_doc("LCS Note", name)
    doc.content = (text or "").strip()
    if not doc.content:
        frappe.throw(_("Note text is empty"))
    existing = {(l.link_doctype, l.link_name) for l in doc.links}
    _, strong = _rank_projects(doc.content)
    for pn in strong:
        if ("LCS Project", pn) not in existing:
            doc.append("links", {"link_doctype": "LCS Project", "link_name": pn})
    doc.save()
    frappe.db.commit()
    return get_note(name)


@frappe.whitelist()
def delete_note(name: str):
    _assert_note_perm(name, "delete")
    frappe.delete_doc("LCS Note", name)
    frappe.db.commit()
    return {"ok": True}


@frappe.whitelist()
def add_note_link(name: str, link_doctype: str, link_name: str):
    _assert_note_perm(name, "write")
    if link_doctype not in ALLOWED_LINK_DOCTYPES:
        frappe.throw(_("Invalid link type"))
    doc = frappe.get_doc("LCS Note", name)
    if not any(l.link_doctype == link_doctype and l.link_name == link_name for l in doc.links):
        doc.append("links", {"link_doctype": link_doctype, "link_name": link_name})
        doc.save()
        frappe.db.commit()
    return get_note(name)


@frappe.whitelist()
def remove_note_link(name: str, link_doctype: str, link_name: str):
    _assert_note_perm(name, "write")
    doc = frappe.get_doc("LCS Note", name)
    doc.set("links", [l for l in doc.links if not (l.link_doctype == link_doctype and l.link_name == link_name)])
    doc.save()
    frappe.db.commit()
    return get_note(name)


def _score_project(p: dict, text_lower: str, text_tokens: set, hinted_type: str | None):
    """Return (score, reasons[]) for how well `p` matches the note."""
    score = 0.0
    reasons = []

    number = (p.get("project_number") or "").lower()
    if number and number in text_lower:
        score += WEIGHT_PROJECT_NUMBER
        reasons.append(f"number:{number}")

    # Full project_name substring — catches cases like "QX-CM" where the
    # name breaks down into tokens too short for the token-based path
    # (tokens <3 chars are stripped as noise).
    full_name = (p.get("project_name") or "").lower()
    if full_name and len(full_name) >= 3 and full_name in text_lower:
        score += WEIGHT_PROJECT_NAME  # same weight as exact token match
        reasons.append(f"name_full:{full_name}")

    abbr = (p.get("project_abbr") or "").lower()
    # Abbreviations <3 chars are too noisy — they'd match random words
    if abbr and len(abbr) >= 3 and _word_in_text(abbr, text_lower):
        score += WEIGHT_PROJECT_ABBR
        reasons.append(f"abbr:{abbr}")

    # Project-name matching — exact first, then fuzzy fallback so Web
    # Speech transcription errors ("SB-Saddan" vs "SB-SADDN") still hit.
    name = (p.get("project_name") or "").lower()
    name_tokens = _tokenize(name)
    name_hits = name_tokens & text_tokens
    if name_tokens and name_hits:
        ratio = len(name_hits) / len(name_tokens)
        interesting = {t for t in name_hits if len(t) >= 4}
        if interesting or ratio == 1.0:
            score += WEIGHT_PROJECT_NAME * ratio
            reasons.append(f"name:{sorted(name_hits)}")
    else:
        # Fuzzy fallback — for each ≥4-char name token, find the closest
        # text token above the similarity threshold. Catches mis-heard
        # project-name tokens that the exact match misses.
        fuzzy_hits = _fuzzy_token_hits(name_tokens, text_tokens)
        if fuzzy_hits:
            ratio = len(fuzzy_hits) / max(len(name_tokens), 1)
            score += WEIGHT_PROJECT_NAME * ratio * 0.8  # penalty for fuzzy match
            reasons.append(f"name_fuzzy:{fuzzy_hits}")

    org = (p.get("organization") or "").lower()
    org_tokens = _tokenize(org)
    org_hits = org_tokens & text_tokens
    if org_tokens and org_hits:
        ratio = len(org_hits) / len(org_tokens)
        score += WEIGHT_ORGANIZATION * ratio
        reasons.append(f"org:{sorted(org_hits)}")
    else:
        fuzzy_hits = _fuzzy_token_hits(org_tokens, text_tokens)
        if fuzzy_hits:
            ratio = len(fuzzy_hits) / max(len(org_tokens), 1)
            score += WEIGHT_ORGANIZATION * ratio * 0.8
            reasons.append(f"org_fuzzy:{fuzzy_hits}")

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


def _fuzzy_token_hits(expected: set, heard: set, threshold: float = 0.78) -> list:
    """For each expected token ≥4 chars, find the closest heard token above
    the similarity threshold. Web Speech API mis-hears project names often
    (SADDN → Saddan, JINNO → Ginno) and exact-match misses them — fuzzy
    matching with a conservative threshold recovers most of those."""
    hits = []
    short_heard = [h for h in heard if len(h) >= 3]
    for needle in expected:
        if len(needle) < 4:
            continue
        best = difflib.get_close_matches(needle, short_heard, n=1, cutoff=threshold)
        if best:
            hits.append(f"{best[0]}~{needle}")
    return hits


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


def _log_as_comment(project: str, text: str, audio_file_url: str | None = None) -> str:
    """Attach the note as a Frappe Comment on the project's activity feed.

    Uses the documented Comment DocType — same thing Frappe's own
    '+ Comment' button produces, so notes show up in the Activity tab
    without extra UI work on our side.

    When an audio file URL is supplied, the uploaded File record is
    re-parented to the LCS Project so the recording appears in the
    project's attachments and can be re-transcribed later.
    """
    header = "📝 **Quick Note**"
    if audio_file_url:
        header += "  🎤 audio attached"

    comment = frappe.new_doc("Comment")
    comment.comment_type = "Comment"
    comment.reference_doctype = "LCS Project"
    comment.reference_name = project
    comment.content = f"{header}\n\n{text.strip()}"
    comment.insert(ignore_permissions=False)

    # Reparent the uploaded audio to the project and link it from
    # the comment for later retrieval. Then queue a Hermes job so the
    # agent can re-transcribe with better quality / custom vocabulary.
    if audio_file_url:
        try:
            file_name = frappe.db.get_value("File", {"file_url": audio_file_url}, "name")
            if file_name:
                frappe.db.set_value("File", file_name, {
                    "attached_to_doctype": "LCS Project",
                    "attached_to_name": project,
                })
        except Exception as e:
            frappe.log_error(
                f"Could not reparent audio file {audio_file_url}: {e}",
                "notes.dispatch",
            )
        # Queue the job. Imported lazily so notes/api.py stays callable
        # on sites that haven't migrated the Job DocType yet.
        try:
            from lcs_integrations.notes.transcription import create_job_for_audio
            create_job_for_audio(
                file_url=audio_file_url,
                project=project,
                comment=comment.name,
                original_transcript=text,
            )
        except Exception as e:
            frappe.log_error(
                f"Could not queue transcription job for {audio_file_url}: {e}",
                "notes.dispatch",
            )

    frappe.db.commit()
    return comment.name


@frappe.whitelist()
def retranscribe_audio(file_url: str, language: str = "de-DE", priority: int = 5):
    """
    Re-queue a saved audio attachment for transcription by the Hermes agent.

    Does not perform the STT itself — just drops a job into the
    LCS Audio Transcription Job queue where Hermes will pick it up via
    `lcs_integrations.notes.transcription.claim_jobs`.
    """
    frappe.only_for(["System Manager", "Sales Manager", "Sales User"])
    file_row = frappe.db.get_value(
        "File",
        {"file_url": file_url},
        ["name", "attached_to_doctype", "attached_to_name"],
        as_dict=True,
    )
    if not file_row:
        frappe.throw(f"File {file_url} not found")

    project = None
    if file_row.attached_to_doctype == "LCS Project":
        if not frappe.has_permission("LCS Project", ptype="write", doc=file_row.attached_to_name):
            frappe.throw("Not permitted", frappe.PermissionError)
        project = file_row.attached_to_name

    from lcs_integrations.notes.transcription import create_job_for_audio
    job_name = create_job_for_audio(
        file_url=file_url,
        project=project,
        language=language,
        priority=int(priority) if priority else 5,
    )

    # Unified note: a voice note is an LCS Note carrying the recording (to replay)
    # and, once Hermes finishes (submit_transcription), the transcript to read/edit.
    note_name = None
    if job_name and not frappe.db.exists("LCS Note", {"source_ref": f"audiojob:{job_name}"}):
        note = frappe.new_doc("LCS Note")
        note.note_type = "voice"
        note.audio_file = file_url
        note.content = _("Transcription in progress …")
        note.source_ref = f"audiojob:{job_name}"
        if project:
            note.append("links", {"link_doctype": "LCS Project", "link_name": project})
        note.insert(ignore_permissions=True)
        note_name = note.name
        frappe.db.commit()

    return {"ok": True, "job": job_name, "note": note_name}
