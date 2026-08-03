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
      :actions="isMobile && funcbarAvailable"
      :user="appbarUser"
      @home="goHome"
      @user-select="onUserSelect"
      @actions="funcbarOpen = !funcbarOpen"
    />
    <div class="flex flex-1 min-h-0">
      <!-- Sidebar-Spalte: KEINE frappe-ui-Fläche (bg-surface-menu-bar) und kein
           doppelter Rahmen — PpSidebar bringt --pp-bg-surface + border-right
           selbst mit (identisch zur Desk-Sidebar). -->
      <!-- Desktop: feste Spalte. Mobile: Off-Canvas-Drawer (fixed + Scrim),
           per Burger in der Topbar geöffnet — die Spalte reserviert dann
           keine Breite mehr. -->
      <div v-if="!isMobile" class="h-full shrink-0">
        <PilandaSidebar />
      </div>
      <PilandaSidebar v-else :drawer="true" v-model:mobile-open="mobileNavOpen" />
      <!-- Ein durchgehender Pilanda-Base-Hintergrund für Header + Seite; weiße
           Karten (--pp-bg-surface) schweben darauf. Verhindert den weiß/grau-
           Bruch zwischen Shell-Chrome und den getokenten Seiten-Canvasen.
           Positionierter Canvas → die absolute PpFunctionBar (Burger im
           Inspektor-Kopf) überlagert oben, ohne mitzuscrollen. -->
      <div class="lcs-pilanda-canvas flex-1 flex min-w-0">
        <PpFunctionBar
          v-model:open="funcbarOpen"
          :page-groups="funcbarGroups || {}"
          @action="onFuncbarAction"
        />
        <div class="lcs-pilanda-content flex-1 flex flex-col h-full overflow-auto min-w-0">
          <AppHeader />
          <slot />
        </div>
      </div>
      <PpInspector
        v-if="inspSpec || inspView || inspPanel"
        class="shrink-0"
        :overlay="isMobile"
        :spec="inspSpec"
        :collapsed="inspCollapsed"
        title="Spezifikation"
        :funcbar-open="funcbarOpen"
        :funcbar-available="funcbarAvailable"
        @update:funcbar-open="funcbarOpen = $event"
        @update:collapsed="setInspCollapsed"
      >
        <!-- Custom-Panel (interaktive Komponente, z. B. ProjectInspector) oder
             reiche Node-View (Netzwerk-Knoten) rendern in den Default-Slot;
             ohne beides fällt PpInspector auf sein eingebautes Spec-Panel
             zurück. #title analog. -->
        <template v-if="inspPanel || inspView" #title>
          {{ (inspPanel && inspPanel.title) || (inspView && inspView.title) || '' }}
        </template>
        <template v-if="inspPanel || inspView" #default>
          <component
            v-if="inspPanel"
            :is="inspPanel.component"
            v-bind="inspPanel.props || {}"
            v-on="inspPanel.on || {}"
          />
          <PpInspectorNodeView v-else :view="inspView" />
        </template>
      </PpInspector>
    </div>
    <!-- Feste Statuszeile unten (Klickdummy-Master Regel 5:
         Marke · LCS Group · Benutzer · Stand). -->
    <footer v-if="!isMobile" class="lcs-statusbar">
      <span class="lcs-statusbar-brand">Pilanda</span>
      <span class="lcs-statusbar-dot">·</span>
      <span>LCS Group</span>
      <span class="lcs-statusbar-dot">·</span>
      <span>{{ appbarUser.name || __('User') }}</span>
      <span class="lcs-statusbar-spacer"></span>
      <span>Pilanda Sales CRM</span>
    </footer>
    <!-- Mobile: untere Tab-Leiste (Design-Master .mnav) statt Statusleiste;
         „Menü" öffnet den Nav-Drawer, die übrigen Tabs sind Modul-Kürzel. -->
    <PpMobileNav
      v-if="isMobile"
      :items="mobileNavItems"
      :active-key="mobileNavActive"
      @select="onMobileNav"
    />
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
    <TaskCreateModal />
  </div>
</template>
<script setup>
import { computed, ref, watch } from 'vue'
import TaskCreateModal from '@/components/lcs/TaskCreateModal.vue'
import AppSidebar from '@/components/Layouts/AppSidebar.vue'
import AppHeader from '@/components/Layouts/AppHeader.vue'
import GlobalModals from '@/components/Modals/GlobalModals.vue'
import LCSBrandHeader from '@/components/lcs/LCSBrandHeader.vue'
import PilandaSidebar from '@/components/lcs/PilandaSidebar.vue'
import PpAppbar from '@/components/pp/PpAppbar.vue'
import PpInspector from '@/components/pp/PpInspector.vue'
import PpFunctionBar from '@/components/pp/PpFunctionBar.vue'
import PpMobileNav from '@/components/pp/PpMobileNav.vue'
import IconMenu from '~icons/lucide/menu'
import IconHouse from '~icons/lucide/house'
import IconFolderKanban from '~icons/lucide/folder-kanban'
import IconSearch from '~icons/lucide/search'
import PpInspectorNodeView from '@/components/lcs/PpInspectorNodeView.vue'
import { useRouter, useRoute } from 'vue-router'
import { usePilandaMode } from '@/composables/usePilandaMode'
import { useViewport } from '@/composables/useViewport'
import { usePilandaInspect } from '@/composables/usePilandaInspect'
import { usePilandaFuncbar } from '@/composables/usePilandaFuncbar'
import { sessionStore } from '@/stores/session'
import { usersStore } from '@/stores/users'
import { useOnboarding } from 'frappe-ui/frappe'

const { pilandaMode } = usePilandaMode()
const { isMobile } = useViewport()
const router = useRouter()
const route = useRoute()
// Mobile nav drawer open-state (off-canvas PilandaSidebar), toggled by the
// bottom-nav "Menü" tab; auto-closes on nav-item / back clicks.
const mobileNavOpen = ref(false)

// Highlight the bottom tab matching the current route.
const mobileNavActive = computed(() => {
  const p = route.path || ''
  if (p.startsWith('/crm/project')) return 'projects'   // list + detail
  if (p.startsWith('/dashboard') || p === '/' || p === '/crm') return 'start'
  return ''
})

// Bottom tab bar (design master .mnav). The master's generic Home/News/
// Assistent become CRM-real targets: Start=Dashboard, Projekte=core screen.
// The 4th slot (master's "Pi" assistant, no bot yet) opens the global search
// palette — the closest smart entry point until pilanda_salesbot exists.
const mobileNavItems = [
  { key: 'menu',     label: __('Menu'),     icon: IconMenu },
  { key: 'start',    label: __('Start'),    icon: IconHouse },
  { key: 'projects', label: __('Projects'), icon: IconFolderKanban },
  { key: 'search',   label: __('Search'),   icon: IconSearch },
]
function onMobileNav(key) {
  if (key === 'menu') { mobileNavOpen.value = !mobileNavOpen.value; return }
  mobileNavOpen.value = false
  if (key === 'start') router.push({ name: 'Dashboard' })
  else if (key === 'projects') router.push('/crm/projects')
  else if (key === 'search') window.dispatchEvent(new Event('lcs-open-search'))
}

const { spec: inspSpec, view: inspView, panel: inspPanel, collapsed: inspCollapsed, setCollapsed: setInspCollapsed } = usePilandaInspect()
const { open: funcbarOpen, groups: funcbarGroups, available: funcbarAvailable, runAction: onFuncbarAction } = usePilandaFuncbar()

// On mobile the nav drawer, the inspector overlay and the function bar are all
// full-screen-ish layers at modal z-index — keep them mutually exclusive so two
// never fight over the screen (and so the funcbar, which otherwise opens BEHIND
// the inspector overlay, becomes visible). Declared AFTER the composables above
// so the refs they watch are already initialised (no temporal-dead-zone error).
watch(mobileNavOpen, (open) => {
  if (open && isMobile.value) setInspCollapsed(true)
})
watch(inspCollapsed, (collapsed) => {
  if (!collapsed && isMobile.value) mobileNavOpen.value = false
})
watch(funcbarOpen, (open) => {
  if (open && isMobile.value) { setInspCollapsed(true); mobileNavOpen.value = false }
})

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

<style scoped>
/* One consistent Pilanda backdrop for the whole content column (header + page),
   so the token-gray page canvases and the shell chrome no longer clash white vs.
   gray. White cards (--pp-bg-surface) float on this base. */
.lcs-pilanda-content { background: var(--pp-bg-base); }
/* Positioned canvas so the absolute PpFunctionBar overlays the top of the
   content area (it fills the top edge of its positioned parent). */
.lcs-pilanda-canvas { position: relative; }

/* Master rule 5: fixed 28px status bar (Marke · LCS Group · Benutzer · Stand). */
.lcs-statusbar { height: 28px; flex: none; display: flex; align-items: center; gap: var(--pp-space-3);
  padding: 0 var(--pp-space-4); font-size: 10.5px; color: var(--pp-text-tertiary);
  background: var(--pp-bg-surface); border-top: 1px solid var(--pp-border-subtle); }
.lcs-statusbar-brand { font-weight: var(--pp-weight-bold); color: var(--pp-brand-primary); letter-spacing: .02em; }
.lcs-statusbar-dot { opacity: .5; }
.lcs-statusbar-spacer { flex: 1; }
</style>
