# Entwicklungsplan — pilanda_sales (Vertrieb: Lastenheft → Kalkulation → Angebot)
> Master: pilanda/ENTWICKLUNGSPLAN.md · Theme-Mitbau: pilanda_theme/CONTRIBUTING.md
> Stand: 07.07.2026 · Regel: NUR echte Zustände abhaken — Wahrheit ist Pflicht.

Rolle: baut aus Oswalds Prototyp (read-only Referenz, **kein Code-Port**) das kaufmännische Angebotswesen für Seilkran-Projekte nach: Questionnaire/Lastenheft → Kalkulation → Angebot (+ Pricing Sheet/LV, Pflichtenheft). Modul „Vertrieb" (4 Bereiche: CRM · Questionnaire · Kalkulation · Angebot). **CRM-App/-Backend liefert Dominik** (eigenes Repo, CRM-SPA `/crm`); Optik/UX baut das Theme.

## Bindende Entscheide
- **Backend rechnet alles, Vue zeigt nur** (E-5/E-14). Formeln 1:1 aus Dossier 11; Beweis per **Golden-Master gegen Referenzquote `03c6eb4dfc`**.
- Custom-Field-Namespace **`custom_sales_`**; Project = ERPNext-SSOT, nur per Custom Field erweitern (E-21/E-28). Technische Namen Englisch, Labels DE/EN (E-26).
- Sätze/Prozente 3-stufig, zentral pro Projekt user-editierbar mit sichtbarem Default, Reset möglich (E-2/E-14). Prozent = `Percent` (5 = 5 %; Prototyp-Brüche beim Import ×100, E-25).
- Intern EUR-Master, Kurs am Projekt, Snapshot friert Kurs ein (E-8). Angebotsversion = read-only JSON-Beleg (E-27). Status/Freigabe = Frappe-Workflow, Revisionen = Submit/Amend (E-23/E-24).
- K-Artikel = eigener, nicht-dispofähiger DocType (K-Präfix, E-22/E-17). PILANDA startet leer, Referenzquote nur Test-Fixture (E-18).
- **Übergabe Vertrieb↔Innendienst↔Projektierung = Statusänderung** am Projekt (`Project.custom_sales_phase`, Eigentum hier; frei setzbares Select, Schleifen erlaubt, kein Einbahn-Workflow — Marco 03.07., `43c6ddb`). Ablauf-SSOT liegt in projeng.
- **Liest, definiert NICHT:** freigegebene Anlagenkonfiguration (projeng), Phasen/Dauern (pm). Konfliktregel der Specs: 99 (E-/K) > 02/03 > Dossiers 10–15 > 04.

## Erledigt
- [x] Phase 1 Datenmodell-Fundament (14.06., `576b84b` u.a.): `custom_sales_*` an Project + Item; DocType `Project Variant` (Kran-Child, Vertragsart, `is_winner`); K-Artikel (K-Präfix, nicht dispofähig, Preis-Zusammensetzung); Feldkatalog (106 Felder / 9+1 Sektionen als Seed `field_catalog_v1.py`); Rollen-Grundgerüst (`seed/roles.py`) — live auf `lcs.local` + DB-verifiziert
- [x] Phase 3.1: DocTypes `Requirement Spec` (Lastenheft) + `Requirement Spec Answer`/`… File` + `derive_to_project()` (leer überschreibt nie) — 14.06., `576b84b`
- [x] Phase 5 Start: Rechenkern-Kern-Primitive `calculation/engine.py` + `test_engine.py` — 14.06., `ef2c9ab`
- [x] Übergabe-Feld `Project.custom_sales_phase` (Lead → Projektierung → Kalkulation → Angebot → Verhandlung → Entscheidung Kunde) — 03.07., `43c6ddb`
- [x] CRM-Rücklink `Project.custom_sales_crm_deal` (Link → `CRM Deal`, nur wenn Frappe CRM installiert) in der CRM-Domäne `crm/custom_fields.py`, Owner Dominik — 02.07., `54077b7`

## Offen — wird wirklich gebaut
- [ ] Phase 3 Rest: Portal-Wizard (Vue/Token/Companion), PDF-Generator + Rück-Import, Datei-Anhänge, International-Felder (E-16)
- [ ] Phase 5 Gros: vollständige VK-Cascade (8 Stufen, 3 Gross-ups), N/E/A/S, Phasen/Manpower, Commission/WHT/Einfuhrzoll/Financing/Buyback/AfA-PMT, Kalkulations-DocType + Kostenübersicht (13 Spalten), **Golden-Master gegen `03c6eb4dfc`** (braucht Phase-2-Daten 🔒)
- [ ] Phase 2 Datenimport (Stammdaten): Item-DB (222, CN passiv), Board-/Markup-Defaults, Textbausteine — Abgleichsprotokoll Pflicht; braucht Prototyp-Lesezugriff (`C:\CoWork\Pilanda\Questionaire`)
- [ ] Phase 6 Angebot: Angebot + Angebotsversion (JSON-Snapshot), DOCX-Commercial (17 Sektionen) + TEPRO (48), Pricing Sheet/LV, Budget-Fastpath vs. Verbindlich; braucht Phase 5 + freigegebene Konfiguration (← projeng)
- [ ] Phase 7: PM-Anbindung (Phasen/Dauern aus pm), Payment-Terms/Cashflow (B-3, nach Oswald-Workshop)
- [ ] Detail-Rechte je DocType/Workflow (Phasen 3–6) — bestehende DocTypes tragen vorerst Standard-Perms

## Grenzen / ehrliche Hinweise
- Backend (DocTypes/Lastenheft/Rechenkern-Code) ist aus den Specs **ohne** Prototyp baubar; Prototyp-Lesezugriff wird erst für Phase 2, den Golden-Master und die [OFFEN]-Semantik nötig.
- **Genuin offen (NICHT bauen, nicht Marcos Tagesgeschäft):** F-3 `cont` / F-4 `parts_condition` → Oswald (Phase 5); F-5 N/E/A/S historisiert? → Technik (Phase 1.5); B-3 Payment/Cashflow → Oswald (Phase 7); F-15 Pflichtenheft-Inhalt → später (Phase 6.7).
- **B-4 CN erledigt** — CN nur passives Attribut, keine Automatik; nicht erneut aufmachen.
- **[OFFEN] Innendienst-Benachrichtigungsmechanik** — *wie* der Innendienst über eine anstehende Übergabe informiert wird (Notification/Assignment/ToDo), ist nicht entschieden. Das Übergabe-Feld steht; die Benachrichtigung darum herum nicht bauen, bis Marco den Mechanismus definiert.
- Nichts aus dem Prototyp portieren; nichts [OFFEN] bauen. Feature-Branch → PR → develop (Review Dominik).
- UI-Vorschläge entstehen als A-Liga-Showcases im Theme (`pilanda_theme/Entwicklungsplan.md §14/§14.1`); Verdrahtung hierher erst, wenn Codes final **und** CRM steht.

## Verweise
- CRM-Domäne `pilanda_sales/crm/` (Owner Dominik) hält als einziges den ERPNext-Rücklink `custom_sales_crm_deal` — ein Eigentümer je Feld, gehört bewusst NICHT in `custom_fields.py`.
- Ablauf-SSOT + Spezifikationspaket (`C:\CoWork\Pilanda\ImportzuPILANDA\`, Entscheidungs-Log 99 = höchste Wahrheitsinstanz): `pilanda_projectengineering/Entwicklungsplan.md`.
