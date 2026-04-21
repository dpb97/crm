/**
 * Offline storage utility — vanilla IndexedDB (no external dependency).
 *
 * Three object stores:
 * - mutations: queued writes (create/update/delete) awaiting server sync
 * - cache:    cached GET responses for document reads (key = doctype + ':' + name)
 * - lists:    cached list query responses (key = doctype + ':' + filter_hash)
 */

const DB_NAME = 'lcs-offline-v1'
const DB_VERSION = 1

let dbPromise = null

function getDB() {
  if (dbPromise) return dbPromise
  dbPromise = new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, DB_VERSION)
    req.onupgradeneeded = (e) => {
      const db = e.target.result
      if (!db.objectStoreNames.contains('mutations')) {
        const store = db.createObjectStore('mutations', { keyPath: 'id', autoIncrement: true })
        store.createIndex('status', 'status', { unique: false })
        store.createIndex('doctype_name', ['doctype', 'name'], { unique: false })
        store.createIndex('timestamp', 'timestamp', { unique: false })
      }
      if (!db.objectStoreNames.contains('cache')) {
        db.createObjectStore('cache', { keyPath: 'key' })
      }
      if (!db.objectStoreNames.contains('lists')) {
        db.createObjectStore('lists', { keyPath: 'key' })
      }
    }
    req.onsuccess = () => resolve(req.result)
    req.onerror = () => reject(req.error)
  })
  return dbPromise
}

function tx(db, storeNames, mode = 'readonly') {
  return db.transaction(storeNames, mode)
}

function awaitReq(req) {
  return new Promise((resolve, reject) => {
    req.onsuccess = () => resolve(req.result)
    req.onerror = () => reject(req.error)
  })
}

function awaitTx(t) {
  return new Promise((resolve, reject) => {
    t.oncomplete = () => resolve()
    t.onabort = t.onerror = () => reject(t.error)
  })
}

// --- MUTATIONS ---

export async function queueMutation({ doctype, name, method, params, description, baseValues, baseModified }) {
  const db = await getDB()
  const mutation = {
    doctype,
    name: name || null,
    method,
    params,
    description: description || `${method} ${doctype}${name ? ` ${name}` : ''}`,
    status: 'pending',             // pending | syncing | failed | conflict | done
    error: null,
    retry_count: 0,
    timestamp: Date.now(),
    // Optimistic concurrency control fields
    base_values: baseValues || null,   // server values at queue time, per field
    base_modified: baseModified || null, // doc.modified at queue time
    conflicts: null,               // populated when status='conflict'
  }
  const t = tx(db, 'mutations', 'readwrite')
  const id = await awaitReq(t.objectStore('mutations').add(mutation))
  await awaitTx(t)
  notifyQueueChange()
  return { id, ...mutation }
}

export async function listMutations(statusFilter = null) {
  const db = await getDB()
  const t = tx(db, 'mutations')
  if (statusFilter) {
    return await awaitReq(t.objectStore('mutations').index('status').getAll(statusFilter))
  }
  return await awaitReq(t.objectStore('mutations').getAll())
}

export async function updateMutation(id, patch) {
  const db = await getDB()
  const t = tx(db, 'mutations', 'readwrite')
  const store = t.objectStore('mutations')
  const existing = await awaitReq(store.get(id))
  if (!existing) { await awaitTx(t); return null }
  const updated = { ...existing, ...patch }
  await awaitReq(store.put(updated))
  await awaitTx(t)
  notifyQueueChange()
  return updated
}

export async function removeMutation(id) {
  const db = await getDB()
  const t = tx(db, 'mutations', 'readwrite')
  await awaitReq(t.objectStore('mutations').delete(id))
  await awaitTx(t)
  notifyQueueChange()
}

export async function countPendingMutations() {
  const db = await getDB()
  const t = tx(db, 'mutations')
  return await awaitReq(t.objectStore('mutations').index('status').count('pending'))
}

// --- DOCUMENT CACHE ---

export async function cacheGet(doctype, name) {
  const db = await getDB()
  const t = tx(db, 'cache')
  const entry = await awaitReq(t.objectStore('cache').get(`${doctype}:${name}`))
  return entry ? entry.doc : null
}

export async function cachePut(doctype, name, doc) {
  const db = await getDB()
  const t = tx(db, 'cache', 'readwrite')
  await awaitReq(t.objectStore('cache').put({
    key: `${doctype}:${name}`, doctype, name, doc, cached_at: Date.now(),
  }))
  await awaitTx(t)
}

export async function cacheDelete(doctype, name) {
  const db = await getDB()
  const t = tx(db, 'cache', 'readwrite')
  await awaitReq(t.objectStore('cache').delete(`${doctype}:${name}`))
  await awaitTx(t)
}

// --- LIST CACHE ---

export async function cacheListGet(key) {
  const db = await getDB()
  const t = tx(db, 'lists')
  const entry = await awaitReq(t.objectStore('lists').get(key))
  return entry ? entry.data : null
}

export async function cacheListPut(key, data) {
  const db = await getDB()
  const t = tx(db, 'lists', 'readwrite')
  await awaitReq(t.objectStore('lists').put({ key, data, cached_at: Date.now() }))
  await awaitTx(t)
}

// --- EVENTS ---

function notifyQueueChange() {
  window.dispatchEvent(new CustomEvent('lcs-offline-queue-changed'))
  try {
    localStorage.setItem('lcs-offline-queue-ts', String(Date.now()))
  } catch {}
}

export function onQueueChange(handler) {
  window.addEventListener('lcs-offline-queue-changed', handler)
  const storageHandler = (e) => {
    if (e.key === 'lcs-offline-queue-ts') handler()
  }
  window.addEventListener('storage', storageHandler)
  return () => {
    window.removeEventListener('lcs-offline-queue-changed', handler)
    window.removeEventListener('storage', storageHandler)
  }
}

// --- UTILITIES ---

export async function clearAll() {
  const db = await getDB()
  const t = tx(db, ['mutations', 'cache', 'lists'], 'readwrite')
  await awaitReq(t.objectStore('mutations').clear())
  await awaitReq(t.objectStore('cache').clear())
  await awaitReq(t.objectStore('lists').clear())
  await awaitTx(t)
  notifyQueueChange()
}
