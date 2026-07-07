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
        <!-- Key facts — inline editable, each change saves immediately -->
        <div class="grid grid-cols-2 gap-x-2 gap-y-3 text-xs">
          <div>
            <div class="mb-1 text-gray-400">{{ __('Phase') }}</div>
            <FormControl
              type="select"
              size="sm"
              :options="PHASE_OPTIONS"
              :modelValue="project.phase"
              @update:modelValue="(v) => save('phase', v)"
            />
          </div>
          <div>
            <div class="mb-1 text-gray-400">{{ __('Status') }}</div>
            <FormControl
              type="select"
              size="sm"
              :options="STATUS_OPTIONS"
              :modelValue="project.status || 'Open'"
              @update:modelValue="(v) => save('status', v)"
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
              :modelValue="project.organization"
              @change="(v) => save('organization', v)"
            />
          </div>
          <div>
            <div class="mb-1 text-gray-400">{{ __('Country') }}</div>
            <Link
              class="text-sm"
              doctype="Country"
              :modelValue="project.country"
              @change="(v) => save('country', v)"
            />
          </div>
          <div>
            <div class="mb-1 text-gray-400">{{ __('Working on it') }}</div>
            <Link
              class="text-sm"
              doctype="User"
              :filters="{ user_type: 'System User', enabled: 1 }"
              :modelValue="project.salesperson"
              @change="(v) => save('salesperson', v)"
            />
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
    </template>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { call, Button, FeatherIcon, FormControl, toast } from 'frappe-ui'
import { watchDebounced } from '@vueuse/core'
import Link from '@/components/Controls/Link.vue'
import QuickContactActions from '@/components/lcs/QuickContactActions.vue'

const props = defineProps({ project: { type: Object, default: null } })
const emit = defineEmits(['open', 'updated'])

const PHASE_OPTIONS = ['Qualified', 'Budget', 'Richtpreis', 'Offer', 'Negotiation', 'Won', 'Execution', 'Completed', 'Lost']
  .map((v) => ({ label: __(v), value: v }))
const STATUS_OPTIONS = ['Open', 'Active', 'On Hold', 'Completed', 'Cancelled']
  .map((v) => ({ label: __(v), value: v }))

const tagList = computed(() => (props.project?.tags || '').split(',').map((s) => s.trim()).filter(Boolean))

// Save a single field immediately; mutate the row so list + inspector stay
// in sync without a full reload, and tell the parent something changed.
async function save(fieldname, value) {
  if (!props.project?.name || props.project[fieldname] === value) return
  try {
    await call('frappe.client.set_value', {
      doctype: 'LCS Project',
      name: props.project.name,
      fieldname,
      value,
    })
    props.project[fieldname] = value
    emit('updated', { name: props.project.name, fieldname, value })
  } catch (e) {
    toast.error(e?.messages?.[0] || __('Could not save'))
  }
}

// Number inputs save debounced — set_value per keystroke would spam the API.
const draft = reactive({ estimated_value: null, probability: null })
watch(
  () => props.project?.name,
  () => {
    draft.estimated_value = props.project?.estimated_value ?? null
    draft.probability = props.project?.probability ?? null
  },
  { immediate: true },
)
watchDebounced(() => draft.estimated_value, (v) => save('estimated_value', Number(v) || 0), { debounce: 800 })
watchDebounced(() => draft.probability, (v) => save('probability', Math.min(100, Math.max(0, Number(v) || 0))), { debounce: 800 })

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
