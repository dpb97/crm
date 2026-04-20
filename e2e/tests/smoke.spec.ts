import { test, expect } from '@playwright/test'

/**
 * Smoke tests — minimum viable "the app is up" coverage.
 *
 * These must pass before a deploy is considered successful. Deep feature
 * coverage lives in topic-specific files (lead-create, abas-sync, …) that
 * should be added alongside each feature PR.
 */

test.describe('LCS CRM smoke', () => {
  test('login page is reachable', async ({ page }) => {
    const response = await page.goto('/login')
    expect(response?.ok()).toBeTruthy()
    await expect(page).toHaveTitle(/Login|Anmelden/i)
  })

  test('login page exposes Entra SSO', async ({ page }) => {
    await page.goto('/login')
    // The Entra Social Login Key is installed as provider "entra"; the
    // Frappe login page renders it with an href containing `provider=entra`.
    const entra = page.locator('a[href*="provider=entra"], button:has-text("Microsoft")')
    await expect(entra.first()).toBeVisible()
  })

  test('crm app shell loads', async ({ page }) => {
    const response = await page.goto('/crm')
    // 200 when already logged in, 302 → /login otherwise. Both are acceptable
    // for a smoke check; we only want to assert the route is wired.
    expect([200, 302]).toContain(response?.status() ?? 0)
  })
})
