<!--
  FusionManageDeepLink — opens the linked Fusion Manage item in a new tab.

  Resolves the URL via the backend API so the tenant name isn't exposed
  in client code / cached at build time.
-->

<template>
  <button
    v-if="workspace && itemId"
    class="inline-flex items-center gap-1 rounded-md border border-purple-200 bg-purple-50 px-2 py-1 text-xs font-medium text-purple-700 hover:border-purple-400 hover:bg-purple-100 disabled:opacity-50"
    :disabled="loading"
    @click="openLink"
  >
    <FeatherIcon :name="loading ? 'loader' : 'box'" class="h-3 w-3" :class="loading ? 'animate-spin' : ''" />
    {{ label || __('Open in Fusion Manage') }}
  </button>
</template>

<script setup>
import { ref } from 'vue'
import { FeatherIcon, call, toast } from 'frappe-ui'

const props = defineProps({
  workspace: { type: String, default: '' },
  itemId: { type: String, default: '' },
  label: { type: String, default: '' },
})

const loading = ref(false)

async function openLink() {
  loading.value = true
  try {
    const url = await call('lcs_integrations.fusion_manage.service.get_deep_link', {
      workspace: props.workspace,
      item_id: props.itemId,
    })
    if (url) window.open(url, '_blank', 'noopener')
  } catch (err) {
    toast({ title: __('Could not open Fusion Manage'), text: err.message, icon: 'alert-circle', iconClasses: 'text-red-500' })
  } finally {
    loading.value = false
  }
}
</script>
