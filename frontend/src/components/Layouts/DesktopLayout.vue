<template>
  <!-- Pilanda-Modus: durchgehende Topbar (PpAppbar) über allem, darunter
       Sidebar + Inhalt — wie in der Desk-Shell (PilandaDesk.vue). Dominiks
       AppHeader (Breadcrumb-Zeile) bleibt im Inhaltsbereich darunter. -->
  <div v-if="pilandaMode" class="flex flex-col h-screen w-screen">
    <PpAppbar
      class="shrink-0"
      :brand-src="BRAND_MARK"
      brand-label="Pilanda"
      :search="false"
      :window-controls="false"
      :user="appbarUser"
      @home="goHome"
      @user-select="onUserSelect"
    />
    <div class="flex flex-1 min-h-0">
      <!-- Sidebar-Spalte: KEINE frappe-ui-Fläche (bg-surface-menu-bar) und kein
           doppelter Rahmen — PpSidebar bringt --pp-bg-surface + border-right
           selbst mit (identisch zur Desk-Sidebar). -->
      <div class="h-full shrink-0">
        <PilandaSidebar />
      </div>
      <div class="flex-1 flex flex-col h-full overflow-auto bg-surface-white min-w-0">
        <AppHeader />
        <slot />
      </div>
      <PpInspector
        class="shrink-0"
        :spec="inspSpec"
        :collapsed="inspCollapsed"
        title="Spezifikation"
        @update:collapsed="setInspCollapsed"
      >
        <!-- Reiche Node-View (z. B. Netzwerk-Knoten) rendert in den Default-
             Slot; ohne View fällt PpInspector auf sein eingebautes Spec-Panel
             zurück. #title analog. -->
        <template v-if="inspView" #title>{{ inspView.title }}</template>
        <template v-if="inspView" #default>
          <PpInspectorNodeView :view="inspView" />
        </template>
      </PpInspector>
    </div>
    <GlobalModals />
  </div>

  <!-- CRM-only (Dominiks Standalone-Ansicht via ?mode=crm) — unverändert. -->
  <div v-else class="flex h-screen w-screen">
    <div class="h-full border-r bg-surface-menu-bar">
      <AppSidebar />
    </div>
    <div class="flex-1 flex flex-col h-full overflow-auto bg-surface-white">
      <LCSBrandHeader
        title="LCS Cable Cranes"
        subtitle="CRM"
        href="/crm"
      />
      <AppHeader />
      <slot />
    </div>
    <GlobalModals />
  </div>
</template>
<script setup>
import { computed } from 'vue'
import AppSidebar from '@/components/Layouts/AppSidebar.vue'
import AppHeader from '@/components/Layouts/AppHeader.vue'
import GlobalModals from '@/components/Modals/GlobalModals.vue'
import LCSBrandHeader from '@/components/lcs/LCSBrandHeader.vue'
import PilandaSidebar from '@/components/lcs/PilandaSidebar.vue'
import PpAppbar from '@/components/pp/PpAppbar.vue'
import PpInspector from '@/components/pp/PpInspector.vue'
import PpInspectorNodeView from '@/components/lcs/PpInspectorNodeView.vue'
import { usePilandaMode } from '@/composables/usePilandaMode'
import { usePilandaInspect } from '@/composables/usePilandaInspect'
import { sessionStore } from '@/stores/session'
import { usersStore } from '@/stores/users'
import { useOnboarding } from 'frappe-ui/frappe'

const { pilandaMode } = usePilandaMode()
const { spec: inspSpec, view: inspView, collapsed: inspCollapsed, setCollapsed: setInspCollapsed } = usePilandaInspect()

// Logo-SSOT pilanda_theme (Laufzeit-URL, von Frappe serviert — wie im Desk).
const BRAND_MARK = '/assets/pilanda_theme/logo/pilanda-mark.svg'

// Topbar-User (minimal — Marke + User-Chip; Fenster-Controls/Suche des Desk
// werden NICHT nachgebaut, siehe :search/:window-controls false). Der User-Chip
// von PpAppbar ist Pflicht-Bestandteil des Bausteins → mit echten Initialen +
// Abmelden verdrahtet.
const session = sessionStore()
const { getUser } = usersStore()
const appbarUser = computed(() => {
  const fn = getUser()?.full_name || ''
  const initials =
    fn.trim().split(/\s+/).slice(0, 2).map((p) => p[0] || '').join('').toUpperCase() || '?'
  return {
    initials,
    name: fn,
    role: 'LCS Group',
    items: [{ key: 'abmelden', label: window.__('Log out'), danger: true }],
  }
})

function goHome() {
  // Marke → Pilanda-Startseite (Desk-Home), wie im Desk.
  window.location.href = '/app/pilanda-home'
}
function onUserSelect(key) {
  if (key === 'abmelden') session.logout.submit()
}

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
