<!--
  OpportunityMatrix
  =================
  A visual scoring matrix with 5 criteria sliders (0-100), a radar/spider
  chart rendered as inline SVG, and a classification badge derived from
  the total score.

  Props: each criterion value (number 0-100).
  Emits: `update` with { field, value } when a slider changes.
-->

<template>
  <div class="space-y-6">
    <!-- Header with total score -->
    <div class="flex items-center justify-between">
      <div>
        <h3 class="text-lg font-semibold text-gray-900">{{ __('Opportunity Matrix') }}</h3>
        <p class="mt-0.5 text-sm text-gray-500">{{ __('Score each dimension 0-100') }}</p>
      </div>
      <div class="flex items-center gap-3">
        <div
          class="flex items-center gap-2 rounded-full px-4 py-2 text-sm font-bold"
          :class="classificationBadgeClass"
        >
          <span class="h-2.5 w-2.5 rounded-full" :class="classificationDotClass" />
          {{ classification }}
        </div>
        <div class="text-right">
          <div class="text-2xl font-bold" :style="{ color: scoreColor }">
            {{ totalScore }}
          </div>
          <div class="text-xs text-gray-400">/ 500</div>
        </div>
      </div>
    </div>

    <div class="grid grid-cols-1 gap-8 lg:grid-cols-2">
      <!-- Sliders -->
      <div class="space-y-5">
        <div v-for="criterion in criteria" :key="criterion.field" class="space-y-1.5">
          <div class="flex items-center justify-between">
            <label class="text-sm font-medium text-gray-700">{{ __(criterion.label) }}</label>
            <span class="min-w-[3ch] text-right text-sm font-semibold tabular-nums" :style="{ color: valueColor(criterion.value) }">
              {{ criterion.value }}
            </span>
          </div>
          <input
            type="range"
            min="0"
            max="100"
            :value="criterion.value"
            class="h-2 w-full cursor-pointer appearance-none rounded-lg bg-gray-200 accent-lcs-secondary"
            @input="onSliderChange(criterion.field, $event)"
          />
          <div class="flex justify-between text-[10px] text-gray-400">
            <span>0</span>
            <span>50</span>
            <span>100</span>
          </div>
        </div>
      </div>

      <!-- Radar chart (SVG) -->
      <div class="flex items-center justify-center">
        <svg :viewBox="`0 0 ${svgSize} ${svgSize}`" class="h-64 w-64">
          <!-- Grid circles -->
          <circle
            v-for="level in [0.2, 0.4, 0.6, 0.8, 1.0]"
            :key="level"
            :cx="center"
            :cy="center"
            :r="radius * level"
            fill="none"
            stroke="#e5e7eb"
            stroke-width="1"
          />
          <!-- Axis lines -->
          <line
            v-for="(_, i) in criteria"
            :key="'axis-' + i"
            :x1="center"
            :y1="center"
            :x2="axisPoint(i, 1).x"
            :y2="axisPoint(i, 1).y"
            stroke="#d1d5db"
            stroke-width="1"
          />
          <!-- Axis labels -->
          <text
            v-for="(criterion, i) in criteria"
            :key="'label-' + i"
            :x="labelPoint(i).x"
            :y="labelPoint(i).y"
            text-anchor="middle"
            dominant-baseline="middle"
            class="fill-gray-500 text-[10px]"
          >
            {{ criterion.short }}
          </text>
          <!-- Data polygon -->
          <polygon
            :points="polygonPoints"
            fill="rgba(30, 120, 194, 0.15)"
            stroke="#1E78C2"
            stroke-width="2"
          />
          <!-- Data points -->
          <circle
            v-for="(criterion, i) in criteria"
            :key="'dot-' + i"
            :cx="dataPoint(i).x"
            :cy="dataPoint(i).y"
            r="4"
            fill="#1E78C2"
            stroke="white"
            stroke-width="2"
          />
        </svg>
      </div>
    </div>

    <!-- Activity level indicator -->
    <div class="flex items-center gap-3 rounded-lg border bg-gray-50 px-4 py-3">
      <span class="text-sm font-medium text-gray-600">{{ __('Recommended Activity Level') }}:</span>
      <div class="flex gap-1">
        <div
          v-for="n in 5"
          :key="n"
          class="h-3 w-6 rounded-sm"
          :class="n <= activityLevel ? activityBarClass : 'bg-gray-200'"
        />
      </div>
      <span class="text-sm font-semibold" :class="activityTextClass">{{ activityLabel }}</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  technicalFit: { type: Number, default: 0 },
  commercialFit: { type: Number, default: 0 },
  relationship: { type: Number, default: 0 },
  competition: { type: Number, default: 0 },
  strategicImportance: { type: Number, default: 0 },
})

const emit = defineEmits(['update'])

const criteria = computed(() => [
  { field: 'technical_fit', label: 'Technical Fit', short: 'Tech', value: props.technicalFit },
  { field: 'commercial_fit', label: 'Commercial Fit', short: 'Comm', value: props.commercialFit },
  { field: 'relationship', label: 'Relationship', short: 'Rel', value: props.relationship },
  { field: 'competition', label: 'Competition', short: 'Comp', value: props.competition },
  { field: 'strategic_importance', label: 'Strategic Importance', short: 'Strat', value: props.strategicImportance },
])

const totalScore = computed(() =>
  criteria.value.reduce((sum, c) => sum + c.value, 0),
)

const avgScore = computed(() => totalScore.value / 5)

const classification = computed(() => {
  if (avgScore.value >= 80) return __('Hot')
  if (avgScore.value >= 60) return __('Warm')
  if (avgScore.value >= 40) return __('Lukewarm')
  if (avgScore.value >= 20) return __('Cold')
  return __('Inactive')
})

const classificationBadgeClass = computed(() => {
  if (avgScore.value >= 80) return 'bg-green-100 text-green-800'
  if (avgScore.value >= 60) return 'bg-amber-100 text-amber-800'
  if (avgScore.value >= 40) return 'bg-yellow-100 text-yellow-800'
  if (avgScore.value >= 20) return 'bg-sky-100 text-sky-800'
  return 'bg-gray-100 text-gray-600'
})

const classificationDotClass = computed(() => {
  if (avgScore.value >= 80) return 'bg-green-500'
  if (avgScore.value >= 60) return 'bg-amber-500'
  if (avgScore.value >= 40) return 'bg-yellow-500'
  if (avgScore.value >= 20) return 'bg-sky-500'
  return 'bg-gray-400'
})

const activityLevel = computed(() => {
  if (avgScore.value >= 80) return 5
  if (avgScore.value >= 60) return 4
  if (avgScore.value >= 40) return 3
  if (avgScore.value >= 20) return 2
  return 1
})

const activityLabel = computed(() => {
  const labels = ['', __('Monitor'), __('Maintain'), __('Engage'), __('Pursue'), __('Full Push')]
  return labels[activityLevel.value]
})

const activityBarClass = computed(() => {
  if (activityLevel.value >= 4) return 'bg-green-500'
  if (activityLevel.value >= 3) return 'bg-amber-500'
  return 'bg-sky-500'
})

const activityTextClass = computed(() => {
  if (activityLevel.value >= 4) return 'text-green-700'
  if (activityLevel.value >= 3) return 'text-amber-700'
  return 'text-sky-700'
})

// Score color: gradient from red (0) through yellow (250) to green (500)
const scoreColor = computed(() => {
  const pct = totalScore.value / 500
  if (pct < 0.5) {
    // Red to yellow
    const r = 220
    const g = Math.round(pct * 2 * 180)
    return `rgb(${r}, ${g}, 30)`
  }
  // Yellow to green
  const r = Math.round((1 - (pct - 0.5) * 2) * 220)
  const g = 160
  return `rgb(${r}, ${g}, 30)`
})

function valueColor(val) {
  if (val >= 70) return '#16A34A'
  if (val >= 40) return '#D97706'
  return '#DC2626'
}

function onSliderChange(field, event) {
  emit('update', { field, value: parseInt(event.target.value) })
}

// Radar chart geometry
const svgSize = 240
const center = svgSize / 2
const radius = 90
const labelOffset = 18
const count = 5

function angleFor(index) {
  // Start at top (-90deg), go clockwise
  return ((2 * Math.PI) / count) * index - Math.PI / 2
}

function axisPoint(index, scale) {
  const angle = angleFor(index)
  return {
    x: center + radius * scale * Math.cos(angle),
    y: center + radius * scale * Math.sin(angle),
  }
}

function labelPoint(index) {
  const angle = angleFor(index)
  return {
    x: center + (radius + labelOffset) * Math.cos(angle),
    y: center + (radius + labelOffset) * Math.sin(angle),
  }
}

function dataPoint(index) {
  const val = criteria.value[index].value / 100
  return axisPoint(index, val)
}

const polygonPoints = computed(() =>
  criteria.value.map((_, i) => {
    const p = dataPoint(i)
    return `${p.x},${p.y}`
  }).join(' '),
)
</script>
