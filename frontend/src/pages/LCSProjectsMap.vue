<!--
  LCSProjectsMap — Projektkarte (Projektkarte-Nav) auf dem Theme-Baustein
  PpGeoMap: echte Seilkran-Trassen (Endmast Tal ↔ Berg) je Projekt mit
  Mast-Koordinaten, sonst ein Länder-Zentroid-Pin. Marker-Form = Anlagentyp,
  Farbe = Lebenszyklus (aus der Phase). Klick → Shell-Inspektor.

  Daten: lcs_integrations.projects.api.get_project_geo → { masten, pins }.
-->
<template>
  <div class="lcspm flex min-h-0 flex-1 flex-col">
    <header class="lcspm-head">
      <PpPageHead
        :title="__('Projects Map')"
        :subtitle="__('Cable-crane routes on a live map · click a project for the details')"
      >
        <template #actions>
          <!-- Layer: Projekte (Trassen) ⇄ Markteinteilung (Territorien) —
               die Projektlandkarte bündelt jetzt alle Karten-Layer. -->
          <div class="lcspm-seg">
            <button
              v-for="l in layers"
              :key="l.key"
              type="button"
              class="lcspm-seg-btn"
              :class="{ 'is-active': layer === l.key }"
              @click="layer = l.key"
            >{{ l.label }}</button>
          </div>
          <div v-if="layer === 'projekte'" class="lcspm-seg">
            <button
              v-for="s in segments"
              :key="s.key"
              type="button"
              class="lcspm-seg-btn"
              :class="{ 'is-active': segment === s.key }"
              @click="segment = s.key"
            >{{ s.label }}</button>
          </div>
          <Button :loading="geo.loading || market.loading" @click="reloadActive">
            <template #prefix><LucideRefreshCw class="h-4 w-4" /></template>
            {{ __('Refresh') }}
          </Button>
        </template>
      </PpPageHead>
    </header>

    <div class="lcspm-body flex-1 min-h-0 overflow-hidden p-3">
      <PpGeoMap v-if="layer === 'projekte'" :masten="masten" :pins="pins" :segment="segment" height="100%" @inspect="onInspect" />
      <TerritoryMap v-else-if="markers.length" :markers="markers" :active-id="activeId" height-class="h-full" @marker-click="pickMarker" />
      <div v-else class="lcspm-empty">{{ market.loading ? __('Loading …') : __('No territories with coordinates yet') }}</div>
    </div>

    <footer class="lcspm-foot">
      <span v-if="layer === 'projekte'">
        {{ masten.length }} {{ __('routes') }} · {{ pins.length }} {{ __('pins') }} ·
        {{ masten.length + pins.length }} {{ __('total') }}
      </span>
      <span v-else>
        {{ markers.length }} {{ __('territories') }} · {{ managerCount }} {{ __('sales managers') }}
      </span>
      <span v-if="geo.loading || market.loading" class="lcspm-foot-muted">{{ __('Loading …') }}</span>
    </footer>
  </div>
</template>

<script setup>
import { computed, ref, watch, onBeforeUnmount } from 'vue'
import { Button, createResource } from 'frappe-ui'
import LucideRefreshCw from '~icons/lucide/refresh-cw'
import PpGeoMap from '@/components/pp/PpGeoMap.vue'
import PpPageHead from '@/components/pp/PpPageHead.vue'
import TerritoryMap from '@/components/lcs/TerritoryMap.vue'
import { usePilandaMode } from '@/composables/usePilandaMode'
import { usePilandaInspect } from '@/composables/usePilandaInspect'

const { pilandaMode } = usePilandaMode()
const { inspectNode } = usePilandaInspect()

const geo = createResource({
  url: 'lcs_integrations.projects.api.get_project_geo',
  auto: true,
})
const masten = computed(() => geo.data?.masten || [])
const pins = computed(() => geo.data?.pins || [])

// Karten-Layer: Projekte (Trassen) ⇄ Markteinteilung (Territorien).
const layer = ref('projekte')
const layers = [
  { key: 'projekte', label: __('Projects') },
  { key: 'markt', label: __('Market assignment') },
]

// PpGeoMap-Status-Segment (Lebenszyklus) statt der alten Phasen-Filterzeile.
const segment = ref('all')
const segments = [
  { key: 'all', label: __('All') },
  { key: 'akquise', label: __('Acquisition') },
  { key: 'bau', label: __('Building') },
  { key: 'betrieb', label: __('Operating') },
  { key: 'service', label: __('Service') },
]

// --- Markteinteilung-Layer (TerritoryMap, aus get_market_assignment) --------
const market = createResource({ url: 'lcs_integrations.projects.api.get_market_assignment' })
// Erst laden, wenn der Layer zum ersten Mal angewählt wird.
watch(layer, (l) => { if (l === 'markt' && !market.data && !market.loading) market.fetch() })
const territories = computed(() => market.data?.territories || [])
const managers = computed(() => market.data?.managers || [])
const managerCount = computed(() => market.data?.summary?.managers || managers.value.length)

const PALETTE = ['brand', 'info', 'success', 'warning', 'danger', 'neutral']
const mgrKindMap = computed(() => {
  const map = {}
  managers.value.forEach((m, i) => { if (m.code && m.code !== '—') map[m.code] = PALETTE[i % PALETTE.length] })
  return map
})
const markers = computed(() =>
  territories.value
    .filter((t) => t.latitude != null && t.longitude != null)
    .map((t) => ({ id: t.territory, lat: t.latitude, lon: t.longitude,
      label: `${t.territory} · ${t.code || '—'}`, kind: mgrKindMap.value[t.code] || 'neutral' })),
)
const activeId = ref(null)
function pickMarker(id) {
  activeId.value = id
  const t = territories.value.find((x) => x.territory === id)
  if (t && pilandaMode.value) {
    inspectNode({
      title: t.territory,
      rows: [
        { label: __('Region'), value: t.region || '—' },
        { label: __('Sales manager'), value: t.sales_manager || t.code || '—' },
        { label: __('Country'), value: t.country || '—' },
      ],
    })
  }
}
function reloadActive() { if (layer.value === 'markt') market.reload(); else geo.reload() }

// Klick auf Anlage/Pin/Seillinie → angedockter Shell-Inspektor.
function onInspect(payload) {
  if (!pilandaMode.value) return
  inspectNode({
    title: payload?.title || '',
    rows: (payload?.rows || []).map((r) => ({ label: r[0], value: r[1] })),
  })
}
onBeforeUnmount(() => {
  if (pilandaMode.value) inspectNode(null)
})
</script>

<style scoped>
.lcspm { background: var(--pp-bg-base); }
.lcspm-head { padding: var(--pp-space-5) var(--pp-space-5) var(--pp-space-4);
  background: var(--pp-bg-surface); border-bottom: 1px solid var(--pp-border-subtle); }
.lcspm-body { background: var(--pp-bg-base); }
.lcspm-foot { display: flex; align-items: center; justify-content: space-between;
  padding: var(--pp-space-2) var(--pp-space-4); font-size: var(--pp-fs-12);
  color: var(--pp-text-tertiary); background: var(--pp-bg-surface);
  border-top: 1px solid var(--pp-border-subtle); }
.lcspm-foot-muted { color: var(--pp-text-tertiary); opacity: 0.75; }
.lcspm-empty { display: flex; align-items: center; justify-content: center; height: 100%;
  color: var(--pp-text-tertiary); font-size: var(--pp-fs-14); }

/* Status-Segment (Lebenszyklus-Filter) */
.lcspm-seg { display: inline-flex; gap: 2px; padding: 2px; border-radius: var(--pp-radius-ui);
  background: var(--pp-bg-base); border: 1px solid var(--pp-border-subtle); }
.lcspm-seg-btn { appearance: none; cursor: pointer; font-family: inherit; font-size: var(--pp-fs-12);
  padding: 4px 10px; border: none; border-radius: var(--pp-radius-ui); background: transparent;
  color: var(--pp-text-secondary); }
.lcspm-seg-btn:hover { color: var(--pp-brand-primary); }
.lcspm-seg-btn.is-active { background: var(--pp-bg-surface); color: var(--pp-brand-primary);
  font-weight: var(--pp-weight-semibold); box-shadow: var(--pp-shadow-xs); }
</style>
