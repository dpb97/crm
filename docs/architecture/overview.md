# LCS CRM — Architecture Overview

Scope: adaptation of the upstream `frappe/crm` fork into the LCS Cable Cranes
integrated business stack. For the "why" behind technology choices see
[ADR 0001](../adr/0001-frappe-over-greenfield.md) ·
[ADR 0002](../adr/0002-postgres-over-mariadb.md) ·
[ADR 0003](../adr/0003-msal-oidc.md) ·
[ADR 0004](../adr/0004-erpnext-over-frappe-crm.md).

> **abas ERP is retired.** Production ERP is ERPNext installed alongside
> frappe/crm on the same bench; PLM is Autodesk Fusion Manage. Anything
> in historical docs or code comments referring to `abas_*` fields is
> stale.

---

## C4 · Context — the six-system landscape

`LCS Project` is the pivot entity. Every downstream system keeps its own
authoritative record and exposes it back to the CRM via typed links.

```mermaid
flowchart LR
    user([LCS Sales / PM / Ops])
    entra[[Microsoft Entra ID<br/>OIDC / MSAL]]
    outlook[[Microsoft 365<br/>Graph + Add-in]]
    fusion[[Autodesk<br/>Fusion Manage PLM]]
    proxess[[Proxess DMS]]

    crm{{LCS Integrated Stack<br/>Frappe Bench}}

    user -->|SSO| entra
    user -->|browser SPA| crm
    user -->|Outlook task-pane| outlook

    crm <-->|authenticate| entra
    crm <-->|delta mail/cal + add-in API| outlook
    crm <-->|item + BOM + state| fusion
    crm <-->|document upload/retrieval| proxess

    classDef external fill:#f3f4f6,stroke:#6b7280,stroke-dasharray: 3 3;
    class entra,outlook,fusion,proxess external;
```

---

## C4 · Container — what runs where

```mermaid
flowchart TB
    subgraph client[Client tier]
        browser[Browser<br/>Vue 3 SPA]
        outlookapp[Outlook Desktop/Web<br/>Add-in task pane]
        pwa[(IndexedDB cache<br/>+ mutation queue)]
    end

    subgraph host[Docker host — lcs.local]
        nginx[[Nginx<br/>TLS · HSTS · rate limit]]

        subgraph bench[Frappe Bench]
            crm_app[crm<br/>upstream frappe/crm]
            erp[erpnext<br/>Customer / Quotation / SO]
            hrms[hrms<br/>Employee]
            lms[lms<br/>Course / Enrollment]
            bsm[bsm<br/>Construction site mgmt]
            lcs[lcs_integrations<br/>LCS-owned logic]
        end

        redis[(Redis<br/>queue · cache · socketio)]
        mariadb[(MariaDB<br/>shared)]
    end

    browser -->|HTTPS + WebSocket| nginx
    outlookapp -->|HTTPS<br/>SSO cookie| nginx
    browser <-->|optimistic write<br/>offline queue| pwa

    nginx --> crm_app
    crm_app <--> erp
    crm_app <--> hrms
    crm_app <--> lms
    crm_app <--> bsm
    crm_app --> lcs

    lcs --> mariadb
    crm_app --> mariadb
    erp --> mariadb
    crm_app --> redis

    lcs -->|OAuth2| outlook_ext[(MS Graph)]
    lcs -->|OAuth2 bearer| fusion[(Fusion Manage)]
    lcs -->|OAuth2 bearer| proxess[(Proxess DMS)]

    classDef ours fill:#eff6ff,stroke:#1E78C2;
    class lcs,outlookapp,pwa ours;
```

---

## Data flow — CRM → ERP → Site (cross-module automation)

```mermaid
sequenceDiagram
    autonumber
    participant U as User (Sales)
    participant CRM as Frappe CRM
    participant LCS as lcs_integrations
    participant ERP as ERPNext
    participant BSM as BSM app
    participant HRMS as HRMS
    participant LMS as LMS

    U->>CRM: Create CRM Organization "AlpenBahn AG"
    CRM->>LCS: hook after_insert
    LCS->>ERP: upsert Customer
    ERP-->>LCS: Customer name
    LCS-->>CRM: store CRM Org.erpnext_customer

    U->>CRM: Create LCS Project → LCS Offer (Draft)
    U->>CRM: LCS Offer.status = Sent
    CRM->>LCS: hook on_update
    LCS->>ERP: upsert Quotation (lcs_offer back-link)
    ERP-->>LCS: Quotation name

    U->>CRM: LCS Offer.status = Accepted
    CRM->>LCS: hook on_update
    LCS->>ERP: submit Quotation → make_sales_order<br/>(set lcs_project back-link)
    ERP->>LCS: after_insert on Sales Order
    LCS->>BSM: create BSM Project (sales_order, lcs_project)
    LCS-->>CRM: LCS Project.bsm_project

    U->>CRM: Add team_members[] + required_trainings[]
    CRM->>LCS: validate hook
    LCS->>HRMS: Employee → User mapping
    LCS->>LMS: check LMS Enrollment per course
    LMS-->>LCS: progress=100 / expiry
    LCS-->>CRM: LCS Project Team Member.training_status
```

---

## Offline edit sync — client-side durable queue

```mermaid
flowchart LR
    user[User] -->|edit| ui[LCS Project UI]
    ui -->|optimistic update| cache[(IndexedDB<br/>cache store)]
    ui -->|if online| api[/frappe.client.set_value/]
    ui -->|if offline| queue[(IndexedDB<br/>mutations store)]

    online{navigator<br/>.onLine = true?} -->|no| wait[Wait for 'online' event]
    wait --> drain[syncEngine.drain]
    drain --> serverCheck[frappe.client.get<br/>current doc]
    serverCheck --> conflict{base_values<br/>!= server values?}
    conflict -->|yes| markConflict[status=conflict<br/>+ conflicts map]
    conflict -->|no| apply[frappe.client.set_value]
    apply --> success[remove from queue<br/>+ refresh cache]

    markConflict --> ui_resolver[ConflictResolver.vue<br/>3-way merge]
    ui_resolver -->|user picks| apply

    classDef local fill:#fef3c7,stroke:#d97706;
    class queue,cache local;
```

---

## Visibility — three-layer access model

```mermaid
flowchart TB
    userRequest[User opens /crm/projects]
    userRequest --> role[Layer 1: Frappe Role Perms]
    role -->|read allowed| profile[Layer 2: LCS Access Profile]
    profile -->|admin-scoped| hook[permission_query_conditions hook]
    hook -->|injects SQL| sql["WHERE country IN (Austria)<br/>AND project_type IN (SB)<br/>AND salesperson IN (me, team)"]
    sql --> rows[rows the user can see]
    rows --> prefs[Layer 3: User Display Preferences]
    prefs -->|show/hide panels| render[Rendered page]

    note1[/Admin-controlled<br/>LCS Access Profile/]
    note2[/User-controlled<br/>LCS User Preferences/]

    note1 -.-> profile
    note2 -.-> prefs

    classDef admin fill:#fef3c7,stroke:#d97706;
    classDef user fill:#dcfce7,stroke:#16a34a;
    class profile,hook admin;
    class prefs user;
```

---

## Module boundaries

| Concern | Home | Rationale |
|---------|------|-----------|
| Core CRM UI & DocTypes | `repo/crm` (upstream) | Stays cherry-pick-compatible with Frappe's develop branch |
| LCS business entities (Project, Offer, Matrix, Team Member, Required Training, Offer Template, Access Profile, User Preferences) | `repo/lcs_integrations/lcs_integrations/lcs_integrations/doctype/` | Separate app → upstream merges never collide |
| ERPNext sync (Customer, Quotation, Sales Order) | `lcs_integrations/erpnext_sync/` | Hook-driven, one module per target doctype |
| Fusion Manage (PLM) | `lcs_integrations/fusion_manage/` | REST v3 client + hourly pull service |
| Cross-module orchestration (Sales Order → BSM Project, LMS training check, integration status) | `lcs_integrations/cross_module/` | Multi-app fan-out lives here, not in individual connectors |
| Visibility + access profiles | `lcs_integrations/visibility/` | `permission_query_conditions` + `has_permission` hooks + whitelisted get/set APIs |
| Outlook Add-in | `lcs_integrations/outlook_addin/` (API) + `www/outlook-addin/` (static) | Office.js manifest + task pane + commands; same-origin SSO |
| Offline sync | `frontend/src/utils/{offlineDB,syncEngine}.js` + `composables/useOfflineList.js` | Vanilla IndexedDB, FIFO mutation queue, field-level conflict detection |

---

## Cross-cutting concerns

- **Observability** — all connectors log through `frappe.log_error()` with namespaced category (`erpnext_sync.quotation`, `fusion_manage.sync`, `bsm_sync`). Dashboard at `/app/error-log?category_like=%sync%`.
- **Security** — every inbound webhook HMAC-signed or OAuth2 bearer; outbound secrets in Azure Key Vault; HTTPS + HSTS enforced on nginx.
- **Feature gating** — hooks.py auto-detects whether a target app is installed (`frappe.db.exists("DocType", "BSM Project")`); missing apps skip silently instead of raising.
- **Caching** — access profiles cached in Redis per-user, invalidated on profile or preferences save.
- **Auditability** — `LCS Offer` on_trash cleans forward links; `test_integration_e2e.py` + `check_production_duplicates.py` assert no orphans or duplicate one-to-one mappings.

---

## See also

- [Offline sync architecture](offline-sync.md)
- [Outlook Add-in](outlook-addin.md)
- [ERPNext + Fusion integrations](erpnext-fusion.md)
- [Visibility & access control](visibility-access.md)
- [Outlook delta sync](outlook-sync.md) (background email/calendar sync — separate from the add-in)
- [Proxess DMS](proxess-dms.md)
- [Lead scoring](lead-scoring.md)
