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
          <button type="button" class="lcspm-seg-btn lcspm-legbtn" :class="{ 'is-active': showLegend }" @click="showLegend = !showLegend">
            {{ __('Legend') }}
          </button>
          <Button :loading="geo.loading || market.loading" @click="reloadActive">
            <template #prefix><LucideRefreshCw class="h-4 w-4" /></template>
            {{ __('Refresh') }}
          </Button>
        </template>
      </PpPageHead>
    </header>

    <div class="lcspm-body flex-1 min-h-0 overflow-hidden p-3">
      <PpGeoMap v-if="layer === 'projekte'" :masten="masten" :pins="pins" :segment="segment" height="100%" @inspect="onInspect" />
      <TerritoryMap v-else-if="territoryPolygons.length" :polygons="territoryPolygons" :pins="pins" :active-id="activeId" height-class="h-full" @marker-click="pickMarker" />
      <div v-else class="lcspm-empty">{{ market.loading ? __('Loading …') : __('No territories with countries yet') }}</div>

      <!-- Legende (einblendbar) -->
      <div v-if="showLegend" class="lcspm-legend">
        <div class="lcspm-legend-head">
          <span>{{ __('Legend') }}</span>
          <button type="button" class="lcspm-legend-x" @click="showLegend = false">×</button>
        </div>
        <template v-if="layer === 'projekte'">
          <div class="lcspm-legend-sec">{{ __('Plant type') }}</div>
          <div class="lcspm-legend-row"><span class="lcspm-gly">▲</span>{{ __('Cable crane') }}</div>
          <div class="lcspm-legend-row"><span class="lcspm-gly">●</span>{{ __('Material ropeway') }}</div>
          <div class="lcspm-legend-row"><span class="lcspm-gly">◆</span>{{ __('Winch') }}</div>
          <div class="lcspm-legend-sec">{{ __('Status') }}</div>
          <div class="lcspm-legend-row"><i class="lcspm-dot" style="background:var(--pp-state-warning)" />{{ __('Building') }}</div>
          <div class="lcspm-legend-row"><i class="lcspm-dot" style="background:var(--pp-state-success)" />{{ __('Operating') }}</div>
          <div class="lcspm-legend-row"><i class="lcspm-dot" style="background:var(--pp-state-danger)" />{{ __('Service due') }}</div>
          <div class="lcspm-legend-row"><i class="lcspm-dot" style="background:var(--pp-brand-primary)" />{{ __('Acquisition') }}</div>
        </template>
        <template v-else>
          <div class="lcspm-legend-sec">{{ __('Territory by sales manager') }}</div>
          <div v-for="m in legendManagers" :key="m.code" class="lcspm-legend-row">
            <i class="lcspm-dot" :style="{ background: toneColor(m.kind) }" />{{ m.code }}<template v-if="m.user_name"> · {{ m.user_name }}</template>
          </div>
          <div class="lcspm-legend-sec">{{ __('Projects') }}</div>
          <div class="lcspm-legend-row"><i class="lcspm-dot" style="background:var(--pp-brand-primary)" />{{ __('Project location') }}</div>
        </template>
      </div>
    </div>

    <footer class="lcspm-foot">
      <span v-if="layer === 'projekte'">
        {{ masten.length }} {{ __('routes') }} · {{ pins.length }} {{ __('pins') }} ·
        {{ masten.length + pins.length }} {{ __('total') }}
      </span>
      <span v-else>
        {{ territoryPolygons.length }} {{ __('territories') }} · {{ managerCount }} {{ __('sales managers') }}
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

// Legende (einblendbar): Symbole/Farben erklären. Tone → CSS-Var wie TerritoryMap.
const showLegend = ref(false)
const TONE_VAR = {
  brand: 'var(--pp-brand-primary)', info: 'var(--pp-state-info)', success: 'var(--pp-state-success)',
  warning: 'var(--pp-state-warning)', danger: 'var(--pp-state-danger)', neutral: 'var(--pp-text-tertiary)',
}
function toneColor(kind) { return TONE_VAR[kind] || TONE_VAR.neutral }
const legendManagers = computed(() =>
  managers.value
    .filter((m) => m.code && m.code !== '—')
    .map((m) => ({ code: m.code, user_name: m.user_name, kind: mgrKindMap.value[m.code] || 'neutral' })),
)
// Territories as filled country polygons, coloured by responsible sales manager.
const territoryPolygons = computed(() =>
  territories.value
    .filter((t) => (t.countries || []).length)
    .map((t) => ({ id: t.territory, countries: t.countries,
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
        { label: __('Sales manager'), value: t.user_name || t.sales_manager || t.code || '—' },
        { label: __('Countries'), value: (t.countries || []).join(', ') || '—' },
        { label: __('Projects'), value: String(t.projects ?? 0) },
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
.lcspm-body { background: var(--pp-bg-base); position: relative; }

/* Legende (Overlay auf der Karte) */
.lcspm-legbtn { border: 1px solid var(--pp-border-subtle); }
.lcspm-legend { position: absolute; top: var(--pp-space-4); right: var(--pp-space-4); z-index: 500;
  min-width: 170px; background: var(--pp-bg-surface); border: 1px solid var(--pp-border-default);
  border-radius: var(--pp-radius-ui); box-shadow: var(--pp-shadow-md); padding: var(--pp-space-3);
  font-size: var(--pp-fs-12, 12px); color: var(--pp-text-primary); }
.lcspm-legend-head { display: flex; align-items: center; justify-content: space-between;
  font-weight: var(--pp-weight-semibold); margin-bottom: var(--pp-space-2); }
.lcspm-legend-x { appearance: none; cursor: pointer; border: 0; background: transparent;
  font-size: 16px; line-height: 1; color: var(--pp-text-tertiary); padding: 0 2px; }
.lcspm-legend-x:hover { color: var(--pp-text-primary); }
.lcspm-legend-sec { font-size: 10px; text-transform: uppercase; letter-spacing: 0.06em;
  color: var(--pp-text-tertiary); font-weight: var(--pp-weight-semibold); margin: var(--pp-space-2) 0 4px; }
.lcspm-legend-row { display: flex; align-items: center; gap: 8px; padding: 2px 0; }
.lcspm-dot { width: 10px; height: 10px; border-radius: var(--pp-radius-full); flex-shrink: 0; }
.lcspm-gly { width: 12px; text-align: center; color: var(--pp-brand-primary); }
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
