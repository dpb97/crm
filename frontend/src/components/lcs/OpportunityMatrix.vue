<!--
  OpportunityMatrix — redesigned per Shneiderman & Nielsen heuristics
  ====================================================================
  H1: Visibility — real-time score feedback, color-coded values
  H3: Feedback — value changes instantly reflected in chart + badge
  H5: Error prevention — constrained sliders (0-100), no invalid states
  H6: Recognition — tooltips explain each dimension
  H7: Flexibility — mouse drag OR direct numeric input
  H8: Reduce memory — dimension descriptions visible, no need to recall
  H10: Help — inline explanations for scoring guidance
-->

<template>
  <div class="space-y-6">
    <!-- Header with score + classification — H1: Always visible system status -->
    <div class="flex flex-wrap items-start justify-between gap-4 rounded-xl border bg-gradient-to-r from-white to-gray-50 p-5">
      <div>
        <h3 class="text-lg font-semibold text-gray-900">{{ __('Opportunity Matrix') }}</h3>
        <p class="mt-0.5 text-sm text-gray-500">
          {{ __('Rate each dimension from 0 (weak) to 100 (strong). Use mouse or arrow keys.') }}
        </p>
      </div>
      <div class="flex items-center gap-4">
        <!-- Classification badge — H6: Recognition over recall -->
        <div
          class="flex items-center gap-2 rounded-lg px-4 py-2.5 text-sm font-bold shadow-sm"
          :class="classificationBadgeClass"
        >
          <span class="h-2.5 w-2.5 rounded-full" :class="classificationDotClass" />
          {{ classification }}
        </div>
        <!-- Score display — H1: Prominent status -->
        <div class="text-center">
          <div class="text-3xl font-bold tabular-nums" :style="{ color: scoreColor }">
            {{ Math.round(weightedScore) }}%
          </div>
          <div class="text-[10px] font-medium uppercase tracking-wide text-gray-400">{{ __('Score') }}</div>
        </div>
      </div>
    </div>

    <div class="grid grid-cols-1 gap-8 lg:grid-cols-2">
      <!-- Sliders — H5: Error prevention (constrained range), H8: Reduce memory (descriptions) -->
      <div class="space-y-6">
        <div v-for="criterion in criteria" :key="criterion.field" class="group">
          <div class="mb-1.5 flex items-center justify-between">
            <div class="flex items-center gap-2">
              <label class="text-sm font-medium text-gray-700">{{ __(criterion.label) }}</label>
              <!-- H10: Help — tooltip with scoring guidance -->
              <Tooltip :text="criterion.help" placement="right">
                <FeatherIcon name="help-circle" class="h-3.5 w-3.5 cursor-help text-gray-300 hover:text-gray-500" />
              </Tooltip>
            </div>
            <!-- H3: Feedback — numeric display updates instantly -->
            <div class="flex items-center gap-1.5">
              <span
                class="min-w-[2.5rem] rounded-md border px-2 py-0.5 text-center text-xs font-bold tabular-nums"
                :class="valueBoxClass(criterion.value)"
              >
                {{ criterion.value }}
              </span>
            </div>
          </div>
          <!-- H7: Flexibility — visual slider with clear semantics -->
          <div class="relative">
            <input
              type="range"
              min="0"
              max="100"
              step="5"
              :value="criterion.value"
              class="h-2.5 w-full cursor-pointer appearance-none rounded-full"
              :class="sliderTrackClass(criterion.value)"
              @input="onSliderChange(criterion.field, $event)"
              :aria-label="criterion.label"
              :aria-valuemin="0"
              :aria-valuemax="100"
              :aria-valuenow="criterion.value"
            />
            <!-- H6: Recognition — labeled scale endpoints -->
            <div class="mt-1 flex justify-between text-[10px] text-gray-400">
              <span>{{ __('Weak') }}</span>
              <span>{{ __('Average') }}</span>
              <span>{{ __('Strong') }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Radar chart — H1: Visual representation of current state -->
      <div class="flex flex-col items-center justify-center">
        <svg :viewBox="`0 0 ${svgSize} ${svgSize}`" class="h-64 w-64" role="img" :aria-label="__('Radar chart showing opportunity scores')">
          <!-- Grid rings with subtle labeling -->
          <circle
            v-for="level in gridLevels"
            :key="level.val"
            :cx="center"
            :cy="center"
            :r="radius * level.val"
            fill="none"
            :stroke="level.val === 0.5 ? '#d1d5db' : '#e5e7eb'"
            :stroke-width="level.val === 0.5 ? 1.5 : 1"
            :stroke-dasharray="level.val === 0.5 ? '4 2' : 'none'"
          />
          <!-- Grid value labels -->
          <text
            v-for="level in gridLevels.filter(l => l.showLabel)"
            :key="'val-' + level.val"
            :x="center + 4"
            :y="center - radius * level.val + 4"
            class="fill-gray-400 text-[9px]"
          >
            {{ Math.round(level.val * 100) }}
          </text>
          <!-- Axis lines -->
          <line
            v-for="(_, i) in criteria"
            :key="'axis-' + i"
            :x1="center"
            :y1="center"
            :x2="axisPoint(i, 1).x"
            :y2="axisPoint(i, 1).y"
            stroke="#e5e7eb"
            stroke-width="1"
          />
          <!-- Axis labels — H8: Reduce memory -->
          <text
            v-for="(criterion, i) in criteria"
            :key="'label-' + i"
            :x="labelPoint(i).x"
            :y="labelPoint(i).y"
            text-anchor="middle"
            dominant-baseline="middle"
            class="fill-gray-600 text-[11px] font-medium"
          >
            {{ criterion.short }}
          </text>
          <!-- Data polygon — H3: Visible feedback -->
          <polygon
            :points="polygonPoints"
            fill="rgba(30, 120, 194, 0.12)"
            stroke="#1E78C2"
            stroke-width="2.5"
            stroke-linejoin="round"
          />
          <!-- Data points with value hint -->
          <circle
            v-for="(criterion, i) in criteria"
            :key="'dot-' + i"
            :cx="dataPoint(i).x"
            :cy="dataPoint(i).y"
            r="5"
            fill="#1E78C2"
            stroke="white"
            stroke-width="2.5"
            class="drop-shadow-sm"
          />
        </svg>
        <!-- H6: Recognition — color legend below chart -->
        <div class="mt-3 flex items-center gap-4 text-[10px] text-gray-400">
          <span class="flex items-center gap-1">
            <span class="h-2 w-2 rounded-full bg-red-400" /> {{ __('< 30') }}
          </span>
          <span class="flex items-center gap-1">
            <span class="h-2 w-2 rounded-full bg-amber-400" /> {{ __('30-70') }}
          </span>
          <span class="flex items-center gap-1">
            <span class="h-2 w-2 rounded-full bg-green-400" /> {{ __('> 70') }}
          </span>
        </div>
      </div>
    </div>

    <!-- Activity level recommendation — H2: Match real world (traffic light metaphor) -->
    <div class="rounded-xl border p-4" :class="activityBorderClass">
      <div class="flex items-center justify-between">
        <div>
          <span class="text-xs font-semibold uppercase tracking-wide text-gray-500">{{ __('Recommended Action') }}</span>
          <div class="mt-1 text-sm font-medium" :class="activityTextClass">{{ activityDescription }}</div>
        </div>
        <!-- H1: Visibility — activity level bar -->
        <div class="flex items-center gap-2">
          <div class="flex gap-0.5">
            <div
              v-for="n in 5"
              :key="n"
              class="h-4 w-2 rounded-sm transition-colors"
              :class="n <= activityLevel ? activityBarClass : 'bg-gray-100'"
            />
          </div>
          <span class="ml-1 text-xs font-bold tabular-nums text-gray-600">{{ activityLevel }}/5</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Tooltip, FeatherIcon } from 'frappe-ui'

const props = defineProps({
  technicalFit: { type: Number, default: 0 },
  commercialFit: { type: Number, default: 0 },
  relationship: { type: Number, default: 0 },
  competition: { type: Number, default: 0 },
  strategicImportance: { type: Number, default: 0 },
})

const emit = defineEmits(['update'])

// H10: Help — each criterion has a description to reduce recall load
const criteria = computed(() => [
  { field: 'technical_fit', label: 'Technical Fit', short: 'Tech', value: props.technicalFit, help: __('How well does our solution match the technical requirements? Consider experience with similar terrain, climate, and load capacities.') },
  { field: 'commercial_fit', label: 'Commercial Fit', short: 'Comm', value: props.commercialFit, help: __('Is the budget realistic? Are payment terms acceptable? Consider competition pricing pressure.') },
  { field: 'relationship_strength', label: 'Relationship', short: 'Rel', value: props.relationship, help: __('How strong is our relationship with the decision makers? Do we have a champion inside?') },
  { field: 'competition_level', label: 'Competition', short: 'Comp', value: props.competition, help: __('How do we compare to competitors? 100 = no competition, 0 = heavily contested with price pressure.') },
  { field: 'strategic_importance', label: 'Strategic Value', short: 'Strat', value: props.strategicImportance, help: __('How important is this project for our long-term positioning? Reference projects, market entry, technology showcase.') },
])

// Weighted score calculation (matches backend)
const weights = { technical_fit: 0.25, commercial_fit: 0.25, relationship_strength: 0.20, competition_level: 0.15, strategic_importance: 0.15 }

const weightedScore = computed(() => {
  return criteria.value.reduce((sum, c) => sum + c.value * (weights[c.field] || 0.2), 0)
})

const classification = computed(() => {
  const score = weightedScore.value
  if (score >= 80) return __('Hot — Likely Win')
  if (score >= 60) return __('Warm — Good Chance')
  if (score >= 40) return __('Moderate — Needs Work')
  if (score >= 20) return __('Cold — Uphill Battle')
  return __('Inactive')
})

const classificationBadgeClass = computed(() => {
  const score = weightedScore.value
  if (score >= 80) return 'bg-green-50 text-green-800 border border-green-200'
  if (score >= 60) return 'bg-amber-50 text-amber-800 border border-amber-200'
  if (score >= 40) return 'bg-yellow-50 text-yellow-800 border border-yellow-200'
  if (score >= 20) return 'bg-sky-50 text-sky-800 border border-sky-200'
  return 'bg-gray-50 text-gray-600 border border-gray-200'
})

const classificationDotClass = computed(() => {
  const score = weightedScore.value
  if (score >= 80) return 'bg-green-500'
  if (score >= 60) return 'bg-amber-500'
  if (score >= 40) return 'bg-yellow-500'
  if (score >= 20) return 'bg-sky-500'
  return 'bg-gray-400'
})

// Activity level with descriptive labels
const activityLevel = computed(() => {
  const score = weightedScore.value
  if (score >= 80) return 5
  if (score >= 65) return 4
  if (score >= 45) return 3
  if (score >= 25) return 2
  return 1
})

// H2: Match real world — action descriptions that map to real sales activities
const activityDescription = computed(() => {
  const labels = [
    '',
    __('Monitor — Keep awareness, no active pursuit'),
    __('Maintain — Periodic check-ins, build relationships'),
    __('Engage — Regular contact, work on proposal'),
    __('Pursue — Active selling, frequent meetings'),
    __('Full Push — All resources committed, close the deal'),
  ]
  return labels[activityLevel.value]
})

const activityBarClass = computed(() => {
  if (activityLevel.value >= 4) return 'bg-green-500'
  if (activityLevel.value >= 3) return 'bg-amber-500'
  return 'bg-sky-400'
})

const activityTextClass = computed(() => {
  if (activityLevel.value >= 4) return 'text-green-700'
  if (activityLevel.value >= 3) return 'text-amber-700'
  return 'text-sky-700'
})

const activityBorderClass = computed(() => {
  if (activityLevel.value >= 4) return 'border-green-100 bg-green-50/30'
  if (activityLevel.value >= 3) return 'border-amber-100 bg-amber-50/30'
  return 'border-sky-100 bg-sky-50/30'
})

// Score color: red → amber → green gradient
const scoreColor = computed(() => {
  const pct = weightedScore.value / 100
  if (pct < 0.4) return '#DC2626'
  if (pct < 0.6) return '#D97706'
  if (pct < 0.8) return '#65A30D'
  return '#16A34A'
})

// H1: Visibility — value box color indicates quality
function valueBoxClass(val) {
  if (val >= 70) return 'border-green-200 bg-green-50 text-green-700'
  if (val >= 40) return 'border-amber-200 bg-amber-50 text-amber-700'
  if (val > 0) return 'border-red-200 bg-red-50 text-red-700'
  return 'border-gray-200 bg-gray-50 text-gray-400'
}

function sliderTrackClass(val) {
  if (val >= 70) return 'accent-green-500 bg-green-100'
  if (val >= 40) return 'accent-amber-500 bg-amber-100'
  return 'accent-red-400 bg-red-100'
}

function onSliderChange(field, event) {
  emit('update', { field, value: parseInt(event.target.value) })
}

// Radar chart geometry
const svgSize = 260
const center = svgSize / 2
const radius = 95
const labelOffset = 22
const count = 5

const gridLevels = [
  { val: 0.25, showLabel: false },
  { val: 0.5, showLabel: true },
  { val: 0.75, showLabel: false },
  { val: 1.0, showLabel: true },
]

function angleFor(index) {
  return ((2 * Math.PI) / count) * index - Math.PI / 2
}

function axisPoint(index, scale) {
  const angle = angleFor(index)
  return { x: center + radius * scale * Math.cos(angle), y: center + radius * scale * Math.sin(angle) }
}

function labelPoint(index) {
  const angle = angleFor(index)
  return { x: center + (radius + labelOffset) * Math.cos(angle), y: center + (radius + labelOffset) * Math.sin(angle) }
}

function dataPoint(index) {
  const val = criteria.value[index].value / 100
  return axisPoint(index, val || 0.02) // min visible point
}

const polygonPoints = computed(() =>
  criteria.value.map((_, i) => { const p = dataPoint(i); return `${p.x},${p.y}` }).join(' '),
)
</script>
