## Description

Brief description of what this PR does.

Closes #<issue-number>

## Type of Change

- [ ] `feat` -- New feature
- [ ] `fix` -- Bug fix
- [ ] `refactor` -- Code restructure (no behavior change)
- [ ] `docs` -- Documentation
- [ ] `test` -- Tests
- [ ] `chore` -- Build / CI / tooling

## Changes Made

- Change 1
- Change 2

## Testing

- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] All existing tests pass (`bench run-tests`)
- [ ] Tested manually

## Checklist

- [ ] Code follows project coding style (Ruff + ESLint)
- [ ] No hardcoded secrets or credentials
- [ ] No `print()` -- using `frappe.logger()` or `frappe.log_error()`
- [ ] API endpoints have permission checks (`frappe.has_permission()`)
- [ ] Frappe patches included in `patches.txt` (if schema changed)
- [ ] PR is focused and < 400 lines changed
