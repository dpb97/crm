# ADR 0002 — PostgreSQL 16 as primary datastore

- Status: Accepted
- Date: 2026-04-16
- Related: ADR 0001

## Context

The upstream Frappe CRM defaults to MariaDB 10.6/10.8 (see
`docker/docker-compose.yml`). The LCS organization standard requires PostgreSQL
16 for all new projects. Frappe ≥ v14 supports Postgres as an alternative via
`db_type = "postgres"` in `site_config.json`.

## Decision

All sites run on PostgreSQL 16 (`postgres:16-alpine` image). MariaDB is used
only where upstream integration tests explicitly require it and is never
deployed to staging or production.

## Consequences

Positive:
- Aligns with the organization database standard.
- Reuses LCS backup, monitoring and DR tooling already standardized on Postgres.
- `Npgsql`-compatible data for future C# services that consume the same data.

Negative / mitigations:
- Some community apps assume MariaDB syntax. We mitigate by running the full
  test suite on Postgres in CI before merging any upstream change.
- `bench` must be invoked with `--db-type postgres`. Documented in
  `scripts/bootstrap_wsl.sh` and `docker/docker-compose.dev.yml`.

Migration plan:
- New sites only. There is no existing production data to migrate.
