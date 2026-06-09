"""
Speech-to-text backend bridge.

The frontend `VoiceInput.vue` component uses the browser's Web Speech API
by default. When an admin enables the Azure backend in
`LCS Speech Settings`, we expose a short-lived auth token here so the
SPA can call Azure's Cognitive Services Speech endpoint directly —
this keeps audio out of our backend while still letting us:

- Gate which users can use the premium backend (via permission layer)
- Centrally rotate the Azure subscription key
- Enforce custom vocabulary / phrase lists for LCS-specific terms

Token is a 10-minute auth token issued by Azure per IP — we cache it
in Redis and reissue when it expires.
"""

import frappe
import requests
from datetime import datetime, timedelta


TOKEN_TTL_SEC = 9 * 60  # Azure tokens are valid for 10 minutes; refresh a minute early


@frappe.whitelist()
def get_speech_config() -> dict:
    """Return configuration the frontend needs to pick a backend.

    Response shape:
      {
        "backend": "webspeech" | "azure",
        "languages": ["de-DE", "en-US", ...],     # supported by the selected backend
        "azure": {                                # only if backend=azure
          "region": "westeurope",
          "token": "eyJ...",                      # 10-min auth token
          "token_expires_at": "2026-04-21T10:00:00",
          "phrase_list": ["Seilbahn", "Richtpreis", ...]   # custom vocabulary
        }
      }
    """
    # Load settings, but fall back gracefully to webspeech when anything is missing
    if not frappe.db.exists("DocType", "LCS Speech Settings"):
        return {"backend": "webspeech", "languages": _default_languages()}

    settings = frappe.get_single("LCS Speech Settings")
    if not settings.enabled or settings.backend != "Azure Cognitive Services":
        return {"backend": "webspeech", "languages": _default_languages()}

    if not settings.azure_region or not settings.azure_subscription_key:
        return {"backend": "webspeech", "languages": _default_languages()}

    try:
        token, expires_at = _get_or_issue_azure_token(settings)
    except Exception as e:
        frappe.log_error(f"Azure token issuance failed: {e}", "speech.api")
        return {"backend": "webspeech", "languages": _default_languages()}

    return {
        "backend": "azure",
        "languages": _default_languages(),
        "azure": {
            "region": settings.azure_region,
            "token": token,
            "token_expires_at": expires_at.isoformat(),
            "phrase_list": _phrase_list(settings),
        },
    }


def _get_or_issue_azure_token(settings) -> tuple[str, datetime]:
    """Return a cached token from Redis if still valid, else issue a new one."""
    cache_key = f"azure_speech_token:{settings.azure_region}"
    cached = frappe.cache().get_value(cache_key)
    if cached and cached.get("expires_at"):
        exp = datetime.fromisoformat(cached["expires_at"])
        if exp > datetime.now() + timedelta(seconds=60):
            return cached["token"], exp

    # Issue fresh token via Azure
    url = f"https://{settings.azure_region}.api.cognitive.microsoft.com/sts/v1.0/issueToken"
    headers = {"Ocp-Apim-Subscription-Key": settings.get_password("azure_subscription_key")}
    r = requests.post(url, headers=headers, timeout=10)
    r.raise_for_status()
    token = r.text
    expires_at = datetime.now() + timedelta(seconds=TOKEN_TTL_SEC)
    frappe.cache().set_value(
        cache_key,
        {"token": token, "expires_at": expires_at.isoformat()},
        expires_in_sec=TOKEN_TTL_SEC,
    )
    return token, expires_at


def _default_languages() -> list[str]:
    """Common locales for LCS — four markets the sales team operates in."""
    return ["de-DE", "en-US", "it-IT", "fr-FR"]


def _phrase_list(settings) -> list[str]:
    """LCS-specific vocabulary that generic STT models recognize poorly.

    Admin can override via the Settings DocType; otherwise the built-in
    list below is used.
    """
    custom = getattr(settings, "custom_phrases", None)
    if custom:
        return [p.strip() for p in custom.splitlines() if p.strip()]
    return [
        # Project types
        "Seilbahn", "Seilbahnanlage", "Winde", "Liftanlage", "Sonderkonstruktion",
        # Pricing stages
        "Richtpreis", "Budget", "Angebot",
        # Project phase vocabulary
        "Inquiry", "Anfrage", "Angebot", "Verhandlung", "Auftrag", "Ausführung",
        # LCS-specific
        "LCS", "Cable Crane", "Baustelle",
        # Common customer-facing terms
        "Seilbahn Inspektion", "Windenprüfung", "Abnahmeprotokoll",
    ]
