"""Optional LLM polish step.

When `POLISH_BACKEND=ollama` and an Ollama server reachable at
`OLLAMA_URL` runs `OLLAMA_MODEL`, we feed it the raw OCR text plus
the heuristic parse and ask for corrections — mostly to recover
names that lost their second token to OCR noise, or to split
"Company AG · 1010 Vienna" into company + address.

Default backend `none` makes this a no-op so the service stays
fully offline and deterministic.
"""

from __future__ import annotations

import json
import os
from typing import Optional

import httpx


BACKEND = (os.getenv("POLISH_BACKEND") or "none").lower()
OLLAMA_URL = os.getenv("OLLAMA_URL") or "http://host.docker.internal:11434"
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL") or "qwen2.5:3b"

_PROMPT_TEMPLATE = """\
You receive raw OCR text from a business card plus a heuristic JSON parse.
Correct obvious mistakes (mis-split names, salutations stuck to company,
city/postal accidentally on the company line). Keep values empty when
unsure. Reply with ONLY a JSON object using the same keys as input.

OCR text:
\"\"\"
{ocr_text}
\"\"\"

Heuristic parse:
{heuristic}
"""


_KEYS = (
    "first_name", "last_name", "company_name", "designation",
    "email_id", "mobile_no", "phone", "website", "address",
)


def polish_with_llm(parsed: dict) -> Optional[dict]:
    if BACKEND != "ollama":
        return None

    raw_text = parsed.get("raw_text") or ""
    heuristic = {k: parsed.get(k, "") for k in _KEYS}

    prompt = _PROMPT_TEMPLATE.format(
        ocr_text=raw_text[:2000],
        heuristic=json.dumps(heuristic, ensure_ascii=False),
    )

    try:
        with httpx.Client(timeout=15.0) as client:
            r = client.post(
                f"{OLLAMA_URL.rstrip('/')}/api/generate",
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json",
                    "options": {"temperature": 0.0},
                },
            )
            r.raise_for_status()
            body = r.json()
    except Exception:
        # Polish is best-effort: a failed LLM call must not break the scan.
        return None

    response_text = body.get("response") or ""
    try:
        polished = json.loads(response_text)
    except json.JSONDecodeError:
        return None

    out = {}
    for k in _KEYS:
        v = polished.get(k)
        if isinstance(v, str) and v.strip():
            out[k] = v.strip()
    return out or None
