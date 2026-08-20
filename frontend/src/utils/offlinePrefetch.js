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

import { reactive } from 'vue'
import { call } from 'frappe-ui'
import { cachePut } from './offlineDB'
import { mirrorPut } from './swMirror'

// Live progress for the offline download, surfaced in the OfflineIndicator so
// the user can see how much is being cached / is available offline.
export const prefetchProgress = reactive({
  running: false,   // a warm-up is in progress
  total: 0,         // number of doctypes to warm
  done: 0,          // doctypes finished
  current: '',      // doctype currently warming
  records: 0,       // records written into IndexedDB so far
  finishedAt: 0,    // ms timestamp of the last completed run
})

// fullDocs: how many records to additionally fetch as FULL documents (incl.
// child tables) so their detail pages are 100% offline. 100000 ≈ "all". The
// list rows (cached for EVERY record) already let detail pages OPEN offline via
// the useDocument cache fallback; full docs add the child-table completeness.
const CORE_DOCTYPES = [
  { doctype: 'CRM Deal', fullDocs: 100000 },
  { doctype: 'CRM Lead', fullDocs: 100000 },
  { doctype: 'CRM Organization', fullDocs: 100000 },
  // Contacts: cache EVERY contact fully (incl. child tables) — the user wants
  // all contacts offline; the mail thread is skipped (see DETAIL_METHODS).
  { doctype: 'Contact', fullDocs: 100000 },
  // LCS Vertrieb core — full docs so detail pages incl. child tables (approvals,
  // relations, versions, matrix) open without a connection.
  { doctype: 'LCS Project', fullDocs: 100000 },
  { doctype: 'LCS Offer', fullDocs: 100000 },
  // Chances back BOTH the Chancen funnel and the Pilot scout page (unrated hits
  // are LCS Chance, source Pilot-Scout) — pre-warm so both open offline.
  { doctype: 'LCS Chance', fullDocs: 100000 },
  { doctype: 'LCS Sales Territory', fullDocs: 0 },
  { doctype: 'LCS Segment', fullDocs: 0 },
  { doctype: 'ToDo', fullDocs: 0 },
  // Calls + notes as raw records too (their pages also read via get_* methods).
  { doctype: 'CRM Call Log', fullDocs: 0 },
  { doctype: 'FCRM Note', fullDocs: 0 },
  // Small lookup doctypes so status pills / territory labels render offline.
  { doctype: 'CRM Lead Status', fullDocs: 0 },
  { doctype: 'CRM Deal Status', fullDocs: 0 },
  { doctype: 'CRM Communication Status', fullDocs: 0 },
  { doctype: 'CRM Territory', fullDocs: 0 },
]

// 0 = every row (the whole table). The user wants ALL data available offline,
// so the list warm-up is no longer capped — the per-doctype full-document
// fetches below stay bounded (those are the expensive ones).
const LIST_LIMIT = 0
const THROTTLE_MS = 30 * 60 * 1000
const LS_KEY = 'lcs-offline-prefetch-at'
// Bump whenever CORE_DOCTYPES / METHOD_WARM change — a version mismatch forces
// one full re-warm (ignoring the throttle) so a client picks up the wider set.
const PREFETCH_VERSION = '6'
const LS_VER = 'lcs-offline-prefetch-ver'

export async function prefetchOfflineData(force = false) {
  if (!navigator.onLine) return
  const verChanged = localStorage.getItem(LS_VER) !== PREFETCH_VERSION
  const last = Number(localStorage.getItem(LS_KEY) || 0)
  if (!force && !verChanged && Date.now() - last < THROTTLE_MS) return
  localStorage.setItem(LS_KEY, String(Date.now()))
  localStorage.setItem(LS_VER, PREFETCH_VERSION)

  prefetchProgress.running = true
  prefetchProgress.total = CORE_DOCTYPES.length
  prefetchProgress.done = 0
  prefetchProgress.records = 0
  prefetchProgress.current = ''

  for (const { doctype, fullDocs } of CORE_DOCTYPES) {
    prefetchProgress.current = doctype
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
      prefetchProgress.records += (rows || []).length
      // Write the list rows straight into the service-worker IndexedDB store so
      // offline get_list reads (offlineListFallback) find them — no dependency
      // on the SW having intercepted this very fetch.
      await mirrorPut(doctype, rows || [])
      // Full documents (child tables etc.) for the hottest records —
      // sequential on purpose: background task, don't hammer the server.
      const fulls = []
      for (const row of (rows || []).slice(0, fullDocs)) {
        try {
          const doc = await call('frappe.client.get', { doctype, name: row.name })
          await cachePut(doctype, doc.name, doc)
          fulls.push(doc)
        } catch (e) {
          // permission or race — skip this record, keep going
        }
      }
      // Overwrite the store rows with the full docs (incl. child tables).
      if (fulls.length) await mirrorPut(doctype, fulls)
      // Per-record detail sub-panels for the hottest records, so those detail
      // pages open FULLY offline (a project's offers + opportunity matrix, a
      // contact's mail thread, a chance's comments) — not just the main doc.
      const detail = DETAIL_METHODS[doctype]
      if (detail) {
        for (const row of (rows || []).slice(0, DETAIL_LIMIT)) {
          for (const d of detail) {
            try {
              await call(d.m, d.args(row))
            } catch (e) {
              /* permission / race — skip */
            }
          }
        }
      }
    } catch (e) {
      console.warn(`offlinePrefetch: ${doctype} failed`, e)
    }
    prefetchProgress.done += 1
  }

  // Warm the custom list-method endpoints too: the service worker caches every
  // get_* response keyed by method-path + args, so calling them here — with the
  // SAME args the pages use — makes those pages open offline without a prior
  // visit. Entries are either a bare method path (no args) or { m, args }.
  for (const entry of METHOD_WARM) {
    const m = typeof entry === 'string' ? entry : entry.m
    const args = typeof entry === 'string' ? undefined : entry.args
    try {
      await call(m, args)
    } catch (e) {
      /* not permitted / needs other args / not configured — skip */
    }
  }

  prefetchProgress.current = ''
  prefetchProgress.running = false
  prefetchProgress.finishedAt = Date.now()
}

const P = 'lcs_integrations.projects.api.'
const METHOD_WARM = [
  // Parameter-less list/analytics endpoints behind the LCS pages.
  P + 'get_pilot_hits',
  P + 'get_chances',
  P + 'get_pilot_users',
  P + 'get_call_logs',
  P + 'get_notes',
  P + 'get_market_assignment',
  P + 'get_project_geo',
  P + 'get_project_map_data',
  P + 'get_forecast',
  P + 'get_source_analytics',
  P + 'get_network_graph',
  P + 'get_dashboard_worklist',
  P + 'get_offer_templates',
  P + 'get_contact_email_counts',
  P + 'get_sales_meeting_lists',
  P + 'get_sales_meeting_dates',
  P + 'get_sales_dashboard',
  // Last-contact map is fetched per parent doctype — warm each variant the
  // Contacts / Firmen / Vertriebsprojekte pages request.
  { m: P + 'get_last_contact_dates', args: { doctype: 'Contact' } },
  { m: P + 'get_last_contact_dates', args: { doctype: 'CRM Organization' } },
  { m: P + 'get_last_contact_dates', args: { doctype: 'LCS Project' } },
]

// Per-record detail endpoints — warmed for the DETAIL_LIMIT most-recent records
// of each doctype so their detail pages open fully offline (sub-panels too).
// Bounded on purpose: warming every record's sub-data would be a huge download.
const DETAIL_LIMIT = 200
const DETAIL_METHODS = {
  'LCS Project': [
    { m: P + 'get_project_offers', args: (r) => ({ project: r.name }) },
    { m: P + 'get_opportunity_matrix', args: (r) => ({ project: r.name }) },
  ],
  // Contacts: mail thread is intentionally NOT prewarmed (large, and not needed
  // offline per request). All contacts are still fully cached via fullDocs below.
  'LCS Chance': [
    { m: P + 'get_chance', args: (r) => ({ name: r.name }) },
    { m: P + 'get_item_comments', args: (r) => ({ doctype: 'LCS Chance', name: r.name }) },
  ],
}

/** Wire once from App.vue — initial warm-up + refresh on reconnect. */
export function startOfflinePrefetch() {
  // Delay the first run so it never competes with initial page load
  setTimeout(() => prefetchOfflineData(), 8000)
  window.addEventListener('online', () => prefetchOfflineData())
}
