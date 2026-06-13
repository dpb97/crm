---
description: Plan implementation for a new feature or change
---

# /plan

## Purpose

Create a detailed implementation plan before writing code.

## Usage

```
/plan "Add Invoice DocType with submission workflow"
```

## Workflow

1. Analyze the requirement
2. Identify affected Frappe components (DocTypes, APIs, hooks, frontend)
3. List files to create or modify
4. Define DocType schema and relationships
5. Plan Frappe patches (if schema changes needed)
6. Identify tests to write
7. Estimate complexity

## Output

A structured implementation plan with:
- Architecture decisions
- DocType definitions and relationships
- File list with descriptions
- Migration / patch plan
- Test plan
- Python / npm dependencies needed
