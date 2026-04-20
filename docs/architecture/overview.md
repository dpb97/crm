# LCS CRM — Architecture Overview

Scope: adaptation of the upstream `frappe/crm` fork to LCS requirements.
For the "why" behind key technology choices see
[ADR 0001](../adr/0001-frappe-over-greenfield.md) ·
[ADR 0002](../adr/0002-postgres-over-mariadb.md) ·
[ADR 0003](../adr/0003-msal-oidc.md).

## C4 · Context

```mermaid
flowchart LR
    user([LCS Sales / Service user])
    entra[[Microsoft Entra ID<br/>OIDC]]
    outlook[[Microsoft Graph<br/>Mail / Calendar]]
    abas[[abas ERP<br/>REST + webhooks]]
    proxess[[Proxess DMS<br/>REST]]
    crm{{LCS CRM<br/>Frappe + Vue}}

    user -->|SSO login| entra
    user -->|daily work| crm
    crm -->|authenticate| entra
    crm <-->|email + calendar delta sync| outlook
    crm <-->|customer / quotation / order| abas
    crm <-->|document upload + retrieval| proxess
```

## C4 · Container

```mermaid
flowchart LR
    subgraph browser[Browser]
        vue[Vue 3 SPA<br/>frappe-ui + Tailwind]
    end

    subgraph host[Docker host]
        nginx[[Nginx<br/>TLS · HSTS · rate limit]]
        subgraph app[Frappe app container]
            crm[crm<br/>upstream]
            lcs[lcs_integrations<br/>LCS-owned]
        end
        queue[(Redis · queue)]
        cache[(Redis · cache)]
        socketio[(Redis · socketio)]
        pg[(PostgreSQL 16)]
    end

    vue -->|HTTPS| nginx
    nginx --> crm
    crm --> lcs
    crm --> pg
    crm --> queue
    crm --> cache
    crm --> socketio
    lcs -->|httpx| outlook[(Microsoft Graph)]
    lcs -->|httpx + HMAC| abas[(abas ERP)]
    lcs -->|httpx + OAuth2| proxess[(Proxess DMS)]
```

## Module boundaries

| Concern                         | Home                                          | Rationale                                                                   |
| ------------------------------- | --------------------------------------------- | --------------------------------------------------------------------------- |
| Core CRM UI & DocTypes          | `repo/crm` (upstream)                         | Stay cherry-pick-compatible with Frappe's `develop` branch.                 |
| LCS-specific DocTypes & hooks   | `repo/lcs_integrations`                       | Separate Frappe app → upstream merges never collide with LCS business rules. |
| External connectors             | `lcs_integrations/{abas,outlook_sync,proxess}` | One package per external system; each has its own client, service, schemas. |
| Authentication                  | Frappe Social Login Key (Entra) + MSAL token  | Single sign-on via Entra, no local password storage.                        |
| Infra                           | `docker/` + `scripts/bootstrap_wsl.sh`        | WSL2 dev, Docker/Compose for CI + prod.                                     |

## Cross-cutting concerns

- **Observability** — all connectors log through the Frappe log; `ABAS Sync Log`, `Outlook Mailbox Binding.last_error` and a dedicated `Error Log` category give operators a single place to triage.
- **Security** — every inbound webhook is HMAC-signed (abas) or OAuth2-bearer (Proxess); outbound calls rotate credentials via Azure Key Vault in production.
- **Feature gating** — `lcs_integrations/hooks.py` fixtures ship with the app; operators can disable a connector by setting `lcs.<system>.enabled = 0` in the site config.
