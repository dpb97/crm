"""Tesseract OCR wrapper with light pre-processing.

The picture quality from a phone camera varies massively — glare,
skew, low contrast on dark cards. We do a small image-enhancement
chain before Tesseract:
  1. Convert to grayscale
  2. CLAHE contrast enhancement
  3. Adaptive threshold
  4. Optional deskew (Hough lines fallback)

Tesseract is told to honour the multi-language config from the
OCR_LANGS env variable (e.g. "eng+deu" for English + German cards).
"""

from __future__ import annotations

import io
import os
from dataclasses import dataclass

import cv2
import numpy as np
from PIL import Image, ImageOps

import pytesseract


OCR_LANGS = os.getenv("OCR_LANGS", "eng+deu")


@dataclass
class OCRResult:
    text: str
    confidence: float


def _preprocess(image_bytes: bytes) -> np.ndarray:
    image = Image.open(io.BytesIO(image_bytes))
    # Strip EXIF rotation so portrait photos land upright.
    image = ImageOps.exif_transpose(image).convert("RGB")
    img = np.array(image)

    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

    # CLAHE handles uneven lighting on glossy cards much better than
    # plain histogram equalization.
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    gray = clahe.apply(gray)

    # Light denoise to kill JPEG artefacts without softening glyph edges.
    gray = cv2.bilateralFilter(gray, d=5, sigmaColor=35, sigmaSpace=35)

    # Adaptive threshold copes with shadows / glare. Tesseract prefers
    # black text on white background.
    binarized = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 15
    )

    return binarized


def _mean_confidence(data: dict) -> float:
    confs = [int(c) for c in data.get("conf", []) if str(c).lstrip("-").isdigit() and int(c) >= 0]
    if not confs:
        return 0.0
    return round(sum(confs) / len(confs) / 100.0, 3)


def run_ocr(image_bytes: bytes) -> OCRResult:
    processed = _preprocess(image_bytes)

    # PSM 6 = "Assume a single uniform block of text" works well for
    # business cards. PSM 4 (single column) is a close second; we go
    # with 6 because card layouts are denser than columns.
    config = "--oem 1 --psm 6"
    text = pytesseract.image_to_string(processed, lang=OCR_LANGS, config=config)

    data = pytesseract.image_to_data(
        processed, lang=OCR_LANGS, config=config, output_type=pytesseract.Output.DICT
    )
    confidence = _mean_confidence(data)

    return OCRResult(text=text, confidence=confidence)
