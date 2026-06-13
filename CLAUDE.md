# CLAUDE.md — pilanda_sales

> Frappe-App im LCS-Pilanda-Stack für **Vertrieb / Sales** — LCS-spezifische
> Vertriebslogik rund um die Frappe-CRM-SPA (`/crm`). Läuft in der geteilten
> Pilanda-Bench (Site `lcs.local`, mehrere Apps). **Frühes Stadium** — Repo
> initialisiert, App-Code folgt via `bench new-app`.

## Modul im Stack
- Pilanda-Modul: **Vertrieb** (`modules_data.py`-Slug `vertrieb`, Navigationsziel `/crm`).
- Eigentum am Project-Objekt: **Vertriebs-/Sales-Felder**.
- Custom-Field-Namespace: **`custom_sales_`**.
- Hinweis: Die Vertriebs-Oberfläche IST die Frappe-CRM-SPA (3rd-party, via
  `chrome_injection` in die Pilanda-Hülle eingebettet). `pilanda_sales` ergänzt
  LCS-spezifische Logik/Felder/Reports — kein Nachbau von CRM.

## Stack-Konvention: das Project-Objekt (SSOT)

Alle `pilanda*`-Apps teilen sich **ein** Project-Objekt (ERPNext-Standard-DocType,
eine `tabProject`). Kein eigenes Projekt-DocType, keine kopierten Stammdaten, keine
doppelt definierten Custom Fields. Erweitern nur per Custom Field (als Code,
`after_migrate`, Präfix `custom_sales_`, **ein** Eigentümer je Feld). Termin-/Planungs-
felder gehören `pilanda_pm` (nur lesen). **Kanonische, verbindliche Regel:**
`pilanda/docs/conventions/project-object-ssot.md` (Repo `pilanda`) — dort
lesen/pflegen, nicht kopieren.

## Theme/CSS
Zentrale SSOT = App `pilanda_theme` (`--pp-*`-Tokens, `--pp-radius-ui`). Keine
nackten Hex/Radien — nur Tokens. Siehe `pilanda_theme/CLAUDE.md`.

## Hinweise
- Bench im Container: `docker exec pilanda-frappe bash -lc "cd /workspace/frappe-bench && bench --site lcs.local <cmd>"`.
- Teil des geteilten Stacks; nicht standalone installieren.
