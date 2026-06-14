# docs/guides -- Developer Guides

Onboarding documentation, how-to guides, and development workflows.

## What Belongs Here

| File                        | Purpose                                    |
|-----------------------------|--------------------------------------------|
| `getting-started.md`        | First-time setup for new developers        |
| `development-workflow.md`   | Daily development process and tools        |
| `frappe-patches.md`         | How to create and apply Frappe patches     |
| `doctype-guide.md`          | How to create and customize DocTypes       |
| `testing-guide.md`          | Testing strategy, running tests, coverage  |
| `deployment-guide.md`       | How to deploy to each environment          |
| `vue-frontend-guide.md`     | Setting up and developing Vue 3 pages      |
| `troubleshooting.md`        | Common issues and solutions                |

> Pilanda-Hinweis: Die geteilte Dev-/Docker-Umgebung liegt zentral in
> `pilanda_pm/_devenv`; Setup/Install via `pilanda_pm/install.sh` (Root-Layout,
> siehe Repo-`README.md` + `pilanda/docs/ARCHITEKTUR-PILANDA.md`). Die
> Vertriebs-UI ist primär die eingebettete Frappe-CRM-SPA.

## Getting Started (Quick Reference)

### Prerequisites

- Python 3.11+
- Node.js 18+ (für Vite/Vue-Frontend-Build, falls eigene Desk-Page)
- MariaDB 10.6+
- Redis 7+
- IDE: VS Code mit Python + Pylance
- Docker (Pilanda-Dev läuft containerisiert, Container `pilanda-frappe`)

### Daily Workflow

```bash
# Bench läuft im Container pilanda-frappe
docker exec pilanda-frappe bash -lc "cd /workspace/frappe-bench && bench start"

# Nach dem Pullen
bench --site lcs.local migrate
bench build --app <app>

# Neue DocType: Frappe-UI unter /app/doctype/new

# Tests
bench --site lcs.local run-tests --app <app>
```

### Feature-Ablauf

1. Aktuellen `develop` pullen
2. Feature-Branch: `feature/<ticket>-<description>`
3. Tests zuerst (TDD)
4. Feature umsetzen
5. Alle Tests: `bench --site lcs.local run-tests --app <app>`
6. Push + PR auf `develop` (Review Dominik)
