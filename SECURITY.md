# Security Policy

## Reporting a vulnerability

Report security issues privately to **security@lcs-cable-cranes.com**. We
acknowledge within 48 h (Europe/Vienna business hours). Please do **not**
open public GitHub issues for security findings.

When reporting, please include:

- affected component (crm / lcs_integrations / infra)
- reproduction steps
- observed vs expected behaviour
- any proof-of-concept payload / request

We will confirm receipt, scope the impact, and work with you on a
coordinated disclosure. We do not currently run a bug bounty, but we credit
reporters in release notes unless anonymity is requested.

## Supported versions

| Branch    | Status                              |
| --------- | ----------------------------------- |
| `main`    | Supported — receives security fixes |
| `develop` | Supported for preview deployments    |
| `feature/*`, `release/*`, `hotfix/*` | Short-lived; merge to `develop` / `main` for fixes |

## Automated controls

- **CodeQL** — `python` + `javascript-typescript` queries, `security-and-quality` pack, on every PR to `main` / `develop` and weekly.
- **Trivy** — container vulnerability scan; CRITICAL + HIGH fail the pipeline.
- **Dependabot** — weekly pip / npm / GitHub-Actions / Docker updates.
- **Commitlint** — every PR enforces Conventional Commits.
- **Branch protection** — no direct pushes to `main` / `develop`; PRs require green CI + 1 approval.

## Secret management

- Never commit secrets; `.env` is gitignored. Production pulls secrets from
  **Azure Key Vault** and injects them as container environment variables.
- HMAC / OAuth client secrets rotate on the schedule documented in
  [`docs/operations/entra-app-registration.md`](docs/operations/entra-app-registration.md).

## Transport & authentication

- All external services are TLS-only.
- Inbound webhooks (abas) require HMAC-SHA256 with a 300-second timestamp skew window; see [`lcs_integrations/abas/client.py::verify_inbound`](lcs_integrations/lcs_integrations/abas/client.py).
- Outbound calls to abas carry the same HMAC signature; to Microsoft Graph and Proxess, OAuth2 bearer tokens via MSAL / client_credentials.
- User authentication is Microsoft Entra OIDC only; local Frappe passwords are disabled on production sites per [ADR 0003](docs/adr/0003-msal-oidc.md).
