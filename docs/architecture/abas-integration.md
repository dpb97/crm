# abas ERP Integration

Bidirectional sync between CRM (`CRM Lead`, `CRM Deal`, `Contact`) and abas
(`Customer`, `Quotation`, `Order`). See
[`lcs_integrations/lcs_integrations/abas/`](../../lcs_integrations/lcs_integrations/abas/)
for the implementation.

## Outbound · CRM → abas

```mermaid
sequenceDiagram
    autonumber
    participant U as Sales user
    participant C as CRM Deal form
    participant H as lcs.abas.hooks
    participant Q as Frappe job queue
    participant S as lcs.abas.service
    participant A as abas REST
    participant M as ABAS Entity Map

    U->>C: save Deal (qualified)
    C->>H: on_deal_created
    H->>Q: enqueue push_customer(deal.name)
    Q->>S: push_customer
    S->>A: POST /customers (HMAC-signed)
    A-->>S: 201 Created, abas_id=K12345
    S->>M: upsert (deal.name ↔ K12345)
    S-->>C: set deal.abas_id = K12345
```

Key properties:

- **Idempotent** — `ABAS Entity Map` carries a unique constraint on `abas_id`; re-running `push_customer` is a no-op once the mapping exists.
- **Async** — the hook only enqueues a job. Save latency stays inside the UI budget even when abas is slow.
- **Signed** — `AbasClient` signs every request with HMAC-SHA256 (`X-LCS-Timestamp`, `X-LCS-Signature`). The shared secret rotates quarterly through Azure Key Vault.
- **Retried** — `tenacity` retries transient 5xx with exponential backoff, 3 attempts, capped at 30 s; after that the job fails and surfaces in `ABAS Sync Log`.

## Inbound · abas → CRM (delivery webhook)

```mermaid
sequenceDiagram
    autonumber
    participant A as abas
    participant N as Nginx (rate-limit 30 r/s)
    participant W as /api/method/.../webhook
    participant V as verify_inbound
    participant S as lcs.abas.service
    participant L as ABAS Sync Log

    A->>N: POST /webhook + X-LCS-Signature
    N->>W: forward
    W->>V: verify HMAC + timestamp skew < 300 s
    alt valid
        V->>S: handle_delivery_webhook
        S->>L: insert(direction=inbound, status=ok)
        W-->>A: 200 OK
    else invalid
        V-->>W: raise PermissionError
        W-->>A: 401
        W->>L: insert(status=error, error=...)
    end
```

## Nightly reconciliation

```mermaid
flowchart LR
    cron["Frappe scheduler<br/>03:15 daily"] --> rec[reconcile_delta]
    rec -->|last successful cursor| abas[(abas delta endpoint)]
    abas --> rec
    rec -->|diffs| deals[(CRM Deal)]
    rec -->|diffs| customers[(Customer)]
    rec -->|entry per run| log[(ABAS Sync Log)]
```

`reconcile_delta` reads the latest successful cursor from `ABAS Sync Log`,
asks abas for everything that changed since, and replays the diff into CRM.
The cursor is stored per entity type so one failing entity does not stall the
others.

## Data contracts

All payloads are typed via Pydantic DTOs in
[`schemas.py`](../../lcs_integrations/lcs_integrations/abas/schemas.py):
`AbasCustomer`, `AbasContact`, `AbasQuotationHeader`, `AbasOrderHeader`,
`DeliveryStatusEvent`. These are the single source of truth for the
integration — any abas schema drift must be handled here, never inline in
service code.

## Failure modes

| Mode                  | Detection                            | Mitigation                                                         |
| --------------------- | ------------------------------------ | ------------------------------------------------------------------ |
| abas returns 5xx      | `tenacity` retry exhaustion           | Job re-queued via Frappe's dead-letter queue, alert raised.        |
| HMAC mismatch inbound | `verify_inbound` raises               | Request rejected with 401, logged to `ABAS Sync Log` with payload. |
| Clock skew > 300 s    | Timestamp check in `verify_inbound`   | Same — prevents replay attacks.                                     |
| Duplicate abas_id     | `ABAS Entity Map` unique constraint   | `_upsert_entity_map` updates instead of inserting.                  |
