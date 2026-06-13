---
description: Review code for quality, security, and maintainability
---

# /code-review

## Purpose

Perform a thorough code review checking quality, security, and patterns.

## Checklist

1. **Architecture** -- Correct Frappe patterns, proper module placement
2. **Security** -- No hardcoded secrets, input validation, SQL injection prevention
3. **Testing** -- Adequate test coverage, meaningful assertions
4. **Code Style** -- Python/TS naming conventions, file size, complexity
5. **Performance** -- N+1 queries, missing pagination, proper use of Frappe ORM
6. **Error Handling** -- Proper Frappe exceptions, `frappe.log_error()`, translatable messages
7. **Permissions** -- `frappe.has_permission()` on all APIs, proper DocType permissions
8. **Documentation** -- Docstrings on public functions, updated README

## Output

A structured review with severity levels:
- **Critical** -- Security issues, data loss risks, missing permissions
- **Major** -- Architecture violations, missing tests, SQL injection
- **Minor** -- Style issues, naming improvements
- **Suggestion** -- Nice-to-have improvements
