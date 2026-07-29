/**
 * Offline Prefetch — proactively warms the IndexedDB document cache so
 * field staff have the core CRM data available offline WITHOUT having to
 * visit every record first (useOfflineDoc only caches what was opened).
 *
 * Strategy per core doctype:
 *   1. get_list (all top-level fields, newest first) → cachePut per row.
 *      Covers list rendering and basic detail views.
 *   2. For the N most recently modified records additionally fetch the
 *      FULL document via frappe.client.get (child tables included) —
 *      same call + cache key useOfflineDoc uses, so detail pages hit
 *      the exact same cache entries.
 *
 * Runs after login and on every reconnect, throttled to once per
 * 30 minutes (localStorage timestamp) to stay cheap on mobile data.
 */

import { call } from 'frappe-ui'
import { cachePut } from './offlineDB'

const CORE_DOCTYPES = [
  { doctype: 'CRM Deal', fullDocs: 25 },
  { doctype: 'CRM Lead', fullDocs: 25 },
  { doctype: 'CRM Organization', fullDocs: 0 },
  { doctype: 'Contact', fullDocs: 0 },
  // LCS Vertrieb core — projects, offers and tasks must be readable offline
  // on site too (they back the project pipeline, the offer workflow and the
  // task lists). Full docs for projects/offers so detail pages incl. child
  // tables (approvals, relations, versions) open without a connection.
  { doctype: 'LCS Project', fullDocs: 25 },
  { doctype: 'LCS Offer', fullDocs: 25 },
  { doctype: 'LCS Sales Territory', fullDocs: 0 },
  { doctype: 'LCS Segment', fullDocs: 0 },
  { doctype: 'ToDo', fullDocs: 0 },
]

const LIST_LIMIT = 200
const THROTTLE_MS = 30 * 60 * 1000
const LS_KEY = 'lcs-offline-prefetch-at'

export async function prefetchOfflineData(force = false) {
  if (!navigator.onLine) return
  const last = Number(localStorage.getItem(LS_KEY) || 0)
  if (!force && Date.now() - last < THROTTLE_MS) return
  localStorage.setItem(LS_KEY, String(Date.now()))

  for (const { doctype, fullDocs } of CORE_DOCTYPES) {
    try {
      const rows = await call('frappe.client.get_list', {
        doctype,
        fields: ['*'],
        limit_page_length: LIST_LIMIT,
        order_by: 'modified desc',
      })
      for (const row of rows || []) {
        await cachePut(doctype, row.name, row)
      }
      // Full documents (child tables etc.) for the hottest records —
      // sequential on purpose: background task, don't hammer the server.
      for (const row of (rows || []).slice(0, fullDocs)) {
        try {
          const doc = await call('frappe.client.get', { doctype, name: row.name })
          await cachePut(doctype, doc.name, doc)
        } catch (e) {
          // permission or race — skip this record, keep going
        }
      }
    } catch (e) {
      console.warn(`offlinePrefetch: ${doctype} failed`, e)
    }
  }
}

/** Wire once from App.vue — initial warm-up + refresh on reconnect. */
export function startOfflinePrefetch() {
  // Delay the first run so it never competes with initial page load
  setTimeout(() => prefetchOfflineData(), 8000)
  window.addEventListener('online', () => prefetchOfflineData())
}
