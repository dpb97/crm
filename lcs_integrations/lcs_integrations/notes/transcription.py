"""
Hermes-agent bridge for audio re-transcription.

The CRM captures audio alongside every voice-dictated note. An external
agent (Hermes) polls `claim_jobs`, downloads each private File, runs its
STT model, and POSTs results back via `submit_transcription`.

Contract (designed to be agent-agnostic — any STT backend can implement it):

  GET/POST  lcs_integrations.notes.transcription.claim_jobs(limit, agent)
            → returns up to `limit` pending jobs, atomically flipping them
              to 'Processing' and stamping with the agent identifier so two
              agent instances can poll the same queue safely.

  POST      lcs_integrations.notes.transcription.submit_transcription(
              job, transcript, model, confidence=None, language=None
            )
            → stores the result, flips status to 'Done', and rewrites the
              source Comment with the cleaner transcript so sales sees it
              immediately on the project's Activity tab.

  POST      lcs_integrations.notes.transcription.fail_job(job, error)
            → records the error, increments retries. If retries < 3 the
              status goes back to 'Pending' so Hermes can retry; otherwise
              it stays 'Failed' for manual review.

Agents authenticate as a dedicated Frappe user with the role
'LCS Transcription Agent' — created manually by the admin with a
long-lived API key. The whitelist decorators below check that role so
a human sales user can't accidentally manipulate the queue.
"""

import frappe
from datetime import datetime


AGENT_ROLES = ["LCS Transcription Agent", "System Manager"]
MAX_RETRIES = 3


def create_job_for_audio(
    file_url: str,
    project: str | None = None,
    comment: str | None = None,
    original_transcript: str | None = None,
    language: str = "de-DE",
    priority: int = 0,
) -> str | None:
    """Queue a transcription job for an uploaded audio attachment.

    Called from notes.api._log_as_comment whenever an audio file is
    attached to a note. Idempotent: if a job already exists for the
    file URL we return the existing one rather than creating duplicates.
    """
    if not file_url:
        return None

    existing = frappe.db.get_value(
        "LCS Audio Transcription Job",
        {"file_url": file_url, "status": ["in", ["Pending", "Processing", "Done"]]},
        "name",
    )
    if existing:
        return existing

    # Look up file metadata so the agent has context without another roundtrip
    file_row = frappe.db.get_value(
        "File",
        {"file_url": file_url},
        ["file_size", "file_type"],
        as_dict=True,
    ) or {}

    job = frappe.new_doc("LCS Audio Transcription Job")
    job.status = "Pending"
    job.file_url = file_url
    job.file_mime = file_row.get("file_type") or ""
    job.file_size_bytes = file_row.get("file_size") or 0
    job.language = language
    job.priority = priority
    job.project = project
    job.comment = comment
    job.original_transcript = original_transcript or ""
    job.insert(ignore_permissions=True)
    frappe.db.commit()
    return job.name


@frappe.whitelist()
def claim_jobs(limit: int = 5, agent: str = "") -> list[dict]:
    """Agent-facing: claim up to `limit` pending jobs atomically.

    Flips status Pending → Processing in one transaction and stamps the
    agent id so parallel agent instances don't duplicate work.
    """
    frappe.only_for(AGENT_ROLES)
    try:
        limit = max(1, min(int(limit), 20))
    except (TypeError, ValueError):
        limit = 5

    claimed: list[dict] = []
    # We fetch-then-update inside a transaction. MariaDB's row-level
    # locking (FOR UPDATE) would be cleaner, but Frappe's abstraction
    # doesn't expose it portably — a compare-and-swap on status gives us
    # the same safety against double-claim without dropping to raw SQL.
    candidates = frappe.get_all(
        "LCS Audio Transcription Job",
        filters={"status": "Pending"},
        fields=["name"],
        order_by="priority desc, creation asc",
        limit=limit,
    )
    now = datetime.now()
    for row in candidates:
        # CAS: only flip if still Pending
        rows_affected = frappe.db.sql(
            """UPDATE `tabLCS Audio Transcription Job`
               SET status = 'Processing', agent = %s, modified = %s
               WHERE name = %s AND status = 'Pending'""",
            (agent or frappe.session.user, now, row.name),
        )
        # MariaDB returns rowcount via affected_rows; treat any
        # follow-up error defensively
        doc = frappe.get_doc("LCS Audio Transcription Job", row.name)
        if doc.status == "Processing" and doc.agent == (agent or frappe.session.user):
            claimed.append({
                "job": doc.name,
                "file_url": doc.file_url,
                "file_mime": doc.file_mime,
                "file_size_bytes": doc.file_size_bytes,
                "language": doc.language,
                "project": doc.project,
                "comment": doc.comment,
                "original_transcript": doc.original_transcript,
                "priority": doc.priority,
            })
    frappe.db.commit()
    return claimed


@frappe.whitelist()
def submit_transcription(
    job: str,
    transcript: str,
    model: str = "",
    confidence: float | None = None,
    language: str | None = None,
) -> dict:
    """Agent-facing: post back the transcription result.

    Side effects on success:
      - Job.status → 'Done', stores transcript + model + confidence
      - Source Comment.content is rewritten to show the new transcript
        with a small 🤖 marker so sales sees the cleaner text immediately
    """
    frappe.only_for(AGENT_ROLES)
    doc = frappe.get_doc("LCS Audio Transcription Job", job)
    doc.new_transcript = transcript
    doc.model = model or "hermes-stt"
    if confidence is not None:
        try:
            doc.confidence = float(confidence)
        except (TypeError, ValueError):
            pass
    if language:
        doc.language = language
    doc.transcribed_at = datetime.now()
    doc.status = "Done"
    doc.error = None
    doc.save(ignore_permissions=True)

    _rewrite_comment(doc)
    _update_lcs_note(doc)

    frappe.db.commit()
    return {"ok": True, "job": doc.name}


def _update_lcs_note(job) -> None:
    """Write the finished transcript into the voice note's LCS Note and auto-link
    every project mentioned in it (same rule as a typed note)."""
    note_name = frappe.db.get_value("LCS Note", {"source_ref": f"audiojob:{job.name}"}, "name")
    if not note_name:
        return
    transcript = (job.new_transcript or job.original_transcript or "").strip()
    if not transcript:
        return
    note = frappe.get_doc("LCS Note", note_name)
    note.content = transcript
    try:
        from lcs_integrations.notes.api import _rank_projects
        existing = {(l.link_doctype, l.link_name) for l in note.links}
        _, strong = _rank_projects(transcript)
        for pn in strong:
            if ("LCS Project", pn) not in existing:
                note.append("links", {"link_doctype": "LCS Project", "link_name": pn})
    except Exception:
        pass
    note.save(ignore_permissions=True)


@frappe.whitelist()
def fail_job(job: str, error: str = "") -> dict:
    """Agent-facing: mark a job as failed. Retries up to MAX_RETRIES."""
    frappe.only_for(AGENT_ROLES)
    doc = frappe.get_doc("LCS Audio Transcription Job", job)
    doc.retries = (doc.retries or 0) + 1
    doc.error = (error or "")[:500]
    if doc.retries < MAX_RETRIES:
        doc.status = "Pending"
    else:
        doc.status = "Failed"
        frappe.log_error(
            f"Transcription job {doc.name} failed after {doc.retries} retries: {error}",
            "notes.transcription",
        )
    doc.save(ignore_permissions=True)
    frappe.db.commit()
    return {"ok": True, "status": doc.status, "retries": doc.retries}


def _rewrite_comment(job) -> None:
    """Replace the original comment body with the re-transcribed text."""
    if not job.comment or not frappe.db.exists("Comment", job.comment):
        return
    comment = frappe.get_doc("Comment", job.comment)
    new_content = (
        f"📝 **Quick Note**  🎤 audio  🤖 re-transcribed by {job.model or 'agent'}\n\n"
        f"{(job.new_transcript or '').strip()}"
    )
    # Preserve the original transcript at the bottom for audit — the user
    # can compare the two if the agent's version is worse.
    if job.original_transcript and job.original_transcript.strip():
        new_content += f"\n\n---\n_Original transcript:_ {job.original_transcript.strip()}"
    frappe.db.set_value("Comment", comment.name, "content", new_content)


@frappe.whitelist()
def queue_stats() -> dict:
    """Dashboard helper — returns per-status counts for the queue."""
    frappe.only_for(["System Manager", "Sales Manager"] + AGENT_ROLES)
    from pypika import functions as fn
    Job = frappe.qb.DocType("LCS Audio Transcription Job")
    rows = (
        frappe.qb.from_(Job)
        .select(Job.status, fn.Count("*").as_("count"))
        .groupby(Job.status)
        .run(as_dict=True)
    )
    out = {"Pending": 0, "Processing": 0, "Done": 0, "Failed": 0, "Skipped": 0}
    for r in rows:
        out[r["status"]] = r["count"]
    return out
