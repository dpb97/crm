# CLAUDE.md — pilanda_sales

> Frappe-App im LCS-Pilanda-Stack für **Vertrieb / Sales** — LCS-spezifische
> Vertriebslogik rund um die Frappe-CRM-SPA (`/crm`). Teil der geteilten
> Pilanda-Bench (Site `lcs.local`, mehrere Apps) — nicht standalone. Root-Layout,
> auf `lcs.local` installiert; Aufbau läuft (Vertriebs-/Kalkulations-DocTypes).
> Aktueller Stand: `Entwicklungsplan.md`.

## Pilanda-Stack-Kontext (verbindlich)

- **Pilanda-Modul:** Vertrieb (`modules_data.py`-Slug `vertrieb`, Navigationsziel `/crm`).
- **Custom-Field-Namespace:** `custom_sales_` — Eigentum: Vertriebs-/Sales-Felder am Project.
- **Project-Objekt-SSOT:** EIN geteiltes Project (ERPNext-Standard, eine `tabProject`).
  Erweitern nur per Custom Field (als Code, `after_migrate`), ein Eigentümer je Feld.
  Kanonische Regel: `pilanda/docs/conventions/project-object-ssot.md` (Repo `pilanda`).
- **Theme/CSS-SSOT:** App `pilanda_theme` (`--pp-*`-Tokens, `--pp-radius-ui`). Keine nackten Hex/Radien.
- Hinweis: Die Vertriebs-Oberfläche IST die Frappe-CRM-SPA (3rd-party, via `chrome_injection` eingebettet); `pilanda_sales` ergänzt LCS-Logik/Felder/Reports — kein CRM-Nachbau.
- **Bench:** `docker exec pilanda-frappe bash -lc "cd /workspace/frappe-bench && bench --site lcs.local <cmd>"`.

## Verweise (SSOT)

Stack-weite Konventionen liegen kanonisch in den Heimat-Repos — `pilanda_sales`
*wendet* sie nur an, **verweist** und dupliziert nicht:

- **Design-System / CSS** (`--pp-*`-Tokens, `--pp-radius-ui`, Palette, Fonts,
  Hell/Dunkel) → `pilanda_theme/CLAUDE.md`. Keine nackten Hex/Radien.
- **Navigation / Shell + Git/Workflow** → `pilanda/CLAUDE.md`.
- **Project-Objekt-SSOT** → `pilanda/docs/conventions/project-object-ssot.md`.

## Stack-Eckdaten

- **Backend:** Python 3.11+ / Frappe Framework (v16), Frappe-ORM, MariaDB.
- **Auth:** Frappe-built-in-Auth (Standard im gesamten Stack).
- **Frontend:** Vue 3 + Vite für eigene Desk-Pages, sonst Frappe-UI (**kein React,
  kein Tailwind**). Vertriebs-UI ist primär die eingebettete Frappe-CRM-SPA;
  Styling ausschließlich über `pilanda_theme`-Tokens (`--pp-*`).
- **Repo-Layout = Root-Layout:** App-Paket + `pyproject.toml` im Repo-Root (wie
  `bench new-app`), **nicht** unter `src/<app>/`. Orientierung an bestehenden Apps
  (`pilanda_pm` etc.); Begründung in `README.md` + `pilanda/docs/ARCHITEKTUR-PILANDA.md`.
- **Geteilte Bench:** Docker/Setup/Deploy zentral in `pilanda_pm/_devenv` +
  `pilanda_pm/install.sh` — kein eigener `infrastructure/`-Ordner je App.

## Frappe-Konventionen

- Custom Fields am Project nur als Code via `after_migrate`, Präfix `custom_sales_`,
  ein Eigentümer je Feld (Project-Objekt-SSOT, siehe Verweise).
- DocTypes je Verzeichnis (Controller + JSON + Tests); `frappe.whitelist()` +
  `frappe.has_permission()` für jede API; keine String-konkatenierten SQL-Queries.
- Nach DocType-/JSON-Änderung `bench migrate`, nach Frontend-/Bundle-Änderung
  `bench build --app pilanda_sales`.

## Git-Workflow

SSOT in `pilanda/CLAUDE.md`. Kurz: Push nur auf `develop`; `main` für uns gesperrt;
Dominik zieht Geprüftes manuell nach `main`.

## Claude-Memory (zentral, stack-weit)

Claudes persistentes Gedächtnis liegt **zentral** in `pilanda_pm/.claude/memory/`
(in Git, SSOT) — auch wenn Claude aus *diesem* Repo gestartet wird, wird dort per
Junction gelesen/geschrieben. Dort pflegen, **nicht** lokal duplizieren. Setup an
einem neuen Gerät (einmalig): `pilanda_pm/.claude/memory/setup-memory-junction.ps1 -All`.
Details/Ablauf: `pilanda_pm/.claude/memory/JUNCTION-SETUP.md`.
