"""Frappe app hooks for lcs_bizcard.

Minimal: the app contributes a www page (`/bizcard/scan`) and two
whitelisted API methods. Nothing else — no DocTypes, no doc_events,
no scheduler. Settings live in the bench's site_config.json under
`bizcard_scanner_url` (and optionally `bizcard_shared_token`).
"""

app_name = "lcs_bizcard"
app_title = "LCS Bizcard"
app_publisher = "LCS Group"
app_description = (
    "Standalone business-card scanner powered by a local Tesseract microservice. "
    "Embedded into Frappe CRM via iframe."
)
app_email = "it@lcs-group.com"
app_license = "proprietary"

# No website route override — the file at www/bizcard/scan/index.html
# is served automatically by Frappe at /bizcard/scan.
website_route_rules: list[dict[str, str]] = []
