/**
 * useOfflineList — cache-aware list fetch.
 *
 * Wraps frappe-ui's createListResource with IndexedDB caching so
 * list queries work offline or when the network is flaky.
 *
 * - On success: cache the response under a key derived from doctype + params
 * - On error OR when offline: serve the last cached data (if any)
 * - Exposes `fromCache` so the UI can show a "stale data" indicator
 */

import { ref, computed, watch, unref, toRaw } from 'vue'
import { createListResource } from 'frappe-ui'
import { cacheListGet, cacheListPut } from '@/utils/offlineDB'

/**
 * Deeply unref + toRaw a value so JSON.stringify doesn't walk into
 * Vue's reactive proxy internals (which contain circular references
 * like `computed.dep.computed`).
 *
 * Handles: computed refs, reactive objects, nested refs in plain
 * objects/arrays, Date, plain values.
 */
function toSerializable(v) {
  v = unref(v)
  if (v == null) return v
  if (typeof v !== 'object') return v
  v = toRaw(v)
  if (Array.isArray(v)) return v.map(toSerializable)
  const out = {}
  for (const k of Object.keys(v)) {
    out[k] = toSerializable(v[k])
  }
  return out
}

export function useOfflineList(config) {
  const data = ref([])
  const loading = ref(false)
  const error = ref(null)
  const fromCache = ref(false)
  const lastCachedAt = ref(null)

  // Stable cache key from doctype + fully-unwrapped params.
  // Every input could be a ref / computed / reactive — unref all the way down
  // before JSON.stringify to avoid "Converting circular structure" crashes.
  const cacheKey = computed(() => {
    const filtersSnapshot = typeof config.filters === 'function'
      ? config.filters()
      : toSerializable(config.filters)
    return `list:${config.doctype}:${JSON.stringify({
      filters: filtersSnapshot,
      fields: toSerializable(config.fields),
      orderBy: toSerializable(config.orderBy),
      pageLength: toSerializable(config.pageLength),
    })}`
  })

  const resource = createListResource({
    ...config,
    auto: false, // we control fetch timing to integrate cache properly
    onSuccess: async (fresh) => {
      data.value = fresh
      fromCache.value = false
      lastCachedAt.value = Date.now()
      try {
        await cacheListPut(cacheKey.value, { data: toSerializable(fresh), cached_at: Date.now() })
      } catch (e) {
        // Cache write failing is non-fatal — UI already rendered fresh
        console.warn('useOfflineList: cache write failed', e)
      }
      if (config.onSuccess) config.onSuccess(fresh)
    },
    onError: async (err) => {
      error.value = err?.messages?.[0] || err?.message || String(err)
      await loadFromCache()
      if (config.onError) config.onError(err)
    },
  })

  async function loadFromCache() {
    try {
      const cached = await cacheListGet(cacheKey.value)
      if (cached) {
        data.value = cached.data
        fromCache.value = true
        lastCachedAt.value = cached.cached_at
        error.value = null
      }
    } catch (e) {
      console.warn('useOfflineList: cache read failed', e)
    }
  }

  async function fetch() {
    loading.value = true
    error.value = null
    if (!navigator.onLine) {
      await loadFromCache()
      loading.value = false
      return
    }
    try {
      await resource.reload()
    } catch (e) {
      // Fallback handled in onError above
    } finally {
      loading.value = false
    }
  }

  // Refetch on filter changes
  watch(cacheKey, () => fetch(), { immediate: true })

  // Refresh when the browser comes back online
  window.addEventListener('online', () => fetch())

  return {
    data,
    loading,
    error,
    fromCache,
    lastCachedAt,
    reload: fetch,
  }
}
