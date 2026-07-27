<!--
  PilandaSidebar — the Pilanda shell sidebar inside the CRM (Pilanda mode).
  Feeds PpSidebar@5 with the Pilanda nav (pilanda.api.get_nav_v2 — EXAKT das
  Desk-Boot-Modell) und routet: /crm/* bleibt in-SPA, alle anderen Ziele laden
  den Pilanda-Desk (window.location).

  Angeglichen an die Desk-Shell (PilandaDesk.vue, 20.07.2026):
    · Icon-Resolver (lucide) — Modul- + Item-Icons wie im Desk (ICON_MAP +
      Schlüsselwort-Fallback iconFor), statt des CircleDot-Platzhalters.
    · Getönter „Allgemein"-Block + „Wissen"-Block — der Host baut aus der
      flachen SSOT (allgemein/wissen) die ANZEIGE-Struktur (wie im Desk).
    · Breite responsiv wie im Desk (242 / 284 / 340 je Breakpoint), ziehbar +
      einklappbar (Collapse-Muster), Zustand in localStorage.
  Nur im Pilanda-Modus gemountet; CRM-only behält Dominiks AppSidebar.
-->

<template>
  <div class="pilanda-sidebar-host">
    <!-- Zurück = schlichter Pfeil als eigene Zeile über dem Modul-Dropdown
         (Klickdummy-Master Regel 3; Label = vorherige Station). -->
    <button
      v-if="canBack"
      type="button"
      class="pilanda-back"
      :class="{ 'is-rail': collapsed }"
      :title="__('Back') + (prevStation ? ' · ' + prevStation : '')"
      @click="goBack"
    >
      <IconArrowLeft class="pilanda-back-ico" />
      <span v-if="!collapsed" class="pilanda-back-label">{{ prevStation || __('Back') }}</span>
    </button>
    <PpSidebar
      class="pilanda-sb-main"
      :modules="modules"
      :zones="zones"
      :allgemein="allgemeinDisplay"
      :wissen="wissenDisplay"
      :icon-resolver="iconResolver"
      v-model:active-id="activeId"
      v-model:active-key="activeKey"
      v-model:collapsed="collapsed"
      v-model:width="sbWidth"
      :min-width="170"
      :max-width="440"
      :rail-width="56"
      @navigate="onNavigate"
    />
    <!-- Kein CRM-Only-Button mehr (Marco 20.07.2026: EINE Shell;
         Standalone-Ansicht nur noch via ?mode=crm). -->
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import { useRouter } from 'vue-router'
import PpSidebar from '@/components/pp/PpSidebar.vue'
import { usePilandaNav } from '@/composables/usePilandaNav'
import IconArrowLeft from '~icons/lucide/arrow-left'

// Lucide-Icons (~icons/lucide/* — frappeui/vite lucideIcons-Plugin, wie im Desk).
import IconHouse from '~icons/lucide/house'
import IconNewspaper from '~icons/lucide/newspaper'
import IconRadar from '~icons/lucide/radar'
import IconTrendingUp from '~icons/lucide/trending-up'
import IconFolderKanban from '~icons/lucide/folder-kanban'
import IconCompass from '~icons/lucide/compass'
import IconShoppingCart from '~icons/lucide/shopping-cart'
import IconFactory from '~icons/lucide/factory'
import IconTruck from '~icons/lucide/truck'
import IconHardHat from '~icons/lucide/hard-hat'
import IconGauge from '~icons/lucide/gauge'
import IconWrench from '~icons/lucide/wrench'
import IconBanknote from '~icons/lucide/banknote'
import IconScale from '~icons/lucide/scale'
import IconUsers from '~icons/lucide/users'
import IconShieldCheck from '~icons/lucide/shield-check'
import IconGraduationCap from '~icons/lucide/graduation-cap'
import IconBookOpen from '~icons/lucide/book-open'
import IconLanguages from '~icons/lucide/languages'
import IconLayoutDashboard from '~icons/lucide/layout-dashboard'
import IconCircleCheck from '~icons/lucide/circle-check'
import IconTicket from '~icons/lucide/ticket'
import IconPlane from '~icons/lucide/plane'
import IconBoxes from '~icons/lucide/boxes'
import IconLayoutGrid from '~icons/lucide/layout-grid'
import IconFileText from '~icons/lucide/file-text'
import IconCircleDot from '~icons/lucide/circle-dot'
import IconMap from '~icons/lucide/map'
import IconBuilding from '~icons/lucide/building-2'
import IconPhone from '~icons/lucide/phone'
import IconTarget from '~icons/lucide/target'
import IconUserPlus from '~icons/lucide/user-plus'
import IconStickyNote from '~icons/lucide/sticky-note'
import IconClipboardCheck from '~icons/lucide/clipboard-check'
import IconCalendarDays from '~icons/lucide/calendar-days'


const ICON_MAP = {
  house: IconHouse, newspaper: IconNewspaper, radar: IconRadar,
  'trending-up': IconTrendingUp, 'folder-kanban': IconFolderKanban,
  compass: IconCompass, 'shopping-cart': IconShoppingCart, factory: IconFactory,
  truck: IconTruck, 'hard-hat': IconHardHat, gauge: IconGauge, wrench: IconWrench,
  banknote: IconBanknote, scale: IconScale, users: IconUsers,
  'shield-check': IconShieldCheck, 'graduation-cap': IconGraduationCap,
  'book-open': IconBookOpen, languages: IconLanguages,
  'layout-dashboard': IconLayoutDashboard, 'circle-check': IconCircleCheck,
  ticket: IconTicket, plane: IconPlane, boxes: IconBoxes,
  'layout-grid': IconLayoutGrid, apps: IconLayoutGrid, 'file-text': IconFileText,
}

// Schlüsselwort-Fallback (Port des Desk-iconFor) für Items ohne icon-Feld.
function iconFor(name) {
  const n = String(name || '').toLowerCase()
  if (/interessent|\blead/.test(n)) return IconUserPlus
  if (/verkaufschance|chance|opportunity|\bdeal/.test(n)) return IconTarget
  if (/auftrag|zuschlag|\border/.test(n)) return IconClipboardCheck
  if (/vertriebsprojekt|\bprojekt/.test(n)) return IconFolderKanban
  if (/karte|landkarte|\bmap/.test(n)) return IconMap
  if (/markt|aufteilung|territor/.test(n)) return IconMap
  if (/meeting|besprechung/.test(n)) return IconCalendarDays
  if (/prognose|forecast/.test(n)) return IconTrendingUp
  if (/firma|firmen|unternehmen|organisation/.test(n)) return IconBuilding
  if (/\bperson/.test(n)) return IconUsers
  if (/notiz|\bnote/.test(n)) return IconStickyNote
  if (/call|anruf|telefon/.test(n)) return IconPhone
  if (/portfolio|forecast|scout|pilot|leitstelle|radar/.test(n)) return IconRadar
  if (/lager|artikel|bestand|inventur|stück|bom|variante/.test(n)) return IconBoxes
  if (/doku|lastenheft|bericht|angebot|vertrag|dokument/.test(n)) return IconFileText
  if (/ticket|helpdesk|todo/.test(n)) return IconTicket
  if (/reise|travel/.test(n)) return IconPlane
  if (/kunde|kontakt|agent|partner|mitarbeiter|ressourc|netzwerk/.test(n)) return IconUsers
  if (/norm|regel|recht|edition|ausgabe/.test(n)) return IconScale
  if (/anwendung|apps|portal|sharefile|vault/.test(n)) return IconLayoutGrid
  if (/wissen|wiki|lern|kurs|schulung/.test(n)) return IconBookOpen
  if (/dashboard|kennzahl/.test(n)) return IconLayoutDashboard
  return IconCircleDot
}
function iconResolver(nameOrKeyword) {
  const key = String(nameOrKeyword || '').replace(/^lucide-/, '')
  return ICON_MAP[key] || iconFor(nameOrKeyword)
}

const router = useRouter()
const { modules, zones, allgemein, wissen, load } = usePilandaNav()

onMounted(load)

// ---------------------------------------------------------------
// Zurück-Zeile (Master Regel 3): schlichter Pfeil über dem Dropdown,
// Label = zuletzt verlassene Station. router.afterEach merkt sich die
// Herkunft; erst nach der ersten SPA-Navigation sichtbar.
const ROUTE_LABELS = {
  Contacts: 'Personen', Contact: 'Person', Organizations: 'Firmen', Organization: 'Firma',
  Leads: 'Interessenten', Lead: 'Interessent', Deals: 'Verkaufschancen', Deal: 'Verkaufschance',
  'LCS Projects': 'Vertriebsprojekte', 'LCS Project': 'Projekt', 'LCS Network': 'Netzwerk',
  'LCS Market Assignment': 'Marktaufteilung', 'LCS Forecasting': 'Prognose',
  'LCS Sales Meeting': 'Sales Meeting', 'LCS Quick Note': 'Quick Note',
  'LCS CRM Dashboard': 'Dashboard', Notes: 'Notizen', Tasks: 'Aufgaben', 'Call Logs': 'Call Logs',
}
function stationLabel(r) {
  if (!r || !r.name) return ''
  return ROUTE_LABELS[r.name] || __(String(r.name))
}
const prevStation = ref('')
const canBack = ref(false)
function goBack() { router.back() }
const _removeAfterEach = router.afterEach((to, from) => {
  if (from && from.name && from.fullPath !== to.fullPath) {
    prevStation.value = stationLabel(from)
    canBack.value = true
  }
})
onBeforeUnmount(() => _removeAfterEach && _removeAfterEach())

const moduleById = (id) => modules.value.find((m) => m.id === id) || null

// Highlight the sales module (our CRM) in the shell.
const activeId = ref('')
watch(
  modules,
  () => {
    if (activeId.value) return
    const m = modules.value.find(
      (x) => x.path === '/crm' || x.target === '/crm' || x.id === 'vertrieb',
    )
    if (m) activeId.value = m.id
  },
  { immediate: true },
)
const activeKey = ref(null)

// ---------------------------------------------------------------
// Allgemein-/Wissen-ANZEIGE (Host-Aufgabe lt. PpSidebar-Vertrag) — portiert
// aus PilandaDesk.vue: die flache SSOT-Liste wird in Anzeige-Reihenfolge mit
// Kind-Gruppen überführt. Labels/Icons kommen aus der SSOT (allgemein) bzw.
// den echten Modulen (moduleById) — keine neuen UI-Texte erfunden.
// ---------------------------------------------------------------
const allgemeinDisplay = computed(() => {
  const A = allgemein.value || []
  const pick = (n) => A.find((x) => x.n === n) || null
  const leaf = (n, icon) => {
    const it = pick(n)
    return it ? { ...it, label: it.n, ...(icon ? { icon } : {}) } : null
  }
  const parent = (n, icon, kids) => {
    const it = pick(n)
    if (!it) return null
    return { ...it, label: it.n, icon, children: kids.map((k) => leaf(k)).filter(Boolean) }
  }
  return [
    // News is hardcoded (not part of the Allgemein SSOT list) — gate it on the
    // module being live so the phased rollout hides it with the rest.
    ...(moduleById('news') ? [{ label: 'News', icon: 'newspaper', moduleId: 'news' }] : []),
    leaf('Projekt', 'folder-kanban'),
    leaf('Artikel', 'boxes'),
    parent('Aufgaben', 'circle-check', ['Team-Arbeitspakete', 'Meine Arbeitspakete', 'Meine To-dos']),
    leaf('Ressourcen', 'users'),
    parent('Tickets', 'ticket', ['Neues Ticket', 'Meine Tickets']),
    leaf('Reisen', 'plane'),
    parent('Anwendungen', 'layout-grid', ['FieldService', 'Sharefile', 'Autodesk Vault']),
  ].filter(Boolean)
})
const wissenDisplay = computed(() => {
  // Phased rollout: the Wissen block is hardcoded here (with fallback labels),
  // so it must be gated on the module being live — otherwise it would show even
  // after the Wissen modules are filtered out of the nav.
  if (!moduleById('wissen')) return []
  const wivio = (allgemein.value || []).find((x) => x.n === 'Wivio')
  // Labels/Icons aus den echten Wissen-Modulen (bereits lokalisiert), mit
  // Rückfall auf die Desk-Literale; Struktur folgt WISSEN aus der SSOT.
  const label = (id, fb) => moduleById(id)?.name || fb
  const icon = (id, fb) => moduleById(id)?.icon || fb
  return [
    {
      label: label('wissen', 'Wissen'), icon: icon('wissen', 'book-open'), moduleId: 'wissen',
      children: [
        { label: label('lms', 'Lernplattform'), icon: icon('lms', 'graduation-cap'), moduleId: 'lms' },
        { label: label('terminologie', 'Terminologie'), icon: icon('terminologie', 'languages'), moduleId: 'terminologie' },
        { label: label('normen', 'Normendatenbank'), icon: icon('normen', 'scale'), moduleId: 'normen' },
        ...(wivio ? [{ ...wivio, label: 'Wivio' }] : []),
      ],
    },
  ]
})

// ---------------------------------------------------------------
// Navigation: /crm bleibt in der SPA, alles andere ist ein Desk-Handoff.
// (Deckt Module, Dashboard, Allgemein-/Wissen-Items ab — PpSidebar reicht
//  entweder ein item mit .t oder eine module-id durch.)
// ---------------------------------------------------------------
// Sidebar clicks only navigate — the right-hand inspector is reserved for
// real detail selections (list rows, network nodes, project/deal/contact).
// The nav-item "Spezifikation" panel was removed on request.
function onNavigate(payload) {
  const item = payload?.item
  let target = (item && (item.t || item.target)) || null
  if (!target && payload?.id) {
    const m = moduleById(payload.id)
    target = m?.target || m?.path || null
  }
  if (!target || target === '#' || target === '—') return
  if (/^https?:/i.test(target)) {
    window.open(target, '_blank', 'noopener') // externe Ziele (Sharefile, Vault, Wivio …)
    return
  }
  // Phased rollout: some Vertrieb nav items point to Desk apps that are not
  // installed yet (e.g. Produktportfolio → /app/product-portfolio, app
  // pilanda_productportfolio). Show an in-SPA "Coming soon" instead of handing
  // off to a broken Desk route. Extend COMING_SOON as features go live.
  const cs = comingSoonFor(target)
  if (cs) {
    router.push({ name: 'Coming Soon', query: { feature: cs.title, desc: cs.desc } })
    return
  }

  if (target.startsWith('/crm')) {
    router.push(target.replace(/^\/crm/, '') || '/') // stay in the SPA
  } else {
    window.location.href = target // hand off to the Pilanda Desk
  }
}

// Desk targets that are not live yet → in-SPA "Coming soon". Keyed by the last
// path segment of the /app|/desk target; title/desc feed the placeholder page.
const COMING_SOON = {
  'product-portfolio': { title: 'Produktportfolio', desc: 'Produktübersicht & Lebenszyklus (PLM)' },
}
function comingSoonFor(target) {
  const m = /\/(?:app|desk)\/([a-z0-9-]+)/i.exec(target || '')
  return m && COMING_SOON[m[1]] ? COMING_SOON[m[1]] : null
}

// ---------------------------------------------------------------
// Breite / Collapse an die Desk-Sidebar angeglichen (SB_DEFAULT je Breakpoint;
// ziehbar + einklappbar via Collapse-Muster). Zustand überlebt Reload.
// ---------------------------------------------------------------
const SB_DEFAULT = [242, 284, 340]
const bpFor = (w) => (w >= 2500 ? 2 : w >= 1700 ? 1 : 0)
const bp = ref(bpFor(window.innerWidth))
const lsGet = (k, d) => {
  try { return localStorage.getItem(k) ?? d } catch { return d }
}
const lsSet = (k, v) => {
  try { localStorage.setItem(k, v) } catch { /* egal */ }
}
const collapsed = ref(lsGet('pilanda_sb_collapsed', '0') === '1')
const sbWidth = ref(Number(lsGet('pilanda_sb_w_' + bp.value, '')) || SB_DEFAULT[bp.value])
watch(collapsed, (v) => lsSet('pilanda_sb_collapsed', v ? '1' : '0'))
watch(sbWidth, (v) => lsSet('pilanda_sb_w_' + bp.value, String(v)))

function onResize() {
  const nb = bpFor(window.innerWidth)
  if (nb !== bp.value) {
    bp.value = nb
    sbWidth.value = Number(lsGet('pilanda_sb_w_' + nb, '')) || SB_DEFAULT[nb]
  }
}
window.addEventListener('resize', onResize)
onBeforeUnmount(() => window.removeEventListener('resize', onResize))
</script>

<style scoped>
/* Der Host trägt keine eigene Fläche — PpSidebar bringt --pp-bg-surface +
   border-right selbst mit (identisch zur Desk-Sidebar). Volle Höhe, damit die
   Sidebar zwischen Topbar und Fensterrand aufspannt. */
.pilanda-sidebar-host { display: flex; flex-direction: column; height: 100%; }
.pilanda-sb-main { flex: 1; min-height: 0; }

/* Zurück-Zeile (Master Regel 3) */
.pilanda-back { display: flex; align-items: center; gap: 8px; width: 100%; flex: none;
  padding: 8px 16px; background: var(--pp-bg-surface); border: none;
  border-bottom: 1px solid var(--pp-border-subtle); cursor: pointer;
  color: var(--pp-text-secondary); font-family: inherit; font-size: 12px; text-align: left; }
.pilanda-back:hover { background: var(--pp-bg-hover); color: var(--pp-brand-primary); }
.pilanda-back.is-rail { justify-content: center; padding: 8px 0; }
.pilanda-back-ico { width: 15px; height: 15px; flex-shrink: 0; }
.pilanda-back-label { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
</style>
