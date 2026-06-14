# tests/ — Test Suite

Zusätzliche Test-Suiten (Unit/Integration/E2E). DocType-Controller-Tests liegen
direkt am DocType (`<app>/<module>/doctype/<name>/test_<name>.py`, Frappe-Runner).

## Test Structure

```
tests/
|-- conftest.py                       # Shared pytest fixtures
|-- unit/                             # Fast, isolated unit tests
|   |-- test_validators.py
|   |-- test_services.py
|-- integration/                      # Tests with real Frappe site / DB
|   |-- test_api.py
|   |-- conftest.py
|-- e2e/                              # End-to-end (optional, Playwright)
    |-- playwright.config.ts
```

## Quick Setup

```bash
# Frappe-Runner (DocType-Tests, voller Kontext)
bench --site lcs.local run-tests --app <app>

# pytest (Unit-Tests außerhalb des Frappe-Kontexts)
cd apps/<app> && python -m pytest tests/unit/ -v --cov=<app> --cov-report=html

# Frontend-Tests (Vitest, falls Frontend vorhanden)
cd apps/<app>/frontend && npm test

# E2E (Playwright)
cd apps/<app>/tests/e2e && npx playwright test
```

## Test Examples

### Unit Test (pytest)

```python
from <app>.utils.validators import validate_item_code


def test_validate_item_code_with_valid_code_returns_true():
    """Valid item code passes validation."""
    assert validate_item_code("ITEM-001") is True
```

### Integration Test (Frappe)

```python
import frappe
from frappe.tests.utils import FrappeTestCase
from <app>.api.items import get_item_details


class TestItemAPI(FrappeTestCase):
    def setUp(self):
        self.item = frappe.get_doc({
            "doctype": "Item",
            "item_code": "TEST-INT-001",
            "item_name": "Integration Test Item",
            "item_group": "All Item Groups",
        }).insert()

    def test_get_item_details_returns_correct_data(self):
        result = get_item_details(self.item.item_code)
        self.assertEqual(result["item_name"], "Integration Test Item")

    def tearDown(self):
        frappe.delete_doc("Item", self.item.name, force=True)
```

### Vue Component Test (Vitest)

```js
import { mount } from "@vue/test-utils";
import { describe, it, expect, vi } from "vitest";
import ItemView from "../components/ItemView.vue";

describe("ItemView", () => {
  it("renders item name when data is loaded", async () => {
    vi.stubGlobal("frappe", {
      call: ({ callback }) => callback({ message: { item_name: "Test Item" } }),
    });
    const wrapper = mount(ItemView, { props: { itemCode: "TEST-001" } });
    await new Promise((r) => setTimeout(r));
    expect(wrapper.text()).toContain("Test Item");
  });
});
```

## Rules

- Name tests: `test_<function>_<scenario>_<expected>`
- Arrange/Act/Assert; clean up test data (`frappe.db.rollback()` oder explizit)
- No `time.sleep` — proper waits/async; keine Test-Interdependenzen
- Mock external dependencies (APIs, E-Mail), nicht den eigenen Code
- 80% minimum coverage; 90%+ für Business-Logik
