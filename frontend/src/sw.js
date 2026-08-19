/**
 * LCS CRM service worker (injectManifest mode).
 *
 * Two jobs:
 *   1. Precache the SPA shell so the app boots offline.
 *   2. Mirror every successful `frappe.client.get_list` / `frappe.client.get`
 *      response into IndexedDB so the SPA can answer offline reads with
 *      structured records — not opaque cached HTTP blobs.
 *
 * Why IndexedDB and not just the Cache API:
 *   - Cache API stores Response objects keyed by URL. Useless for
 *     "give me all open deals for the current user" on the bus.
 *   - IDB stores records keyed by `doctype` + `name`. Queryable.
 *
 * Write side: every fetch event for `/api/method/frappe.client.get_list`
 * or `/api/method/frappe.client.get` is intercepted; the parsed response
 * is fanned out into an object store named after the doctype.
 *
 * Read side: on network failure for the same endpoints we return a
 * synthetic Frappe-shaped response built from the IDB store.
 *
 * Non-API requests still flow through a plain network-first +
 * Cache-API fallback for the SPA shell.
 */

import {
  precacheAndRoute,
  cleanupOutdatedCaches,
  createHandlerBoundToURL,
} from 'workbox-precaching'
import { registerRoute, NavigationRoute } from 'workbox-routing'
import { clientsClaim } from 'workbox-core'

precacheAndRoute(self.__WB_MANIFEST || [])
cleanupOutdatedCaches()

// SPA navigation fallback: serve the precached app shell for ANY in-scope
// page navigation so deep links and hard refreshes boot fully offline (the
// SPA then routes client-side). Without this, an offline reload on e.g.
// /crm/projects/PROJ-1 hits the network and white-screens. Backend paths
// (Frappe desk, API, static assets, files) are denylisted so only real SPA
// navigations fall back to index.html.
registerRoute(
  new NavigationRoute(createHandlerBoundToURL('index.html'), {
    denylist: [
      /^\/app(\/|$)/,
      /^\/api\//,
      /^\/assets\//,
      /^\/files\//,
      /^\/private\//,
      /\/sw\.js$/,
    ],
  }),
)

self.skipWaiting()
clientsClaim()

// ---------------------------------------------------------------------------
// IndexedDB layer
// ---------------------------------------------------------------------------

const DB_NAME = 'lcs-crm'
// v2: added the `_methods` store for custom read-method (get_*) response caching.
// v3: pre-create the LCS Chance + lookup doctype stores so the full-data offline
//     prefetch lights up immediately (stores otherwise appear on first use).
const DB_VERSION = 3
// Stores we proactively keep around so the offline reads light up
// immediately. New doctypes are auto-created on first use, but their
// store has to live through a `versionchange` upgrade — so when the
// SPA grows we bump DB_VERSION and add to STATIC_STORES.
const STATIC_STORES = [
  'CRM Lead',
  'CRM Deal',
  'CRM Organization',
  'Contact',
  'LCS Project',
  'LCS Sales Territory',
  'LCS Segment',
  'LCS Offer',
  'LCS Chance',
  'ToDo',
  'CRM Call Log',
  'FCRM Note',
  'CRM Lead Status',
  'CRM Deal Status',
  'CRM Communication Status',
  'CRM Territory',
  // Generic cache for custom read-method (get_*) responses — keyed by
  // method-path + args hash, so offline reads of the dashboard, geo, relations
  // etc. return their last successful payload.
  '_methods',
]

let dbPromise = null

function openDB() {
  if (dbPromise) return dbPromise
  dbPromise = new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, DB_VERSION)
    req.onupgradeneeded = () => {
      const db = req.result
      for (const name of STATIC_STORES) {
        if (!db.objectStoreNames.contains(name)) {
          db.createObjectStore(name, { keyPath: 'name' })
        }
      }
    }
    req.onsuccess = () => resolve(req.result)
    req.onerror = () => reject(req.error)
  })
  return dbPromise
}

async function ensureStore(doctype) {
  const db = await openDB()
  if (db.objectStoreNames.contains(doctype)) return db
  // New doctype seen at runtime — close, bump version, recreate.
  db.close()
  dbPromise = null
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, db.version + 1)
    req.onupgradeneeded = () => {
      const upgraded = req.result
      if (!upgraded.objectStoreNames.contains(doctype)) {
        upgraded.createObjectStore(doctype, { keyPath: 'name' })
      }
    }
    req.onsuccess = () => {
      dbPromise = Promise.resolve(req.result)
      resolve(req.result)
    }
    req.onerror = () => reject(req.error)
  })
}

async function putMany(doctype, records) {
  if (!doctype || !Array.isArray(records) || records.length === 0) return
  const db = await ensureStore(doctype)
  await new Promise((resolve, reject) => {
    const tx = db.transaction(doctype, 'readwrite')
    const store = tx.objectStore(doctype)
    for (const rec of records) {
      if (rec && rec.name) store.put(rec)
    }
    tx.oncomplete = resolve
    tx.onerror = () => reject(tx.error)
  })
}

async function getAll(doctype, filters = null, limit = 200) {
  try {
    const db = await ensureStore(doctype)
    return await new Promise((resolve, reject) => {
      const tx = db.transaction(doctype, 'readonly')
      const store = tx.objectStore(doctype)
      const req = store.getAll(null, limit)
      req.onsuccess = () => resolve(applyFilters(req.result || [], filters))
      req.onerror = () => reject(req.error)
    })
  } catch {
    return []
  }
}

async function getOne(doctype, name) {
  if (!doctype || !name) return null
  try {
    const db = await ensureStore(doctype)
    return await new Promise((resolve, reject) => {
      const tx = db.transaction(doctype, 'readonly')
      const req = tx.objectStore(doctype).get(name)
      req.onsuccess = () => resolve(req.result || null)
      req.onerror = () => reject(req.error)
    })
  } catch {
    return null
  }
}

function applyFilters(rows, filters) {
  if (!filters) return rows
  // filters may be a dict (Frappe `{field: value}`) or a list of triples
  // (`[field, operator, value]`). Only the common shapes are honoured here.
  const dict = Array.isArray(filters) ? null : filters
  const triples = Array.isArray(filters) ? filters : []
  return rows.filter((row) => {
    if (dict) {
      for (const [k, v] of Object.entries(dict)) {
        if (row[k] !== v) return false
      }
    }
    for (const t of triples) {
      if (!Array.isArray(t)) continue
      const [field, , value] = t
      if (row[field] !== value) return false
    }
    return true
  })
}

// ---------------------------------------------------------------------------
// Fetch interception
// ---------------------------------------------------------------------------

const GET_LIST_RE = /\/api\/method\/frappe\.client\.get_list/
const GET_ONE_RE = /\/api\/method\/frappe\.client\.get(?!_)/  // get but not get_list
// Custom whitelisted read methods — any /api/method path containing `get_<name>`
// (e.g. …api.get_sales_dashboard, get_project_geo, get_relations). Write methods
// (save/insert/delete/create_*/*_to_lead) never match `get_`, so they are never
// cached or served from cache. get_list / get are handled by the blocks above,
// which return before this one is reached.
const METHOD_READ_RE = /\/api\/method\/[^?]*get_[a-z0-9_]+/i

function readArg(url, body, name) {
  const u = new URL(url)
  if (u.searchParams.has(name)) return u.searchParams.get(name)
  if (body && typeof body === 'object' && name in body) return body[name]
  return null
}

function parseJsonField(value) {
  if (!value) return null
  if (typeof value === 'object') return value
  try {
    return JSON.parse(value)
  } catch {
    return null
  }
}

async function handleListResponse(req, res) {
  try {
    const url = req.url
    const body = await safeJsonClone(req)
    const doctype = readArg(url, body, 'doctype')
    if (!doctype) return
    const cloned = res.clone()
    const payload = await cloned.json()
    const records = payload?.message
    if (Array.isArray(records)) {
      await putMany(doctype, records)
    }
  } catch (e) {
    // Swallow — caching is best-effort and must never break the SPA.
    console.warn('[lcs-sw] list cache write failed', e)
  }
}

async function handleSingleResponse(req, res) {
  try {
    const url = req.url
    const body = await safeJsonClone(req)
    const doctype = readArg(url, body, 'doctype')
    if (!doctype) return
    const cloned = res.clone()
    const payload = await cloned.json()
    const record = payload?.message
    if (record && record.name) {
      await putMany(doctype, [record])
    }
  } catch (e) {
    console.warn('[lcs-sw] single cache write failed', e)
  }
}

async function safeJsonClone(req) {
  if (req.method !== 'POST') return null
  try {
    const clone = req.clone()
    const text = await clone.text()
    return text ? JSON.parse(text) : null
  } catch {
    return null
  }
}

async function offlineListFallback(req) {
  const url = req.url
  const body = await safeJsonClone(req)
  const doctype = readArg(url, body, 'doctype')
  if (!doctype) return null
  const filters = parseJsonField(readArg(url, body, 'filters'))
  const limitRaw = readArg(url, body, 'limit_page_length') || readArg(url, body, 'limit')
  const limit = limitRaw ? parseInt(limitRaw, 10) : 200
  const rows = await getAll(doctype, filters, limit || 200)
  return jsonResponse({ message: rows, _lcs_offline: true })
}

async function offlineSingleFallback(req) {
  const url = req.url
  const body = await safeJsonClone(req)
  const doctype = readArg(url, body, 'doctype')
  const name = readArg(url, body, 'name')
  if (!doctype || !name) return null
  const rec = await getOne(doctype, name)
  if (!rec) return null
  return jsonResponse({ message: rec, _lcs_offline: true })
}

function jsonResponse(body) {
  return new Response(JSON.stringify(body), {
    status: 200,
    headers: {
      'Content-Type': 'application/json',
      'X-LCS-Offline': '1',
    },
  })
}

// ---------------------------------------------------------------------------
// Custom read-method cache (get_* whitelisted methods)
// ---------------------------------------------------------------------------

// djb2 — a tiny stable string hash for the cache key (method-path + args).
function hashKey(str) {
  let h = 5381
  for (let i = 0; i < str.length; i++) h = ((h << 5) + h + str.charCodeAt(i)) | 0
  return (h >>> 0).toString(36)
}

// Build a stable key from the method path + query params + JSON body, so the
// same call with the same args maps to the same cached payload. `req` must be
// an un-consumed clone (the body is read here).
async function methodCacheKey(req) {
  const u = new URL(req.url)
  const body = await safeJsonClone(req)
  const bodyStr = body ? JSON.stringify(body) : ''
  return u.pathname + '::' + hashKey(u.search + '|' + bodyStr)
}

async function cacheMethodResponse(keyReq, res) {
  try {
    const key = await methodCacheKey(keyReq)
    const payload = await res.clone().json()
    // Store the full Frappe-shaped payload ({message: ...}) under `name`=key
    // so the existing `name`-keyed store machinery can hold it.
    await putMany('_methods', [{ name: key, payload }])
  } catch (e) {
    console.warn('[lcs-sw] method cache write failed', e)
  }
}

async function offlineMethodFallback(keyReq) {
  try {
    const key = await methodCacheKey(keyReq)
    const rec = await getOne('_methods', key)
    if (!rec || !rec.payload) return null
    return jsonResponse({ ...rec.payload, _lcs_offline: true })
  } catch {
    return null
  }
}

self.addEventListener('fetch', (event) => {
  const { request } = event
  const url = request.url

  // Frappe API — get_list
  if (GET_LIST_RE.test(url)) {
    event.respondWith(
      (async () => {
        // Clone BEFORE fetch consumes the body — get_list is a POST whose
        // doctype/filters live in the body, so both the IDB write and the
        // offline fallback need an unconsumed copy (mirrors the get_* path).
        const keyReq = request.clone()
        try {
          const res = await fetch(request)
          if (res && res.ok) {
            // fire-and-forget IDB write; don't make the SPA wait.
            event.waitUntil(handleListResponse(keyReq, res))
          }
          return res
        } catch {
          const fallback = await offlineListFallback(keyReq)
          return (
            fallback ||
            new Response(JSON.stringify({ exc_type: 'OfflineError' }), {
              status: 503,
              headers: { 'Content-Type': 'application/json' },
            })
          )
        }
      })(),
    )
    return
  }

  // Frappe API — get (single record)
  if (GET_ONE_RE.test(url)) {
    event.respondWith(
      (async () => {
        const keyReq = request.clone() // BEFORE fetch consumes the body
        try {
          const res = await fetch(request)
          if (res && res.ok) {
            event.waitUntil(handleSingleResponse(keyReq, res))
          }
          return res
        } catch {
          const fallback = await offlineSingleFallback(keyReq)
          return (
            fallback ||
            new Response(JSON.stringify({ exc_type: 'OfflineError' }), {
              status: 503,
              headers: { 'Content-Type': 'application/json' },
            })
          )
        }
      })(),
    )
    return
  }

  // Custom read methods (get_*) — network-first, offline-fallback from the
  // `_methods` IDB store. Clone the request BEFORE fetch consumes its body so
  // the cache key can be derived from the POST body offline too.
  if (METHOD_READ_RE.test(url)) {
    event.respondWith(
      (async () => {
        const keyReq = request.clone()
        try {
          const res = await fetch(request)
          if (res && res.ok) {
            event.waitUntil(cacheMethodResponse(keyReq, res))
          }
          return res
        } catch {
          const fallback = await offlineMethodFallback(keyReq)
          return (
            fallback ||
            new Response(JSON.stringify({ exc_type: 'OfflineError' }), {
              status: 503,
              headers: { 'Content-Type': 'application/json' },
            })
          )
        }
      })(),
    )
    return
  }

  // Everything else: workbox-precaching handles shell GETs; pass through
  // the rest to the network so writes (POST/PUT/DELETE) never get cached.
})

// Expose a couple of helpers to the SPA in case it wants to display
// "Offline mode — N records cached" badges later. Use postMessage from
// the SPA: { type: 'lcs.cache.stats' } → resolves with store sizes.
self.addEventListener('message', async (event) => {
  if (!event.data || event.data.type !== 'lcs.cache.stats') return
  try {
    const db = await openDB()
    const out = {}
    const names = Array.from(db.objectStoreNames)
    await Promise.all(
      names.map(
        (n) =>
          new Promise((resolve) => {
            const tx = db.transaction(n, 'readonly')
            const req = tx.objectStore(n).count()
            req.onsuccess = () => {
              out[n] = req.result
              resolve()
            }
            req.onerror = () => resolve()
          }),
      ),
    )
    event.source?.postMessage({ type: 'lcs.cache.stats.result', stores: out })
  } catch (e) {
    event.source?.postMessage({ type: 'lcs.cache.stats.result', error: String(e) })
  }
})
