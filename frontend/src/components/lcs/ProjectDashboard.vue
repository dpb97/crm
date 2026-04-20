<!--
  ProjectDashboard
  ================
  Dashboard widget showing pipeline funnel, type distribution,
  map preview, and key metrics for LCS Projects.
-->

<template>
  <div class="space-y-6">
    <!-- Key metrics row -->
    <div class="grid grid-cols-2 gap-4 sm:grid-cols-4">
      <div class="rounded-lg border bg-white p-4">
        <div class="text-xs font-medium uppercase text-gray-500">{{ __('Total Projects') }}</div>
        <div class="mt-1 text-2xl font-bold text-gray-900">{{ metrics.totalProjects }}</div>
      </div>
      <div class="rounded-lg border bg-white p-4">
        <div class="text-xs font-medium uppercase text-gray-500">{{ __('Pipeline Value') }}</div>
        <div class="mt-1 text-2xl font-bold text-lcs-primary">{{ formatCurrency(metrics.totalValue) }}</div>
      </div>
      <div class="rounded-lg border bg-white p-4">
        <div class="text-xs font-medium uppercase text-gray-500">{{ __('Avg Probability') }}</div>
        <div class="mt-1 text-2xl font-bold text-gray-900">{{ metrics.avgProbability }}%</div>
      </div>
      <div class="rounded-lg border bg-white p-4">
        <div class="text-xs font-medium uppercase text-gray-500">{{ __('Active Phases') }}</div>
        <div class="mt-1 text-2xl font-bold text-lcs-secondary">{{ metrics.activeCount }}</div>
      </div>
    </div>

    <div class="grid grid-cols-1 gap-6 lg:grid-cols-2">
      <!-- Pipeline funnel -->
      <div class="rounded-lg border bg-white p-5">
        <h3 class="mb-4 text-sm font-semibold uppercase text-gray-500">{{ __('Pipeline by Phase') }}</h3>
        <div class="space-y-2">
          <div v-for="phase in phasePipeline" :key="phase.name" class="flex items-center gap-3">
            <span
              :class="phaseClass(phase.name)"
              class="inline-flex w-24 items-center justify-center rounded-full px-2 py-0.5 text-xs font-semibold"
            >
              {{ __(phase.name) }}
            </span>
            <div class="flex-1">
              <div class="relative h-6 overflow-hidden rounded-full bg-gray-100">
                <div
                  class="absolute inset-y-0 left-0 rounded-full transition-all duration-500"
                  :class="phaseBarClass(phase.name)"
                  :style="{ width: `${phase.pct}%` }"
                />
                <div class="absolute inset-0 flex items-center px-3 text-xs font-medium text-gray-700">
                  {{ phase.count }} {{ __('projects') }} &middot; {{ formatCurrency(phase.value) }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Type distribution -->
      <div class="rounded-lg border bg-white p-5">
        <h3 class="mb-4 text-sm font-semibold uppercase text-gray-500">{{ __('Type Distribution') }}</h3>
        <div class="flex items-center justify-center">
          <!-- Simple donut chart with SVG -->
          <svg viewBox="0 0 200 200" class="h-48 w-48">
            <circle cx="100" cy="100" r="80" fill="none" stroke="#e5e7eb" stroke-width="24" />
            <circle
              v-for="(segment, i) in typeSegments"
              :key="segment.type"
              cx="100"
              cy="100"
              r="80"
              fill="none"
              :stroke="segment.color"
              stroke-width="24"
              :stroke-dasharray="`${segment.arc} ${circumference - segment.arc}`"
              :stroke-dashoffset="-segment.offset"
              :style="{ transition: 'stroke-dasharray 0.5s, stroke-dashoffset 0.5s' }"
            />
            <text x="100" y="95" text-anchor="middle" class="fill-gray-900 text-2xl font-bold">
              {{ metrics.totalProjects }}
            </text>
            <text x="100" y="115" text-anchor="middle" class="fill-gray-400 text-xs">
              {{ __('Projects') }}
            </text>
          </svg>
        </div>
        <!-- Legend -->
        <div class="mt-4 flex flex-wrap justify-center gap-4">
          <div v-for="segment in typeSegments" :key="'legend-' + segment.type" class="flex items-center gap-1.5">
            <span class="h-3 w-3 rounded-full" :style="{ backgroundColor: segment.color }" />
            <span class="text-xs text-gray-600">{{ segment.type }} ({{ segment.count }})</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Map preview -->
    <div class="rounded-lg border bg-white p-5">
      <h3 class="mb-4 text-sm font-semibold uppercase text-gray-500">{{ __('Project Locations') }}</h3>
      <ProjectMap :projects="projectsWithCoords" />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import ProjectMap from '@/components/lcs/ProjectMap.vue'

const props = defineProps({
  projects: { type: Array, default: () => [] },
})

const metrics = computed(() => {
  const list = props.projects
  const totalProjects = list.length
  const totalValue = list.reduce((sum, p) => sum + (p.estimated_value || 0), 0)
  const withProb = list.filter((p) => p.probability != null)
  const avgProbability = withProb.length
    ? Math.round(withProb.reduce((sum, p) => sum + p.probability, 0) / withProb.length)
    : 0
  const activePhases = ['Inquiry', 'Offer', 'Negotiation', 'Order', 'Execution']
  const activeCount = list.filter((p) => activePhases.includes(p.phase)).length
  return { totalProjects, totalValue, avgProbability, activeCount }
})

const phaseOrder = ['Inquiry', 'Offer', 'Negotiation', 'Order', 'Execution', 'Completed', 'Lost']

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
      pct: Math.round((value / maxValue) * 100),
    }
  })
})

const typeColors = {
  SB: '#3b82f6',
  WI: '#a855f7',
  LL: '#10b981',
  SK: '#f59e0b',
  Other: '#6b7280',
}

const circumference = 2 * Math.PI * 80

const typeSegments = computed(() => {
  const counts = {}
  props.projects.forEach((p) => {
    const t = p.project_type || 'Other'
    counts[t] = (counts[t] || 0) + 1
  })
  const total = props.projects.length || 1
  let offset = 0
  return Object.keys(counts).map((type) => {
    const count = counts[type]
    const arc = (count / total) * circumference
    const segment = { type, count, color: typeColors[type] || '#6b7280', arc, offset }
    offset += arc
    return segment
  })
})

const projectsWithCoords = computed(() =>
  props.projects.filter((p) => p.latitude && p.longitude),
)

function phaseClass(phase) {
  const map = {
    Inquiry: 'bg-sky-100 text-sky-700',
    Offer: 'bg-amber-100 text-amber-700',
    Negotiation: 'bg-orange-100 text-orange-700',
    Order: 'bg-green-100 text-green-700',
    Execution: 'bg-lcs-primary/10 text-lcs-primary',
    Completed: 'bg-gray-100 text-gray-600',
    Lost: 'bg-red-100 text-red-700',
  }
  return map[phase] || 'bg-gray-100 text-gray-600'
}

function phaseBarClass(phase) {
  const map = {
    Inquiry: 'bg-sky-200',
    Offer: 'bg-amber-200',
    Negotiation: 'bg-orange-200',
    Order: 'bg-green-200',
    Execution: 'bg-lcs-secondary/20',
    Completed: 'bg-gray-200',
    Lost: 'bg-red-200',
  }
  return map[phase] || 'bg-gray-200'
}

function formatCurrency(val) {
  return new Intl.NumberFormat('de-DE', {
    style: 'currency',
    currency: 'EUR',
    maximumFractionDigits: 0,
  }).format(val || 0)
}
</script>
