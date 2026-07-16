# Entra ID · App-Registration Runbook

One-time setup to connect LCS CRM to Microsoft Entra for SSO and to
Microsoft Graph for Outlook mail sync. Requires **Global Administrator** or
**Application Administrator** in the LCS tenant.

## 1 · Create the SSO app registration

1. Portal → **Microsoft Entra ID** → **App registrations** → *New registration*.
2. Name: `LCS CRM · SSO`.
3. Supported account types: *Accounts in this organizational directory only*.
4. Redirect URI: **Web** · `https://<your-crm-host>/api/method/frappe.integrations.oauth2_logins.custom` and add `http://localhost:8000/...` for dev.
5. Register.
6. **Certificates & secrets** → *New client secret* (24 months) → copy the
   **Value** into `.env` as `ENTRA_CLIENT_SECRET`. Never commit.
7. **API permissions** → *Add a permission* → *Microsoft Graph* → *Delegated*:
   `openid · profile · email · offline_access · User.Read`. Grant admin consent.
8. **Authentication** → *ID tokens* checkbox on.
9. Copy from **Overview**:
   - *Application (client) ID* → `.env` `ENTRA_CLIENT_ID`
   - *Directory (tenant) ID* → `.env` `ENTRA_TENANT_ID`

## 2 · Install the Social Login Key in Frappe

The `lcs_integrations` app registers an idempotent installer that creates /
updates the `Social Login Key` record named `entra` from the env vars above:

```bash
bench --site crm.lcs.local execute lcs_integrations.msal_sso.provider.install_or_update
```

Re-run after every secret rotation. CI runs it automatically on every
`bench migrate` via the `after_migrate` hook.

## 3 · Create the Graph (Outlook sync) app registration

Separate app → blast radius per credential stays small.

1. *New registration* · name `LCS CRM · Graph`.
2. **API permissions** → *Application* permissions on *Microsoft Graph*:
   `Mail.ReadBasic.All`, `Mail.Read`. Grant admin consent.
3. Client secret → 24 months → copy as `GRAPH_CLIENT_SECRET`.
4. Copy client-id / tenant-id to `GRAPH_CLIENT_ID` / `GRAPH_TENANT_ID`.

### Per-mailbox opt-in

Operators add a mailbox to the sync loop via the **Outlook Mailbox Binding**
DocType. Set `mailbox_upn` and `active = 1`; the scheduler picks it up on
the next 5-min tick.

## 4 · Validate

```bash
# SSO end-to-end
curl -I https://<host>/api/method/frappe.integrations.oauth2_logins.custom?provider=entra

# Graph token acquisition
bench --site crm.lcs.local execute \
    lcs_integrations.outlook_sync.graph_client.acquire_token_smoketest
```

## 5 · Rotation policy

| Secret                  | Cadence       | Owner          |
| ----------------------- | ------------- | -------------- |
| `ENTRA_CLIENT_SECRET`   | every 12 mo   | IT-SecOps      |
| `GRAPH_CLIENT_SECRET`   | every 12 mo   | IT-SecOps      |
| `ABAS_HMAC_KEY`         | every 3 mo    | Integrations   |
| `PROXESS_CLIENT_SECRET` | every 6 mo    | Integrations   |

Rotation procedure: store the new value in Azure Key Vault *alongside* the
old one, roll the CRM pods, confirm green metrics, then remove the old
value. Never hot-swap a secret without overlap.
