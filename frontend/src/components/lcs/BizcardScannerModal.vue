<!--
  BizcardScannerModal — pure iframe wrapper around the standalone
  /bizcard/scan page served by the lcs_bizcard custom app.

  The CRM SPA imports NOTHING from lcs_bizcard. We talk to it only
  through:
    - a URL (`/bizcard/scan?embed=1`)
    - window.postMessage events (see EVENT_TYPES below)

  Emits:
    - 'created' (contact_name)   when a Contact was created/found
    - 'cancelled'                user backed out
-->

<template>
  <Dialog
    v-model="open"
    :options="{
      title: __('Visitenkarte scannen'),
      size: 'lg',
    }"
  >
    <template #body-content>
      <div class="relative" style="height: 75vh; min-height: min(540px, 80vh);">
        <iframe
          ref="iframeEl"
          :src="iframeSrc"
          allow="camera; microphone"
          class="h-full w-full rounded-lg border border-gray-200 bg-white"
          @load="onLoad"
        />
        <div
          v-if="!iframeReady"
          class="absolute inset-0 flex items-center justify-center bg-white/80 backdrop-blur-sm"
        >
          <div class="flex flex-col items-center gap-2">
            <div class="h-6 w-6 animate-spin rounded-full border-2 border-gray-200 border-t-lcs-secondary" />
            <span class="text-xs text-gray-500">{{ __('Scanner loading…') }}</span>
          </div>
        </div>
      </div>

      <div
        v-if="lastError"
        class="mt-3 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-700"
      >
        {{ lastError }}
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { Dialog } from 'frappe-ui'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
})
const emit = defineEmits(['update:modelValue', 'created', 'cancelled'])

// Two-way bound `open` keeps the dialog driven by the parent's v-model.
const open = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v),
})

const iframeEl = ref(null)
const iframeReady = ref(false)
const lastError = ref('')

// Use a per-mount cache-bust so re-opening the modal gives a clean
// scanner state without an explicit reset endpoint.
const iframeKey = ref(Date.now())
watch(open, (isOpen) => {
  if (isOpen) {
    iframeKey.value = Date.now()
    iframeReady.value = false
    lastError.value = ''
  }
})

const iframeSrc = computed(() => `/bizcard/scan?embed=1&t=${iframeKey.value}`)

const EVENT_TYPES = new Set(['ready', 'created', 'cancelled', 'closed', 'errored'])

function onMessage(ev) {
  const data = ev.data
  if (!data || data.source !== 'lcs.bizcard') return
  if (!EVENT_TYPES.has(data.type)) return

  switch (data.type) {
    case 'ready':
      iframeReady.value = true
      break
    case 'created':
      emit('created', data.contact)
      open.value = false
      break
    case 'cancelled':
    case 'closed':
      emit('cancelled')
      open.value = false
      break
    case 'errored':
      lastError.value = data.message || __('Scanner error')
      break
  }
}

function onLoad() {
  // Fallback in case the embedded page forgets to send `ready`.
  setTimeout(() => { if (!iframeReady.value) iframeReady.value = true }, 1500)
}

window.addEventListener('message', onMessage)
onBeforeUnmount(() => window.removeEventListener('message', onMessage))
</script>
