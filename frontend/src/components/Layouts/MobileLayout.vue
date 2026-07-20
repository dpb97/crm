<template>
  <div class="flex h-screen w-screen">
    <MobileSidebar />
    <!-- min-w-0 + overflow-x-hidden: without them any over-wide child
         (mail cards, long addresses) stretches past the viewport and the
         whole page scrolls horizontally on phones. Inner tables keep
         their own overflow-x-auto containers. -->
    <div class="flex h-full min-w-0 flex-1 flex-col overflow-y-auto overflow-x-hidden bg-surface-white">
      <MobileAppHeader />
      <slot />
    </div>
    <GlobalModals />
  </div>
</template>
<script setup>
import MobileSidebar from '@/components/Mobile/MobileSidebar.vue'
import MobileAppHeader from '@/components/Mobile/MobileAppHeader.vue'
import GlobalModals from '@/components/Modals/GlobalModals.vue'
import { useOnboarding } from 'frappe-ui/frappe'

// LCS (20.07.2026): Mobile rendert kein Onboarding-Panel, aber Pages/
// Modals rufen useOnboarding('frappecrm') auf → frappe-ui fetcht den
// Server-Onboarding-Status und crasht in syncStatus, wenn nie setUp()
// lief (onboardings[appName] === undefined; auf Desktop registriert
// AppSidebar die echten Steps). Deshalb hier die Minimal-Registrierung
// — gleiche 9 Step-Namen wie AppSidebar/backfill.ensure_german_ux.
const { setUp } = useOnboarding('frappecrm')
setUp(
  [
    'setup_your_password', 'create_first_lead', 'invite_your_team',
    'convert_lead_to_deal', 'create_first_task', 'create_first_note',
    'add_first_comment', 'send_first_email', 'change_deal_status',
  ].map((name) => ({ name, completed: false })),
)
</script>
