# ADR 0001 — Adapt Frappe CRM instead of a greenfield C#/React build

- Status: Accepted
- Date: 2026-04-16
- Deciders: Head of IT (LCS Group), JustRelate Scoping Workshop attendees
- Related: ADR 0002 (Postgres), ADR 0003 (MSAL/OIDC)

## Context

The LCS organization standard (`~/.claude/CLAUDE.md`) mandates C# ASP.NET Core 8+
backend and a React frontend for new projects. The starting point for the CRM
initiative, however, is a fork of the upstream open-source Frappe CRM
(`frappe/crm`), which is written in Python on the Frappe framework with a Vue 3
frontend.

The LCS minimum feature set (see `SystemDesigne/Re Anfrage Richtpreis – …`)
requires email sync, abas ERP two-way sync, Proxess DMS integration, lead
management and delivery-status surfacing — capabilities that Frappe CRM already
covers roughly 70% of out of the box (Leads, Deals, Contacts, Tasks, Calls,
Communications, WhatsApp, Role/User permissions).

Rebuilding these capabilities greenfield would consume the full budget envelope
discussed with JustRelate (5–7 PT for training + significant custom build) and
delay the Scoping Workshop goal of having a production-capable system.

## Decision

We adapt the existing `dpb97/crm` Frappe fork rather than start a greenfield
C#/React codebase. All LCS-specific customization lives in a dedicated Frappe
app `lcs_integrations` inside this monorepo so the upstream `crm` app remains
merge-compatible with `frappe/crm`.

## Consequences

Positive:
- Feature parity for ≥70% of the minimum feature set on day one.
- Upstream security fixes and UI improvements remain cherry-pickable.
- Python/Vue ecosystem is well-understood by the existing IT team.

Negative (tracked as exceptions to organisation standards):
- Backend language differs from the C# standard. Accepted because the effort to
  replicate Frappe's metadata-driven form engine in C# is not justified by
  business value.
- Frontend framework differs from React. Accepted because Frappe UI is already
  Tailwind-based, which complies with the CSS standard.

Follow-ups:
- Team Lead sign-off to be captured in the meeting minutes of the kickoff.
- `lcs_integrations` CI/CD pipelines target the same GHCR registry and follow
  the LCS security standards (CodeQL, Dependabot, Trivy, secret scanning).
