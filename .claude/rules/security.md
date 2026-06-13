# Security Rules

## Secrets Management

- NEVER hardcode secrets (API keys, passwords, connection strings)
- Use environment variables or Frappe `site_config.json` (dev), Azure Key Vault (prod)
- Always add secrets files to `.gitignore` (`site_config.json` is gitignored by bench)
- Rotate secrets regularly
- MSAL credentials only in environment variables, never in code

## Input Validation

- Validate ALL user input on the server side
- Use Frappe validators or custom validation functions
- Sanitize strings to prevent XSS — use `frappe.utils.escape_html()`
- Validate file uploads (type, size, content) via Frappe File DocType hooks

## Database Security

- Parameterized queries ONLY — never concatenate SQL strings
- Use Frappe ORM (`frappe.get_doc`, `frappe.get_list`, `frappe.db.get_value`)
- When raw SQL is needed: `frappe.db.sql(query, values=params, as_dict=True)`
- Principle of least privilege for DB users
- Never expose connection strings in logs or errors

## Authentication & Authorization

- Frappe built-in auth for development
- MSAL (Microsoft Identity / OIDC) for release/production builds
- Enforce HTTPS everywhere in production
- Use `frappe.has_permission()` for authorization checks
- Use `frappe.only_for()` for role-based access in whitelisted APIs
- Implement rate limiting on auth endpoints via Frappe rate limiter

## API Security

- Return generic error messages to clients — log details server-side with `frappe.log_error()`
- CSRF token is handled by Frappe automatically for cookie-based auth
- Set security headers (CSP, HSTS, X-Frame-Options) via Nginx or Frappe hooks
- Implement request rate limiting (`frappe.rate_limiter`)
- Log all authentication failures

## Dependency Security

- Keep pip/npm packages updated
- Run `pip-audit` and `npm audit` regularly
- Review transitive dependencies
- Use Dependabot or similar for automated updates
- Pin dependency versions in `pyproject.toml` and `package.json`
