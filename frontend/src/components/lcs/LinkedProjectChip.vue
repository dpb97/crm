<!--
  LinkedProjectChip — tiny badge shown on CRM Deal / CRM Lead detail pages
  that links to the LCS Project record for the current entity.

  Resolves the project via lcs_integrations.projects.api.find_project_for
  so we don't leak the project link graph into the upstream DocType.
  Gracefully shows a "No project linked yet" state when the deal/lead
  predates the CRM rollout.
-->

<template>
  <div v-if="loading" class="inline-flex items-center gap-1 rounded-full bg-gray-50 px-2 py-1 text-xs text-gray-400">
    <div class="h-3 w-3 animate-spin rounded-full border-2 border-gray-200 border-t-gray-400" />
    {{ __('Checking...') }}
  </div>

  <router-link
    v-else-if="project"
    :to="{ name: 'LCS Project', params: { id: project.name } }"
    class="group inline-flex items-center gap-1.5 rounded-full border border-lcs-primary/20 bg-lcs-primary/5 px-2.5 py-1 text-xs font-medium text-lcs-primary transition hover:bg-lcs-primary/10 hover:border-lcs-primary/40"
    :title="__('Open linked LCS Project')"
  >
    <FeatherIcon name="folder-kanban" class="h-3 w-3" />
    <span class="font-semibold">{{ project.project_name }}</span>
    <span class="font-mono text-[10px] text-lcs-primary/60">{{ project.project_number }}</span>
    <span
      v-if="project.phase"
      class="ml-1 rounded-full px-1.5 py-0 text-[9px] font-bold uppercase"
      :class="phaseClass(project.phase)"
    >
      {{ project.phase }}
    </span>
    <FeatherIcon name="arrow-right" class="h-3 w-3 opacity-0 transition group-hover:opacity-100" />
  </router-link>

  <span v-else class="inline-flex items-center gap-1 rounded-full bg-gray-50 px-2 py-1 text-xs text-gray-400">
    <FeatherIcon name="folder" class="h-3 w-3" />
    {{ __('No project linked') }}
  </span>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { FeatherIcon, call } from 'frappe-ui'

const props = defineProps({
  doctype: { type: String, required: true },  // 'CRM Deal' | 'CRM Lead'
  name: { type: String, required: true },
})

const project = ref(null)
const loading = ref(false)

async function load() {
  if (!props.name) return
  loading.value = true
  try {
    const res = await call('lcs_integrations.projects.api.find_project_for', {
      doctype: props.doctype,
      name: props.name,
    })
    project.value = res.message || res || null
  } catch (err) {
    console.warn('find_project_for failed:', err)
    project.value = null
  } finally {
    loading.value = false
  }
}

onMounted(load)
watch(() => props.name, load)

function phaseClass(phase) {
  const m = {
    Inquiry: 'bg-sky-100 text-sky-800',
    Offer: 'bg-amber-100 text-amber-800',
    Negotiation: 'bg-orange-100 text-orange-800',
    Order: 'bg-green-100 text-green-800',
    Execution: 'bg-emerald-100 text-emerald-800',
    Completed: 'bg-gray-100 text-gray-600',
    Lost: 'bg-red-100 text-red-700',
  }
  return m[phase] || 'bg-gray-100 text-gray-600'
}
</script>
