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

import { precacheAndRoute, cleanupOutdatedCaches } from 'workbox-precaching'
import { clientsClaim } from 'workbox-core'

precacheAndRoute(self.__WB_MANIFEST || [])
cleanupOutdatedCaches()

self.skipWaiting()
clientsClaim()

// ---------------------------------------------------------------------------
// IndexedDB layer
// ---------------------------------------------------------------------------

const DB_NAME = 'lcs-crm'
const DB_VERSION = 1
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
  'ToDo',
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

self.addEventListener('fetch', (event) => {
  const { request } = event
  const url = request.url

  // Frappe API — get_list
  if (GET_LIST_RE.test(url)) {
    event.respondWith(
      (async () => {
        try {
          const res = await fetch(request)
          if (res && res.ok) {
            // fire-and-forget IDB write; don't make the SPA wait.
            event.waitUntil(handleListResponse(request, res))
          }
          return res
        } catch {
          const fallback = await offlineListFallback(request)
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
        try {
          const res = await fetch(request)
          if (res && res.ok) {
            event.waitUntil(handleSingleResponse(request, res))
          }
          return res
        } catch {
          const fallback = await offlineSingleFallback(request)
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
