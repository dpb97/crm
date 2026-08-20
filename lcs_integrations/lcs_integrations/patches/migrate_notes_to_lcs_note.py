"""Migrate the two legacy note stores into the unified LCS Note doctype:

  * FCRM Note                         → one LCS Note + a link to its reference
  * Quick-Note Comments (📝 header)   → one LCS Note per distinct text, linked to
                                        EVERY project the same note was filed on

Idempotent via LCS Note.source_ref. Copies (does not delete the originals), and
preserves the original owner + creation timestamp.
"""

from __future__ import annotations

import frappe

ALLOWED = ("LCS Project", "CRM Lead", "LCS Chance", "Contact", "CRM Organization")
QUICKNOTE_HEADER = "📝 **Quick Note**"


def _strip_header(content: str) -> str:
    c = content or ""
    if c.startswith(QUICKNOTE_HEADER):
        parts = c.split("\n\n", 1)
        return (parts[1] if len(parts) > 1 else "").strip()
    return c.strip()


def _make_note(source_ref, content, owner, creation, note_type, links, audio_file=None):
    if not content or frappe.db.exists("LCS Note", {"source_ref": source_ref}):
        return
    doc = frappe.new_doc("LCS Note")
    doc.content = content
    doc.note_type = note_type
    doc.audio_file = audio_file
    doc.source_ref = source_ref
    seen = set()
    for dt, dn in links:
        if dt in ALLOWED and dn and (dt, dn) not in seen and frappe.db.exists(dt, dn):
            seen.add((dt, dn))
            doc.append("links", {"link_doctype": dt, "link_name": dn})
    doc.insert(ignore_permissions=True)
    # Preserve original author + timestamp so the notes board keeps its order.
    frappe.db.set_value("LCS Note", doc.name, {"owner": owner, "creation": creation}, update_modified=False)


def execute():
    # `bench migrate` does not reliably auto-sync a brand-new doctype folder, so
    # force it in before the data migration (idempotent).
    frappe.reload_doc("lcs_integrations", "doctype", "lcs_note", force=True)
    if not frappe.db.exists("DocType", "LCS Note"):
        return

    # 1) FCRM Note → LCS Note
    if frappe.db.exists("DocType", "FCRM Note"):
        for n in frappe.get_all(
            "FCRM Note",
            fields=["name", "title", "content", "owner", "creation", "reference_doctype", "reference_docname"],
        ):
            body = (n.content or "").strip() or (n.title or "").strip()
            links = []
            if n.reference_doctype in ALLOWED and n.reference_docname:
                links.append((n.reference_doctype, n.reference_docname))
            _make_note(f"fcrm:{n.name}", body, n.owner, n.creation, "text", links)

    # 2) Quick-Note Comments → LCS Note (grouped by author + text)
    comments = frappe.get_all(
        "Comment",
        filters={"comment_type": "Comment", "content": ["like", f"{QUICKNOTE_HEADER}%"]},
        fields=["name", "content", "reference_doctype", "reference_name", "owner", "creation"],
        order_by="creation asc",
    )
    groups: dict = {}
    for c in comments:
        body = _strip_header(c.content)
        if not body:
            continue
        key = (c.owner, body)
        g = groups.setdefault(key, {"first": c.name, "owner": c.owner, "creation": c.creation, "text": body, "projects": []})
        if c.reference_doctype == "LCS Project" and c.reference_name:
            g["projects"].append(c.reference_name)
    for g in groups.values():
        _make_note(
            f"comment:{g['first']}", g["text"], g["owner"], g["creation"], "text",
            [("LCS Project", p) for p in g["projects"]],
        )

    # 3) Voice notes: LCS Audio Transcription Job → LCS Note (voice)
    if frappe.db.exists("DocType", "LCS Audio Transcription Job"):
        for j in frappe.get_all(
            "LCS Audio Transcription Job",
            fields=["name", "file_url", "new_transcript", "original_transcript", "project", "owner", "creation"],
        ):
            transcript = (j.new_transcript or j.original_transcript or "").strip() or "🎤"
            links = [("LCS Project", j.project)] if j.project else []
            _make_note(f"audiojob:{j.name}", transcript, j.owner, j.creation, "voice", links, audio_file=j.file_url)

    frappe.db.commit()
