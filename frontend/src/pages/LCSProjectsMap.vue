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
          <div class="lcspm-seg">
            <button
              v-for="s in segments"
              :key="s.key"
              type="button"
              class="lcspm-seg-btn"
              :class="{ 'is-active': segment === s.key }"
              @click="segment = s.key"
            >{{ s.label }}</button>
          </div>
          <Button :loading="geo.loading" @click="geo.reload()">
            <template #prefix><LucideRefreshCw class="h-4 w-4" /></template>
            {{ __('Refresh') }}
          </Button>
        </template>
      </PpPageHead>
    </header>

    <div class="lcspm-body flex-1 min-h-0 overflow-hidden p-3">
      <PpGeoMap :masten="masten" :pins="pins" :segment="segment" height="100%" @inspect="onInspect" />
    </div>

    <footer class="lcspm-foot">
      <span>
        {{ masten.length }} {{ __('routes') }} · {{ pins.length }} {{ __('pins') }} ·
        {{ masten.length + pins.length }} {{ __('total') }}
      </span>
      <span v-if="geo.loading" class="lcspm-foot-muted">{{ __('Loading …') }}</span>
    </footer>
  </div>
</template>

<script setup>
import { computed, ref, onBeforeUnmount } from 'vue'
import { Button, createResource } from 'frappe-ui'
import LucideRefreshCw from '~icons/lucide/refresh-cw'
import PpGeoMap from '@/components/pp/PpGeoMap.vue'
import PpPageHead from '@/components/pp/PpPageHead.vue'
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

// PpGeoMap-Status-Segment (Lebenszyklus) statt der alten Phasen-Filterzeile.
const segment = ref('all')
const segments = [
  { key: 'all', label: __('All') },
  { key: 'akquise', label: __('Acquisition') },
  { key: 'bau', label: __('Building') },
  { key: 'betrieb', label: __('Operating') },
  { key: 'service', label: __('Service') },
]

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
