<!--
  Drop-in CTA. Place this anywhere a "scan a business card" entry
  point makes sense (Contacts list header, Lead detail, LCS Project
  detail). Renders a button + the modal, hides itself behind a single
  prop when the user lacks the role or the scanner is unreachable.
-->

<template>
  <Button v-if="enabled" @click="open = true" v-bind="$attrs">
    <template #prefix>
      <LucideScanLine class="h-4 w-4" />
    </template>
    {{ label }}
  </Button>
  <BizcardScannerModal
    v-model="open"
    @created="onCreated"
    @cancelled="onCancelled"
  />
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { Button, createResource } from 'frappe-ui'
import LucideScanLine from '~icons/lucide/scan-line'
import BizcardScannerModal from './BizcardScannerModal.vue'

defineOptions({ inheritAttrs: false })

const props = defineProps({
  label: { type: String, default: () => __('Visitenkarte scannen') },
  // When true the button hides itself if the scanner microservice
  // isn't reachable. Defaults to false so an offline scanner shows
  // an error inside the modal instead of pretending the feature
  // doesn't exist.
  hideWhenOffline: { type: Boolean, default: false },
})
const emit = defineEmits(['created', 'cancelled'])

const open = ref(false)
const scannerOk = ref(true)

const health = createResource({
  url: 'lcs_bizcard.api.health',
  auto: false,
})

onMounted(async () => {
  if (!props.hideWhenOffline) return
  try {
    const r = await health.fetch()
    scannerOk.value = !!(r && r.ok)
  } catch {
    scannerOk.value = false
  }
})

const enabled = computed(() => (props.hideWhenOffline ? scannerOk.value : true))

function onCreated(contactName) {
  emit('created', contactName)
}
function onCancelled() {
  emit('cancelled')
}
</script>
