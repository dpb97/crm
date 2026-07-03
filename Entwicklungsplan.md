# Entwicklungsplan — pilanda_sales (Vertrieb)

> **App-Fachplan (pilanda_sales).** Teil des zentralen Master-Plans `pilanda/ENTWICKLUNGSPLAN.md`. Stack-weite Regeln (Branch-Policy, Design/Tokens/Logos, Project-Objekt-SSOT, Dev-Env/Install) stehen dort bzw. in den referenzierten SSOTs und werden hier nicht dupliziert. CRM-SPA `/crm` = Dominiks Repo (nicht hier). Design-SSOT: `pilanda_theme`.

> **Stand:** 03.07.2026 · **Version:** v0.3 · **Reifegrad:** Aufbau · verbindliche Arbeitsgrundlage für dieses Repo.
>
> **Umgesetzt (Code auf `develop`, gegen Realität geprüft 03.07.2026):**
> - **Übergabe-Mechanik (Entscheid Marco 03.07.2026, Commit `43c6ddb`):** Feld
>   `Project.custom_sales_phase` (Select: Lead → Projektierung → Kalkulation →
>   Angebot → Verhandlung → Entscheidung Kunde) in `custom_fields.py`. Übergabe
>   an die Projektierung = **Statusänderung am Projekt**, kein Einbahn-Workflow
>   (Schleifen je Angebotsrunde: Budget → Richtpreis → Finales Angebot). Eigentum
>   `pilanda_sales`; Ablauf-SSOT in `pilanda_projectengineering` (§Ablauf).
>   Programmier-Review Dominik.
> - **CRM-Rücklink (Dominik, Commit `54077b7` 02.07.2026):** `Project.custom_sales_crm_deal`
>   (Link → `CRM Deal`) in der CRM-Domäne `pilanda_sales/crm/custom_fields.py` —
>   nur angelegt, wenn Frappe CRM installiert ist (`required_apps` = erpnext +
>   pilanda_theme, crm optional). CRM-**SPA** `/crm` bleibt Dominiks eigenes Repo.
> - **Phase 3.1 (Commit `576b84b`, 14.06.2026):** DocType `Requirement Spec`
>   (Lastenheft) + `Requirement Spec Answer`/`… File` + Ableitung. Offen bleiben
>   Portal-Wizard, PDF-Generator und Rück-Import.
> - **Phase 5 Start (Commit `ef2c9ab`, 14.06.2026):** Rechenkern-Kern-Primitive
>   (`calculation/engine.py` + `test_engine.py`). Golden-Master gegen `03c6eb4dfc`
>   und die vollständige VK-Cascade weiter offen.

**Logos/Marken:** SSOT `pilanda_theme` §15.
**Git/Branch:** nur `develop`; SSOT `pilanda/CLAUDE.md`.

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
- **Ablauf-SSOT:** Der Gesamtablauf Vertrieb ↔ Vertriebsinnendienst ↔
  Projektierung (1 Projekt / n Varianten, Rollen, Freigabe, manuelle
  Ausführungs-Überführung) steht kanonisch in
  `pilanda_projectengineering/Entwicklungsplan.md` §„Ablauf … (SSOT)" —
  hier nur verweisen, nicht duplizieren.

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
| 12 | Übergabe Vertrieb↔Innendienst↔Projektierung = **Statusänderung** am Projekt (`Project.custom_sales_phase`, Eigentum `pilanda_sales`); frei setzbares Select (Schleifen erlaubt), kein Einbahn-Workflow | Marco 03.07.2026 · Commit `43c6ddb` · Ablauf-SSOT = projeng |

## 3. Phasen (repo-scoped; Nummern = Master-Plan 03)

### Phase 1 — Datenmodell-Fundament  ·  Aufwand M  ·  ✅ **ERLEDIGT 14.06.2026**
> 1.1–1.6 live auf lcs.local + DB-verifiziert (DocTypes Project Variant, K Item,
> Field Catalog* inkl. 106-Felder-Seed; custom_sales_-Felder an Project+Item; Rollen).
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

### Phase 3 — Questionnaire/Lastenheft  ·  L  ·  🔧 **3.1 ERLEDIGT (14.06.2026, `576b84b`)** · Rest offen
> 3.1 live: DocType `Requirement Spec` + `Requirement Spec Answer`/`… File` +
> Ableitung. **Offen:** Portal-Wizard (Vue/Token/Companion), PDF-Generator +
> Rück-Import, Datei-Anhänge, International-Felder (E-16).

Lastenheft-DocType + Ableitungsregeln (leer überschreibt nie), Portal-Wizard (Vue,
Token, Companion-Logik), PDF-Generator + Rück-Import aus **einem** Feldkatalog,
Datei-Anhänge (echte Files), International-Felder nachziehen (E-16). Dossier 10.

### Phase 5 — Kalkulation: der Rechenkern  ·  XL  ·  Herzstück  ·  🔧 **Start (14.06.2026, `ef2c9ab`)**
> Angelegt: `calculation/engine.py` (Kern-Primitive) + `test_engine.py`.
> **Offen (Gros der Phase):** vollständige VK-Cascade (8 Stufen), N/E/A/S,
> Phasen/Manpower, Commission/WHT/Duties/Financing/Buyback, Kalkulations-DocType +
> Kostenübersicht, und der **Golden-Master gegen `03c6eb4dfc`** (🔒 Prototyp/Phase 2).

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

## 3a. Bau-Reihenfolge & Gates (Abhängigkeiten)

Abgeleitet aus dem Abhängigkeitsgraph (Paket 03 §Abhängigkeiten). Marker:
🟢 ohne Prototyp-Daten baubar · 🔒 braucht Prototyp-Lesezugriff
(`C:\CoWork\Pilanda\Questionaire`) · 🎨 braucht Vue/Querschnitt Q.

1. ✅ **Phase 1 Datenmodell** — komplett (1.1–1.6).
2. 🔧 **Phase 3 Lastenheft** — DocType + Ableitung **erledigt** (`576b84b`); offen: Portal-Wizard/PDF/Rück-Import 🎨.
3. 🔧 **Phase 5 Kalkulations-Rechenkern** — Kern-Primitive **begonnen** (`ef2c9ab`); Formeln aus Dossier 11 **codierbar ohne Prototyp**, der **Golden-Master gegen `03c6eb4dfc` ist 🔒**.
4. 🔒 **Phase 2 Datenimport** — echte Stammdaten (Item-DB, Board-/Markup-Defaults, Textbausteine); liefert auch die Golden-Master-Quote.
5. **Phase 6 Angebot** — braucht Phase 5 + freigegebene Konfiguration (← projeng) + Templates (← Phase 2).
6. **Phase 7** — Payment/Cashflow nach Oswald-Workshop (B-2/B-3).

**Cross-Repo (nur LESEND):** Die Kalkulation **liest** die *freigegebene* Anlagenkonfiguration
aus `pilanda_projectengineering` (dessen Phase 4) und Phasen/Dauern aus `pilanda_pm`.
`pilanda_sales` **definiert** diese Objekte NICHT (Leserichtung, SSOT §3.4). Vue-Tabellen-
Komponenten kommen aus `pilanda_theme` (Querschnitt Q).

**Strategisch:** Backend (DocTypes/Lastenheft/Rechenkern-**Code**) ist aus den vollständigen
Specs ohne Prototyp baubar — der Prototyp-Lesezugriff wird erst für Phase 2, den
Golden-Master und die [OFFEN]-Semantik nötig.

## 4. Genuin offene Punkte (NICHT bauen; nicht Marcos Tagesgeschäft)
- **F-3** `cont` (Contingency-Semantik), **F-4** `parts_condition` → Oswald, betrifft erst Phase 5.
- **F-5** N/E/A/S historisiert? → Technik, betrifft Phase 1.5.
- **B-3** Payment-Terms/Cashflow-Inhalte → Oswald, Phase 7.
- **F-15** Pflichtenheft-Inhalt → später, Phase 6.7.
- **B-4 CN: erledigt** — CN nur passives Attribut, keine Automatik; nicht erneut aufmachen.
- **[OFFEN] Innendienst-Benachrichtigungsmechanik** — *wie* der Vertriebsinnendienst
  über eine anstehende Übergabe informiert wird (Notification/Assignment/ToDo an
  die Projektierung), ist noch nicht entschieden. Das Übergabe-**Feld**
  (`custom_sales_phase`) steht; die Benachrichtigung darum herum bleibt offen —
  nicht bauen, bis Marco den Mechanismus definiert.

## 5. Arbeitsweise
Pro Phase: Akzeptanz nachgewiesen (Test/Protokoll, nicht behauptet); `migrate`/CI grün;
für Phase 5 zusätzlich Golden-Master. Feature-Branch → PR → develop (Review Dominik).
Nichts aus dem Prototyp portieren. Nichts [OFFEN] bauen.

## 6. UI-Vorschläge (A-Liga-Showcases im Theme, ab 23.06.2026)

> Querverweis, nicht duplizieren: `pilanda_theme/Entwicklungsplan.md §14 / §14.1`.

Solange die Codes/Datenmodelle hier noch nicht final sind, entstehen die
Oberflächen-Vorschläge als **A-Liga-Showcases in `pilanda_theme`** (Theme = reine
CSS-/Design-Schicht). Verdrahtung in dieses Repo erst, wenn die Codes final sind
**und** das CRM (Dominik, eigenes Repo) steht.

- **„Vertrieb"** = CRM (Dominik) + **Lastenheft** + **Kalkulation (inkl. Varianten)**
  + **Angebot**. CRM ist nicht Scope dieses Repos.
- **Bau-Reihenfolge der Showcases** (bestätigt 23.06.): Lastenheft → Varianten →
  Kalkulation → Angebot.
- **Datengrundlage Lastenheft** verifiziert: `seed/field_catalog_v1.py` (9 Kunden-
  Sektionen + LCS-intern, 106 Felder, Companion-Logik „other"/„specify", SI-Einheiten).
- **Status:** Lastenheft-Showcase in Arbeit (Schritt 1). Kein Eingriff ins
  Datenmodell/keine [OFFEN]-Punkte — reiner UI-Entwurf.

## 7. Schnittstellen zu Nachbar-Apps

- **→ `pilanda_projectengineering`** (`../pilanda_projectengineering/Entwicklungsplan.md`): liest
  freigegebene Anlagenkonfiguration/Projektierung als Grundlage für Kalkulation/Angebot.
- **→ `pilanda_pm`** (`../pilanda_pm/Entwicklungsplan.md`): Übergabe gewonnener Angebote in die
  Projekt-/Terminierung (Angebot → Auftrag → Projekt).
- **CRM-SPA `/crm`** = **Dominiks** Repo (nicht Scope dieses Repos). Die **CRM-Domäne
  `pilanda_sales/crm/`** (Owner Dominik) hält als einziges den ERPNext-seitigen
  Rücklink `Project.custom_sales_crm_deal` (Link → `CRM Deal`, `54077b7`); Frappe
  CRM ist optional (Feld wird ohne CRM übersprungen). Ein Eigentümer je Feld —
  dieser Rücklink gehört bewusst NICHT in `pilanda_sales/custom_fields.py`.
- **Design:** `pilanda_theme` (Tokens/CSS/PpBausteine). Stack-weit: Master `pilanda/ENTWICKLUNGSPLAN.md`.
