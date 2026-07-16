# ADR 0004 — Target ERPNext, not `frappe/crm`

- **Status:** Accepted · 2026-04-16
- **Supersedes in part:** ADR 0001 (which framed the adaptation as a
  `frappe/crm` fork).

## Context

The LCS production bench already runs:

- `frappe` 17-dev
- `erpnext` 17-dev
- `hrms` 17-dev
- `lcs_theme` (corporate branding for ERPNext Desk)
- `beveren_bsm` (construction-site management)

There is no `crm` app installed. ERPNext ships its own CRM modelling
(`Lead`, `Customer`, `Opportunity`, `Quotation`, `Sales Order`) that is
already in use.

Adding `frappe/crm` on top would create a second, parallel CRM datamodel
(`CRM Lead`, `CRM Deal`) and force operators to pick between two truths for
every customer record.

## Decision

`lcs_integrations` targets **ERPNext DocTypes**:

| Purpose                       | DocType         |
| ----------------------------- | --------------- |
| Lead capture + scoring        | `Lead`          |
| Customer master → abas push   | `Customer`      |
| Quotations → abas link        | `Quotation`     |
| Orders + delivery status      | `Sales Order`   |
| Contacts                      | `Contact`       |
| Inbound emails (auto-linking) | `Communication` |

ADR 0001 remains valid in spirit — we still accept Frappe over a greenfield
C#/React build — but the target CRM surface is ERPNext instead of
`frappe/crm`.

## Consequences

Positive:

- One CRM datamodel, not two. No duplicate customer records.
- Immediate integration with the existing LCS stack (no new app to install).
- Reuses `lcs_theme` for branding; no Vue SPA needed on the LCS bench.

Negative:

- The Vue components in `repo/frontend/src/components/lcs/` (built against
  frappe/crm's Vue SPA) are not directly usable against ERPNext's Desk,
  which is server-rendered. They are kept in-tree for a possible future
  frappe/crm scenario but are **not** deployed on `lcs.local`.
- The Playwright specs under `repo/e2e/tests/` need adjustment (ERPNext
  URLs differ from frappe/crm's `/crm/...` routes).

## Doctype migration notes

Every prior reference to `CRM Lead` / `CRM Deal` has been retargeted:

- `hooks.py` · `doc_events`: `CRM Lead` → `Lead`, `CRM Deal` → `Customer`.
- `patches/v1_0/install_custom_fields.py`:
  - `lcs_source`, `lcs_score` on `Lead`
  - `abas_id` on `Customer`
  - `abas_quotation_no` on `Quotation`
  - `abas_order_no`, `lcs_delivery_status`, `lcs_planned_ship_date`,
    `lcs_real_revenue` on `Sales Order`. ERPNext already ships a core
    `delivery_status` field with its own lifecycle — the LCS fields are
    `lcs_`-namespaced to avoid collision and to keep abas semantics
    (`Pending/Planned/Shipped/Delivered`) separate from ERPNext's
    (`Not Delivered/Fully Delivered/…`).
  - `abas_contact_id` on `Contact` (unchanged)
- `abas/hooks.py`: `on_deal_created/on_deal_updated` → `on_customer_created/on_customer_updated`.
- `abas/service.py` · `handle_delivery_webhook`: searches `Sales Order`, not `CRM Deal`.
- `lead_scoring/hooks.py`: `set_value("Lead", …)`.
