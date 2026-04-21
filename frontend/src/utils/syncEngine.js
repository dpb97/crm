/**
 * Sync Engine — drains the offline mutation queue when online.
 *
 * Strategy:
 * - On `online` event, trigger drain
 * - On app boot while online, drain any leftover mutations
 * - Mutations processed FIFO (oldest first) — preserves causal order per record
 * - Per-mutation exponential backoff (capped at 5 retries)
 * - Mutations marked 'syncing' during the attempt, 'done' or 'failed' after
 */

import { call } from 'frappe-ui'
import { listMutations, updateMutation, removeMutation, cachePut, cacheDelete } from './offlineDB'

const MAX_RETRIES = 5
const BACKOFF_BASE_MS = 1000

let draining = false

export async function startSyncEngine() {
  window.addEventListener('online', () => drain())
  // If we load online with queued items, drain immediately
  if (navigator.onLine) {
    await drain()
  }
}

export async function drain() {
  if (draining || !navigator.onLine) return
  draining = true
  try {
    const pending = await listMutations('pending')
    // Sort FIFO
    pending.sort((a, b) => a.timestamp - b.timestamp)
    for (const mutation of pending) {
      if (!navigator.onLine) break // reconnect broke mid-drain
      await processMutation(mutation)
    }
    // Also retry failed mutations if they haven't exceeded retry budget
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
    const result = await executeMutation(mutation)
    // On success: update cache with server's authoritative response and remove
    if (mutation.method === 'update' && mutation.name) {
      // Refresh the cached doc with whatever the server returned
      if (result && typeof result === 'object') {
        await cachePut(mutation.doctype, mutation.name, result)
      }
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

// Expose a manual retry + discard so the UI drawer can act on individual items

export async function retryMutation(id) {
  await updateMutation(id, { status: 'pending', retry_count: 0, error: null })
  if (navigator.onLine) drain()
}

export async function discardMutation(id) {
  await removeMutation(id)
}
