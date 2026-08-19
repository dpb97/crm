/**
 * swMirror — write prefetched records DIRECTLY into the service worker's
 * IndexedDB (`lcs-crm`, per-doctype stores). The SW serves offline
 * `frappe.client.get_list` / `get` from these stores (offlineListFallback), so
 * writing here makes offline reads work reliably WITHOUT depending on the SW
 * intercepting the prefetch's own network calls.
 *
 * IMPORTANT: DB_NAME / DB_VERSION / STORES must stay in sync with sw.js — this
 * is the same database the service worker owns; we only open it as a second
 * writer. Keep the store list = sw.js STATIC_STORES.
 */

const DB_NAME = 'lcs-crm'
const DB_VERSION = 3
const STORES = [
  'CRM Lead', 'CRM Deal', 'CRM Organization', 'Contact', 'LCS Project',
  'LCS Sales Territory', 'LCS Segment', 'LCS Offer', 'LCS Chance', 'ToDo',
  'CRM Call Log', 'FCRM Note', 'CRM Lead Status', 'CRM Deal Status',
  'CRM Communication Status', 'CRM Territory', '_methods',
]

let dbPromise = null

function open() {
  if (dbPromise) return dbPromise
  dbPromise = new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, DB_VERSION)
    req.onupgradeneeded = () => {
      const db = req.result
      for (const s of STORES) {
        if (!db.objectStoreNames.contains(s)) db.createObjectStore(s, { keyPath: 'name' })
      }
    }
    req.onsuccess = () => {
      const db = req.result
      // If the SW later needs to bump the version (a brand-new doctype seen at
      // runtime), close our connection so its upgrade is not blocked.
      db.onversionchange = () => { try { db.close() } catch (_) {} dbPromise = null }
      resolve(db)
    }
    req.onerror = () => reject(req.error)
  })
  return dbPromise
}

/** Write records into the SW store for `doctype` (keyPath 'name'). */
export async function mirrorPut(doctype, records) {
  if (!doctype || !Array.isArray(records) || records.length === 0) return
  let db
  try {
    db = await open()
  } catch (_) {
    return
  }
  // Unknown store (doctype not pre-created) — leave it to the SW on first visit.
  if (!db.objectStoreNames.contains(doctype)) return
  await new Promise((resolve) => {
    try {
      const tx = db.transaction(doctype, 'readwrite')
      const store = tx.objectStore(doctype)
      for (const rec of records) {
        if (rec && rec.name) store.put(rec)
      }
      tx.oncomplete = resolve
      tx.onerror = () => resolve()
    } catch (_) {
      resolve()
    }
  })
}
