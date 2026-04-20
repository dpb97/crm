"""Thin wrapper around Microsoft Graph mail endpoints.

Uses MSAL for token acquisition. We only need a handful of endpoints — no
reason to pull in the heavy `msgraph-sdk` package.
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

    def messages_delta(self, user_principal: str, delta_link: str | None = None) -> dict[str, Any]:
        """Return a page of message delta for the given mailbox."""
        headers = {"Authorization": f"Bearer {self._bearer()}", "Prefer": "odata.track-changes"}
        if delta_link:
            resp = self._http.get(delta_link, headers=headers)
        else:
            resp = self._http.get(f"/users/{user_principal}/mailFolders/Inbox/messages/delta",
                                  headers=headers)
        if resp.status_code >= 400:
            raise GraphClientError(f"Graph HTTP {resp.status_code}: {resp.text[:500]}")
        return resp.json()

    def close(self) -> None:
        self._http.close()
