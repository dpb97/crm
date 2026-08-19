<template>
  <FrappeUIProvider>
    <NotPermitted v-if="$route.name === 'Not Permitted'" />
    <Layout v-else-if="session.isLoggedIn" class="isolate" :class="{ 'lcs-compact': isCompact }">
      <router-view :key="$route.fullPath" />
    </Layout>
    <OfflineIndicator />
    <DisplayPreferencesDialog
      v-if="session.isLoggedIn"
      v-model:open="showPreferences"
      @saved="onPrefsSaved"
    />
    <GlobalSearchDialog v-if="session.isLoggedIn" v-model="showGlobalSearch" />
    <PwaInstallBanner v-if="session.isLoggedIn" />
    <Dialogs />
    <DoctypeModals />
    <EventNotificationPopup />
  </FrappeUIProvider>
</template>

<script setup>
import NotPermitted from '@/pages/NotPermitted.vue'
import EventNotificationPopup from '@/components/EventNotificationPopup.vue'
import OfflineIndicator from '@/components/lcs/OfflineIndicator.vue'
import DisplayPreferencesDialog from '@/components/lcs/DisplayPreferencesDialog.vue'
import GlobalSearchDialog from '@/components/lcs/GlobalSearchDialog.vue'
import PwaInstallBanner from '@/components/lcs/PwaInstallBanner.vue'
import DoctypeModals from '@/components/Modals/DoctypeModals.vue'
import { Dialogs } from '@/utils/dialogs'
import { sessionStore } from '@/stores/session'
import { FrappeUIProvider, setConfig, useTheme } from 'frappe-ui'
import { computed, defineAsyncComponent, provide, onMounted, onUnmounted, ref } from 'vue'
import { startSyncEngine } from '@/utils/syncEngine'
import { startOfflinePrefetch } from '@/utils/offlinePrefetch'
import { useUserPreferences } from '@/composables/useUserPreferences'
import { usePilandaMode } from '@/composables/usePilandaMode'
import { useViewport } from '@/composables/useViewport'

// Global preferences dialog — opened via window event dispatched from
// anywhere (e.g. UserDropdown menu item)
const showPreferences = ref(false)
function openPrefs() { showPreferences.value = true }

const userPrefs = useUserPreferences()
const { reload: reloadPrefs } = userPrefs
function onPrefsSaved() { reloadPrefs() }

// Drives the global `.lcs-compact` body class consumed by the
// reusable component classes in index.css (.lcs-card, .lcs-kpi).
const isCompact = computed(() => !!userPrefs.state.prefs.compact_mode)

const session = sessionStore()
provide('session', session)

const { setTheme } = useTheme()
if (!localStorage.getItem('theme')) {
  setTheme('light')
}

const MobileLayout = defineAsyncComponent(
  () => import('./components/Layouts/MobileLayout.vue'),
)
const DesktopLayout = defineAsyncComponent(
  () => import('./components/Layouts/DesktopLayout.vue'),
)
const { pilandaMode } = usePilandaMode()
const { isMobile } = useViewport()
const Layout = computed(() => {
  // The Pilanda shell is responsive on its own (drawer sidebar + overlay
  // inspector on narrow screens), so it stays on mobile too — otherwise the
  // whole Vertrieb navigation would be unreachable behind the upstream
  // MobileLayout. Only the CRM-only escape (?mode=crm) falls back to it.
  if (pilandaMode.value) return DesktopLayout
  return isMobile.value ? MobileLayout : DesktopLayout
})

setConfig('systemTimezone', window.timezone?.system || null)
setConfig('localTimezone', window.timezone?.user || null)
setConfig('translatedMessages', window.translated_messages || {})

// Ctrl/Cmd+K — global search across leads, deals, contacts, projects
const showGlobalSearch = ref(false)
function onGlobalKeydown(e) {
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
    e.preventDefault()
    showGlobalSearch.value = !showGlobalSearch.value
  }
}
// Opened from the mobile bottom-nav search tab (no Ctrl+K on touch).
function openSearch() { showGlobalSearch.value = true }

// Start the offline sync engine — replays queued mutations when online
onMounted(() => {
  startSyncEngine()
  startOfflinePrefetch()
  window.addEventListener('lcs-open-preferences', openPrefs)
  window.addEventListener('lcs-open-search', openSearch)
  window.addEventListener('keydown', onGlobalKeydown)
})
onUnmounted(() => {
  window.removeEventListener('lcs-open-preferences', openPrefs)
  window.removeEventListener('lcs-open-search', openSearch)
  window.removeEventListener('keydown', onGlobalKeydown)
})
</script>
