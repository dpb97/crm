/**
 * useUserPreferences — singleton composable that fetches the current user's
 * LCS preferences + access profile once and keeps them reactive.
 *
 * Everywhere in the UI that needs to hide/show an element based on user
 * settings imports this and reads `prefs.show_*` / `accessProfile.hide_*`.
 */

import { reactive, readonly, ref } from 'vue'
import { call } from 'frappe-ui'

const state = reactive({
  loaded: false,
  loading: false,
  prefs: {
    show_forecasting: 1,
    show_integration_panel: 1,
    show_team_section: 1,
    show_fusion_section: 1,
    show_bsm_section: 1,
    show_training_section: 1,
    show_opportunity_matrix: 1,
    show_pricing_details: 1,
    default_list_view: 'Table',
    default_show_only_mine: 0,
    default_period_forecasting: 'month',
    compact_mode: 0,
    confirm_phase_changes: 1,
    voice_input_language: 'de-DE',
  },
  accessProfile: null,
  isSystemManager: false,
})

let loadPromise = null

async function load(force = false) {
  if (state.loaded && !force) return state
  if (loadPromise && !force) return loadPromise
  state.loading = true
  loadPromise = call('lcs_integrations.visibility.service.get_user_preferences')
    .then(res => {
      const payload = res.message || res
      if (payload.preferences) Object.assign(state.prefs, payload.preferences)
      state.accessProfile = payload.access_profile || null
      state.isSystemManager = !!payload.is_system_manager
      state.loaded = true
      return state
    })
    .finally(() => { state.loading = false; loadPromise = null })
  return loadPromise
}

/** Lazy load on first use — components calling this before init get defaults. */
export function useUserPreferences() {
  if (!state.loaded && !state.loading) load()

  return {
    state: readonly(state),
    reload: () => load(true),
    /** Per-user column selection for LCS list pages (see ColumnPicker). */
    getListColumns(tableKey) {
      try {
        const all = JSON.parse(state.prefs.list_columns || '{}')
        return Array.isArray(all[tableKey]) ? all[tableKey] : null
      } catch (e) {
        return null
      }
    },
    async saveListColumns(tableKey, columns) {
      let all = {}
      try {
        all = JSON.parse(state.prefs.list_columns || '{}')
      } catch (e) {
        all = {}
      }
      all[tableKey] = columns
      const serialized = JSON.stringify(all)
      state.prefs.list_columns = serialized
      await call('lcs_integrations.visibility.service.save_user_preferences', {
        preferences: { list_columns: serialized },
      })
    },
    /** Per-user list VIEW STATE (column order, filters, view mode …) keyed by
        table id. Distinct from list_columns (selection) so the column picker
        and the view-state persistence don't clobber each other. */
    getListState(tableKey) {
      try {
        const all = JSON.parse(state.prefs.list_view_state || '{}')
        const st = all[tableKey]
        return st && typeof st === 'object' ? st : {}
      } catch (e) {
        return {}
      }
    },
    async saveListState(tableKey, patch) {
      let all = {}
      try {
        all = JSON.parse(state.prefs.list_view_state || '{}')
      } catch (e) {
        all = {}
      }
      all[tableKey] = { ...(all[tableKey] || {}), ...patch }
      const serialized = JSON.stringify(all)
      state.prefs.list_view_state = serialized
      await call('lcs_integrations.visibility.service.save_user_preferences', {
        preferences: { list_view_state: serialized },
      })
    },
    /** Combined "should-show" helper: true unless admin profile blocks it. */
    canShow(key) {
      const hideKey = {
        show_forecasting: 'hide_forecasting',
        show_team_section: 'hide_team',
        show_training_section: 'hide_team',
        show_fusion_section: 'hide_fusion',
        show_bsm_section: 'hide_bsm',
        show_opportunity_matrix: 'hide_opportunity_matrix',
        show_pricing_details: 'hide_pricing',
      }[key]
      if (hideKey && state.accessProfile?.[hideKey]) return false
      return !!state.prefs[key]
    },
  }
}
