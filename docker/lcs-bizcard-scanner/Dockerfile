# Local business-card OCR service for LCS CRM.
#
# Tesseract-only by default — fully offline, ~200 MB image. The LLM
# polish path (`POLISH_BACKEND=ollama`) is optional and reaches out to
# an Ollama instance on the same host network at runtime.
#
# No model weights are baked into the image; languages are installed
# from Debian packages (eng, deu — extend OCR_LANGS in the compose
# file when you need more).

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
        tesseract-ocr \
        tesseract-ocr-eng \
        tesseract-ocr-deu \
        libgl1 \
        libglib2.0-0 \
        ca-certificates \
        curl \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY app /app/app

# Non-root for safety. The slim image already provides `nobody:nogroup`,
# but a dedicated user is cleaner for log filtering.
RUN useradd --create-home --shell /bin/false bizcard
USER bizcard

EXPOSE 8089
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD curl -fsS http://localhost:8089/healthz || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8089"]
