# Entwicklungsplan — pilanda_sales (Vertrieb: Lastenheft → Kalkulation → Angebot)
> Master: pilanda/ENTWICKLUNGSPLAN.md · Theme-Mitbau: pilanda_theme/CONTRIBUTING.md
> Stand: 16.07.2026 · Regel: NUR echte Zustände abhaken — Wahrheit ist Pflicht.

Rolle: baut aus Oswalds Prototyp (read-only Referenz, **kein Code-Port**) das kaufmännische Angebotswesen für Seilkran-Projekte nach: Questionnaire/Lastenheft → Kalkulation → Angebot (+ Pricing Sheet/LV, Pflichtenheft). Im Vertriebsschnitt der Nav (Master §6) liefert die App vor allem **„Projekte ▸ Lastenheft" + „Angebote ▸ Varianten"**; der CRM-Teil erscheint dort als eigener Bereich **„Netzwerk"** (Kunden/Kontakte/Agenten/Partner). **CRM-SPA = Frappe CRM App `/crm`** (Owner Dominik; sein CRM-Fork liegt seit **PR #13 (16.07.2026) GEMERGT auf `develop`** — s. Entscheid unten); die LCS-Rücklink-Logik liegt im Python-Subpackage `pilanda_sales/crm/` (nicht zu verwechseln mit dem Top-Level-Fork-Paket `crm/`) — Optik/UX baut das Theme.

## Bindende Entscheide
- **VERTRIEB-INTEGRATION (Marco 16.07.2026, nach PR #13) — Zielbild:**
  EIN Modul Vertrieb in der Pilanda-Shell, EINE App `pilanda_sales` — keine
  zwei App-Welten. (1) **Backend = Dominiks CRM-Funktionen** (Deal=Projekt,
  Leads, Outlook, FX, Opportunity-Matrix): wir nutzen seine bereits
  aufbereiteten Pages oder bauen die Pages — Datenschicht bleibt seine.
  (2) **Struktur übernehmen wir von Dominik** (Sub-Pages: Pilot, Projekte,
  Netzwerk, Kunden, …) und **ergänzen eigene Punkte**, wo er noch nichts
  gebaut hat. (3) **UI IMMER aus `pilanda_theme`** (Pp*-Kopien nach
  Copy-Modell + Token-CSS) — keine Fremd-Optik, keine Neubauten neben dem
  Theme. (4) **salesbot/Pilot wird als eigene Page „Pilot" im Modul
  Vertrieb eingebunden.** Alles zusammengeführt auf einem sauberen
  develop, in der Bench lauffähig (Wahrheit = E2E).
- **CRM-Fork liegt AUF develop (PR #13, Dominik, 16.07.2026)** — ersetzt den
  Vormittags-Entscheid „Fork-Branch ignorieren" (der Fork ist nicht mehr
  eigenständig): Dominik hat unser develop in `feature/unify-deal-project`
  gemergt (`--allow-unrelated-histories`, Repo hat jetzt 3 Root-Commits;
  Konfliktauflösung sauber dokumentiert im Merge-Commit `9150ff62`) und per
  PR #13 nach develop gezogen. develop enthält seither BEIDE Welten:
  unser App-Paket `pilanda_sales/` (im Merge unangetastet) + der komplette
  Fork (`crm/`, `frontend/` = CRM-SPA — unser Dashboard lebt dort weiter
  unter `src/dashboard/` + `vite.dashboard.config.js` —, `mobile/`,
  `lcs_integrations/`, `lcs_bizcard/`, `e2e/`, `docker/`, Submodule
  `frappe-ui`). **Hoheiten unverändert:** Upstream-/Fork-Teile (`crm/`,
  CRM-SPA-Kern) pflegt Dominik — Upstream bleibt unberührt, damit Merges
  billig bleiben (Prinzip in `README.LCS.md`); wir arbeiten weiter auf
  develop in unseren Teilen (`pilanda_sales/`, `frontend/src/dashboard/`,
  Doku, Theme-Konsum).
- **Vom Merge geerbte OFFEN-Punkte (Quelle: Merge-Commit `9150ff62`, von
  Dominik selbst benannt):** (a) ein Repo installiert nur EINE Frappe-App —
  pyproject zeigt auf `pilanda_sales`, `[tool.bench.assets]` weiter auf
  `crm/` (inkonsistent; die Repo-Schnitt-Frage ist damit faktisch wieder
  offen [Marco/Dominik]); (b) `frontend/` trug zwei Frontends — der
  sales_dashboard-Build ist mit dem Insel-Rückbau 20.07. entfallen
  (nur noch CRM-SPA-Build); (c) kein Build/Install
  aus dem gemergten Stand verifiziert. → Abarbeitung s. „Offen".
- **README-Auflösung (Dominik, Merge `9150ff62`):** Root-`README.md` = Upstream-
  Frappe-CRM-README (bleibt unberührt für billige Upstream-Merges); das frühere
  pilanda_sales-README (Stand `f8e3a6df`) wurde dabei ersetzt. Repo-Identität +
  LCS-Kontext stehen jetzt in `README.LCS.md` (Kopfblock); App-Wahrheit bleibt
  HIER. Volle README-Wiederherstellung nur per Marco-Entscheid (Konfliktkosten
  bei Dominiks Upstream-Merges).
- **lcs_integrations in der Bench INSTALLIERT (Marco-GO 16.07.2026 nach
  Fehlbefund-Screenshot):** Die App enthält das komplette CRM-Datenmodell
  (30 DocTypes: LCS Project, Opportunity-Matrix, Offer, Funnel-Phasen,
  Segmente/Territories) — ohne sie war „Vertriebsprojekte" tot („DocType
  LCS Project nicht gefunden") und jede CRM-Seite warf den
  get_user_preferences-Fehler. Install: Symlink `apps/lcs_integrations`
  → Repo-Unterordner, pip -e, apps.txt, install-app + Patches.
  **Zwei Stolpersteine dokumentiert:** (a) Redis-Modul-Cache hielt
  `lcs_integrations: []` → DocType-Sync lief leer durch und ALLE Patches
  wurden als „ausgeführt" verbucht ohne zu wirken — Fix: clear-cache,
  sync_for, Patches erneut (26/26 OK); (b) CONTAINER-LOKAL wie die
  crm-App: nach Recreate Symlink+apps.txt+pip -e neu setzen, dann
  clear-cache VOR migrate. Verifiziert: /crm/projects,/network,
  /organizations,/contacts,/forecasting eingeloggt = 0 Fehlerboxen,
  0 JS-Fehler. **Seit 16.07. abends: Einspielen/Redeploy = EIN Befehl:**
  `docker exec pilanda-frappe bash /workspace/frappe-bench/apps/pilanda/_devenv/install-crm.sh`
  (Skript `pilanda/_devenv/install-crm.sh`, idempotent — Marco #1).
- **CRM-Bestandsdaten-Übernahme (Marco-Befund „nur ein Datensatz sichtbar",
  16.07.2026 abends):** Dominiks CRM ist eine EIGENE Datenwelt und startete
  leer — der ERPNext-Bestand (8 Leads, 22 Customers, 38 Contacts) war in den
  CRM-Sub-Pages unsichtbar; zusätzlich fehlten die crm-eigenen Standard-Seeds
  (CRM Lead/Deal Status = 0 → auch Neuanlage unmöglich; gleiche Wurzel wie
  der Cache-Stolperstein). Fix: (a) `crm.install.after_install()` nachgeholt
  (7+7 Statuses + Layouts/Quellen), (b) NEU `pilanda_sales/crm/backfill.py`
  = einmalige idempotente Übernahme Customer→CRM Organization (12; Upsert
  per Name, kein Echo mit Dominiks Rück-Sync) + Lead→CRM Lead (8; Idempotenz
  über E-Mail/Name+Firma). 2. Lauf verifiziert 0 neu.
  **VERVOLLSTÄNDIGT (Marco „keine importierten Schattenwelten", 16.07. spät):**
  (c) Opportunity→CRM Deal ebenfalls migriert (8; Status-Mapping
  Converted→Won/Lost→Lost/Quotation→Proposal-Quotation, Lost-Pflichtgrund
  ehrlich als „Altbestand, Grund nicht erfasst"); Deal-Insert-Hook erzeugte
  automatisch 8 LCS Projects (Deal=Projekt ✓). (d) **ERPNext-Altbestand
  GELÖSCHT (Marco-GO):** tabLead 8→0, tabOpportunity 8→0 via delete_doc,
  0 Fehler — Vertriebsprozess-Daten leben seither NUR im CRM (eine
  Wahrheit); ERPNext behält nur Downstream (Customer/Quotation/SO via
  Dominiks Ein-Weg-Sync). E2E: alle CRM-Seiten zeigen die Daten,
  0 Fehlerboxen/0 JS-Fehler.
- **CRM-Laufzeit in der Dev-Bench (16.07.2026, für Audit + Nav):** die App
  `crm` ist CONTAINER-LOKAL installiert (Frontend gebaut, Assets-Symlink
  `sites/assets/crm`, migrate grün) — überlebt Container-Restart, NICHT
  Recreate; danach neu einspielen, seit PR #13 direkt **aus Repo-develop**
  (git archive des Branch entfällt): Quelle → apps/crm, pip -e, apps.txt,
  frontend yarn build, Symlink, migrate. Der bis dahin geblockte Compose-
  Mount kann mit dem Repo-Stand neu bewertet werden — hängt am Repo-Schnitt-
  /Zwei-Apps-Punkt oben [Marco]. Bekannte Fork-Reste auf Dominiks Liste:
  Aufruf `lcs_integrations.*` (seit PR #13 im Repo, Install-Status in der
  Bench ungeklärt), Service-Worker-Scope-Warnung, einzelne 417/403-Calls.
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
- [x] **Vertrieb-Modul-Dashboard — ZURÜCKGEBAUT (Marco-Freigabe 20.07.2026):**
  abgelöst durch das EINE Vertriebs-Dashboard `/crm/dashboard`
  (`LCSCRMDashboard.vue`; Ein-Dashboard-Entscheid Marco 20.07., pilanda
  `e153ab2`). Entfernt: `frontend/src/dashboard/*` (inkl. Doppel-Kopien
  PpDashboard/PpDataGrid), `vite.dashboard.config.js` +
  `build:dashboard`/`dev:dashboard`, Page-Ordner
  `vertrieb/page/sales_dashboard/`, `pilanda_sales/api.py`
  (`get_sales_dashboard` — einziger Konsument war diese Insel); DB-Eintrag
  via Patch `v0_1.remove_sales_dashboard_page`. Pilot-Feed lebt im
  CRM-Dashboard weiter; Alt-KPIs Angebote/Aufträge/Kunden entstehen dort
  neu, wenn das Angebotswesen kommt (AP s. „Offen"). Historie: Git.
  Ursprünglicher Bau (nur Historie): (N10 Welle 2, Master §6.2, `0674222`) — Desk-Page `/app/sales-dashboard` (Titel „Vertrieb"), erstes Vue-Frontend der App (`frontend/`, IIFE-Bundle `sales_dashboard`, Muster wie `pilanda_pls`). KOPIE des Theme-Bausteins `PpDashboard@1` + `PpDataGrid@3` (Copy-Modell, PP_REV mitkopiert); rein `--pp-*`-Tokens, hell+dunkel, Regel 6.1-6. **NUR echte Quellen** über `pilanda_sales.api.get_sales_dashboard`: KPI-Zeile Pilot-Treffer / Vertriebsprojekte / Aufträge / Angebote / Kunden; Karten Pilot-Feed (`Pilot Tender`, App optional → ehrlicher Leerzustand wenn fehlend), Projekte nach `custom_sales_phase`, Aufträge (`status=Auftrag`, E3 — SO-Automatik/Feld noch offen, s. u.), Absprünge (CRM-SPA `/crm`, Pilot-Workbench, Angebote, Kunden, Lastenheft, Varianten). **CRM-SPA `/crm` (Dominik) NICHT angefasst.** Verifiziert 14.07. (eingeloggt t.tester): 5 KPI (3/3/0/6/22) + 4 Karten + 3 Pilot-Treffer + 7 Phasen-Zeilen + 6 Absprünge, hell+dunkel, 0 Konsolenfehler. Build seit PR #13: `cd frontend && yarn build:dashboard` (`npm run build` baut jetzt die CRM-SPA!); dist = Build-Artefakt, gitignored — wie Schwester-Apps. **Handoff ERLEDIGT (Marco 15.07., Master N10/E8-Nachtrag):** Modul „vertrieb" = live mit Nav-Ziel `/app/sales-dashboard`; Interessent → `/crm/leads`, Verkaufschance → `/crm/deals` (Laufzeit = Dominiks CRM-Fork, s. Entscheide)

- [x] **Theme-Konsistenz develop verifiziert (16.07.):** Kopien `PpDashboard@1`
  + `PpDataGrid@3` drift-frei (pp-rev-report ✓); Dashboard rein `--pp-*`-Tokens.
  Der CRM-Fork konsumiert die Tokens ebenfalls byte-gleich (pp-tokens.css =
  Theme-SSOT, Diff leer) — dort aber Dominiks Pflege.

## Offen — wird wirklich gebaut
- [ ] **Angebotswesen-KPIs ins EINE Dashboard** (Folge Insel-Rückbau 20.07.):
  wenn das Angebotswesen (Lastenheft/Kalkulation/Angebote) kommt, entstehen
  die Zähler Angebote/Aufträge/Kunden im `/crm/dashboard` neu (Quellen wie
  ehem. `get_sales_dashboard`: Quotation/Customer/Project-status=Auftrag).
- [ ] **Bizcard-Scanner-UI verdrahten [Dominik]:** `BizcardScannerButton/-
  Modal.vue` existieren ohne Einbau; Ziel laut Marco 20.07.: mobil scannen
  (Phone/Tablet) → Datenvorschlag in Personen/Kontakte. Backend +
  Scanner-Docker stehen.
- [ ] **Test-only-Widgets entscheiden:** Outlook-/Teams-/WhatsApp-Widgets +
  SyncStatusBadge haben je nur ihre Spec, keinen Einbau — verdrahten oder
  samt Spec entfernen (Marco/Dominik).
- [ ] Dokumentierte Rückbau-Kandidaten (liegen gelassen, Marco 20.07. nur
  Dashboard-Insel freigegeben): `LinkedProjectChip.vue` (Funktion lebt als
  Projekt-Button in `LCSDeal.vue`), `pilanda/api.py::get_workspace_items`
  (+3 Helfer, stack-weit 0 Aufrufer).
- [ ] **Vertrieb-Integration (Entscheid oben) — Wellenplan:**
  - [x] Welle 1 (16.07., pilanda `33e628f`): erste 4 Punkte auf CRM-Seiten.
  - [x] Welle 2 ERLEDIGT durch die VOLLSTÄNDIGE CRM-Übernahme (16.07.,
    pilanda `2ab8645`): Modul vertrieb = Dominiks Sidebar 1:1 (17 Punkte,
    Target /crm, Zähler 142); ALLE seine Seiten sind Nav-Punkte.
    „Aufträge" entfällt als Nav-Punkt bis E3-SO-Spez (Marco #8).
  - [ ] Welle 3 = **Vue-Neubau der CRM-Optik (Marco-GO 16.07., Phasen):**
    - [x] V0 Token-Konformität: nackte Hex/Alt-Navy in Dominiks
      LCS-Komponenten → `var(--pp-*)` (Entscheid #4; Umsetzung 16.07.,
      Verifikation s. u.).
    - [x] V1 Showcase-Serie KOMPLETT (17.–19.07., theme `75a520e`):
      #3 Lead-Liste, #4 Deal-Kanban, #5 Projekt-Workspace, #6 Netzwerk,
      #7 Sales Meeting, #8 Marktaufteilung+Karte, #9 Schnellnotizen mit
      NEUEM Baustein PpSpeakOrType@1 (echte MediaRecorder-Aufnahme).
    - [x] **V2 Adoption Wellen 1+2 (19.07., produktiv + E2E-bewiesen):**
      W1 `0789d47d`/`e57bac88`/`c750efea` — Netzwerk (PpNetworkGraph/
      Drawer-Profile an get_network_graph) + Projekt-Workspace
      (PhasenStepper/KPI/Tabs/echte Frappe-Comments an LCS Project);
      Datenlücken-Fix `c01e7004` (Contact→CRM-Org-Links + company_name,
      erst dadurch Graph gefüllt: 20 Knoten/10 Kanten). W2 `d15a561a`/
      `77632e86`/`a9d0b866`/`7a35f682` — Sales Meeting (KPI+Grid+
      Summenfußzeile), Marktaufteilung (PpMap-Marker aus echten Länder-
      Zentroiden + Territorien-Grids, Umverteilung erhalten),
      Schnellnotiz (PpSpeakOrType → dispatch_note/Audio-Upload+
      Transkriptions-Job, komplett deutsch; Browser-Live-Transkription
      bewusst durch serverseitige ersetzt). 10 neue Pp*-Kopien, Drift 0.
      E2E: Alle Seiten Desktop 0 Fehler; Mobil (iPhone 13) 0 Overflow,
      0 geclippte Controls (PpTabs-„Clip" war Mess-Artefakt — Leiste
      scrollt, SSOT-CSS hatte overflow-x längst).
    - [x] **Mobile-Fix-Welle (19.07., `4a07d43c`/`a7398e61` + portfolio
      `ac9edd9`):** Forecasting mobil (Controls scrollen, Chart unter
      KPIs), geteilter LayoutHeader (Root-Cause des Dashboard-Clips),
      Produktportfolio-Tabelle scrollt statt kollabiert (E2E iPhone).
      **PWA:** Manifest/Icons/theme_color #008B8B korrekt; SW-Scope-Hook
      `lcs_integrations/pwa/sw_scope.py` (Service-Worker-Allowed: /crm)
      — WIRKT NUR HINTER NGINX/PROD (Dev-Bench: werkzeug
      SharedDataMiddleware liefert /assets VOR der App aus, Hook feuert
      dort nicht; nginx.conf setzt den Header bereits). EHRLICHE GRENZE:
      /crm-Offline-Scope ist auf der Dev-Bench nicht beobachtbar.
    - [ ] V2 Rest (mit Dominik): Upstream-Flächen Leads/Deals-Listen +
      CRM-Dashboard/Prognose-Umbau (Merge-Billigkeit!), Capacitor-Builds
      (mobile/, braucht native Toolchain + Stores).
- [x] **#3 Repo-Schnitt FESTGESCHRIEBEN (Marco 16.07., „wie empfohlen"):**
  EIN Repo `pilanda_sales` mit drei Paketen (pilanda_sales, crm,
  lcs_integrations); Bench-Einspielung/Persistenz = `pilanda/_devenv/
  install-crm.sh` (idempotent, auch Redeploy; ersetzt die manuelle
  Recreate-Anleitung oben). pyproject↔bench.assets bleibt wie von Dominik
  gemergt (Pfad-relativ korrekt). Dominik-Bestätigung: nachrichtlich.
- [x] **#7 README bleibt Upstream** (Marco 16.07.) — Identität in
  README.LCS.md, Merges billig.
- [x] **#5 Sicherheits-Patches (16.07., `38024739`):** 14/15 critical+high
  gefixt (trivy-action 0.35.0, 6 frontend-resolutions, Pillow 12.2.0 +
  python-multipart 0.0.30 im bizcard-Scanner — dessen Docker-Image braucht
  beim nächsten Deploy einen Rebuild). **Bewusst OFFEN: vite #27** — kein
  5.x-Backport, Fix nur via Major 6+ = Dominik-Entscheid (SPA-Baubarkeit).
- [x] **#6 Fork-CI auf PR-only (16.07., `b763e381`):** CI/LCS-CI/CodeQL/
  Trivy feuern nicht mehr je develop-Push (Dauerrot beseitigt); CodeQL
  behält den Wochenplan.
- [ ] **Merge-Nacharbeit PR #13 (aus `9150ff62`):**
  - [x] (a) sales_dashboard-Build unter vite 5 VERIFIZIERT (16.07.; Insel
    inzwischen zurückgebaut 20.07., s. o. — Punkt nur Historie):
    `yarn build:dashboard` grün (89,55 kB JS + 18,91 kB CSS), Assets über
    Bench 200, `/app/sales-dashboard` eingeloggt gerendert (4 Karten,
    0 JS-Fehler). Engine-Tests 10/10 (pytest im Bench-Env; Achtung:
    `bench run-tests` sammelt die pytest-Stil-Tests NICHT ein — 0 Tests,
    Exit 0; nicht als grün fehlinterpretieren).
  - [x] (b) Theme-Drift-Check (16.07.): `frontend/src/pp-tokens.css`
    BYTE-GLEICH zum Theme-SSOT (SHA-256 identisch); pp-rev-report: alle
    sales-Kopien aktuell (inkl. Dominiks PpCommandPalette@2/PpMap@1/
    PpNetworkGraph@1); einziger Drift PpSidebar @4→@5 in der CRM-SPA
    → auf @5 gehoben (byte-gleiche Theme-Kopie; @5 = E8 „bald"-Badge raus;
    Wrapper PilandaSidebar nutzt kein Badge/Status-Markup).
  - [ ] (c) pyproject ↔ `[tool.bench.assets]`-Inkonsistenz = Repo-Schnitt-/
    Zwei-Apps-Entscheid [Marco/Dominik — nicht von uns lösen]. Randnotizen
    dazu: `frontend/` trägt yarn.lock (maßgeblich, Fork) UND unser altes
    package-lock.json (stale, npm-Ära — Entfernung empfohlen, Marco-Freigabe
    ausstehend); Fork-CI-Workflows (ci/lcs-ci/lcs-codeql/lcs-trivy) feuern
    jetzt auf jeden develop-Push; GitHub meldet seit dem Merge 39
    Dependabot-Funde (1 critical/14 high) aus der Fork-Dependency-Masse
    [Dominiks Liste]; nackte Hex-Farben in Dominiks LCS-Komponenten
    (OpportunityMatrix `#1E78C2`, ProjectDashboard Alt-Navy `#0B3A6F` u. a.)
    statt `var(--pp-*)` — CI-Korrektur analog Scout = Marco-Entscheid.
- [ ] **SO-Automatik spezifizieren (Master §6/E3, WICHTIG):** beim Statuswechsel → „Auftrag" automatisch verdeckter ERPNext Sales Order (1:1 aufs Projekt, nirgends in der Nav; „Aufträge"-Sicht = gefilterte Projektliste `q:status=Auftrag`). Zu klären: Verhältnis eigener Angebots-DocType ↔ ERPNext Quotation ↔ Sales Order; welches Feld speist die „Aufträge"-Filterliste (`Project.custom_sales_phase` vs. `Project.status`) — mit dem projectengineering-Ablauf-SSOT abstimmen. Detail-Spez gehört in diese App (`pilanda_sales`).
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
- UI-Vorschläge entstehen als A-Liga-Showcases im Theme (`pilanda_theme/Entwicklungsplan.md`, Abschnitt „Modul-Roadmap"/Baustein-Index); Verdrahtung hierher erst, wenn Codes final **und** CRM steht.

## Verweise
- CRM-Domäne `pilanda_sales/crm/` (Owner Dominik) hält als einziges den ERPNext-Rücklink `custom_sales_crm_deal` — ein Eigentümer je Feld, gehört bewusst NICHT in `custom_fields.py`.
- Ablauf-SSOT + Spezifikationspaket (`C:\CoWork\Pilanda\ImportzuPILANDA\`, Entscheidungs-Log 99 = höchste Wahrheitsinstanz): `pilanda_projectengineering/Entwicklungsplan.md`.
