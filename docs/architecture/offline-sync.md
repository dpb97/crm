# Offline Edit Sync

LCS sales and field users work from trucks, ski lifts, and construction
sites where connectivity is spotty at best. This doc covers how the CRM
UI keeps working when the network drops — and how it reconciles the
edits with the server when it comes back.

---

## Design goals

1. **Writes never get lost.** Every edit is captured in IndexedDB before
   it leaves the UI thread; even a hard reload doesn't drop work.
2. **Reads keep working.** List queries and opened project records are
   cached so the UI renders instantly on reconnect, not blank.
3. **Conflicts are visible.** If another user changed the same field
   on the server while we were offline, we surface the three values
   (mine / server / base) and let the user pick — never silently
   overwrite.
4. **Zero new runtime deps.** Uses vanilla IndexedDB, not `idb` — the
   bundle stays small.

---

## Architecture

```mermaid
flowchart LR
    ui[LCS Project page<br/>updateField] -->|optimistic| local[IndexedDB<br/>cache store]
    ui -->|queue| queue[IndexedDB<br/>mutations store]

    queue -->|drain| sync[syncEngine<br/>FIFO + backoff]
    sync -->|GET| verify[frappe.client.get<br/>current doc]
    verify --> check{base_values<br/>changed?}

    check -->|no| push[frappe.client.set_value]
    push -->|200 OK| persist[remove from queue<br/>update cache]

    check -->|yes| conflict[status=conflict<br/>store 3 values per field]
    conflict --> drawer[OfflineIndicator<br/>banner opens drawer]
    drawer -->|user clicks| resolver[ConflictResolver.vue<br/>Mine | Theirs | Custom]
    resolver -->|resolution| queue

    indicator[OfflineIndicator<br/>top banner] -.-|listens| queue
```

---

## IndexedDB schema

Database: `lcs-offline-v1`, three object stores.

### `mutations`

Auto-increment key. Index on `status`, `timestamp`, `(doctype, name)`.

| field | type | purpose |
|-------|------|---------|
| `doctype`, `name` | string | target record |
| `method` | 'insert' \| 'update' \| 'delete' | operation |
| `params` | object | fieldname → new value |
| `base_values` | object | fieldname → value *at queue time* — used for conflict detection |
| `base_modified` | string | doc.modified at queue time (future: optimistic locking) |
| `status` | 'pending' \| 'syncing' \| 'failed' \| 'conflict' \| 'done' | state |
| `retry_count` | int | exponential backoff counter |
| `error` | string | last error message |
| `conflicts` | object | `{ field: { base, server, local } }` when status=conflict |

### `cache`

Keyed by `${doctype}:${name}`. Stores the last known server state of
single documents so `useOfflineDoc` can serve reads when offline.

### `lists`

Keyed by `list:${doctype}:${hash(filters+fields+orderBy)}`. Stores list
query results for the offline-aware `useOfflineList` composable.

---

## Conflict detection — field-level, not row-level

The naive implementation ("if doc.modified changed, conflict") is too
noisy — most saves bump `modified` but touch unrelated fields.

Our detector is field-scoped:

```python
for field in mutation.params:
    base    = mutation.base_values[field]  # what we saw when we queued
    server  = current_doc[field]           # what the server has now
    local   = mutation.params[field]       # what we want to write
    if base != server:
        conflicts[field] = { base, server, local }
```

A mutation that only changed `notes` is *never* blocked by someone else
changing `phase` on the same record. The two writes compose cleanly.

Values are compared via `valuesEqual()` which normalises Frappe's
inconsistent empty-vs-null-vs-zero representations.

---

## Conflict resolution UI

`ConflictResolver.vue` renders one row per conflicted field with three
columns:

- **Mine (offline)** — the value I typed
- **Theirs (server)** — what someone else wrote while I was offline
- **Custom** — free-text override if neither is right

Plus two one-click bulk actions at the footer: *Keep all mine* / *Use
all server*.

On "Apply Resolution" we update `mutation.params` with the chosen
values, rewrite `base_values` to the current server state (so a
re-conflict on the same fields becomes impossible), set status back
to `pending`, and drain — the sync engine replays immediately.

---

## Retry + backoff

Exponential backoff: 1s, 2s, 4s, 8s, 16s. Max 5 retries, then status →
`failed`. Users can manually `Retry` or `Discard` individual mutations
from the drawer.

`conflict` status sits forever (no auto-retry) — conflicts require
human judgment.

---

## What still lives on the server

- Permission checks — we still hit `frappe.client.set_value`, so
  access profile filters apply. An offline edit against a record the
  user is no longer allowed to write fails gracefully with status=failed.
- Validation — Frappe-side `validate()` and `on_update()` hooks run
  on replay. A queued value rejected by validation becomes `failed`
  with the validation error as `mutation.error`.

---

## Caveats

- **List cache freshness.** `useOfflineList` returns stale data with a
  visible "cached (3m)" chip. Users see the last-known list until a
  background refetch completes.
- **Insert not wired into UI yet.** The queue supports `method=insert`
  but no page currently queues inserts — new project / new offer
  dialogs still require the user to be online. Wiring is a one-line
  change in each dialog's submit handler.
- **Cross-tab sync.** Queue changes broadcast via a custom event +
  `storage` event so multiple tabs stay consistent. Service Worker
  background sync is out of scope for Phase 1.

---

## Testing

Manual test recipe:

1. Open `/crm/projects/LCS-PROJ-2026-0001` in two tabs.
2. Tab 1: DevTools → Network → *Offline*.
3. Tab 1: edit Notes, save. "Saved offline" toast.
4. Tab 2: edit Notes on same record, save. Server now has different value.
5. Tab 1: Network → *Online*. Orange banner "1 conflict".
6. Click banner → drawer → git-merge icon → ConflictResolver.
7. Pick Mine / Theirs / Custom → Apply Resolution.
8. Queue drains, banner disappears, both tabs converge.
