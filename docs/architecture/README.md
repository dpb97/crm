# docs/architecture -- Architecture Documentation

Architecture decisions, system diagrams, and technical design documents.

## What Belongs Here

| File / Folder               | Purpose                                    |
|-----------------------------|--------------------------------------------|
| `adr/`                      | Architecture Decision Records              |
| `diagrams/`                 | System/component/sequence diagrams         |
| `data-model.md`             | DocType relationships and entity model     |
| `tech-stack.md`             | Technology choices and rationale            |
| `deployment.md`             | Deployment architecture and environments   |

## Architecture Decision Records (ADRs)

Use ADRs to document significant architecture decisions.

### ADR Template

```markdown
# ADR-001: [Title]

## Status
Accepted | Proposed | Deprecated | Superseded by ADR-XXX

## Context
What is the issue we're facing? What forces are at play?

## Decision
What is the change we're proposing and/or doing?

## Consequences
What becomes easier or harder as a result?

## Alternatives Considered
What other options were evaluated?
```

### Naming Convention

`ADR-001-use-frappe-framework.md`

## System Overview

```
[Browser / React App]
        |
        v
[Nginx Reverse Proxy]
        |
    +---+---+
    |       |
    v       v
[Frappe   [Frappe
 Gunicorn  Socketio]
 Workers]
    |       |
    v       v
[MariaDB] [Redis]
```

## DocType Relationship Patterns

```
Parent DocType
  |-- Child Table (table field)
  |-- Link Field --> Other DocType
  |-- Dynamic Link --> Any DocType
```
    [SQL Server]  [External Services]
           ↓
    [Cache (Redis)]  ← optional
```
