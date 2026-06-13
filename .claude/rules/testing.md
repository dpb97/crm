# Testing Rules

## Philosophy

- TDD: Write tests FIRST, then implement
- Tests are documentation — name them clearly
- Tests should be independent and idempotent

## Coverage Requirements

- 80% minimum code coverage
- 90%+ for domain/business logic
- Critical paths must have integration + E2E tests

## Test Structure (pytest)

```python
# Naming: test_<function>_<scenario>_<expected>
def test_get_item_details_with_valid_code_returns_item():
    """Valid item code returns correct item details."""
    # Arrange
    item = frappe.get_doc({
        "doctype": "Item",
        "item_code": "TEST-001",
        "item_name": "Test Item",
    }).insert()

    # Act
    result = get_item_details(item.item_code)

    # Assert
    assert result is not None
    assert result["item_name"] == "Test Item"
```

## Test Structure (React — Vitest)

```typescript
import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { ItemView } from "./ItemView";

describe("ItemView", () => {
  it("renders item name when data is loaded", async () => {
    render(<ItemView itemCode="TEST-001" />);
    expect(await screen.findByText("Test Item")).toBeInTheDocument();
  });
});
```

## Test Types

| Type        | Location              | What to Test                              |
|-------------|-----------------------|-------------------------------------------|
| Unit        | `tests/unit/`         | Utils, services, business logic           |
| Integration | `tests/integration/`  | API endpoints, DocType workflows, DB      |
| E2E         | `tests/e2e/`          | Critical user flows (Playwright/Cypress)  |
| DocType     | `<doctype>/test_*.py` | DocType controller logic (Frappe runner)  |

## Libraries

- **pytest** — Python test framework
- **frappe.tests** — Frappe test runner and utilities
- **unittest.mock** / **pytest-mock** — Mocking
- **Factory Boy** — Test data generation
- **Vitest** — TypeScript/React test framework
- **Testing Library** — React component testing
- **Playwright** — E2E browser testing

## Rules

- No `time.sleep` in tests — use proper waits or async patterns
- No test interdependencies
- Clean up test data (use `frappe.set_user("Administrator")` + rollback)
- Test edge cases: None, empty, boundary values
- Mock external dependencies, not your own code
- Use `frappe.tests.utils.FrappeTestCase` for DocType tests
