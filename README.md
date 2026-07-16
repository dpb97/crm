# pilanda_sales

Frappe-App im **LCS-Pilanda-Stack** für **Vertrieb / Sales** — Angebotswesen
(Lastenheft → Kalkulation → Angebot), Vertriebs-Custom-Fields am Project und das
Vertrieb-Modul-Dashboard. Teil der geteilten Pilanda-Bench (Site `lcs.local`) —
**nicht standalone**. Maßgeblicher Status/Fahrplan: [`Entwicklungsplan.md`](Entwicklungsplan.md).

> **CRM:** Dominiks Frappe-CRM-Fork liegt als eigenständiger Branch
> `feature/unify-deal-project` in diesem Repo (keine gemeinsame Historie —
> Dominiks Hoheit, wird von uns nicht bearbeitet; Entscheid Marco 16.07.2026,
> s. Entwicklungsplan). Unsere Arbeit läuft ausschließlich auf `develop`.

## Pilanda-Stack-Kontext

- **Modul:** Vertrieb (`modules_data.py`-Slug `vertrieb`, **live** — Navigationsziel `/app/sales-dashboard`; Interessent/Verkaufschance → `/crm/leads`//`crm/deals`)
- **Custom-Field-Namespace:** `custom_sales_` (Eigentum: Vertriebs-/Sales-Felder am Project)
- **Oberfläche:** Modul-Dashboard `/app/sales-dashboard` (eigenes Vue-Frontend
  `frontend/`, Theme-Kopien `PpDashboard@1`/`PpDataGrid@3`) + die Frappe-CRM-SPA
  `/crm` (Dominiks Fork, `chrome_injection` liefert unsere Sidebar) —
  **kein** CRM-Nachbau in dieser App.
- **Project-Objekt-SSOT:** ein geteiltes ERPNext-`Project`; erweitern nur per Custom
  Field (als Code, `after_migrate`), ein Eigentümer je Feld. Regel:
  `pilanda/docs/conventions/project-object-ssot.md`.
- **Theme/CSS-SSOT:** `pilanda_theme` (`--pp-*`-Tokens, `--pp-radius-ui`).
- **Architektur-SSOT:** `pilanda/docs/ARCHITEKTUR-PILANDA.md`.

## Repo-Layout: Root-Layout (Pilanda-Standard)

Frappe-Apps im Pilanda-Stack liegen im **Root-Layout** — die Repo-Wurzel **ist** die
installierbare App, exakt wie `bench new-app` / `bench get-app` es erzeugen und
erwarten und wie es die bestehenden Apps (`pilanda_pm`, `pilanda_pls`,
`pilanda_resource`, `pilanda`, `pilanda_theme`) handhaben:

```
/
|-- pilanda_sales/                # App-Paket (Python-Modul)
|   |-- __init__.py
|   |-- hooks.py                  # app_name, doc_events, scheduler, fixtures
|   |-- modules.txt
|   |-- custom_fields.py          # custom_sales_* via after_migrate
|   |-- vertrieb/                 # Frappe-Modul (doctype/, report/, …)
|   |-- public/                   # statische Assets
|-- pyproject.toml                # im ROOT -> pip install -e .
|-- license.txt
|-- docs/                         # ADRs, Guides
|-- scripts/                      # app-spezifische Helfer
|-- tests/                        # zusätzliche Test-Suiten
|-- .claude/  .github/  .editorconfig  .gitignore  CLAUDE.md  README.md
```

**Kein `src/<app>/`-Layout, kein per-App `infrastructure/`.** Begründung: `bench
get-app <url>` klont das Repo nach `apps/<name>` und führt `pip install -e` aus — das
setzt `pyproject.toml` + App-Paket im **Repo-Root** voraus. Dasselbe gilt für die
Bind-Mounts der Dev-Umgebung (`pilanda/_devenv/docker-compose.dev.yml`, Repo-Root →
`apps/<name>`) und für `pilanda/install.sh` (`pip install -e apps/<app>`). Ein
`src/`-Layout würde `bench get-app`, die Mounts und `install.sh` brechen. Setup,
Docker und Deploy liegen **zentral** in `pilanda/_devenv` + `pilanda/install.sh`
(eine geteilte Bench) — deshalb kein eigener `infrastructure/`-Ordner je App.

## Frontend

`frontend/` (Vue 3 + Vite, IIFE-Bundle `sales_dashboard` → `public/dist`,
gitignored — Build: `cd frontend && npm run build`). Optik ausschließlich über
`pilanda_theme`-Tokens/Kopien (Copy-Modell, PP_REV). Die CRM-SPA selbst ist
Dominiks Fork und wird hier nicht gebaut.

## Git-Workflow

`develop` → Review (Dominik) → `main`. Feature-Branches `feature/<ticket>-<kurz>`,
Conventional Commits, PR-Pflicht. Nicht direkt auf `main`/`develop` pushen.

## Erste Schritte (App scaffolden)

```bash
# in der laufenden Pilanda-Bench (Container pilanda-frappe)
cd /workspace/frappe-bench
bench new-app pilanda_sales                       # erzeugt Root-Layout
bench --site lcs.local install-app pilanda_sales
```

Anschließend die App in `pilanda_pm/_devenv/docker-compose.dev.yml` (Bind-Mount) und
`pilanda_pm/install.sh` (`get_app`/`install_app` + pip-Loop) verdrahten — siehe dortige
Muster der fünf bestehenden Apps.
