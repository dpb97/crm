import { defineConfig, devices } from '@playwright/test'

/**
 * LCS CRM Playwright config.
 *
 * Tests run against a local bench started by `scripts/bootstrap_wsl.sh`.
 * The base URL is read from the environment so CI can point at a preview
 * site without editing the config.
 */
const baseURL = process.env.LCS_CRM_BASE_URL ?? 'http://localhost:8000'

export default defineConfig({
  testDir: './tests',
  timeout: 30_000,
  expect: { timeout: 5_000 },
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [
    ['list'],
    ['html', { open: 'never', outputFolder: 'playwright-report' }],
  ],
  use: {
    baseURL,
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
})
