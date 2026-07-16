# LCS CRM — adaptation of `frappe/crm`

> **Repo-Einordnung (Pilanda-ERP/pilanda_sales):** Dieses Repo ist die
> Pilanda-Vertriebs-App und enthält seit PR #13 (16.07.2026, Merge
> `9150ff62`) **zwei App-Pakete**: `pilanda_sales/` (Angebotswesen
> Lastenheft → Kalkulation → Angebot + Vertrieb-Dashboard; maßgeblicher
> Status/Fahrplan: [`Entwicklungsplan.md`](Entwicklungsplan.md)) und
> `crm/` (Dominiks Frappe-CRM-Fork — dieser Doc beschreibt IHN). Das
> Root-`README.md` ist bewusst das unveränderte Upstream-README (billige
> Upstream-Merges). Stack-Kontext: [`CLAUDE.md`](CLAUDE.md).

This fork adapts [Frappe CRM](./README.md) to LCS Cable Cranes' needs:
MSAL / Entra SSO, bidirectional abas ERP sync, Outlook mail delta sync,
Proxess DMS integration, and rule-driven lead scoring.

The upstream `frappe/crm` code is untouched to keep merges cheap; everything
LCS-specific lives in a separate Frappe app (`lcs_integrations/`) plus infra
files under `docker/`, `scripts/`, `docs/`, `e2e/`.

---

## What is different from upstream

| Area          | Upstream                               | LCS adaptation                                                |
| ------------- | -------------------------------------- | ------------------------------------------------------------- |
| Database      | MariaDB                                | **PostgreSQL 16** — see [ADR 0002](docs/adr/0002-postgres-over-mariadb.md) |
| Auth          | Local password / any Social Login      | **Microsoft Entra** (OIDC) — see [ADR 0003](docs/adr/0003-msal-oidc.md) |
| Runtime       | Bench on bare metal                    | Docker multi-stage, non-root, Alpine — `docker/Dockerfile`     |
| Extra DocTypes| —                                      | `ABAS Sync Log`, `ABAS Entity Map`, `Proxess Document Link`, `Outlook Mailbox Binding`, `Lead Scoring Rule` |
| CI            | `server-tests.yml`, `linters.yml`       | + CodeQL, Trivy, dependabot, LCS PR template, commitlint      |
| E2E           | —                                      | Playwright smoke suite in `e2e/`                               |
| Styling       | frappe-ui defaults                     | Tailwind theme extension with LCS palette + 3 Vue components   |

## Repo layout

```
repo/
├── crm/                     # ← upstream Frappe app (do not modify)
├── frontend/                # ← upstream Vue SPA (additive Tailwind + components)
│   └── src/components/lcs/  # ← LCS-only Vue components + vitest specs
├── lcs_integrations/        # ← LCS Frappe app (all business logic)
│   ├── lcs_integrations/
│   │   ├── abas/            # abas ERP client + service + schemas
│   │   ├── outlook_sync/    # Microsoft Graph delta sync
│   │   ├── proxess/         # Proxess DMS client + service
│   │   ├── email_domain_autolink/
│   │   ├── msal_sso/        # Entra Social Login Key installer
│   │   ├── lead_scoring/    # rule engine + doc-event hook
│   │   ├── doctype/         # 5 custom DocTypes (json + py)
│   │   └── patches/v1_0/    # custom-field migration
│   └── tests/               # pytest (framework-free)
├── docker/                  # Dockerfile + compose + nginx
├── scripts/
│   └── bootstrap_wsl.sh     # one-shot WSL2 dev env
├── docs/
│   ├── adr/                 # architecture decision records
│   └── architecture/        # C4 + sequence diagrams (mermaid)
├── e2e/                     # Playwright smoke tests
└── .github/
    ├── workflows/lcs-*.yml  # CodeQL · Trivy · LCS CI
    ├── dependabot.yml
    └── pull_request_template.md
```

## Getting started (WSL 2)

```bash
# Clone outside /mnt/* — filesystem perf is >10× better under $HOME
git clone https://github.com/dpb97/crm.git ~/lcs-crm
cd ~/lcs-crm
./scripts/bootstrap_wsl.sh   # Python 3.12, Node LTS, bench, Postgres site
bench start                  # serves http://localhost:8000
```

## Testing

| Layer      | Command                                       | Gate             |
| ---------- | --------------------------------------------- | ---------------- |
| Python     | `cd lcs_integrations && pytest`               | Coverage ≥ 80 %  |
| Vue        | `cd frontend && yarn test:coverage`           | Coverage ≥ 80 % on `components/lcs/**` |
| E2E        | `cd e2e && yarn test`                         | Smoke green      |
| Containers | CI: `docker build . && trivy image`           | 0 CRITICAL/HIGH  |

## Documentation

- **Why** — start with [architecture overview](docs/architecture/overview.md) and the [ADRs](docs/adr/).
- **How** — per-integration sequence diagrams under [`docs/architecture/`](docs/architecture/):
  - [abas](docs/architecture/abas-integration.md)
  - [Outlook mail sync](docs/architecture/outlook-sync.md)
  - [Proxess DMS](docs/architecture/proxess-dms.md)
  - [Lead scoring](docs/architecture/lead-scoring.md)

## Branch model & conventions

- **GitFlow**: `main` / `develop` / `feature/*` / `release/*` / `hotfix/*`
- **Commits**: [Conventional Commits](https://www.conventionalcommits.org/) — enforced via commitlint in CI
- **PRs**: fill the [template](.github/pull_request_template.md) completely
- **Dependencies**: weekly Dependabot PRs, Tuesday bench triage

## Secrets & config

Never commit secrets. Local: `.env` (gitignored). CI / prod: Azure Key Vault.
Required environment variables per connector:

| Connector        | Required env                                                                 |
| ---------------- | ---------------------------------------------------------------------------- |
| abas             | `ABAS_BASE_URL`, `ABAS_HMAC_KEY`                                             |
| Outlook (Graph)  | `GRAPH_TENANT_ID`, `GRAPH_CLIENT_ID`, `GRAPH_CLIENT_SECRET`                  |
| Proxess          | `PROXESS_BASE_URL`, `PROXESS_CLIENT_ID`, `PROXESS_CLIENT_SECRET`             |
| Entra SSO        | `ENTRA_TENANT_ID`, `ENTRA_CLIENT_ID`, `ENTRA_CLIENT_SECRET`                  |

## Support matrix

| Component     | Version                  |
| ------------- | ------------------------ |
| Python        | 3.12                     |
| Node.js       | 20 LTS                   |
| PostgreSQL    | 16-alpine                |
| Frappe        | ≥ 15, < 17 (dev)         |
| Vue           | 3.5                      |
| Tailwind      | 3.4                      |
