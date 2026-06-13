# docs/api -- API Documentation

API endpoint documentation and integration guides for Frappe whitelisted APIs.

## What Belongs Here

| File / Folder               | Purpose                                    |
|-----------------------------|--------------------------------------------|
| `endpoints.md`              | Human-readable endpoint reference          |
| `authentication.md`         | Auth flow documentation (Frappe + MSAL)    |
| `error-codes.md`            | Error code reference with descriptions     |
| `examples/`                 | Request/response examples                  |

## Rules

- Document all `@frappe.whitelist()` endpoints
- Include permission requirements for each endpoint
- Document error responses and codes
- Include authentication examples (Frappe session + MSAL)
- Version the API docs alongside the code

## API Response Convention

Frappe wraps all responses in `{"message": ...}` automatically.

For custom structured responses:

```json
{
  "message": {
    "success": true,
    "data": { ... },
    "error": null
  }
}
```

Error response:

```json
{
  "exc_type": "ValidationError",
  "exception": "frappe.exceptions.ValidationError: ...",
  "_server_messages": "[\"Validation failed: ...\"]"
}
```

## Endpoint Documentation Template

```markdown
### get_item_details

**Method:** `my_app.api.items.get_item_details`
**Permission:** Item (read)

**Args:**
| Param     | Type   | Required | Description       |
|-----------|--------|----------|-------------------|
| item_code | string | Yes      | The item code     |

**Returns:**
```json
{
  "item_code": "ITEM-001",
  "item_name": "Widget",
  "stock_uom": "Nos"
}
```
```
