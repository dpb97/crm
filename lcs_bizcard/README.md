# lcs_bizcard

Frappe Custom App that hosts a **local** business-card scanner and
exposes it to the rest of the bench (Frappe CRM, ERPNext, …) as a
single embeddable URL.

```
CRM (Vue SPA)
  └─ <iframe src="/bizcard/scan?embed=1">
        ↓
     lcs_bizcard www page
        ├─ camera capture / file upload
        ├─ POST /api/method/lcs_bizcard.api.scan_card  (image_b64)
        │     ↓ proxies to →
        │   lcs-bizcard-scanner container (Tesseract, port 8089)
        ├─ user reviews fields
        └─ POST /api/method/lcs_bizcard.api.create_contact_from_scan
            → creates a Frappe Contact, posts result back via
              window.postMessage("lcs.bizcard.contact-created", ...)
```

No cloud calls. Everything OCR-related happens inside the local
docker network.

## Install

```bash
# 1) Start the OCR microservice
cd repo/docker/lcs-bizcard-scanner
docker compose up -d --build

# 2) Install the Frappe app
cd /home/dboeckle/frappe-bench
bench get-app /mnt/c/Users/d.boeckle/Dev/FrappeCRM/repo/lcs_bizcard
bench --site lcs.local install-app lcs_bizcard

# 3) Configure the scanner URL (defaults to http://host.docker.internal:8089)
bench --site lcs.local set-config bizcard_scanner_url http://localhost:8089
```

## Endpoints

| URL | Purpose |
|-----|---------|
| `/bizcard/scan` | Standalone scan UI — also the iframe target |
| `/api/method/lcs_bizcard.api.scan_card` | Image → parsed contact draft |
| `/api/method/lcs_bizcard.api.create_contact_from_scan` | Draft → Frappe Contact |
| `/api/method/lcs_bizcard.api.health` | Liveness probe forwarded to the scanner |

## Why a separate app

- **Reusable** — works for ERPNext leads, HR onboarding, anything that
  consumes Frappe `Contact`, not just CRM.
- **Updates decoupled** — upstream CRM upgrades don't touch this app.
- **Embed-first** — exposed by URL, not by Vue import, so any frontend
  can integrate it via `<iframe>` plus a 5-line `postMessage` handler.
