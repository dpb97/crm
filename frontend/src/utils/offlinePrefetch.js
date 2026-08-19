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
  { doctype: 'CRM Deal', fullDocs: 50 },
  { doctype: 'CRM Lead', fullDocs: 50 },
  { doctype: 'CRM Organization', fullDocs: 25 },
  { doctype: 'Contact', fullDocs: 25 },
  // LCS Vertrieb core — projects, offers and tasks must be readable offline
  // on site too (they back the project pipeline, the offer workflow and the
  // task lists). Full docs for projects/offers so detail pages incl. child
  // tables (approvals, relations, versions) open without a connection.
  { doctype: 'LCS Project', fullDocs: 50 },
  { doctype: 'LCS Offer', fullDocs: 50 },
  // Chances back BOTH the Chancen funnel and the Pilot scout page (unrated hits
  // are LCS Chance, source Pilot-Scout) — pre-warm so both open offline.
  { doctype: 'LCS Chance', fullDocs: 50 },
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
const PREFETCH_VERSION = '2'
const LS_VER = 'lcs-offline-prefetch-ver'

export async function prefetchOfflineData(force = false) {
  if (!navigator.onLine) return
  const verChanged = localStorage.getItem(LS_VER) !== PREFETCH_VERSION
  const last = Number(localStorage.getItem(LS_KEY) || 0)
  if (!force && !verChanged && Date.now() - last < THROTTLE_MS) return
  localStorage.setItem(LS_KEY, String(Date.now()))
  localStorage.setItem(LS_VER, PREFETCH_VERSION)

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

/** Wire once from App.vue — initial warm-up + refresh on reconnect. */
export function startOfflinePrefetch() {
  // Delay the first run so it never competes with initial page load
  setTimeout(() => prefetchOfflineData(), 8000)
  window.addEventListener('online', () => prefetchOfflineData())
}
