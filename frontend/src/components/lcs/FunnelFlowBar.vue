<!--
  FunnelFlowBar
  =============
  One unified business-process flow across the whole LCS funnel:
  Lead → Qualifiziert → Budget → Richtpreis → Angebot → Verhandlung → Auftrag.
  The same bar is shown on Lead, Angebot (Deal) and Projekt; the current
  position is derived from the record's own status/phase. Stages are grouped
  into labelled entity segments (Interessent | Angebot | Projekt) — the label
  sits ABOVE its stages, the active segment is highlighted. "Verloren" is a
  terminal red node.

  On a Projekt the bar is clickable (advances the project phase, gated);
  on Lead/Deal it is read-only display.
-->

<template>
  <div class="border-b bg-surface-white px-5 py-2">
    <div class="flex items-stretch gap-1.5 overflow-x-auto">
      <template v-for="(g, gi) in GROUPS" :key="g.name">
        <!-- hand-over chevron between entity segments -->
        <div v-if="gi > 0" class="flex items-center self-stretch pt-3">
          <FeatherIcon
            name="chevron-right"
            class="h-4 w-4 shrink-0"
            :class="groupReached(gi) && !isLost ? 'text-lcs-primary' : 'text-gray-300'"
          />
        </div>

        <div
          class="flex min-w-fit flex-col rounded-lg border px-3 pb-1.5 pt-1 transition"
          :class="groupBoxClass(gi)"
          :style="{ flexGrow: g.stages.length, flexBasis: 0 }"
        >
          <!-- entity label above its stages -->
          <div
            class="mb-1 text-[10px] font-bold uppercase tracking-wider"
            :class="groupActive(gi) && !isLost ? 'text-lcs-primary' : 'text-gray-400'"
          >
            {{ __(g.name) }}
          </div>

          <div class="flex w-full items-center" :class="g.stages.length === 1 ? 'justify-center' : ''">
            <template v-for="(s, si) in g.stages" :key="s.label">
              <div
                v-if="si > 0"
                class="mx-1 h-0.5 min-w-[1rem] flex-1 rounded"
                :class="s.idx <= currentIdx && !isLost ? 'bg-lcs-primary' : 'bg-gray-200'"
              />
              <button
                type="button"
                class="group flex shrink-0 items-center gap-1.5 rounded-md px-1 py-0.5 transition hover:bg-gray-50"
                :title="`${__(g.name)}: ${__(s.label)}`"
                @click="openInfo(s.idx)"
              >
                <span
                  class="flex h-6 w-6 shrink-0 items-center justify-center rounded-full border-2 text-[11px] font-bold transition"
                  :class="nodeClass(s.idx)"
                >
                  <FeatherIcon v-if="s.idx < currentIdx && !isLost" name="check" class="h-3 w-3" />
                  <span v-else>{{ s.idx + 1 }}</span>
                </span>
                <span
                  class="whitespace-nowrap text-[13px] leading-none"
                  :class="s.idx === currentIdx && !isLost
                    ? 'font-semibold text-ink-gray-9'
                    : s.idx < currentIdx && !isLost
                      ? 'text-ink-gray-7'
                      : 'text-gray-400'"
                >
                  {{ __(s.label) }}
                </span>
              </button>
            </template>
          </div>
        </div>
      </template>

      <!-- Terminal: Verloren -->
      <template v-if="isLost">
        <div class="flex items-center self-stretch pt-3">
          <FeatherIcon name="chevron-right" class="h-4 w-4 shrink-0 text-red-300" />
        </div>
        <div class="flex min-w-fit flex-col rounded-lg border border-red-200 bg-red-50/60 px-3 pb-1.5 pt-1">
          <div class="mb-1 text-[10px] font-bold uppercase tracking-wider text-red-500">{{ __('Ende') }}</div>
          <div class="flex items-center gap-1.5 px-1 py-0.5">
            <span class="flex h-6 w-6 items-center justify-center rounded-full border-2 border-red-500 bg-red-500 text-white">
              <FeatherIcon name="x" class="h-3 w-3" />
            </span>
            <span class="whitespace-nowrap text-[13px] font-semibold leading-none text-red-600">{{ __('Lost') }}</span>
          </div>
        </div>
      </template>
    </div>
  </div>

  <!-- Phase detail side bar — closes on outside click / Escape so the
       page sidebar underneath stays reachable -->
  <div
    v-if="infoStage"
    ref="panelRef"
    class="fixed right-0 top-0 z-40 flex h-screen w-full flex-col border-l bg-white shadow-2xl sm:w-80"
  >
    <div class="flex items-center justify-between border-b px-4 py-3">
      <span class="lcs-section-label">{{ __('Phase') }}</span>
      <button class="text-gray-400 hover:text-gray-700" @click="infoIdx = null"><FeatherIcon name="x" class="h-4 w-4" /></button>
    </div>
    <div class="flex-1 space-y-4 overflow-y-auto p-4">
      <div>
        <span class="rounded px-1.5 py-0.5 text-[10px] font-bold uppercase" :class="groupClass(infoStage.group)">{{ __(infoStage.group) }}</span>
        <h3 class="mt-2 text-lg font-semibold text-gray-900">{{ __(infoStage.label) }}</h3>
      </div>
      <p class="text-sm leading-relaxed text-gray-600">{{ phaseInfo(infoStage.label).desc }}</p>
      <div v-if="phaseInfo(infoStage.label).criteria?.length">
        <div class="lcs-section-label mb-1">{{ __('Criteria') }}</div>
        <ul class="space-y-1 text-sm text-gray-700">
          <li v-for="c in phaseInfo(infoStage.label).criteria" :key="c" class="flex gap-2"><span class="text-lcs-secondary">•</span>{{ c }}</li>
        </ul>
      </div>

      <!-- Inline filling of the phase's fields on the current record -->
      <div v-if="record && fieldDefs.length" class="space-y-3 rounded-lg border p-3">
        <div class="lcs-section-label">{{ __('Fill directly') }}</div>
        <div v-for="df in fieldDefs" :key="df.fieldname">
          <div class="mb-1 flex items-center gap-1 text-xs text-gray-400">
            {{ __(df.label) }}
            <FeatherIcon v-if="isFilled(df.fieldname)" name="check" class="h-3 w-3 text-green-500" />
          </div>
          <Link
            v-if="df.fieldtype === 'Link'"
            class="text-sm"
            :doctype="df.options"
            :modelValue="record[df.fieldname]"
            @change="(v) => queueSave(df.fieldname, v, true)"
          />
          <FormControl
            v-else-if="df.fieldtype === 'Select'"
            type="select"
            size="sm"
            :options="selectOptions(df.options)"
            :modelValue="record[df.fieldname]"
            @update:modelValue="(v) => queueSave(df.fieldname, v, true)"
          />
          <FormControl
            v-else-if="['Date', 'Datetime'].includes(df.fieldtype)"
            type="date"
            size="sm"
            :modelValue="record[df.fieldname]"
            @update:modelValue="(v) => queueSave(df.fieldname, v, true)"
          />
          <FormControl
            v-else-if="df.fieldtype === 'Check'"
            type="checkbox"
            size="sm"
            :modelValue="record[df.fieldname]"
            @update:modelValue="(v) => queueSave(df.fieldname, v ? 1 : 0, true)"
          />
          <FormControl
            v-else-if="['Int', 'Float', 'Currency', 'Percent'].includes(df.fieldtype)"
            type="number"
            size="sm"
            :modelValue="record[df.fieldname]"
            @update:modelValue="(v) => queueSave(df.fieldname, Number(v) || 0)"
          />
          <FormControl
            v-else
            type="text"
            size="sm"
            :modelValue="record[df.fieldname]"
            @update:modelValue="(v) => queueSave(df.fieldname, v)"
          />
        </div>
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
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { onClickOutside } from '@vueuse/core'
import { FeatherIcon, Button, FormControl, createResource, call, toast } from 'frappe-ui'
import Link from '@/components/Controls/Link.vue'

const props = defineProps({
  entity: { type: String, required: true }, // 'lead' | 'deal' | 'project'
  status: { type: String, default: '' },
  clickable: { type: Boolean, default: false },
  // For inline filling in the phase panel: the page's doctype + its
  // reactive doc object. Optional — without them the panel is read-only.
  doctype: { type: String, default: '' },
  record: { type: Object, default: null },
})
const emit = defineEmits(['change'])

// Editable phase definitions (Settings -> Funnel Phases); falls back to
// the built-in PHASE_INFO until loaded / when a stage has no record yet.
const phasesConfig = createResource({
  url: 'lcs_integrations.projects.api.get_funnel_phases',
  cache: 'lcs-funnel-phases',
  auto: true,
})
function phaseInfo(label) {
  const cfg = phasesConfig.data?.[label]
  if (cfg) return cfg
  return { desc: PHASE_INFO[label]?.desc, criteria: PHASE_INFO[label]?.criteria || [], fields: [] }
}

// Field definitions of the open phase, resolved against the page doctype
const fieldDefs = ref([])
async function loadFieldDefs() {
  fieldDefs.value = []
  if (!props.doctype || !props.record || !infoStage.value) return
  const fields = phaseInfo(infoStage.value.label).fields || []
  if (!fields.length) return
  try {
    fieldDefs.value = await call('lcs_integrations.projects.api.get_phase_field_defs', {
      doctype: props.doctype,
      fieldnames: JSON.stringify(fields),
    })
  } catch (e) {
    fieldDefs.value = []
  }
}

function selectOptions(options) {
  return (options || '').split('\n').filter(Boolean)
}
function isFilled(fieldname) {
  const v = props.record?.[fieldname]
  return v !== null && v !== undefined && v !== '' && v !== 0
}

// Save on change; text/number inputs debounce so we don't spam set_value.
const saveTimers = {}
function queueSave(fieldname, value, immediate = false) {
  clearTimeout(saveTimers[fieldname])
  if (immediate) return saveField(fieldname, value)
  saveTimers[fieldname] = setTimeout(() => saveField(fieldname, value), 700)
}
async function saveField(fieldname, value) {
  if (!props.record?.name || props.record[fieldname] === value) return
  try {
    await call('frappe.client.set_value', {
      doctype: props.doctype,
      name: props.record.name,
      fieldname,
      value,
    })
    props.record[fieldname] = value
  } catch (e) {
    toast.error(e?.messages?.[0] || __('Could not save'))
  }
}

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

// Entity segments with their stages (stage keeps its global funnel index)
const GROUPS = computed(() => {
  const groups = []
  STAGES.forEach((s, i) => {
    let g = groups[groups.length - 1]
    if (!g || g.name !== s.group) {
      g = { name: s.group, stages: [] }
      groups.push(g)
    }
    g.stages.push({ ...s, idx: i })
  })
  return groups
})

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

function groupActive(gi) {
  return GROUPS.value[gi].stages.some((s) => s.idx === currentIdx.value)
}
function groupReached(gi) {
  return currentIdx.value >= GROUPS.value[gi].stages[0].idx
}
function groupBoxClass(gi) {
  if (isLost.value) return 'border-gray-200 bg-gray-50/40'
  if (groupActive(gi)) return 'border-lcs-primary/40 bg-lcs-primary/[0.04] shadow-sm'
  if (groupReached(gi)) return 'border-gray-200 bg-white'
  return 'border-gray-200 bg-gray-50/40'
}

function projectPhaseFor(i) {
  return props.entity === 'project' ? IDX_TO_PHASE[i] : null
}

// Phase detail side bar
const infoIdx = ref(null)
const infoStage = computed(() => (infoIdx.value !== null ? STAGES[infoIdx.value] : null))
function openInfo(i) {
  infoIdx.value = i
}
watch(infoIdx, loadFieldDefs)

// Close on outside click / Escape. Popovers (autocomplete lists) portal
// to <body>, so clicks inside them must not count as "outside".
const panelRef = ref(null)
onClickOutside(panelRef, () => (infoIdx.value = null), {
  ignore: ['.PopoverContent'],
})
function onKeydown(e) {
  if (e.key === 'Escape' && infoIdx.value !== null) infoIdx.value = null
}
onMounted(() => window.addEventListener('keydown', onKeydown))
onUnmounted(() => window.removeEventListener('keydown', onKeydown))
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
