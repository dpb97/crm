# LCS CRM — End-to-end tests

Playwright-based smoke + feature tests. Runs against a live bench site.

## Run locally

```bash
# 1. Start the dev stack (in another terminal)
cd ../
./scripts/bootstrap_wsl.sh  # first time only
bench start                 # brings up the Frappe site on :8000

# 2. Install Playwright browsers (first time only)
cd e2e
yarn install
yarn install-browsers

# 3. Run
yarn test                   # headless
yarn test:ui                # interactive, recommended for writing tests
```

## Environment

| Variable            | Default                     | Purpose                            |
| ------------------- | --------------------------- | ---------------------------------- |
| `LCS_CRM_BASE_URL`  | `http://localhost:8000`     | Target site. CI points at preview. |
