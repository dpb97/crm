# ADR 0003 — Authentication via MSAL / OIDC against LCS Entra tenant

- Status: Accepted
- Date: 2026-04-16
- Related: ADR 0001

## Context

The LCS organization standard mandates Microsoft Identity (MSAL) with OpenID
Connect as the only supported auth protocol. Frappe ships with its own cookie
session auth and supports OAuth / OIDC social logins via the Frappe
`Social Login Key` DocType.

The LCS directory (Entra ID) already owns all employee accounts that will use
the CRM; users must not maintain a separate password.

## Decision

- Enable Frappe's OIDC Social Login against the LCS Entra tenant as the only
  production login method.
- Local password login remains enabled only on developer sites (flag in
  `site_config.json`, disabled by default for any site named `lcs.*`).
- Outlook / MS Graph integration (see architecture doc `outlook-sync.md`) reuses
  the same app registration with delegated `Mail.ReadWrite` and `Mail.Send`
  scopes.

## Consequences

Positive:
- Single sign-on for all CRM users.
- Credential lifecycle is owned by IT via Entra (offboarding, MFA, conditional
  access) — the CRM stores no passwords.
- Reuses existing Entra app registrations for Outlook sync.

Negative / mitigations:
- An Entra outage blocks CRM access. Mitigated by keeping an emergency
  break-glass local admin (only active on request, disabled by default).
- Token refresh requires a background job keyed on `Outlook Mailbox Binding`.
  Implemented in `lcs_integrations.outlook_sync.delta_service`.
