"""Teams Outgoing Webhook -> Quick Note.

Wires the existing quick-note engine (notes.api.dispatch_note — scoring,
auto-match, comment logging) to Microsoft Teams via the *Outgoing Webhook*
feature: no Azure Bot Service, no public bot registration — a team owner
registers a webhook pointing at this endpoint and gets a shared HMAC secret.

Usage in Teams:  @QuickNote Vinci Kranbahn: Statik freigegeben, Montage Montag
Reply (inline):  "OK — Notiz geloggt an ..." or the top candidates.

Auth: Teams sends `Authorization: HMAC <base64sig>` — a 2-part header Frappe's
validate_auth rejects (2-part + Guest -> AuthenticationError) before our
endpoint runs. The auth_hook `authenticate` verifies the HMAC over the raw
body and, on success, sets the configured service user so routing proceeds.

Reply: Teams expects a raw Bot-Framework activity `{"type":"message",...}`;
we return a werkzeug Response directly so Frappe does not wrap it in its
usual {"message": ...} envelope.

site_config:
  teams_quicknote_hmac_secret : base64 secret from the Teams webhook dialog
  teams_quicknote_user        : Frappe user the notes are logged as
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import re

import frappe
from werkzeug.wrappers import Response

from lcs_integrations.notes.api import dispatch_note

_WEBHOOK_CMD = "lcs_integrations.teams.quicknote_webhook.handle"
_MENTION_RE = re.compile(r"<at>.*?</at>", re.IGNORECASE | re.DOTALL)
_TAG_RE = re.compile(r"<[^>]+>")


def _is_webhook_request() -> bool:
    # Mirror helpdesk/lms auth hooks: prefer form_dict.cmd (legacy ?cmd=),
    # else request.path (/api/method/<dotted>).
    try:
        if frappe.form_dict.get("cmd"):
            path = "/api/method/" + str(frappe.form_dict.cmd)
        else:
            path = frappe.request.path or ""
    except Exception:
        return False
    return path.rstrip("/").endswith(_WEBHOOK_CMD)


def _valid_signature(raw_body: bytes, secret_b64: str) -> bool:
    header = frappe.get_request_header("Authorization") or ""
    if not header.startswith("HMAC "):
        return False
    provided = header[5:].strip()
    try:
        key = base64.b64decode(secret_b64)
    except Exception:
        return False
    expected = base64.b64encode(
        hmac.new(key, raw_body, hashlib.sha256).digest()
    ).decode("ascii")
    return hmac.compare_digest(provided, expected)


def authenticate() -> None:
    """auth_hook — verify the Teams HMAC and set the service user so
    Frappe's validate_auth does not reject the request."""
    if not _is_webhook_request():
        return
    secret = frappe.conf.get("teams_quicknote_hmac_secret")
    service_user = frappe.conf.get("teams_quicknote_user")
    if not (secret and service_user):
        return
    try:
        raw_body = frappe.request.get_data() or b""
    except Exception:
        return
    if _valid_signature(raw_body, secret):
        frappe.set_user(service_user)


@frappe.whitelist(allow_guest=True, methods=["POST"])
def handle():
    """Messaging endpoint for the Teams outgoing webhook."""
    secret = frappe.conf.get("teams_quicknote_hmac_secret")
    service_user = frappe.conf.get("teams_quicknote_user")
    if not secret or not service_user:
        return _reply(503, "Quick-Note-Webhook ist nicht konfiguriert.")

    raw_body = frappe.request.get_data() or b""
    # Defense in depth — the auth_hook already verified this.
    if not _valid_signature(raw_body, secret):
        return _reply(401, "Ungueltige HMAC-Signatur.")

    activity = frappe.parse_json(raw_body.decode("utf-8", errors="replace")) or {}
    text = _strip_mentions(activity.get("text") or "")
    sender = ((activity.get("from") or {}).get("name") or "Unbekannt").strip()
    if not text:
        return _reply(200, "Kein Text erhalten — schreib die Notiz hinter die @Erwaehnung.")

    if frappe.session.user in ("", "Guest"):
        frappe.set_user(service_user)
    try:
        result = dispatch_note(text="[Teams - " + sender + "] " + text)
    except Exception:
        frappe.log_error(title="teams.quicknote_webhook",
                         message=frappe.get_traceback())
        return _reply(200, "Notiz konnte nicht verarbeitet werden — siehe Error Log.")

    return _reply(200, _format_reply(result))


def _strip_mentions(text: str) -> str:
    text = _MENTION_RE.sub("", text)
    text = _TAG_RE.sub(" ", text)
    return re.sub(r"\s+", " ", text).strip()


def _format_reply(result: dict) -> str:
    if result.get("auto_dispatched"):
        target = result.get("target_project")
        label = frappe.db.get_value("LCS Project", target, "project_name") or target
        return "OK — Notiz geloggt an " + str(label) + " (" + str(target) + ")."
    candidates = result.get("candidates") or []
    if not candidates:
        return "Kein Projekt erkannt. Nenne Projektname oder -nummer im Text."
    lines = ["Nicht eindeutig — schick die Notiz nochmal mit Projektname/-nummer:"]
    for c in candidates[:3]:
        lines.append(
            "- " + str(c.get("project_name")) + " (" + str(c.get("name"))
            + ") — " + str(c.get("confidence"))
        )
    return "\n".join(lines)


def _reply(status: int, text: str) -> Response:
    """Raw Bot-Framework activity — returned directly so Frappe does not
    wrap it in its {"message": ...} envelope."""
    return Response(
        json.dumps({"type": "message", "text": text}),
        status=status,
        mimetype="application/json",
    )
