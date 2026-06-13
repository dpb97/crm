# docs/ -- Documentation

All project documentation lives here, organized by purpose.

## Structure

```
docs/
|-- api/            # API documentation
|-- architecture/   # Architecture decisions and diagrams
|-- guides/         # Developer guides and how-tos
```

## What Goes Where

| Folder         | Content                                          |
|----------------|--------------------------------------------------|
| `api/`         | API endpoint docs, whitelisted function reference |
| `architecture/`| ADRs, system diagrams, data models, tech choices |
| `guides/`      | Onboarding, development setup, deployment guides |

## Documentation Principles

1. **Keep docs close to code** -- update docs when code changes
2. **Architecture Decision Records (ADRs)** -- document WHY, not just WHAT
3. **Up-to-date API docs** -- document all whitelisted endpoints
4. **Onboarding guide** -- new developers should be productive in < 1 day

> **Tip:** Use `/plan` Claude command to generate documentation alongside implementation plans.
