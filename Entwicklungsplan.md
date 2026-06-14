# Entwicklungsplan — pilanda_sales (Vertrieb)

> Stand: 14.06.2026 · v0.1 · verbindliche Arbeitsgrundlage für dieses Repo.
> **Übergeordnet (nicht duplizieren, referenzieren):**
> - Spezifikationspaket: `C:\CoWork\Pilanda\ImportzuPILANDA\` — Architektur (01),
>   Objektmodell (02), Master-Entwicklungsplan (03), Dossiers 10–15, Datenimport (20),
>   **Entscheidungs-Log (99, E-1…E-29 = höchste Wahrheitsinstanz)**.
> - Stack-Architektur: `pilanda/docs/ARCHITEKTUR-PILANDA.md`.
> - Project-Objekt-SSOT: `pilanda/docs/conventions/project-object-ssot.md`.
>
> **Konfliktregel:** 99 (E-/K) > 02/03 > Dossiers 10–15 > 04 (Ist-Stand Prototyp).
> **Wahrheit ist Pflicht:** nichts raten; Unklares als [OFFEN] kennzeichnen, nicht bauen.

## 1. Auftrag dieses Repos

`pilanda_sales` baut aus Oswalds Prototyp (read-only Referenz, **kein Code-Port**) das
kaufmännische Angebotswesen nach: **Questionnaire/Lastenheft → Kalkulation → Angebot**
(+ Pricing Sheet/LV, Pflichtenheft). **Alle Berechnungen im Python-Backend** [E-5];
Vue zeigt nur an. Beweis der Formeln per **Golden-Master** gegen Referenzquote
`03c6eb4dfc` [03 §5.1].

- **App-Modul:** `Vertrieb` (eine Frappe-Module). Darin die **vier Bereiche**
  CRM · Questionnaire · Kalkulation · Angebot. **CRM liefert Dominik** (eigener,
  klar abgegrenzter Bereich → minimiert Merge-Konflikte). Übergabe sales an Dominik,
  sobald Marcos Teil + Projektierung zusammenstimmen.
- **Custom-Field-Namespace:** `custom_sales_` (kaufmännische Project-/Item-Felder).
- **Liest, definiert NICHT:** freigegebene Anlagenkonfiguration aus
  `pilanda_projectengineering`; Phasen/Dauern aus `pilanda_pm`.

## 2. Verbindliche Entscheidungen (für dieses Repo relevant)

| # | Entscheidung | Quelle |
|---|---|---|
| 1 | Backend rechnet alles, Vue zeigt nur | E-5/E-14 |
| 2 | Formeln 1:1 aus Dossier 11, Golden-Master gegen `03c6eb4dfc` | 03 §5.1 |
| 3 | Sätze/Prozente **3-stufig**, **zentral pro Projekt** user-editierbar, sichtbarer Default (z. B. 3 %); Reset möglich | E-2/E-14 (Marco 14.06.) |
| 4 | Prozent = `Percent` (5 = 5 %); Prototyp-Brüche beim Import ×100 | E-25 |
| 5 | Intern EUR-Master; Kurs am Projekt; Snapshot friert Kurs ein | E-8 |
| 6 | Technische Namen Englisch; Labels DE/EN | E-26 |
| 7 | Snapshot je Angebotsversion = **JSON-Beleg** (read-only) | E-27 |
| 8 | Status/Freigabe = Frappe-Workflow; Revisionen = Submit/Amend | E-23/E-24 |
| 9 | K-Artikel = eigener, nicht-dispofähiger DocType (K-Präfix) | E-22/E-17 |
| 10 | PILANDA startet leer; Referenzquote nur Test-Fixture | E-18 |
| 11 | Project = ERPNext-SSOT, nur per `custom_sales_`-Custom-Field erweitern | E-21/E-28 |

## 3. Phasen (repo-scoped; Nummern = Master-Plan 03)

### Phase 1 — Datenmodell-Fundament  ·  Aufwand M  ·  **AKTIV**
| AP | Inhalt | Akzeptanz |
|---|---|---|
| 1.1 | **Project-Custom-Fields** (`custom_sales_…`) via `custom_fields.py` + `after_migrate`; ERPNext-Standardfelder zuerst nutzen (02 §2.1) | Felder idempotent angelegt; `migrate` grün; Liste abgenommen |
| 1.2 | **DocType `Projektvariante`** (Link → Project, Kran-Child-Table, Vertragsart, ist_gewinner) (02 §2.2) | anlegbar; ein Projekt n Varianten |
| 1.3 | **K-Artikel** (eigener DocType, K-Präfix, nicht dispofähig, Preis-Zusammensetzung-Child, ziel_item) (02 §2.3b) | anlegbar; kann Item + K-Artikel als Baugruppe referenzieren |
| 1.4 | **Feldkatalog** (+ Feld/Sektion/Option/Companion + Versionierung) (02 §2.4) | Katalog-V1 (106 Felder, Dossier 10 §2) als Fixture/Seed; Version abfragbar |
| 1.5 | **kaufm. Item-Custom-Fields** (`custom_sales_…`: cn_nummer (passiv, B-4), board-Kategorie, N/E/A/S-Preise, Tagessätze, Flags, AfA, Invest-Klasse) (02 §2.3a) | Felder am Item; Validierung |
| 1.6 | Rollen-Grundgerüst (Verkäufer/Projektant/PM/VL/Stammdatenpflege) | Rechte-Matrix |

**Rechte-Matrix (1.6, Grundgerüst — Domänen-Rollen via `pilanda_sales.seed.roles.seed_roles`):**

| Rolle | Schwerpunkt | Schreibhoheit (Objekte) |
|---|---|---|
| **Verkäufer** | Anfrage → Angebot | Project/Variante, Lastenheft, Kalkulation, Angebot, K-Artikel; Anlagenkonfiguration *befüllen* (NICHT freigeben) |
| **Projektant** | Technik-Freigabe | Anlagenkonfiguration (Freigabe = Submit), technische Item-Felder |
| **Vertriebsleitung** (VL) | Angebots-Freigabe | verbindliche Angebote ab Schwelle (E-19) |
| **Projects Manager** (PM, ERPNext-Standard) | Plan/Phasen | `pilanda_pm` |
| **Technik-Stammdaten** | Stammdatenpflege | Item, Seil-Matrix, Machine Configuration, Field Catalog |

Detail-Rechte je DocType werden mit dem jeweiligen Objekt/Workflow gesetzt (Phasen 3–6);
die bestehenden DocTypes tragen vorerst die Standard-Perms (System Manager / Projects Manager / Projects User).

### Phase 2 — Datenimport (Stammdaten)  ·  M  ·  parallel zu 3
Quellen + Reihenfolge: Paket `20_DATENIMPORT.md`. Item-DB (222, CN passiv), Board-/
Markup-Defaults, kleine Kataloge, Textbaustein-Bibliothek. **Wahrheits-Gate:**
jeder Import erzeugt Abgleichsprotokoll (Quelle vs. importiert). **Braucht** lesenden
Zugriff auf den Prototyp-Ordner (`C:\CoWork\Pilanda\Questionaire`) — erst hier nötig.

### Phase 3 — Questionnaire/Lastenheft  ·  L
Lastenheft-DocType + Ableitungsregeln (leer überschreibt nie), Portal-Wizard (Vue,
Token, Companion-Logik), PDF-Generator + Rück-Import aus **einem** Feldkatalog,
Datei-Anhänge (echte Files), International-Felder nachziehen (E-16). Dossier 10.

### Phase 5 — Kalkulation: der Rechenkern  ·  XL  ·  Herzstück
Python-Rechenkern (UI-frei), **alle** Formeln aus Dossier 11: Equipment HK/VK +
Overrides, Seil-HK, VK-Cascade (8 Stufen, 3 Gross-ups), N/E/A/S, Phasen (Manpower +
`_sideBreak`), Commission, WHT, Import Duties, Financing (Auto-Basen, azyklisch),
Buyback (+Degression), AfA/PMT. **Golden-Master** gegen `03c6eb4dfc`. Kalkulations-
DocType + Kostenübersicht (13 Spalten). Inkonsistenz-Entscheide VOR Code (Dossier 11
§OFFEN 11 a–f). Multi-Varianten sauber statt Prototyp-Vollkopien.

### Phase 6 — Angebot  ·  L
Angebot + Angebotsversion (JSON-Snapshot), DOCX-Commercial (17 Sektionen) + TEPRO
(48), Namensschema, Budget-Fastpath vs. Verbindlich (Workflow-Gate), **Pricing
Sheet/LV** (Zuordnung Kalk→LV 1:1, Summenprüfung Pflicht), Pflichtenheft (F-15,
später). Dossier 13.

### Phase 7 — PM-Anbindung / Ausbau
Phasen/Dauern aus `pilanda_pm`; Payment-Terms/Cashflow (B-3, nach Oswald-Workshop).

## 4. Genuin offene Punkte (NICHT bauen; nicht Marcos Tagesgeschäft)
- **F-3** `cont` (Contingency-Semantik), **F-4** `parts_condition` → Oswald, betrifft erst Phase 5.
- **F-5** N/E/A/S historisiert? → Technik, betrifft Phase 1.5.
- **B-3** Payment-Terms/Cashflow-Inhalte → Oswald, Phase 7.
- **F-15** Pflichtenheft-Inhalt → später, Phase 6.7.
- **B-4 CN: erledigt** — CN nur passives Attribut, keine Automatik; nicht erneut aufmachen.

## 5. Arbeitsweise
Pro Phase: Akzeptanz nachgewiesen (Test/Protokoll, nicht behauptet); `migrate`/CI grün;
für Phase 5 zusätzlich Golden-Master. Feature-Branch → PR → develop (Review Dominik).
Nichts aus dem Prototyp portieren. Nichts [OFFEN] bauen.
