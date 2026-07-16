# lcs_integrations

LCS-specific Frappe app that adds the abas ERP connector, Proxess DMS
integration, Outlook (MS Graph) email sync, MSAL/OIDC single sign-on and the
rules-based lead scoring engine to the Frappe CRM fork.

See `docs/architecture/` in the repository root for the system diagrams and
`docs/adr/` for the accepted decisions that shape this app.

## Install (inside an existing bench)

```bash
bench get-app /path/to/this/repo/lcs_integrations
bench --site <site> install-app lcs_integrations
bench --site <site> migrate
```

## Layout

- `abas/`          — bidirectional sync with abas ERP
- `proxess/`       — Proxess DMS upload + document linking
- `outlook_sync/`  — Microsoft Graph mailbox delta sync
- `msal_sso/`      — Entra OIDC social login provider
- `lead_scoring/`  — configurable rule engine
- `email_domain_autolink/` — auto-link incoming mail to Customer by sender domain
- `doctype/`       — new DocTypes (sync logs, mappings, bindings, rules)
- `fixtures/`      — Custom fields for upstream DocTypes (Lead, Deal, Contact)

## Tests

Unit tests use `pytest`; integration tests require a live Frappe test site
(`bench --site test_site run-tests --app lcs_integrations`).
