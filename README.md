# pilanda_sales

Frappe-App im **LCS-Pilanda-Stack** für **Vertrieb / Sales** — LCS-spezifische
Vertriebslogik rund um die Frappe-CRM-SPA (`/crm`). Teil der geteilten Pilanda-Bench
(Site `lcs.local`) — **nicht standalone**.

> **Frühes Stadium:** aus dem Org-Template initialisiert. Der eigentliche App-Code
> wird per `bench new-app pilanda_sales` **im Repo-Root** angelegt (Root-Layout,
> siehe unten).

## Pilanda-Stack-Kontext

- **Modul:** Vertrieb (`modules_data.py`-Slug `vertrieb`, Navigationsziel `/crm`)
- **Custom-Field-Namespace:** `custom_sales_` (Eigentum: Vertriebs-/Sales-Felder am Project)
- **Oberfläche:** die Vertriebs-UI **ist** die Frappe-CRM-SPA (3rd-party, via
  `chrome_injection` eingebettet); `pilanda_sales` ergänzt LCS-Logik/Felder/Reports —
  **kein** CRM-Nachbau, daher i. d. R. **kein** eigenes Vue-Frontend.
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
Bind-Mounts der Dev-Umgebung (`pilanda_pm/_devenv/docker-compose.dev.yml`, Repo-Root →
`apps/<name>`) und für `pilanda_pm/install.sh` (`pip install -e apps/<app>`). Ein
`src/`-Layout würde `bench get-app`, die Mounts und `install.sh` brechen. Setup,
Docker und Deploy liegen **zentral** in `pilanda_pm/_devenv` + `pilanda_pm/install.sh`
(eine geteilte Bench) — deshalb kein eigener `infrastructure/`-Ordner je App.

## Frontend

In der Regel **keines** — die Vertriebsoberfläche ist die eingebettete Frappe-CRM-SPA.
Falls doch eine eigene Desk-Page nötig wird: Vue 3 + Vite (analog `pilanda_pm/frontend`),
Optik nur über `pilanda_theme`-Tokens. (Das generische Org-Template nennt React —
im Pilanda-Stack gilt **Vue 3**, siehe `ARCHITEKTUR-PILANDA.md §6`.)

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
