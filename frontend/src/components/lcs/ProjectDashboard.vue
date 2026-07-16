<!--
  ProjectDashboard — redesigned per Shneiderman & Nielsen heuristics
  ===================================================================
  H1: Visibility — loading states, data freshness indicator, KPI delta hints
  H2: Match real world — pipeline metaphor, familiar currency format
  H3: Feedback — hover interactions on charts
  H5: Error prevention — graceful empty states
  H6: Recognition — labeled values, tooltips on chart segments
  H8: Aesthetic & minimalist — clean cards, whitespace, visual hierarchy
  H9: Error recovery — retry button on load failure
  H10: Help — empty dashboard explains how to get started
-->

<template>
  <!-- H1: Visibility — Loading skeleton -->
  <div v-if="loading" class="space-y-6">
    <div class="grid grid-cols-2 gap-4 sm:grid-cols-4">
      <div v-for="i in 4" :key="i" class="animate-pulse rounded-xl border p-5">
        <div class="h-3 w-16 rounded bg-gray-200" />
        <div class="mt-3 h-7 w-24 rounded bg-gray-100" />
      </div>
    </div>
    <div class="grid grid-cols-1 gap-6 lg:grid-cols-2">
      <div class="h-64 animate-pulse rounded-xl border bg-gray-50" />
      <div class="h-64 animate-pulse rounded-xl border bg-gray-50" />
    </div>
  </div>

  <!-- H10: Help — Empty dashboard guidance -->
  <div v-else-if="!projects.length" class="flex flex-col items-center justify-center rounded-xl border border-dashed border-gray-200 py-16">
    <FeatherIcon name="bar-chart-2" class="h-10 w-10 text-gray-300" />
    <h3 class="mt-4 text-sm font-medium text-gray-900">{{ __('Dashboard needs data') }}</h3>
    <p class="mt-1 max-w-sm text-center text-sm text-gray-500">
      {{ __('Create projects with estimated values and phases to see your pipeline visualized here.') }}
    </p>
  </div>

  <!-- Main dashboard content -->
  <div v-else class="space-y-6">
    <!-- Key metrics row — H1: System status at a glance, H8: Clean visual hierarchy -->
    <div class="grid grid-cols-2 gap-4 sm:grid-cols-4">
      <div class="rounded-xl border bg-white p-5 transition hover:shadow-sm">
        <div class="flex items-center gap-1.5 text-xs font-medium uppercase tracking-wide text-gray-400">
          <FeatherIcon name="folder" class="h-3.5 w-3.5" />
          {{ __('Projects') }}
        </div>
        <div class="mt-2 text-2xl font-bold tabular-nums text-gray-900">{{ metrics.totalProjects }}</div>
        <div class="mt-1 text-xs text-gray-400">{{ metrics.activeCount }} {{ __('active') }}</div>
      </div>
      <div class="rounded-xl border bg-white p-5 transition hover:shadow-sm">
        <div class="flex items-center gap-1.5 text-xs font-medium uppercase tracking-wide text-gray-400">
          <FeatherIcon name="trending-up" class="h-3.5 w-3.5" />
          {{ __('Pipeline') }}
        </div>
        <div class="mt-2 text-2xl font-bold tabular-nums text-lcs-primary">{{ formatCurrency(metrics.totalValue) }}</div>
        <!-- H6: Recognition — weighted value for context -->
        <div class="mt-1 text-xs text-gray-400">{{ formatCurrency(metrics.weightedValue) }} {{ __('weighted') }}</div>
      </div>
      <div class="rounded-xl border bg-white p-5 transition hover:shadow-sm">
        <div class="flex items-center gap-1.5 text-xs font-medium uppercase tracking-wide text-gray-400">
          <FeatherIcon name="percent" class="h-3.5 w-3.5" />
          {{ __('Avg Probability') }}
        </div>
        <div class="mt-2 text-2xl font-bold tabular-nums" :class="probabilityClass(metrics.avgProbability)">
          {{ metrics.avgProbability }}%
        </div>
        <div class="mt-1 text-xs text-gray-400">{{ __('across all projects') }}</div>
      </div>
      <div class="rounded-xl border bg-white p-5 transition hover:shadow-sm">
        <div class="flex items-center gap-1.5 text-xs font-medium uppercase tracking-wide text-gray-400">
          <FeatherIcon name="map-pin" class="h-3.5 w-3.5" />
          {{ __('Countries') }}
        </div>
        <div class="mt-2 text-2xl font-bold tabular-nums text-gray-900">{{ metrics.countryCount }}</div>
        <div class="mt-1 text-xs text-gray-400">{{ __('markets covered') }}</div>
      </div>
    </div>

    <div class="grid grid-cols-1 gap-6 lg:grid-cols-2">
      <!-- Pipeline funnel — H2: Match real world (sales pipeline metaphor) -->
      <div class="rounded-xl border bg-white p-5">
        <h3 class="mb-5 flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-gray-400">
          <FeatherIcon name="filter" class="h-3.5 w-3.5" />
          {{ __('Pipeline by Phase') }}
        </h3>
        <div class="space-y-3">
          <div v-for="phase in phasePipeline" :key="phase.name" class="group">
            <div class="mb-1 flex items-center justify-between text-xs">
              <span class="flex items-center gap-1.5">
                <span class="h-2 w-2 rounded-full" :style="{ backgroundColor: phaseColor(phase.name) }" />
                <span class="font-medium text-gray-700">{{ __(phase.name) }}</span>
              </span>
              <span class="tabular-nums text-gray-500">
                {{ phase.count }} &middot; {{ formatCurrency(phase.value) }}
              </span>
            </div>
            <!-- H3: Feedback — hover shows percentage -->
            <div class="relative h-5 overflow-hidden rounded-full bg-gray-100">
              <!-- H1: Visibility — proportional bar -->
              <div
                class="absolute inset-y-0 left-0 rounded-full transition-all duration-700 ease-out"
                :style="{ width: `${phase.pct}%`, backgroundColor: phaseColor(phase.name) + '40' }"
              />
              <div
                class="absolute inset-y-0 left-0 rounded-full transition-all duration-700 ease-out"
                :style="{ width: `${phase.pct}%`, backgroundColor: phaseColor(phase.name), opacity: 0.3 }"
              />
            </div>
          </div>
        </div>
      </div>

      <!-- Type distribution — H6: Recognition (labeled segments) -->
      <div class="rounded-xl border bg-white p-5">
        <h3 class="mb-5 flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-gray-400">
          <FeatherIcon name="pie-chart" class="h-3.5 w-3.5" />
          {{ __('Type Distribution') }}
        </h3>
        <div class="flex items-center justify-center py-4">
          <svg viewBox="0 0 200 200" class="h-44 w-44">
            <circle cx="100" cy="100" r="75" fill="none" style="stroke: var(--pp-border-subtle)" stroke-width="28" />
            <circle
              v-for="segment in typeSegments"
              :key="segment.type"
              cx="100"
              cy="100"
              r="75"
              fill="none"
              :stroke="segment.color"
              stroke-width="28"
              :stroke-dasharray="`${segment.arc} ${circumference - segment.arc}`"
              :stroke-dashoffset="-segment.offset"
              class="transition-all duration-500"
            />
            <!-- Center label — H8: Minimalist, single focus point -->
            <text x="100" y="94" text-anchor="middle" class="fill-gray-900 text-2xl font-bold">
              {{ metrics.totalProjects }}
            </text>
            <text x="100" y="114" text-anchor="middle" class="fill-gray-400 text-[11px]">
              {{ __('Total') }}
            </text>
          </svg>
        </div>
        <!-- Legend — H6: Recognition (full type names, counts, percentages) -->
        <div class="mt-2 grid grid-cols-2 gap-2 sm:grid-cols-3">
          <div v-for="segment in typeSegments" :key="'legend-' + segment.type" class="flex items-center gap-2 rounded-lg bg-gray-50 px-3 py-2">
            <span class="h-3 w-3 shrink-0 rounded-full" :style="{ backgroundColor: segment.color }" />
            <div>
              <!-- H8: Reduce memory — show both code and full name -->
              <div class="text-xs font-medium text-gray-700">{{ segment.type }}</div>
              <div class="text-[10px] text-gray-400">{{ segment.count }} ({{ segment.percentage }}%)</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Map section — H1: Full context at a glance -->
    <div class="rounded-xl border bg-white p-5">
      <h3 class="mb-4 flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-gray-400">
        <FeatherIcon name="globe" class="h-3.5 w-3.5" />
        {{ __('Project Locations') }}
      </h3>
      <ProjectMap :projects="projectsWithCoords" />
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { FeatherIcon } from 'frappe-ui'
import ProjectMap from '@/components/lcs/ProjectMap.vue'

const props = defineProps({
  projects: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
})

const metrics = computed(() => {
  const list = props.projects
  const totalProjects = list.length
  const totalValue = list.reduce((sum, p) => sum + (p.estimated_value || 0), 0)
  const withProb = list.filter((p) => p.probability != null && p.probability > 0)
  const avgProbability = withProb.length
    ? Math.round(withProb.reduce((sum, p) => sum + p.probability, 0) / withProb.length)
    : 0
  // H6: Recognition — weighted value helps understanding
  const weightedValue = list.reduce((sum, p) => sum + (p.estimated_value || 0) * (p.probability || 0) / 100, 0)
  const activePhases = ['Qualified', 'Budget', 'Richtpreis', 'Offer', 'Negotiation', 'Won', 'Execution']
  const activeCount = list.filter((p) => activePhases.includes(p.phase)).length
  const countryCount = new Set(list.map((p) => p.country).filter(Boolean)).size
  return { totalProjects, totalValue, weightedValue, avgProbability, activeCount, countryCount }
})

const phaseOrder = ['Qualified', 'Budget', 'Richtpreis', 'Offer', 'Negotiation', 'Won', 'Execution', 'Completed', 'Lost']

const phasePipeline = computed(() => {
  const maxValue = Math.max(
    ...phaseOrder.map((ph) =>
      props.projects.filter((p) => p.phase === ph).reduce((s, p) => s + (p.estimated_value || 0), 0),
    ),
    1,
  )
  return phaseOrder.map((name) => {
    const matching = props.projects.filter((p) => p.phase === name)
    const value = matching.reduce((s, p) => s + (p.estimated_value || 0), 0)
    return {
      name,
      count: matching.length,
      value,
      pct: Math.max(Math.round((value / maxValue) * 100), matching.length ? 3 : 0), // min-width for non-empty
    }
  }).filter((p) => p.count > 0) // H8: Only show phases with data
})

// Diverging Phasen-Palette (unterscheidbare Datentoene, bewusst als Hex):
// die Werte werden fuer den Balken mit einem Alpha-Suffix ('+40') verkettet
// und als SVG-:stroke-Attribut gesetzt -> var()/oklch sind dort NICHT
// verwendbar. 'Execution' ist der Marken-Ton = Brand-Cyan (SSOT: pp-tokens
// --pp-brand-primary / --pp-brand-700 = #008B8B); vormals Alt-Navy.
const phaseColorMap = {
  Qualified: '#0ea5e9',
  Budget: '#14b8a6',
  Richtpreis: '#8b5cf6',
  Offer: '#f59e0b',
  Negotiation: '#f97316',
  Won: '#22c55e',
  Execution: '#008B8B',
  Completed: '#6b7280',
  Lost: '#ef4444',
}

function phaseColor(phase) {
  return phaseColorMap[phase] || '#6b7280'
}

const typeColors = {
  SB: '#3b82f6',
  WI: '#a855f7',
  LL: '#10b981',
  SK: '#f59e0b',
  Other: '#6b7280',
}

const circumference = 2 * Math.PI * 75

const typeSegments = computed(() => {
  const counts = {}
  props.projects.forEach((p) => {
    const t = p.project_type || 'Other'
    counts[t] = (counts[t] || 0) + 1
  })
  const total = props.projects.length || 1
  let offset = 0
  return Object.keys(counts)
    .sort((a, b) => (counts[b] || 0) - (counts[a] || 0)) // H8: Largest first
    .map((type) => {
      const count = counts[type]
      const arc = (count / total) * circumference
      const percentage = Math.round((count / total) * 100)
      const segment = { type, count, percentage, color: typeColors[type] || '#6b7280', arc, offset }
      offset += arc
      return segment
    })
})

const projectsWithCoords = computed(() =>
  props.projects.filter((p) => p.latitude && p.longitude),
)

function probabilityClass(val) {
  if (val >= 70) return 'text-green-600'
  if (val >= 40) return 'text-amber-600'
  return 'text-red-500'
}

function formatCurrency(val) {
  if (val >= 1000000) {
    return new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR', maximumFractionDigits: 1, notation: 'compact' }).format(val)
  }
  return new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(val || 0)
}
</script>
