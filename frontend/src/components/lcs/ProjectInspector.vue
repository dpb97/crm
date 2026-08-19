<!--
  ProjectInspector
  ================
  Right-hand inspector: shows details of the item selected in the list on
  the left, plus quick communication actions (call / mail / WhatsApp /
  Teams) on the project's primary contact. Read-only summary + "Open".
-->

<template>
  <div class="flex h-full w-full flex-col">
    <div v-if="!project" class="flex h-full flex-col items-center justify-center px-6 text-center text-sm text-gray-400">
      <FeatherIcon name="mouse-pointer" class="h-7 w-7 text-gray-300" />
      <p class="mt-3">{{ __('Select a project to see details') }}</p>
    </div>

    <template v-else>
      <!-- Header -->
      <div class="flex items-start justify-between gap-2 border-b px-4 py-3">
        <div class="min-w-0">
          <div class="flex items-center gap-1.5">
            <button type="button" :title="__('Mark important')" @click="toggleImportant">
              <FeatherIcon name="star" class="h-4 w-4 transition" :class="project.is_important ? 'text-amber-400' : 'text-gray-300 hover:text-amber-300'" />
            </button>
            <h3 class="truncate text-sm font-semibold text-gray-900">{{ project.project_name }}</h3>
          </div>
          <p class="font-mono text-xs text-gray-400">{{ project.project_number }}</p>
        </div>
        <Button size="sm" variant="solid" iconLeft="external-link" :label="__('Open')" @click="$emit('open', project)" />
      </div>

      <div class="flex-1 space-y-4 overflow-y-auto p-4">
        <!-- Key facts — edits collect in a draft, the footer saves them -->
        <div class="grid grid-cols-2 gap-x-2 gap-y-3 text-xs">
          <div>
            <div class="mb-1 text-gray-400">{{ __('Phase') }}</div>
            <FormControl
              type="select"
              size="sm"
              :options="PHASE_OPTIONS"
              v-model="draft.phase"
            />
          </div>
          <div>
            <div class="mb-1 text-gray-400">{{ __('Status') }}</div>
            <FormControl
              type="select"
              size="sm"
              :options="STATUS_OPTIONS"
              v-model="draft.status"
            />
          </div>
          <div>
            <div class="mb-1 text-gray-400">{{ __('Value') }} (€)</div>
            <FormControl type="number" size="sm" v-model="draft.estimated_value" />
          </div>
          <div>
            <div class="mb-1 text-gray-400">{{ __('Chance') }} (%)</div>
            <FormControl type="number" size="sm" :min="0" :max="100" v-model="draft.probability" />
          </div>
          <div class="col-span-2">
            <div class="mb-1 text-gray-400">{{ __('Customer') }}</div>
            <Link
              class="text-sm"
              doctype="CRM Organization"
              :modelValue="draft.organization"
              @update:modelValue="(v) => (draft.organization = v)"
            />
          </div>
          <div>
            <div class="mb-1 text-gray-400">{{ __('Country') }}</div>
            <Link
              class="text-sm"
              doctype="Country"
              :modelValue="draft.country"
              @update:modelValue="(v) => (draft.country = v)"
            />
          </div>
          <div>
            <div class="mb-1 text-gray-400">{{ __('Working on it') }}</div>
            <Link
              class="text-sm"
              doctype="User"
              :filters="{ user_type: 'System User', enabled: 1 }"
              :modelValue="draft.salesperson"
              @update:modelValue="(v) => (draft.salesperson = v)"
            />
          </div>
        </div>

        <!-- Opportunity-Matrix: Radar + Schätz-Schieber (einfach hinschätzen) -->
        <div class="rounded-lg border p-3">
          <div class="mb-2 text-[10px] font-bold uppercase tracking-wider text-gray-400">{{ __('Opportunity matrix') }}</div>
          <LcsRadar :axes="MATRIX_AXES" :model-value="matrixModel" />
          <div class="mt-2 flex flex-col gap-2">
            <label v-for="a in MATRIX_AXES" :key="a.key" class="flex flex-col gap-0.5">
              <span class="flex items-baseline justify-between text-[11px] text-gray-500">
                {{ a.label }}<b class="font-semibold tabular-nums text-lcs-secondary">{{ draft[a.key] || 0 }}</b>
              </span>
              <input type="range" min="0" max="100" step="5" v-model.number="draft[a.key]" class="w-full" style="accent-color: var(--pp-brand-primary)" />
            </label>
          </div>
        </div>

        <!-- Primary contact + comms -->
        <div class="rounded-lg border p-3">
          <div class="mb-2 text-[10px] font-bold uppercase tracking-wider text-gray-400">{{ __('Primary contact') }}</div>
          <div v-if="contact.loading" class="text-xs text-gray-400">{{ __('Loading...') }}</div>
          <template v-else-if="contact.data">
            <div class="text-sm font-medium text-gray-900">{{ contact.data.full_name }}</div>
            <div class="text-xs text-gray-400">{{ contact.data.email_id || '—' }} · {{ contact.data.mobile_no || '—' }}</div>
            <QuickContactActions class="mt-3" :email="contact.data.email_id" :phone="contact.data.mobile_no" />
          </template>
          <div v-else class="text-xs text-gray-400">{{ __('No contact linked.') }}</div>
        </div>

        <!-- Tags -->
        <div v-if="tagList.length" class="flex flex-wrap gap-1">
          <span v-for="t in tagList" :key="t" class="rounded bg-lcs-secondary/10 px-1.5 py-0.5 text-[11px] text-lcs-secondary">{{ t }}</span>
        </div>
      </div>

      <!-- Footer: save collected edits / advance the funnel phase -->
      <div class="flex items-center gap-2 border-t px-4 py-3">
        <Button
          class="flex-1"
          variant="solid"
          size="sm"
          iconLeft="save"
          :label="__('Save')"
          :disabled="!isDirty"
          :loading="saving"
          @click="saveAll()"
        />
        <Button
          class="flex-1"
          variant="subtle"
          size="sm"
          iconRight="arrow-right"
          :label="__('Next phase')"
          :disabled="!nextPhase || saving"
          :title="nextPhase ? __(draft.phase) + ' → ' + __(nextPhase) : ''"
          @click="advancePhase()"
        />
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { call, Button, FeatherIcon, FormControl, toast } from 'frappe-ui'
import Link from '@/components/Controls/Link.vue'
import QuickContactActions from '@/components/lcs/QuickContactActions.vue'
import LcsRadar from '@/components/lcs/LcsRadar.vue'

// Opportunity-Matrix (Radar): 5 Dimensionen 0–100, am Projekt schätzbar.
const MATRIX_AXES = [
  { key: 'technical_fit', label: __('Technical fit') },
  { key: 'commercial_fit', label: __('Commercial fit') },
  { key: 'relationship_strength', label: __('Relationship') },
  { key: 'competition_level', label: __('Competition') },
  { key: 'strategic_importance', label: __('Strategic value') },
]
const MATRIX_KEYS = MATRIX_AXES.map((a) => a.key)

const props = defineProps({ project: { type: Object, default: null } })
const emit = defineEmits(['open', 'updated'])

const PHASES = ['Qualified', 'Budget', 'Richtpreis', 'Offer', 'Negotiation', 'Won', 'Execution', 'Completed']
const PHASE_OPTIONS = [...PHASES, 'Lost'].map((v) => ({ label: __(v), value: v }))
const STATUS_OPTIONS = ['Open', 'Active', 'On Hold', 'Completed', 'Cancelled']
  .map((v) => ({ label: __(v), value: v }))

const tagList = computed(() => (props.project?.tags || '').split(',').map((s) => s.trim()).filter(Boolean))

// Edits collect in a local draft; the footer Save button writes all
// changed fields in one set_value call.
const FIELDS = ['phase', 'status', 'estimated_value', 'probability', 'organization', 'country', 'salesperson', ...MATRIX_KEYS]
const draft = reactive({})
const matrixModel = computed(() => Object.fromEntries(MATRIX_KEYS.map((k) => [k, Number(draft[k]) || 0])))
const saving = ref(false)

watch(
  () => props.project?.name,
  () => {
    for (const f of FIELDS) draft[f] = props.project?.[f] ?? null
    if (!draft.status) draft.status = 'Open'
  },
  { immediate: true },
)

function normalized(f) {
  if (f === 'estimated_value') return Number(draft[f]) || 0
  if (f === 'probability' || MATRIX_KEYS.includes(f)) return Math.min(100, Math.max(0, Number(draft[f]) || 0))
  return draft[f]
}
const changedFields = computed(() => {
  if (!props.project) return {}
  const out = {}
  for (const f of FIELDS) {
    const v = normalized(f)
    if (v !== (props.project[f] ?? (f === 'status' ? 'Open' : null))) out[f] = v
  }
  return out
})
const isDirty = computed(() => Object.keys(changedFields.value).length > 0)

// Next stage in the funnel order (Lost is a terminal, never suggested)
const nextPhase = computed(() => {
  const i = PHASES.indexOf(draft.phase)
  return i >= 0 && i < PHASES.length - 1 ? PHASES[i + 1] : null
})

async function saveAll(extra = {}) {
  if (!props.project?.name) return
  const fields = { ...changedFields.value, ...extra }
  if (!Object.keys(fields).length) return
  // Optimistic: list row + inspector reflect the edit immediately;
  // reverted if the server rejects it.
  const prev = {}
  for (const [f, v] of Object.entries(fields)) {
    prev[f] = props.project[f]
    props.project[f] = v
    draft[f] = v
  }
  saving.value = true
  try {
    await call('frappe.client.set_value', {
      doctype: 'LCS Project',
      name: props.project.name,
      fieldname: fields,
    })
    emit('updated', { name: props.project.name, fields })
    toast.success(__('Saved'))
  } catch (e) {
    for (const [f, v] of Object.entries(prev)) {
      props.project[f] = v
      draft[f] = v
    }
    toast.error(e?.messages?.[0] || __('Could not save'))
  } finally {
    saving.value = false
  }
}

async function advancePhase() {
  if (!nextPhase.value) return
  draft.phase = nextPhase.value
  await saveAll({ phase: nextPhase.value })
}

async function toggleImportant() {
  if (!props.project?.name) return
  const v = props.project.is_important ? 0 : 1
  try {
    await call('frappe.client.set_value', { doctype: 'LCS Project', name: props.project.name, fieldname: 'is_important', value: v })
    props.project.is_important = v
    emit('updated', { name: props.project.name, fieldname: 'is_important', value: v })
  } catch (e) {
    /* ignore */
  }
}

// Primary contact of the selected project (first / primary linked contact).
const contact = ref({ loading: false, data: null })
async function loadContact() {
  if (!props.project?.name) {
    contact.value = { loading: false, data: null }
    return
  }
  contact.value = { loading: true, data: null }
  try {
    const data = await call('lcs_integrations.projects.api.get_project_primary_contact', {
      project: props.project.name,
    })
    contact.value = { loading: false, data: data || null }
  } catch (e) {
    contact.value = { loading: false, data: null }
  }
}
watch(() => props.project?.name, loadContact, { immediate: true })

function money(v) {
  const n = Number(v) || 0
  if (n >= 1_000_000) return '€' + (n / 1_000_000).toFixed(1) + 'M'
  if (n >= 1_000) return '€' + Math.round(n / 1_000) + 'k'
  return '€' + n
}
</script>
