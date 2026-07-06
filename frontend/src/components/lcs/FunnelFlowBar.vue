<!--
  FunnelFlowBar
  =============
  One unified business-process flow across the whole LCS funnel:
  Lead → Qualifiziert → Budget → Richtpreis → Angebot → Verhandlung → Auftrag.
  The same bar is shown on Lead, Angebot (Deal) and Projekt; the current
  position is derived from the record's own status/phase and grouped by
  entity (Lead | Angebot | Projekt). The hand-over to the next entity only
  happens at the group boundary. "Verloren" is a terminal red node.

  On a Projekt the bar is clickable (advances the project phase, gated);
  on Lead/Deal it is read-only display.
-->

<template>
  <div class="border-b bg-surface-white px-5 py-2">
    <div class="flex items-start gap-0 overflow-x-auto">
      <template v-for="(s, i) in STAGES" :key="s.label">
        <!-- connector line — uniform spacing, runs through the circle center;
             a subtle divider marks the entity-group boundary -->
        <div v-if="i > 0" class="flex h-6 min-w-[1.5rem] flex-1 items-center">
          <div
            class="h-0.5 w-full"
            :class="[
              i <= currentIdx && !isLost ? 'bg-lcs-primary' : 'bg-gray-200',
              s.group !== STAGES[i - 1].group ? 'border-l-2 border-dotted border-gray-300' : '',
            ]"
          />
        </div>

        <component
          :is="'button'"
          type="button"
          class="flex shrink-0 flex-col items-center gap-0.5 px-1"
          :title="`${s.group}: ${s.label}`"
          @click="openInfo(i)"
        >
          <span
            class="flex h-6 w-6 items-center justify-center rounded-full border-2 text-[10px] font-bold transition"
            :class="nodeClass(i)"
          >
            <FeatherIcon v-if="i < currentIdx && !isLost" name="check" class="h-3 w-3" />
            <span v-else>{{ i + 1 }}</span>
          </span>
          <span class="whitespace-nowrap text-[10px]" :class="i === currentIdx && !isLost ? 'font-semibold text-ink-gray-9' : 'text-gray-400'">
            {{ __(s.label) }}
          </span>
        </component>
      </template>

      <!-- Terminal: Verloren -->
      <template v-if="isLost">
        <div class="flex h-6 min-w-[1rem] flex-1 items-center"><div class="h-0.5 w-full bg-red-300" /></div>
        <div class="flex shrink-0 flex-col items-center gap-0.5 px-1">
          <span class="flex h-6 w-6 items-center justify-center rounded-full border-2 border-red-500 bg-red-500 text-white">
            <FeatherIcon name="x" class="h-3 w-3" />
          </span>
          <span class="whitespace-nowrap text-[10px] font-semibold text-red-600">{{ __('Lost') }}</span>
        </div>
      </template>
    </div>

    <!-- entity group legend -->
    <div class="mt-1 flex items-center gap-3 text-[9px] uppercase tracking-wider text-gray-400">
      <span :class="entity === 'lead' ? 'font-bold text-lcs-primary' : ''">{{ __('Lead') }}</span>
      <span>›</span>
      <span :class="entity === 'deal' ? 'font-bold text-lcs-primary' : ''">{{ __('Angebot') }}</span>
      <span>›</span>
      <span :class="entity === 'project' ? 'font-bold text-lcs-primary' : ''">{{ __('Projekt') }}</span>
    </div>
  </div>

  <!-- Phase detail side bar -->
  <div v-if="infoStage" class="fixed right-0 top-0 z-40 flex h-screen w-80 flex-col border-l bg-white shadow-2xl">
    <div class="flex items-center justify-between border-b px-4 py-3">
      <span class="lcs-section-label">{{ __('Phase') }}</span>
      <button class="text-gray-400 hover:text-gray-700" @click="infoIdx = null"><FeatherIcon name="x" class="h-4 w-4" /></button>
    </div>
    <div class="flex-1 space-y-4 overflow-y-auto p-4">
      <div>
        <span class="rounded px-1.5 py-0.5 text-[10px] font-bold uppercase" :class="groupClass(infoStage.group)">{{ __(infoStage.group) }}</span>
        <h3 class="mt-2 text-lg font-semibold text-gray-900">{{ __(infoStage.label) }}</h3>
      </div>
      <p class="text-sm leading-relaxed text-gray-600">{{ PHASE_INFO[infoStage.label]?.desc }}</p>
      <div v-if="PHASE_INFO[infoStage.label]?.criteria">
        <div class="lcs-section-label mb-1">{{ __('Criteria') }}</div>
        <ul class="space-y-1 text-sm text-gray-700">
          <li v-for="c in PHASE_INFO[infoStage.label].criteria" :key="c" class="flex gap-2"><span class="text-lcs-secondary">•</span>{{ c }}</li>
        </ul>
      </div>
      <Button
        v-if="clickable && projectPhaseFor(infoIdx) && infoIdx !== currentIdx && !isLost"
        variant="solid"
        iconLeft="arrow-right"
        :label="__('Move to this phase')"
        @click="onAdvance(infoIdx)"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { FeatherIcon, Button } from 'frappe-ui'

const props = defineProps({
  entity: { type: String, required: true }, // 'lead' | 'deal' | 'project'
  status: { type: String, default: '' },
  clickable: { type: Boolean, default: false },
})
const emit = defineEmits(['change'])

const STAGES = [
  { label: 'Neu', group: 'Lead' },
  { label: 'Kontaktiert', group: 'Lead' },
  { label: 'Qualifiziert', group: 'Lead' },
  { label: 'Budget', group: 'Angebot' },
  { label: 'Richtpreis', group: 'Angebot' },
  { label: 'Angebot', group: 'Angebot' },
  { label: 'Verhandlung', group: 'Angebot' },
  { label: 'Auftrag', group: 'Projekt' },
]

const LEAD_MAP = { New: 0, Contacted: 1, Nurture: 1, Qualified: 2, Converted: 3 }
const PROJECT_MAP = { Qualified: 2, Budget: 3, Richtpreis: 4, Offer: 5, Negotiation: 6, Won: 7, Execution: 7, Completed: 7 }
const LOST = ['Lost', 'Unqualified', 'Junk', 'Closed Lost']
// funnel index -> project phase (for click-to-advance on a project)
const IDX_TO_PHASE = { 2: 'Qualified', 3: 'Budget', 4: 'Richtpreis', 5: 'Offer', 6: 'Negotiation', 7: 'Won' }

function dealIdx(status) {
  const s = (status || '').toLowerCase()
  if (s.includes('won') || s.includes('order') || s.includes('auftrag')) return 7
  if (s.includes('negoti') || s.includes('verhandl') || s.includes('ready')) return 6
  if (s.includes('proposal') || s.includes('quot') || s.includes('angebot')) return 5
  if (s.includes('demo') || s.includes('making') || s.includes('richt')) return 4
  if (s.includes('qualif') || s.includes('budget')) return 3
  return 3
}

const isLost = computed(() => LOST.includes(props.status))
const currentIdx = computed(() => {
  if (isLost.value) return STAGES.length
  if (props.entity === 'lead') return LEAD_MAP[props.status] ?? 0
  if (props.entity === 'project') return PROJECT_MAP[props.status] ?? 2
  return dealIdx(props.status)
})

function projectPhaseFor(i) {
  return props.entity === 'project' ? IDX_TO_PHASE[i] : null
}

// Phase detail side bar
const infoIdx = ref(null)
const infoStage = computed(() => (infoIdx.value !== null ? STAGES[infoIdx.value] : null))
function openInfo(i) {
  infoIdx.value = i
}
function onAdvance(i) {
  const phase = projectPhaseFor(i)
  if (phase) emit('change', phase)
  infoIdx.value = null
}
function groupClass(g) {
  return { Lead: 'bg-amber-50 text-amber-700', Angebot: 'bg-blue-50 text-blue-700', Projekt: 'bg-green-50 text-green-700' }[g] || 'bg-gray-100 text-gray-600'
}
const PHASE_INFO = {
  Neu: { desc: 'Neuer Interessent — noch nicht kontaktiert. Quelle erfassen und Verantwortlichen zuordnen.', criteria: ['Quelle hinterlegt', 'Verantwortlicher gesetzt'] },
  Kontaktiert: { desc: 'Erstkontakt erfolgt. Ansprechpartner und Bedarf klären.', criteria: ['Ansprechpartner bekannt', 'Bedarf grob erfasst'] },
  Qualifiziert: { desc: 'Bedarf und Budgetrahmen bestätigt — Übergang ins Angebot.', criteria: ['Budgetrahmen bekannt', 'Zeitrahmen geklärt', 'Entscheidungsebene identifiziert'] },
  Budget: { desc: 'Budgetschätzung erstellt — grobe Hausnummer für den Kunden.', criteria: ['Budgetschätzung dokumentiert'] },
  Richtpreis: { desc: 'Interner Richtpreis kalkuliert.', criteria: ['Richtpreis hinterlegt'] },
  Angebot: { desc: 'Verbindliches Angebot gelegt — Status und Gültigkeitsdatum gesetzt.', criteria: ['Angebot erstellt', 'Gültig-bis gesetzt', 'Dokumente angehängt'] },
  Verhandlung: { desc: 'Angebot in Verhandlung — Konditionen und Liefertermin final klären.', criteria: ['Verhandlungspunkte erfasst'] },
  Auftrag: { desc: 'Gewonnen — wird zum laufenden Projekt (Ausführung in ERPNext).', criteria: ['Angebot akzeptiert', 'Projekt angelegt'] },
}
function nodeClass(i) {
  if (isLost.value) return 'border-gray-300 bg-white text-gray-400'
  if (i < currentIdx.value) return 'border-lcs-primary bg-lcs-primary text-white'
  if (i === currentIdx.value) return 'border-lcs-primary bg-white text-lcs-primary ring-2 ring-lcs-primary/30'
  return 'border-gray-300 bg-white text-gray-400'
}
</script>
