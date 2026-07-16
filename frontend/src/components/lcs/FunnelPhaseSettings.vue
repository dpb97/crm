<!--
  FunnelPhaseSettings
  ===================
  Settings page (managers only) to maintain the funnel phase definitions
  shown in the FunnelFlowBar: description, criteria and the fields offered
  for inline filling in the phase panel. Stored in the LCS Funnel Phase
  doctype; the bar picks changes up on its next load (server cache is
  invalidated on save).
-->

<template>
  <div class="flex h-full flex-col gap-4 overflow-y-auto p-8">
    <div>
      <h2 class="text-lg font-semibold text-ink-gray-9">{{ __('Funnel Phases') }}</h2>
      <p class="mt-1 text-sm text-ink-gray-6">
        {{ __('Description, criteria and fillable fields per funnel stage. One criterion / fieldname per line.') }}
      </p>
    </div>

    <div v-if="phases.loading" class="text-sm text-gray-400">{{ __('Loading...') }}</div>

    <div v-for="p in phases.data || []" :key="p.name" class="rounded-lg border p-4">
      <div class="mb-3 flex items-center gap-2">
        <span class="flex h-6 w-6 items-center justify-center rounded-full border-2 border-lcs-primary bg-white text-[11px] font-bold text-lcs-primary">
          {{ p.funnel_index + 1 }}
        </span>
        <h3 class="text-sm font-semibold text-ink-gray-9">{{ __(p.stage) }}</h3>
        <span class="rounded bg-gray-100 px-1.5 py-0.5 text-[10px] font-bold uppercase text-gray-500">{{ __(p.entity_group) }}</span>
        <span v-if="savedAt[p.name]" class="ml-auto flex items-center gap-1 text-xs text-green-600">
          <FeatherIcon name="check" class="h-3 w-3" /> {{ __('Saved') }}
        </span>
      </div>

      <div class="grid gap-3 md:grid-cols-3">
        <div>
          <div class="mb-1 text-xs text-gray-400">{{ __('Description') }}</div>
          <FormControl type="textarea" :rows="4" v-model="p.description" @update:modelValue="markDirty(p)" />
        </div>
        <div>
          <div class="mb-1 text-xs text-gray-400">{{ __('Criteria') }} — {{ __('one per line') }}</div>
          <FormControl type="textarea" :rows="4" v-model="p.criteria" @update:modelValue="markDirty(p)" />
        </div>
        <div>
          <div class="mb-1 text-xs text-gray-400">{{ __('Fields to fill') }} — {{ __('one fieldname per line') }}</div>
          <FormControl type="textarea" :rows="4" v-model="p.fields_to_fill" @update:modelValue="markDirty(p)" />
        </div>
      </div>

      <div class="mt-3 flex justify-end">
        <Button
          variant="solid"
          size="sm"
          :label="__('Save')"
          :disabled="!dirty[p.name]"
          :loading="saving[p.name]"
          @click="save(p)"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive } from 'vue'
import { createResource, call, Button, FormControl, FeatherIcon, toast } from 'frappe-ui'

const dirty = reactive({})
const saving = reactive({})
const savedAt = reactive({})

const phases = createResource({
  url: 'frappe.client.get_list',
  params: {
    doctype: 'LCS Funnel Phase',
    fields: ['name', 'stage', 'entity_group', 'funnel_index', 'description', 'criteria', 'fields_to_fill'],
    order_by: 'funnel_index asc',
    limit_page_length: 0,
  },
  auto: true,
})

function markDirty(p) {
  dirty[p.name] = true
  savedAt[p.name] = false
}

async function save(p) {
  saving[p.name] = true
  try {
    await call('frappe.client.set_value', {
      doctype: 'LCS Funnel Phase',
      name: p.name,
      fieldname: {
        description: p.description || '',
        criteria: p.criteria || '',
        fields_to_fill: p.fields_to_fill || '',
      },
    })
    dirty[p.name] = false
    savedAt[p.name] = true
  } catch (e) {
    toast.error(e?.messages?.[0] || __('Could not save'))
  } finally {
    saving[p.name] = false
  }
}
</script>
