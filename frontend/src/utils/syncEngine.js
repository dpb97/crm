/**
 * Sync Engine — drains the offline mutation queue when online.
 *
 * On each update-mutation we fetch the current server state first and
 * compare it against the base values captured when the mutation was
 * queued. If any field we are writing has been changed on the server
 * since, we mark the mutation as 'conflict' and leave it for the user
 * to resolve via ConflictResolver.
 */

import { call } from 'frappe-ui'
import { listMutations, updateMutation, removeMutation, cachePut, cacheDelete } from './offlineDB'

const MAX_RETRIES = 5
const BACKOFF_BASE_MS = 1000

let draining = false

export async function startSyncEngine() {
  window.addEventListener('online', () => drain())
  if (navigator.onLine) {
    await drain()
  }
}

export async function drain() {
  if (draining || !navigator.onLine) return
  draining = true
  try {
    const pending = await listMutations('pending')
    pending.sort((a, b) => a.timestamp - b.timestamp)
    for (const mutation of pending) {
      if (!navigator.onLine) break
      await processMutation(mutation)
    }
    // Retry failed with backoff; skip conflicts (wait for user)
    const failed = await listMutations('failed')
    for (const mutation of failed) {
      if (!navigator.onLine) break
      if ((mutation.retry_count || 0) >= MAX_RETRIES) continue
      const wait = BACKOFF_BASE_MS * Math.pow(2, mutation.retry_count || 0)
      if (Date.now() - (mutation.last_attempt || 0) < wait) continue
      await processMutation(mutation)
    }
  } finally {
    draining = false
  }
}

async function processMutation(mutation) {
  await updateMutation(mutation.id, { status: 'syncing', last_attempt: Date.now() })
  try {
    // Detect conflicts on updates before applying
    if (mutation.method === 'update' && mutation.name) {
      const conflicts = await detectConflicts(mutation)
      if (conflicts && Object.keys(conflicts).length) {
        await updateMutation(mutation.id, {
          status: 'conflict',
          conflicts,
          error: null,
        })
        return
      }
    }

    const result = await executeMutation(mutation)

    // Sync cache with authoritative server response
    if (mutation.method === 'update' && mutation.name && result && typeof result === 'object') {
      await cachePut(mutation.doctype, mutation.name, result)
    } else if (mutation.method === 'delete' && mutation.name) {
      await cacheDelete(mutation.doctype, mutation.name)
    } else if (mutation.method === 'insert' && result?.name) {
      await cachePut(mutation.doctype, result.name, result)
    }
    await removeMutation(mutation.id)
  } catch (err) {
    const retry_count = (mutation.retry_count || 0) + 1
    const errorMsg = err?.messages?.[0] || err?.message || String(err)
    await updateMutation(mutation.id, {
      status: retry_count >= MAX_RETRIES ? 'failed' : 'pending',
      retry_count,
      error: errorMsg,
    })
    console.warn('[sync] mutation failed', mutation, err)
  }
}

/**
 * Returns a { field: { base, server, local } } object for each field
 * where the server's current value differs from the base we captured
 * when the mutation was queued. Returns null if no base values were
 * recorded (backward compat — treat as last-write-wins).
 */
async function detectConflicts(mutation) {
  if (!mutation.base_values) return null
  let current
  try {
    current = await call('frappe.client.get', {
      doctype: mutation.doctype,
      name: mutation.name,
    })
  } catch {
    return null // doc gone or unreachable — let the mutation attempt proceed
  }

  const conflicts = {}
  for (const [field, localValue] of Object.entries(mutation.params)) {
    const baseValue = mutation.base_values[field]
    const serverValue = current[field]
    if (!valuesEqual(baseValue, serverValue)) {
      conflicts[field] = {
        base: baseValue,
        server: serverValue,
        local: localValue,
      }
    }
  }
  return conflicts
}

// Field equality ignoring empty-vs-null differences that Frappe emits inconsistently
function valuesEqual(a, b) {
  if (a === b) return true
  if ((a == null || a === '') && (b == null || b === '')) return true
  // Numeric equivalence (Frappe returns numbers as floats sometimes)
  if (typeof a === 'number' && typeof b === 'string' && parseFloat(b) === a) return true
  if (typeof b === 'number' && typeof a === 'string' && parseFloat(a) === b) return true
  return false
}

async function executeMutation(mutation) {
  const { doctype, name, method, params } = mutation
  if (method === 'update') {
    return await call('frappe.client.set_value', {
      doctype,
      name,
      fieldname: params,
    })
  }
  if (method === 'insert') {
    return await call('frappe.client.insert', {
      doc: { doctype, ...params },
    })
  }
  if (method === 'delete') {
    return await call('frappe.client.delete', { doctype, name })
  }
  throw new Error(`Unsupported mutation method: ${method}`)
}

export async function retryMutation(id) {
  await updateMutation(id, { status: 'pending', retry_count: 0, error: null, conflicts: null })
  if (navigator.onLine) drain()
}

export async function discardMutation(id) {
  await removeMutation(id)
}

/**
 * Resolve a conflict by choosing, per field, either the local or server
 * value (or a custom merged value). Rewrites mutation.params with the
 * resolved values and marks it pending for the next drain.
 */
export async function resolveConflict(id, resolutions) {
  const all = await listMutations()
  const mutation = all.find(m => m.id === id)
  if (!mutation) return
  // resolutions: { field: resolvedValue } — fields not in resolutions keep the local value
  const newParams = { ...mutation.params, ...resolutions }
  // Capture current server values as new base so re-conflict is unlikely
  let newBase = mutation.base_values || {}
  try {
    const current = await call('frappe.client.get', {
      doctype: mutation.doctype, name: mutation.name,
    })
    newBase = { ...newBase }
    for (const field of Object.keys(newParams)) {
      newBase[field] = current[field]
    }
  } catch {}
  await updateMutation(id, {
    params: newParams,
    base_values: newBase,
    conflicts: null,
    status: 'pending',
    retry_count: 0,
    error: null,
  })
  if (navigator.onLine) drain()
}
