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
        <!-- Key facts -->
        <div class="grid grid-cols-2 gap-2 text-xs">
          <div><div class="text-gray-400">{{ __('Phase') }}</div><div class="font-medium text-gray-800">{{ __(project.phase) }}</div></div>
          <div><div class="text-gray-400">{{ __('Status') }}</div><div class="font-medium text-gray-800">{{ __(project.status) }}</div></div>
          <div><div class="text-gray-400">{{ __('Value') }}</div><div class="font-medium tabular-nums text-gray-800">{{ money(project.estimated_value) }}</div></div>
          <div><div class="text-gray-400">{{ __('Chance') }}</div><div class="font-medium tabular-nums text-gray-800">{{ Math.round(project.probability || 0) }}%</div></div>
          <div><div class="text-gray-400">{{ __('Customer') }}</div><div class="truncate font-medium text-gray-800">{{ project.organization || '—' }}</div></div>
          <div><div class="text-gray-400">{{ __('Country') }}</div><div class="font-medium text-gray-800">{{ project.country || '—' }}</div></div>
          <div class="col-span-2">
            <div class="text-gray-400">{{ __('Working on it') }}</div>
            <div class="font-medium text-gray-800">{{ (project.salesperson || '').split('@')[0] || '—' }}</div>
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
import { ref, computed, watch } from 'vue'
import { call, Button, FeatherIcon } from 'frappe-ui'
import QuickContactActions from '@/components/lcs/QuickContactActions.vue'

const props = defineProps({ project: { type: Object, default: null } })
defineEmits(['open'])

const tagList = computed(() => (props.project?.tags || '').split(',').map((s) => s.trim()).filter(Boolean))

async function toggleImportant() {
  if (!props.project?.name) return
  const v = props.project.is_important ? 0 : 1
  try {
    await call('frappe.client.set_value', { doctype: 'LCS Project', name: props.project.name, fieldname: 'is_important', value: v })
    props.project.is_important = v
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
