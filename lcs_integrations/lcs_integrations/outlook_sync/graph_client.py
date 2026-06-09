"""Thin wrapper around Microsoft Graph endpoints.

Uses MSAL for token acquisition. We only need a handful of endpoints — no
reason to pull in the heavy `msgraph-sdk` package.

Covered surface:
- Mail delta (Inbox)         — `messages_delta`
- Calendar delta             — `events_delta`
- Contacts delta (mailbox)   — `contacts_delta`
- Contacts CRUD (mailbox)    — `contact_create / _update / _delete`
- Teams channel posting      — `team_channel_post_message`
- Teams channel discovery    — `team_channels_list`

All methods raise `GraphClientError` for non-2xx responses; callers should
log and persist the error on the bound DocType row.
"""

from __future__ import annotations

import os
from typing import Any

import httpx
import msal


class GraphClientError(RuntimeError):
    pass


class GraphClient:
    def __init__(self, *, transport: httpx.BaseTransport | None = None) -> None:
        self._tenant = os.environ["ENTRA_TENANT_ID"]
        self._client_id = os.environ["ENTRA_CLIENT_ID"]
        self._client_secret = os.environ["ENTRA_CLIENT_SECRET"]
        self._authority = f"https://login.microsoftonline.com/{self._tenant}"
        self._scopes = ["https://graph.microsoft.com/.default"]
        self._http = httpx.Client(
            base_url="https://graph.microsoft.com/v1.0",
            transport=transport,
            timeout=httpx.Timeout(connect=5.0, read=30.0, write=30.0, pool=5.0),
        )
        self._app = msal.ConfidentialClientApplication(
            self._client_id,
            authority=self._authority,
            client_credential=self._client_secret,
        )
        self._token: str | None = None

    def _bearer(self) -> str:
        if self._token:
            return self._token
        result = self._app.acquire_token_for_client(scopes=self._scopes)
        if "access_token" not in result:
            raise GraphClientError(result.get("error_description", "token acquisition failed"))
        self._token = result["access_token"]
        return self._token

    def _headers(self, *, prefer_track_changes: bool = False) -> dict[str, str]:
        h = {"Authorization": f"Bearer {self._bearer()}", "Content-Type": "application/json"}
        if prefer_track_changes:
            h["Prefer"] = "odata.track-changes"
        return h

    def _check(self, resp: httpx.Response, *expected: int) -> dict[str, Any]:
        if resp.status_code not in expected:
            raise GraphClientError(f"Graph HTTP {resp.status_code}: {resp.text[:500]}")
        if resp.status_code == 204 or not resp.content:
            return {}
        return resp.json()

    # --------------------------------------------------------------- Mail

    def messages_delta(self, user_principal: str, delta_link: str | None = None) -> dict[str, Any]:
        """Return a page of message delta for the given mailbox."""
        headers = self._headers(prefer_track_changes=True)
        if delta_link:
            resp = self._http.get(delta_link, headers=headers)
        else:
            resp = self._http.get(
                f"/users/{user_principal}/mailFolders/Inbox/messages/delta",
                headers=headers,
            )
        return self._check(resp, 200)

    # ----------------------------------------------------------- Calendar

    def events_delta(
        self,
        user_principal: str,
        *,
        start_iso: str,
        end_iso: str,
        delta_link: str | None = None,
    ) -> dict[str, Any]:
        """Calendar view delta for a user's primary calendar.

        Graph requires `startDateTime` / `endDateTime` on the first call;
        subsequent calls follow the returned `@odata.deltaLink`.
        """
        headers = self._headers(prefer_track_changes=True)
        if delta_link:
            resp = self._http.get(delta_link, headers=headers)
        else:
            resp = self._http.get(
                f"/users/{user_principal}/calendarView/delta",
                params={"startDateTime": start_iso, "endDateTime": end_iso},
                headers=headers,
            )
        return self._check(resp, 200)

    # ----------------------------------------------------------- Contacts

    def contacts_delta(self, mailbox: str, delta_link: str | None = None) -> dict[str, Any]:
        """Pull a delta page of contacts from the given mailbox."""
        headers = self._headers(prefer_track_changes=True)
        if delta_link:
            resp = self._http.get(delta_link, headers=headers)
        else:
            resp = self._http.get(f"/users/{mailbox}/contacts/delta", headers=headers)
        return self._check(resp, 200)

    def contact_create(self, mailbox: str, payload: dict[str, Any]) -> dict[str, Any]:
        resp = self._http.post(
            f"/users/{mailbox}/contacts",
            json=payload,
            headers=self._headers(),
        )
        return self._check(resp, 201)

    def contact_update(self, mailbox: str, graph_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        resp = self._http.patch(
            f"/users/{mailbox}/contacts/{graph_id}",
            json=payload,
            headers=self._headers(),
        )
        return self._check(resp, 200)

    def contact_delete(self, mailbox: str, graph_id: str) -> None:
        resp = self._http.delete(
            f"/users/{mailbox}/contacts/{graph_id}",
            headers=self._headers(),
        )
        self._check(resp, 204)

    def contacts_by_domain(self, mailbox: str, domain: str) -> list[dict[str, Any]]:
        """All mailbox contacts whose any email address ends with @domain.

        Graph's `$filter` does not support substring matches on the
        `emailAddresses` collection, so we page through the address book and
        filter client-side. Domains are small enough that this stays cheap.
        """
        suffix = f"@{domain.lower().strip()}"
        matches: list[dict[str, Any]] = []
        url: str | None = f"/users/{mailbox}/contacts?$top=100"
        while url:
            resp = self._http.get(url, headers=self._headers())
            body = self._check(resp, 200)
            for entry in body.get("value", []):
                for email in entry.get("emailAddresses") or []:
                    if (email.get("address") or "").lower().endswith(suffix):
                        matches.append(entry)
                        break
            url = body.get("@odata.nextLink")
        return matches

    # ----------------------------------------------------------- Photos

    def contact_photo_get(self, mailbox: str, graph_id: str) -> bytes | None:
        """Raw photo bytes for a mailbox contact, or None if it has none."""
        resp = self._http.get(
            f"/users/{mailbox}/contacts/{graph_id}/photo/$value",
            headers={"Authorization": f"Bearer {self._bearer()}"},
        )
        if resp.status_code == 404:
            return None
        if resp.status_code != 200:
            raise GraphClientError(f"Graph HTTP {resp.status_code}: {resp.text[:200]}")
        return resp.content

    def contact_photo_put(self, mailbox: str, graph_id: str, image: bytes) -> None:
        """Upload a JPEG/PNG photo to a mailbox contact."""
        resp = self._http.put(
            f"/users/{mailbox}/contacts/{graph_id}/photo/$value",
            content=image,
            headers={
                "Authorization": f"Bearer {self._bearer()}",
                "Content-Type": "image/jpeg",
            },
        )
        self._check(resp, 200)

    # -------------------------------------------------------------- Teams

    def team_channels_list(self, team_id: str) -> list[dict[str, Any]]:
        resp = self._http.get(
            f"/teams/{team_id}/channels",
            headers=self._headers(),
        )
        body = self._check(resp, 200)
        return body.get("value", [])

    def team_channel_post_message(
        self,
        team_id: str,
        channel_id: str,
        *,
        subject: str | None,
        adaptive_card: dict[str, Any],
    ) -> dict[str, Any]:
        """Post an adaptive card to a channel.

        Graph wraps the card in a `body.contentType=html` envelope plus an
        `attachments` array referencing the card by ID.
        """
        attachment_id = "1"
        payload = {
            "subject": subject,
            "body": {
                "contentType": "html",
                "content": f'<attachment id="{attachment_id}"></attachment>',
            },
            "attachments": [
                {
                    "id": attachment_id,
                    "contentType": "application/vnd.microsoft.card.adaptive",
                    "contentUrl": None,
                    "content": str(adaptive_card).replace("'", '"'),
                    "name": None,
                    "thumbnailUrl": None,
                }
            ],
        }
        # Graph expects the card content as a JSON-encoded string. Use json.dumps
        # rather than str(...) repr to keep booleans / null correct.
        import json

        payload["attachments"][0]["content"] = json.dumps(adaptive_card)
        resp = self._http.post(
            f"/teams/{team_id}/channels/{channel_id}/messages",
            json=payload,
            headers=self._headers(),
        )
        return self._check(resp, 201)

    def close(self) -> None:
        self._http.close()
