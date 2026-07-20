<!--
  PilandaSidebar — the Pilanda shell sidebar inside the CRM (Pilanda mode).
  Feeds PpSidebar with the Pilanda nav (pilanda.api.get_modules) and routes:
  /crm/* stays in-SPA, other modules load the Desk (/app/*). Only mounted when
  Pilanda mode is on; CRM-only mode keeps the native AppSidebar.
-->

<template>
  <div class="flex h-full flex-col">
    <PpSidebar
      class="flex-1 min-h-0"
      :modules="modules"
      :zones="zones"
      :active-id="activeId"
      :collapsed="collapsed"
      @update:collapsed="collapsed = $event"
      @navigate="onNavigate"
    />
    <!-- Kein CRM-Only-Button mehr (Marco 20.07.2026: EINE Shell;
         Standalone-Ansicht nur noch via ?mode=crm). -->
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import PpSidebar from '@/components/pp/PpSidebar.vue'
import { usePilandaNav } from '@/composables/usePilandaNav'

const router = useRouter()
const { modules, zones, load } = usePilandaNav()
const collapsed = ref(false)

onMounted(load)

// Highlight the sales module (our CRM) in the shell.
const activeId = computed(() => {
  const m = modules.value.find(
    (x) => x.path === '/crm' || x.target === '/crm' || x.id === 'vertrieb',
  )
  return m?.id || ''
})

function onNavigate(payload) {
  const item = payload?.item
  let target = (item && (item.t || item.target)) || null
  if (!target && payload?.id) {
    const m = modules.value.find((x) => x.id === payload.id)
    target = m?.target || m?.path
  }
  if (!target || target === '#') return
  if (target.startsWith('/crm')) {
    router.push(target.replace(/^\/crm/, '') || '/') // stay in the SPA
  } else {
    window.location.href = target // hand off to the Pilanda Desk
  }
}
</script>
