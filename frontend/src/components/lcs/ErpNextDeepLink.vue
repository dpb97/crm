<!--
  ErpNextDeepLink — opens a Customer / Quotation / Sales Order record
  in the ERPNext Desk in a new tab.
-->

<template>
  <a
    v-if="url"
    :href="url"
    target="_blank"
    rel="noopener noreferrer"
    class="inline-flex items-center gap-1 rounded-md border border-gray-200 bg-white px-2 py-1 text-xs font-medium text-gray-700 hover:border-lcs-secondary hover:text-lcs-primary"
    :title="__('Open in ERPNext')"
  >
    <FeatherIcon name="external-link" class="h-3 w-3" />
    {{ label || __('Open in ERPNext') }}
  </a>
</template>

<script setup>
import { computed } from 'vue'
import { FeatherIcon } from 'frappe-ui'

const props = defineProps({
  doctype: { type: String, required: true }, // 'Customer' | 'Quotation' | 'Sales Order'
  name: { type: String, required: true },
  label: { type: String, default: '' },
})

const url = computed(() => {
  if (!props.doctype || !props.name) return null
  // ERPNext desk path — url-encode the doctype (handles spaces)
  const dt = encodeURIComponent(props.doctype.toLowerCase().replace(/\s+/g, '-'))
  const n = encodeURIComponent(props.name)
  return `/app/${dt}/${n}`
})
</script>
