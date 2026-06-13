---
description: Test-driven development workflow
---

# /tdd

## Purpose

Enforce TDD methodology: Red-Green-Refactor.

## Workflow

1. **RED** -- Write a failing test that defines the expected behavior
2. **GREEN** -- Write the minimum code to make the test pass
3. **REFACTOR** -- Clean up code while keeping tests green
4. **VERIFY** -- Run all tests, check coverage >= 80%

## Rules

- Never write production code without a failing test first
- One test at a time
- Keep tests small and focused
- Use assert statements with clear messages
- Name tests: `test_<function>_<scenario>_<expected>`
- Use `frappe.tests.utils.FrappeTestCase` for DocType tests
- Use pytest for unit tests outside Frappe context
