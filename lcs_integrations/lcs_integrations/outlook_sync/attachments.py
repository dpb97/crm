"""On-demand email attachment enrichment for the reader modal.

The sync stores only the mail body, so inline images (cid:) render broken and
file attachments are absent. When an email is opened we fetch its attachments
live from Graph (using the stored Graph message id + the mailbox), inline the
images into the HTML as data URIs, and return the file attachments as data URIs
for display/download. Best-effort: any Graph error leaves the email unchanged.
"""

from __future__ import annotations

from .graph_client import GraphClient

_IMG_TYPES = {
    "image/png", "image/jpeg", "image/jpg", "image/gif",
    "image/webp", "image/bmp", "image/svg+xml",
}


def enrich_email(comm: dict) -> dict:
    """Fetch Graph attachments for a synced email and fold them into `comm`:
    inline images are substituted into `content`, other files are returned as
    `comm["attachments"]` (name/content_type/is_image/size/data_url)."""
    comm["attachments"] = []
    graph_id = comm.get("message_id")
    mailbox = comm.get("user")
    if not graph_id or not mailbox:
        return comm

    try:
        client = GraphClient()
        try:
            atts = client.message_attachments(mailbox, graph_id)
        finally:
            client.close()
    except Exception:  # noqa: BLE001 — reader must still work without attachments
        return comm

    content = comm.get("content") or ""
    files: list[dict] = []
    for a in atts:
        if a.get("@odata.type") != "#microsoft.graph.fileAttachment":
            continue
        raw = a.get("contentBytes")
        if not raw:
            continue
        ctype = (a.get("contentType") or "application/octet-stream").lower()
        data_url = f"data:{ctype};base64,{raw}"
        cid = a.get("contentId")
        if a.get("isInline") and cid:
            content = content.replace(f"cid:{cid}", data_url)
            content = content.replace(f"cid:&lt;{cid}&gt;", data_url)
            content = content.replace(f"cid:<{cid}>", data_url)
        else:
            files.append({
                "name": a.get("name") or "attachment",
                "content_type": ctype,
                "is_image": ctype in _IMG_TYPES,
                "size": a.get("size") or 0,
                "data_url": data_url,
            })

    comm["content"] = content
    comm["attachments"] = files
    return comm
