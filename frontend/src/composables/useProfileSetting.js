import { ref, watch } from 'vue'
import { useUserPreferences } from './useUserPreferences'

/**
 * Profile-backed replacement for `useStorage` — persists a single list-view
 * setting (column order, filter, view mode …) to the user's LCS User
 * Preferences (server, cross-device) instead of localStorage.
 *
 *   const columnOrder = useProfileSetting('lcs_projects', 'col_order', DEFAULT)
 *
 * Reads hydrate once the preferences have loaded; writes are debounced and
 * pushed to the server. Guarded so the initial hydration never echoes the
 * default value back to the server.
 */
export function useProfileSetting(tableKey, key, def) {
  const prefs = useUserPreferences()
  const value = ref(def)
  let hydrated = false

  watch(
    () => [prefs.state.loaded, prefs.state.prefs.list_view_state],
    () => {
      if (!prefs.state.loaded) return
      const st = prefs.getListState(tableKey)
      if (key in st && st[key] !== undefined) value.value = st[key]
      hydrated = true
    },
    { immediate: true, deep: false },
  )

  let timer = null
  watch(
    value,
    (v) => {
      if (!hydrated) return
      clearTimeout(timer)
      timer = setTimeout(() => {
        prefs.saveListState(tableKey, { [key]: v }).catch(() => {})
      }, 400)
    },
    { deep: true },
  )

  return value
}
