"""FastAPI entrypoint for the LCS business-card OCR microservice.

Endpoints:
  GET  /healthz       -> liveness probe (no auth)
  POST /scan          -> multipart image -> structured contact
  POST /scan-base64   -> JSON {image_base64} -> structured contact

The service is intentionally minimal: it does OCR + heuristic field
extraction, and optionally a small LLM polish pass when configured.
No data is persisted; the response is the only output.

Auth: shared-secret header `X-LCS-Token` if the environment variable
`SHARED_TOKEN` is set; otherwise open (intended for a private docker
network).
"""

from __future__ import annotations

import base64
import io
import os
from typing import Optional

from fastapi import FastAPI, File, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .ocr import run_ocr
from .parser import parse_card_text
from .polish import polish_with_llm


MAX_UPLOAD = int(os.getenv("MAX_UPLOAD_BYTES", str(5 * 1024 * 1024)))
SHARED_TOKEN = os.getenv("SHARED_TOKEN") or ""


app = FastAPI(title="LCS Bizcard Scanner", version="1.0.0")

# CORS for the Frappe bench origin. The compose ENV can override
# ALLOWED_ORIGINS when needed.
app.add_middleware(
    CORSMiddleware,
    allow_origins=(os.getenv("ALLOWED_ORIGINS") or "*").split(","),
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "X-LCS-Token"],
)


class ScanRequest(BaseModel):
    image_base64: str
    mime_type: Optional[str] = "image/jpeg"


class ScanResponse(BaseModel):
    first_name: str = ""
    last_name: str = ""
    company_name: str = ""
    designation: str = ""
    email_id: str = ""
    mobile_no: str = ""
    phone: str = ""
    website: str = ""
    address: str = ""
    raw_text: str = ""
    engine: str = "tesseract"
    polished: bool = False
    confidence: float = 0.0


def _check_token(token: Optional[str]) -> None:
    if not SHARED_TOKEN:
        return
    if not token or token != SHARED_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid X-LCS-Token")


def _process(image_bytes: bytes) -> ScanResponse:
    if len(image_bytes) > MAX_UPLOAD:
        raise HTTPException(status_code=413, detail="Image too large")

    ocr_result = run_ocr(image_bytes)
    parsed = parse_card_text(ocr_result.text)
    parsed["raw_text"] = ocr_result.text
    parsed["confidence"] = ocr_result.confidence

    polished = polish_with_llm(parsed)
    if polished is not None:
        parsed.update(polished)
        parsed["polished"] = True

    return ScanResponse(**parsed)


@app.get("/healthz")
def healthz() -> dict:
    return {
        "status": "ok",
        "ocr": "tesseract",
        "polish_backend": os.getenv("POLISH_BACKEND", "none"),
    }


@app.post("/scan", response_model=ScanResponse)
async def scan_multipart(
    file: UploadFile = File(...),
    x_lcs_token: Optional[str] = Header(None),
) -> ScanResponse:
    _check_token(x_lcs_token)
    image_bytes = await file.read()
    return _process(image_bytes)


@app.post("/scan-base64", response_model=ScanResponse)
async def scan_base64(
    req: ScanRequest,
    x_lcs_token: Optional[str] = Header(None),
) -> ScanResponse:
    _check_token(x_lcs_token)
    try:
        image_bytes = base64.b64decode(req.image_base64)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid base64: {e}")
    return _process(image_bytes)
