# tests/ — Test Suite

This folder is intentionally empty. Create your test structure here when scaffolding.

---

## Test Structure

```
tests/
|-- conftest.py                       # Shared pytest fixtures
|
|-- unit/                             # Fast, isolated unit tests
|   |-- __init__.py
|   |-- test_validators.py            # Utility/validator tests
|   |-- test_formatters.py            # Formatter tests
|   |-- test_services.py              # Service function tests
|
|-- integration/                      # Tests with real Frappe site / DB
|   |-- __init__.py
|   |-- test_api_items.py             # API endpoint tests
|   |-- test_invoice_workflow.py      # DocType workflow tests
|   |-- conftest.py                   # Integration-specific fixtures
|
|-- e2e/                              # End-to-end tests (optional)
    |-- playwright.config.ts          # Playwright configuration
    |-- tests/
        |-- test_login_flow.spec.ts   # Browser-based E2E tests
        |-- test_invoice_create.spec.ts
```

---

## In-App DocType Tests

Frappe places DocType tests alongside the DocType:

```
my_app/<module>/doctype/<doctype_name>/test_<doctype_name>.py
```

These are run by the Frappe test runner and have access to the full Frappe context.

---

## Quick Setup

```bash
# Create test directories
mkdir -p tests/unit tests/integration tests/e2e

# Create conftest.py with shared fixtures
cat > tests/conftest.py << 'EOF'
import frappe
import pytest


@pytest.fixture(autouse=True)
def setup_test_context():
    """Set up Frappe test context for each test."""
    frappe.set_user("Administrator")
    yield
    frappe.db.rollback()
EOF

# Run all tests (via Frappe test runner)
bench --site my-site.localhost run-tests --app my_app

# Run specific test module
bench --site my-site.localhost run-tests --module my_app.my_module.doctype.my_doctype.test_my_doctype

# Run pytest tests (for unit tests outside Frappe context)
cd apps/my_app
python -m pytest tests/unit/ -v

# Run with coverage
python -m pytest tests/ --cov=my_app --cov-report=html

# Run frontend tests (Vitest)
cd frontend
npm test

# Run E2E tests (Playwright)
cd tests/e2e
npx playwright test
```

---

## Test Examples

### Unit Test (pytest)

```python
from my_app.utils.validators import validate_item_code


def test_validate_item_code_with_valid_code_returns_true():
    """Valid item code passes validation."""
    # Arrange
    item_code = "ITEM-001"

    # Act
    result = validate_item_code(item_code)

    # Assert
    assert result is True


def test_validate_item_code_with_empty_string_raises():
    """Empty item code raises ValueError."""
    import pytest

    with pytest.raises(ValueError, match="Item code cannot be empty"):
        validate_item_code("")
```

### Integration Test (Frappe)

```python
import frappe
from frappe.tests.utils import FrappeTestCase
from my_app.api.items import get_item_details


class TestItemAPI(FrappeTestCase):
    def setUp(self):
        self.item = frappe.get_doc({
            "doctype": "Item",
            "item_code": "TEST-INT-001",
            "item_name": "Integration Test Item",
            "item_group": "All Item Groups",
        }).insert()

    def test_get_item_details_returns_correct_data(self):
        """API returns correct item details for valid code."""
        result = get_item_details(self.item.item_code)

        self.assertIsNotNone(result)
        self.assertEqual(result["item_name"], "Integration Test Item")

    def tearDown(self):
        frappe.delete_doc("Item", self.item.name, force=True)
```

### React Component Test (Vitest)

```typescript
import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { ItemView } from "../components/ItemView";

// Mock frappe.call
vi.stubGlobal("frappe", {
  call: vi.fn().mockImplementation(({ callback }) => {
    callback({
      message: {
        item_code: "TEST-001",
        item_name: "Test Item",
        stock_uom: "Nos",
      },
    });
  }),
});

describe("ItemView", () => {
  it("renders item name when data is loaded", async () => {
    render(<ItemView itemCode="TEST-001" />);
    expect(await screen.findByText("Test Item")).toBeInTheDocument();
  });
});
```

---

## Rules

- Name tests: `test_<function>_<scenario>_<expected>`
- Use Arrange/Act/Assert pattern
- Clean up test data (use `frappe.db.rollback()` or explicit deletion)
- No `time.sleep` — use proper waits or async patterns
- No test interdependencies — each test must be independent
- Mock external dependencies (APIs, email), not your own code
- 80% minimum coverage; 90%+ for business logic
dotnet add tests/MyApp.Integration.Tests reference src/MyApp.Infrastructure/MyApp.Infrastructure.csproj

# Add common test NuGet packages
dotnet add tests/MyApp.Unit.Tests package Moq
dotnet add tests/MyApp.Unit.Tests package FluentAssertions
dotnet add tests/MyApp.Unit.Tests package Bogus
dotnet add tests/MyApp.Integration.Tests package Microsoft.AspNetCore.Mvc.Testing
dotnet add tests/MyApp.Integration.Tests package Testcontainers.MsSql
```

---

## What Goes Where

| Project                    | Speed  | Dependencies         | What to Test                         |
|----------------------------|--------|----------------------|--------------------------------------|
| `MyApp.Unit.Tests`         | Fast   | None (mocked)        | Services, domain logic, validators   |
| `MyApp.Integration.Tests`  | Medium | Database, HTTP       | Repositories, API endpoints, EF Core |
| `MyApp.E2E.Tests`          | Slow   | Full running app     | Critical user journeys, workflows    |

---

## Running Tests

```powershell
# Run all tests
dotnet test

# Run only unit tests
dotnet test tests/MyApp.Unit.Tests

# Run with coverage
dotnet test --collect:"XPlat Code Coverage"

# Run filtered by name
dotnet test --filter "FullyQualifiedName~UserService"
```

---

## Test Method Naming

```
MethodName_Scenario_ExpectedResult
```

Examples:
- `GetById_WithValidId_ReturnsUser`
- `Create_WithDuplicateEmail_ThrowsConflictException`
- `Delete_WithNonExistentId_ReturnsNotFound`

## Coverage Target

- **80% minimum** overall
- **90%+** for domain and business logic
- Focus on meaningful tests, not coverage numbers

> Skip `MyApp.E2E.Tests` if you don't need end-to-end tests initially.
