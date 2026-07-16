<template>
  <div class="flex h-screen w-screen">
    <div class="h-full border-r bg-surface-menu-bar">
      <PilandaSidebar v-if="pilandaMode" />
      <AppSidebar v-else />
    </div>
    <div class="flex-1 flex flex-col h-full overflow-auto bg-surface-white">
      <LCSBrandHeader
        v-if="!pilandaMode"
        title="LCS Cable Cranes"
        subtitle="CRM"
        href="/crm"
      />
      <AppHeader />
      <slot />
    </div>
    <GlobalModals />
    <!-- Mode switch: CRM-only <-> Pilanda shell -->
    <button
      class="fixed right-3 top-1.5 z-[60] rounded-md border bg-white/90 px-2 py-1 text-[11px] font-medium text-ink-gray-6 shadow-sm hover:bg-surface-gray-2"
      :title="pilandaMode ? 'Zur CRM-Only-Ansicht' : 'In den Pilanda-Modus wechseln'"
      @click="toggle"
    >
      {{ pilandaMode ? 'CRM-Only' : 'Pilanda-Modus' }}
    </button>
  </div>
</template>
<script setup>
import AppSidebar from '@/components/Layouts/AppSidebar.vue'
import AppHeader from '@/components/Layouts/AppHeader.vue'
import GlobalModals from '@/components/Modals/GlobalModals.vue'
import LCSBrandHeader from '@/components/lcs/LCSBrandHeader.vue'
import PilandaSidebar from '@/components/lcs/PilandaSidebar.vue'
import { usePilandaMode } from '@/composables/usePilandaMode'

const { pilandaMode, toggle } = usePilandaMode()
</script>
