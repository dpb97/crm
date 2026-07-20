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
    <!-- Kein Modus-Umschalt-Button mehr (Marco 20.07.2026: EINE Shell).
         CRM-only (Dominiks Standalone-Ansicht) bleibt via ?mode=crm
         erreichbar — usePilandaMode. -->
  </div>
</template>
<script setup>
import AppSidebar from '@/components/Layouts/AppSidebar.vue'
import AppHeader from '@/components/Layouts/AppHeader.vue'
import GlobalModals from '@/components/Modals/GlobalModals.vue'
import LCSBrandHeader from '@/components/lcs/LCSBrandHeader.vue'
import PilandaSidebar from '@/components/lcs/PilandaSidebar.vue'
import { usePilandaMode } from '@/composables/usePilandaMode'
import { useOnboarding } from 'frappe-ui/frappe'

const { pilandaMode } = usePilandaMode()

// LCS (20.07.2026): Im Pilanda-Modus rendert die PilandaSidebar — Dominiks
// AppSidebar (die einzige Stelle mit vollem Onboarding-setUp) wird nie
// gemountet, aber Pages/Modals fetchen den Server-Onboarding-Status →
// frappe-ui syncStatus crasht auf onboardings[app] === undefined.
// Minimal-Registrierung wie in MobileLayout (setUp ist idempotent; im
// CRM-only-Escape registriert AppSidebar danach nicht erneut — bekannter,
// akzeptierter Randfall: Panel dort ohne Icons).
const { setUp } = useOnboarding('frappecrm')
setUp(
  [
    'setup_your_password', 'create_first_lead', 'invite_your_team',
    'convert_lead_to_deal', 'create_first_task', 'create_first_note',
    'add_first_comment', 'send_first_email', 'change_deal_status',
  ].map((name) => ({ name, completed: false })),
)
</script>
