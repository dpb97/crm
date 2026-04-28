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
    <Dialogs />
    <EventNotificationPopup />
  </FrappeUIProvider>
</template>

<script setup>
import NotPermitted from '@/pages/NotPermitted.vue'
import EventNotificationPopup from '@/components/EventNotificationPopup.vue'
import OfflineIndicator from '@/components/lcs/OfflineIndicator.vue'
import DisplayPreferencesDialog from '@/components/lcs/DisplayPreferencesDialog.vue'
import { Dialogs } from '@/utils/dialogs'
import { sessionStore } from '@/stores/session'
import { FrappeUIProvider, setConfig, useTheme } from 'frappe-ui'
import { computed, defineAsyncComponent, provide, onMounted, onUnmounted, ref } from 'vue'
import { startSyncEngine } from '@/utils/syncEngine'
import { useUserPreferences } from '@/composables/useUserPreferences'

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
const Layout = computed(() => {
  if (window.innerWidth < 640) {
    return MobileLayout
  } else {
    return DesktopLayout
  }
})

setConfig('systemTimezone', window.timezone?.system || null)
setConfig('localTimezone', window.timezone?.user || null)
setConfig('translatedMessages', window.translated_messages || {})

// Start the offline sync engine — replays queued mutations when online
onMounted(() => {
  startSyncEngine()
  window.addEventListener('lcs-open-preferences', openPrefs)
})
onUnmounted(() => window.removeEventListener('lcs-open-preferences', openPrefs))
</script>
