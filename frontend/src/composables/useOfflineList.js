/**
 * useOfflineList — cache-aware list fetch.
 *
 * Wraps frappe-ui's createListResource with IndexedDB caching so
 * list queries work offline or when the network is flaky.
 *
 * - On success: cache the response under a key derived from doctype + params
 * - On error OR when offline: serve the last cached data (if any)
 * - Exposes `fromCache` so the UI can show a "stale data" indicator
 *
 * Conflict-free: cache is read-only for reads, all writes go through the
 * existing mutation queue and update single-doc caches separately.
 */

import { ref, computed, watch } from 'vue'
import { createListResource } from 'frappe-ui'
import { cacheListGet, cacheListPut } from '@/utils/offlineDB'

export function useOfflineList(config) {
  const data = ref([])
  const loading = ref(false)
  const error = ref(null)
  const fromCache = ref(false)
  const lastCachedAt = ref(null)

  // Stable cache key from doctype + serialized filters/fields
  const cacheKey = computed(() => {
    const filtersSnapshot = typeof config.filters === 'function'
      ? config.filters()
      : (config.filters?.value ?? config.filters ?? {})
    return `list:${config.doctype}:${JSON.stringify({
      filters: filtersSnapshot,
      fields: config.fields,
      orderBy: config.orderBy,
      pageLength: config.pageLength,
    })}`
  })

  const resource = createListResource({
    ...config,
    auto: false, // we control fetch timing to integrate cache properly
    onSuccess: async (fresh) => {
      data.value = fresh
      fromCache.value = false
      lastCachedAt.value = Date.now()
      await cacheListPut(cacheKey.value, { data: fresh, cached_at: Date.now() })
      if (config.onSuccess) config.onSuccess(fresh)
    },
    onError: async (err) => {
      error.value = err?.messages?.[0] || err?.message || String(err)
      await loadFromCache()
      if (config.onError) config.onError(err)
    },
  })

  async function loadFromCache() {
    const cached = await cacheListGet(cacheKey.value)
    if (cached) {
      data.value = cached.data
      fromCache.value = true
      lastCachedAt.value = cached.cached_at
      error.value = null
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
