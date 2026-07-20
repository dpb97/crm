<!--
  LCSDeals — CRM-Verkaufschancen (V2, Showcase #4 „Deal-Kanban").
  ============================================================
  Pilanda-UX für die CRM-Kernfläche „Verkaufschance": Pipeline als Kanban-
  Board mit ECHTEM Drag & Drop (PpKanban) statt der Frappe-CRM-Listen-UI.
  Spalten = CRM Deal Status in position-Reihenfolge (LIVE aus der API, nicht
  hartkodiert), Karten = CRM Deal. Status-Wechsel per Drag&Drop wird
  optimistisch angezeigt und über frappe.client.set_value persistiert
  (Fehler → Rollback + Toast). Backend = Dominiks Frappe-CRM (unverändert).

  Sonderfall „Lost": Der Ziel-Status vom Typ „Lost" verlangt serverseitig
  ein Pflicht-lost_reason (crm_deal.py::validate_lost_reason). Ablage daher
  NIE stumm — beim Drop auf eine Lost-Spalte öffnet ein Dialog zur Auswahl
  des Verlustgrunds (CRM Lost Reason, LIVE geladen); Abbruch = Rollback.

  Präsentation nach pilanda_theme-Showcase #4 (ThemePreviewCrmDeals):
  PpPageHead + PpStatTile-KPI-Zeile + PpKanban + PpDrawer. AUSSCHLIESSLICH
  aus echten Pp*-Bausteinen komponiert, token-only, Vollbreiten-Canvas.
-->

<template>
  <div class="flex h-full flex-col">
    <LayoutHeader>
      <template #left-header>
        <Breadcrumbs :items="[{ label: __('Deals'), route: { name: 'Deals' } }]" />
      </template>
      <template #right-header>
        <Button :label="__('Refresh')" iconLeft="refresh-cw" @click="reload" :loading="dealsRes.loading" />
      </template>
    </LayoutHeader>

    <div class="lcsd">
      <div class="lcsd-inner">
        <PpPageHead
          :eyebrow="__('Sales / CRM')"
          :title="__('Deals')"
          :subtitle="subtitle"
        />

        <section class="lcsd-kpis">
          <PpStatTile v-for="k in kpis" :key="k.label" v-bind="k" />
        </section>

        <section class="lcsd-board">
          <div v-if="!statuses.length" class="lcsd-empty">
            {{ dealsRes.loading || statusStore.dealStatuses.loading ? __('Loading opportunities …') : __('No open opportunities') }}
          </div>
          <PpKanban
            v-else
            :columns="columns"
            :cards="cards"
            @card-click="openDeal"
            @move="onMove"
          >
            <!-- Phasen-Summe dezent im Spaltenkopf (statt im Label gequetscht) -->
            <template #column-meta="{ column }">
              <span v-if="columnSum(column.key)" class="lcsd-col-sum">{{ eurShort(columnSum(column.key)) }}</span>
            </template>
          </PpKanban>
        </section>
      </div>
    </div>

    <!-- Chancen-Profil (Detail-Drawer, echt verdrahtet an die API-Daten) -->
    <PpDrawer v-model:open="drawerOpen" :width="480" :title="sel ? sel.name : ''">
      <template v-if="sel" #title>
        <span class="lcsd-dh">{{ sel.name }} · <span class="lcsd-dh-org">{{ sel.organization || '—' }}</span></span>
      </template>
      <div v-if="sel" class="lcsd-detail">
        <h3 class="lcsd-detail-title">{{ sel.organization || sel.name }}</h3>
        <div class="lcsd-figures">
          <div class="lcsd-figure">
            <span class="lcsd-figure-cap">{{ __('Value') }}</span>
            <span class="lcsd-figure-val">{{ eur(sel.annual_revenue, sel.currency) }}</span>
          </div>
          <div class="lcsd-figure">
            <span class="lcsd-figure-cap">{{ __('Phase') }}</span>
            <span class="lcsd-figure-val lcsd-figure-val--phase">{{ statusLabel(sel.status) }}</span>
          </div>
          <div class="lcsd-figure">
            <span class="lcsd-figure-cap">{{ __('Close Probability') }}</span>
            <span class="lcsd-figure-val">{{ dealProbability(sel) }} %</span>
          </div>
        </div>

        <dl class="lcsd-meta">
          <div>
            <dt>{{ __('Owner') }}</dt>
            <dd class="lcsd-owner">
              <span v-if="sel.deal_owner" class="lcsd-avatar" :title="ownerName(sel.deal_owner)">{{ initials(ownerName(sel.deal_owner)) }}</span>
              {{ sel.deal_owner ? ownerName(sel.deal_owner) : '—' }}
            </dd>
          </div>
          <div><dt>{{ __('Currency') }}</dt><dd>{{ sel.currency || '—' }}</dd></div>
          <div><dt>{{ __('Last update') }}</dt><dd>{{ formatDate(sel.modified) }}</dd></div>
        </dl>

        <a class="lcsd-open" :href="`/crm/deals/${sel.name}`">
          <FeatherIcon name="external-link" class="h-4 w-4" />
          {{ __('Open in CRM') }}
        </a>
      </div>
    </PpDrawer>

    <!-- Lost: Pflicht-Verlustgrund NIE stumm überspringen (geteilter Baustein) -->
    <LostReasonDialog v-model="lostOpen" :saving="saving" @confirm="onLostConfirm" />
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { call, createListResource, toast, Breadcrumbs, Button, FeatherIcon } from 'frappe-ui'
import LayoutHeader from '@/components/LayoutHeader.vue'
import PpPageHead from '@/components/pp/PpPageHead.vue'
import PpStatTile from '@/components/pp/PpStatTile.vue'
import PpKanban from '@/components/pp/PpKanban.vue'
import PpDrawer from '@/components/pp/PpDrawer.vue'
import LostReasonDialog from '@/components/lcs/LostReasonDialog.vue'
import { statusesStore } from '@/stores/statuses'
import { usersStore } from '@/stores/users'

const statusStore = statusesStore()
const { getUser } = usersStore()

/* ---- Formatierung (de-DE, metrisch) --------------------------------- */
function eur(n, currency = 'EUR') {
  if (n == null || n === '') return '—'
  return new Intl.NumberFormat('de-DE', {
    style: 'currency',
    currency: currency || 'EUR',
    maximumFractionDigits: 0,
  }).format(Number(n))
}
// Kompakt für Spaltenkopf-Summen (k€ / M€).
function eurShort(n) {
  const v = Number(n) || 0
  if (v >= 1_000_000) return (v / 1_000_000).toLocaleString('de-DE', { maximumFractionDigits: 1 }) + ' M€'
  if (v >= 1_000) return Math.round(v / 1_000).toLocaleString('de-DE') + ' k€'
  return eur(v)
}
function formatDate(v) {
  if (!v) return '—'
  const d = new Date(v)
  return isNaN(d) ? String(v) : d.toLocaleDateString('de-DE')
}
function initials(name) {
  return (name || '').split(/\s+/).map((w) => w[0]).join('').slice(0, 2).toUpperCase()
}
function ownerName(email) {
  return getUser(email)?.full_name || email
}

/* ---- Status-SSOT: CRM Deal Status LIVE aus Dominiks API ------------- */
// statusesStore lädt CRM Deal Status (name/color/position/type) auto,
// orderBy position asc. Spalten spiegeln exakt Dominiks Funnel.
const statuses = computed(() => statusStore.dealStatuses.data || [])
function statusType(name) {
  return statusStore.getDealStatus(name)?.type || 'Open'
}
function statusProb(name) {
  return Number(statusStore.getDealStatus(name)?.probability) || 0
}
function statusLabel(name) {
  return name ? __(name) : '—'
}

/* ---- Deals LIVE laden (dieselben Felder wie Dominiks Deal-Liste) ---- */
const dealsRes = createListResource({
  doctype: 'CRM Deal',
  fields: ['name', 'organization', 'annual_revenue', 'currency', 'probability', 'status', 'deal_owner', 'modified'],
  orderBy: 'modified desc',
  pageLength: 500,
  cache: 'lcs-deals-board',
  auto: true,
})
function reload() {
  dealsRes.reload()
}

// Lokaler, mutierbarer Board-Zustand (Klon) für optimistisches Verschieben.
const boardDeals = ref([])
watch(
  () => dealsRes.data,
  (d) => { boardDeals.value = (d || []).map((x) => ({ ...x })) },
  { immediate: true, deep: true },
)

function dealProbability(d) {
  const p = d.probability != null && d.probability !== '' ? Number(d.probability) : statusProb(d.status)
  return Math.round(p)
}

/* ---- Kennzahlen je Spalte (Anzahl + Summe für den Spaltenkopf) ------ */
const perColumn = computed(() => {
  const map = {}
  for (const s of statuses.value) map[s.name] = { count: 0, sum: 0 }
  for (const d of boardDeals.value) {
    const c = map[d.status] || (map[d.status] = { count: 0, sum: 0 })
    c.count += 1
    c.sum += Number(d.annual_revenue) || 0
  }
  return map
})

// PpKanban-Spalten: Label = reiner Phasenname (Anzahl liefert der Zähler-Badge,
// die Phasen-Summe kommt als eigenes Element über den #column-meta-Slot, @3).
const columns = computed(() =>
  statuses.value.map((s) => ({ key: s.name, label: __(s.name) })),
)
// Phasen-Summe je Spalte (für den #column-meta-Slot).
function columnSum(key) {
  return perColumn.value[key]?.sum || 0
}

// PpKanban-Karten aus den echten Deals abgeleitet.
const cards = computed(() =>
  boardDeals.value.map((d) => {
    const type = statusType(d.status)
    const tone = type === 'Won' ? 'success' : type === 'Lost' ? 'danger' : 'info'
    return {
      id: d.name,
      col: d.status,
      title: d.organization || d.name,
      badges: [
        { label: eurShort(d.annual_revenue), tone },
        { label: dealProbability(d) + ' %', tone: 'neutral' },
      ],
      assignee: d.deal_owner ? ownerName(d.deal_owner) : null,
    }
  }),
)

/* ---- KPI-Strip: gewichtete/ungewichtete Pipeline, offene Chancen ---- */
const openDeals = computed(() =>
  boardDeals.value.filter((d) => !['Won', 'Lost'].includes(statusType(d.status))),
)
const weighted = computed(() =>
  openDeals.value.reduce((a, d) => a + (Number(d.annual_revenue) || 0) * dealProbability(d) / 100, 0),
)
const openTotal = computed(() =>
  openDeals.value.reduce((a, d) => a + (Number(d.annual_revenue) || 0), 0),
)
const wonTotal = computed(() =>
  boardDeals.value.filter((d) => statusType(d.status) === 'Won').reduce((a, d) => a + (Number(d.annual_revenue) || 0), 0),
)
const openCount = computed(() => openDeals.value.length)

const subtitle = computed(() =>
  `${openCount.value} ${__('opportunities')} · ${eur(Math.round(weighted.value))} ${__('weighted pipeline')} · ${__('drag cards between phases')}`,
)

const kpis = computed(() => [
  { label: __('Pipeline (weighted)'), value: eur(Math.round(weighted.value)), hint: __('Σ value × P(win)') },
  { label: __('Open pipeline'), value: eur(Math.round(openTotal.value)), hint: `${openCount.value} ${__('opportunities')}` },
  { label: __('Open opportunities'), value: String(openCount.value), hint: __('across open phases') },
  { label: __('Won'), value: eur(Math.round(wonTotal.value)), hint: __('closed orders') },
])

/* ---- Drag & Drop persistieren (optimistisch + Rollback + Toast) ----- */
const saving = ref(false)

async function persistStatus(deal, fields, oldStatus) {
  saving.value = true
  try {
    await call('frappe.client.set_value', {
      doctype: 'CRM Deal',
      name: deal.name,
      fieldname: fields,
    })
    toast({ title: __('Status updated'), icon: 'check-circle', iconClasses: 'text-green-500' })
    dealsRes.reload()
    return true
  } catch (e) {
    // Rollback: Karte springt in die Ausgangsspalte zurück.
    deal.status = oldStatus
    toast({
      title: __('Could not save. Please try again.'),
      text: e?.messages?.[0] || e?.message || '',
      icon: 'alert-circle',
      iconClasses: 'text-red-500',
    })
    return false
  } finally {
    saving.value = false
  }
}

function onMove({ cardId, fromCol, toCol }) {
  if (fromCol === toCol) return
  const deal = boardDeals.value.find((d) => d.name === cardId)
  if (!deal) return
  const oldStatus = fromCol
  // Optimistisch: neuer Status sofort (Karte bleibt in der Zielspalte).
  deal.status = toCol

  if (statusType(toCol) === 'Lost') {
    // Lost verlangt einen Pflicht-Grund → Dialog statt stummer Ablage.
    openLostDialog(deal, oldStatus)
    return
  }
  persistStatus(deal, { status: toCol }, oldStatus)
}

/* ---- Lost-Dialog (Pflicht-Verlustgrund, geteilter Baustein) --------- */
// Reason-Auswahl + Validierung lebt in LostReasonDialog; hier bleibt nur die
// Orchestrierung (welche Chance, Optimistik, Persistenz, Rollback).
const lostOpen = ref(false)
const lostDeal = ref(null)
const lostOldStatus = ref(null)
let lostResolved = false

function openLostDialog(deal, oldStatus) {
  lostDeal.value = deal
  lostOldStatus.value = oldStatus
  lostResolved = false
  lostOpen.value = true
}

async function onLostConfirm({ reason, notes }) {
  const fields = { status: lostDeal.value.status, lost_reason: reason }
  if (notes) fields.lost_notes = notes
  const ok = await persistStatus(lostDeal.value, fields, lostOldStatus.value)
  if (ok) {
    lostResolved = true
    lostOpen.value = false
  }
}

// Jeder Schließweg ohne erfolgreiche Persistenz → Karte zurück in die
// Ausgangsspalte (X, Backdrop, ESC, Abbrechen).
watch(lostOpen, (open) => {
  if (!open && !lostResolved && lostDeal.value) {
    lostDeal.value.status = lostOldStatus.value
    lostDeal.value = null
  }
})

/* ---- Detail-Drawer --------------------------------------------------- */
const drawerOpen = ref(false)
const selId = ref(null)
const sel = computed(() => boardDeals.value.find((d) => d.name === selId.value) || null)
function openDeal(id) {
  selId.value = id
  drawerOpen.value = true
}
</script>

<style scoped>
/* Vollbreiten-Canvas (kein max-width-Zentrieren), token-only. */
.lcsd { flex: 1; min-height: 0; overflow: auto; background: var(--pp-bg-base); }
.lcsd-inner {
  display: flex;
  flex-direction: column;
  gap: var(--pp-space-5);
  padding: var(--pp-space-6) var(--pp-space-6) var(--pp-space-12);
}

.lcsd-kpis {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: var(--pp-space-3);
}
.lcsd-board { min-width: 0; }
/* Phasen-Summe im Spaltenkopf (#column-meta-Slot) — dezent, token-only. */
.lcsd-col-sum {
  font-size: var(--pp-fs-12);
  font-weight: var(--pp-weight-semibold);
  color: var(--pp-text-secondary);
  font-variant-numeric: tabular-nums;
}
.lcsd-empty {
  padding: var(--pp-space-8);
  text-align: center;
  color: var(--pp-text-tertiary);
  font-size: var(--pp-fs-14);
}

/* Drawer-Detail */
.lcsd-dh { font-variant-numeric: tabular-nums; }
.lcsd-dh-org { color: var(--pp-text-tertiary); font-weight: var(--pp-weight-regular); }
.lcsd-detail { display: flex; flex-direction: column; gap: var(--pp-space-4); }
.lcsd-detail-title {
  margin: 0;
  font-size: var(--pp-fs-20);
  font-weight: var(--pp-weight-semibold);
  color: var(--pp-text-primary);
  font-family: var(--pp-font-heading);
}

.lcsd-figures {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--pp-space-2);
  padding: var(--pp-space-3);
  background: var(--pp-bg-sunken);
  border: 1px solid var(--pp-border-subtle);
  border-radius: var(--pp-radius-ui);
}
.lcsd-figure { display: flex; flex-direction: column; gap: 3px; }
.lcsd-figure-cap {
  font-size: 10px; font-weight: var(--pp-weight-bold); letter-spacing: 0.04em;
  text-transform: uppercase; color: var(--pp-text-tertiary);
}
.lcsd-figure-val {
  font-size: var(--pp-fs-15, 15px); font-weight: var(--pp-weight-semibold);
  color: var(--pp-text-primary); font-variant-numeric: tabular-nums;
}
.lcsd-figure-val--phase { color: var(--pp-brand-primary); }

.lcsd-meta { display: grid; grid-template-columns: 1fr 1fr; gap: var(--pp-space-2) var(--pp-space-4); margin: 0; }
.lcsd-meta dt { font-size: var(--pp-fs-12); color: var(--pp-text-tertiary); }
.lcsd-meta dd { margin: 0; font-size: var(--pp-fs-14); color: var(--pp-text-primary); }
.lcsd-owner { display: inline-flex; align-items: center; gap: var(--pp-space-2); }
.lcsd-avatar {
  display: inline-flex; align-items: center; justify-content: center; flex-shrink: 0;
  width: 20px; height: 20px; border-radius: var(--pp-radius-full);
  background: color-mix(in oklab, var(--pp-brand-primary) 16%, transparent);
  color: var(--pp-brand-primary); font-size: 9px; font-weight: var(--pp-weight-bold);
}

.lcsd-open {
  display: inline-flex; align-items: center; gap: var(--pp-space-2);
  align-self: flex-start;
  font-size: var(--pp-fs-13, 13px); color: var(--pp-brand-primary);
  text-decoration: none; font-weight: var(--pp-weight-semibold);
}
.lcsd-open:hover { text-decoration: underline; }

@media (max-width: 1080px) {
  .lcsd-kpis { grid-template-columns: repeat(2, 1fr); }
}
</style>
