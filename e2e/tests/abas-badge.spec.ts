import { test, expect } from '@playwright/test'

/**
 * Visual presence check for the LCS SyncStatusBadge on a Deal detail page.
 * Requires the fixture Deal `DEAL-LCS-CI-FIXTURE` to exist with an
 * `abas_id` and an `ABAS Sync Log` entry in state `ok`.
 *
 * Until fixtures are seeded in CI this test is marked `@needs-fixtures` and
 * skipped. Removing the skip in a follow-up PR is tracked in the backlog.
 */

test.describe('abas SyncStatusBadge', () => {
  test.skip(true, 'fixture seeding not yet in CI')

  test('renders synchronised state on seeded deal', async ({ page }) => {
    await page.goto('/crm/deals/DEAL-LCS-CI-FIXTURE')
    const badge = page.locator('[data-test="lcs-sync-badge-abas"]')
    await expect(badge).toBeVisible()
    await expect(badge).toContainText('synchronised')
  })
})
