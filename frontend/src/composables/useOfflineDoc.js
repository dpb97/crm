/**
 * useOfflineDoc — wraps Frappe document access with offline support.
 *
 * Reads:
 * - If online: fetch fresh from server, cache response
 * - If offline: serve from cache; if not cached, error state
 *
 * Writes (saveField):
 * - Apply optimistically to local doc immediately
 * - If online: send to server, update cache on success
 * - If offline: queue the mutation, update cache; sync engine replays later
 */

import { ref, computed, watch } from 'vue'
import { call } from 'frappe-ui'
import {
  queueMutation,
  cacheGet,
  cachePut,
  listMutations,
  onQueueChange,
} from '@/utils/offlineDB'
import { drain } from '@/utils/syncEngine'

export function useOfflineDoc(doctype, nameRef) {
  const doc = ref(null)
  const loading = ref(false)
  const error = ref(null)
  const fromCache = ref(false)
  const pendingMutations = ref([])

  const nameValue = computed(() => typeof nameRef === 'function' ? nameRef() : nameRef.value ?? nameRef)

  async function fetch() {
    const name = nameValue.value
    if (!name) return
    loading.value = true
    error.value = null
    try {
      if (navigator.onLine) {
        const result = await call('frappe.client.get', { doctype, name })
        doc.value = result
        fromCache.value = false
        await cachePut(doctype, name, result)
      } else {
        throw new Error('Offline — falling back to cache')
      }
    } catch (err) {
      // Fall back to cache
      const cached = await cacheGet(doctype, name)
      if (cached) {
        doc.value = cached
        fromCache.value = true
        error.value = null
      } else {
        error.value = err?.messages?.[0] || err?.message || 'Failed to load'
      }
    } finally {
      loading.value = false
      await refreshPendingMutations()
    }
  }

  async function refreshPendingMutations() {
    const name = nameValue.value
    if (!name) { pendingMutations.value = []; return }
    const all = await listMutations()
    pendingMutations.value = all.filter(m =>
      m.doctype === doctype && m.name === name && m.status !== 'done'
    )
  }

  /**
   * Save a single field change.
   * Applies optimistically, then routes via server OR queue.
   */
  async function saveField(fieldname, value) {
    const name = nameValue.value
    if (!name || !doc.value) return { ok: false, error: 'No document loaded' }

    // 1. Optimistic local update
    const patch = { [fieldname]: value }
    doc.value = { ...doc.value, ...patch, modified: new Date().toISOString() }
    await cachePut(doctype, name, doc.value)

    // 2. Online path: direct to server
    if (navigator.onLine) {
      try {
        const result = await call('frappe.client.set_value', { doctype, name, fieldname: patch })
        if (result) {
          doc.value = result
          await cachePut(doctype, name, result)
        }
        return { ok: true, queued: false }
      } catch (err) {
        // Server refused — queue as fallback, surface error
        await queueMutation({
          doctype, name, method: 'update', params: patch,
          description: `Update ${fieldname}`,
        })
        await refreshPendingMutations()
        return { ok: false, queued: true, error: err?.messages?.[0] || err?.message }
      }
    }

    // 3. Offline path: queue for replay
    await queueMutation({
      doctype, name, method: 'update', params: patch,
      description: `Update ${fieldname}`,
    })
    await refreshPendingMutations()
    return { ok: true, queued: true }
  }

  /**
   * Save multiple fields atomically.
   */
  async function saveFields(patch) {
    const name = nameValue.value
    if (!name || !doc.value) return { ok: false, error: 'No document loaded' }

    doc.value = { ...doc.value, ...patch, modified: new Date().toISOString() }
    await cachePut(doctype, name, doc.value)

    if (navigator.onLine) {
      try {
        const result = await call('frappe.client.set_value', { doctype, name, fieldname: patch })
        if (result) {
          doc.value = result
          await cachePut(doctype, name, result)
        }
        return { ok: true, queued: false }
      } catch (err) {
        await queueMutation({ doctype, name, method: 'update', params: patch, description: `Update ${Object.keys(patch).join(', ')}` })
        await refreshPendingMutations()
        return { ok: false, queued: true, error: err?.messages?.[0] || err?.message }
      }
    }
    await queueMutation({ doctype, name, method: 'update', params: patch, description: `Update ${Object.keys(patch).join(', ')}` })
    await refreshPendingMutations()
    return { ok: true, queued: true }
  }

  function hasPendingFieldChange(fieldname) {
    return pendingMutations.value.some(m =>
      m.method === 'update' && m.params && fieldname in m.params
    )
  }

  // Refetch when name changes
  watch(nameValue, () => fetch(), { immediate: true })

  // When online again, try a fresh fetch to overwrite cache with server truth
  window.addEventListener('online', async () => {
    await drain()
    await fetch()
  })

  // React to queue changes (e.g. sync engine finished)
  const unsub = onQueueChange(() => refreshPendingMutations())

  return {
    doc,
    loading,
    error,
    fromCache,
    pendingMutations,
    hasPendingFieldChange,
    saveField,
    saveFields,
    reload: fetch,
  }
}
