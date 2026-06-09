<!--
  WhatsAppPanel
  =============
  Drop-in for Contact / Lead / Deal pages: shows the WhatsApp message
  history with the same phone number and offers a quick send box.

  Sending requires `LCS WhatsApp Settings.enabled` and a valid token —
  the input collapses to a tooltip if the integration isn't configured,
  so the panel is harmless to render unconditionally.
-->

<template>
  <div class="rounded-xl border bg-white p-4">
    <div class="mb-3 flex items-center justify-between">
      <h3 class="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-gray-400">
        <FeatherIcon name="message-circle" class="h-3.5 w-3.5" />
        {{ __('WhatsApp') }}
        <span v-if="phone" class="rounded-full bg-gray-100 px-1.5 py-0.5 text-[10px] font-mono text-gray-500">
          {{ phone }}
        </span>
      </h3>
      <button
        v-if="phone"
        class="flex items-center gap-1 text-xs text-gray-400 transition hover:text-gray-600 disabled:opacity-50"
        @click="reload"
        :disabled="loading"
        :aria-label="__('Refresh history')"
      >
        <FeatherIcon name="refresh-cw" class="h-3 w-3" :class="loading ? 'animate-spin' : ''" />
        {{ __('Refresh') }}
      </button>
    </div>

    <!-- No phone -->
    <div v-if="!phone" class="rounded-lg border border-dashed border-gray-200 px-3 py-4 text-center text-xs text-gray-500">
      {{ __('No phone number on this contact — add one to enable WhatsApp.') }}
    </div>

    <template v-else>
      <!-- History -->
      <div v-if="loading && !messages.length" class="space-y-2">
        <div v-for="i in 3" :key="i" class="h-10 animate-pulse rounded-md bg-gray-50" />
      </div>

      <div v-else-if="!messages.length" class="rounded-lg border border-dashed border-gray-200 px-3 py-4 text-center text-xs text-gray-500">
        {{ __('No WhatsApp messages yet.') }}
      </div>

      <ul v-else class="max-h-64 space-y-1.5 overflow-y-auto pr-1" data-testid="wa-list">
        <li
          v-for="m in messages"
          :key="m.name"
          class="flex"
          :class="m.direction === 'Outbound' ? 'justify-end' : 'justify-start'"
        >
          <div
            class="max-w-[85%] rounded-lg px-3 py-1.5 text-xs"
            :class="
              m.direction === 'Outbound'
                ? 'bg-lcs-primary/10 text-gray-900'
                : 'bg-gray-50 text-gray-800'
            "
          >
            <div class="whitespace-pre-line break-words leading-snug">{{ m.body }}</div>
            <div class="mt-1 flex items-center justify-between gap-2 text-[10px] text-gray-400">
              <span>{{ formatTimestamp(m.creation) }}</span>
              <span class="uppercase tracking-wider">{{ m.status }}</span>
            </div>
          </div>
        </li>
      </ul>

      <!-- Send box -->
      <form v-if="canSend" class="mt-3 space-y-2" @submit.prevent="send">
        <textarea
          v-model="draft"
          rows="2"
          class="block w-full rounded-md border border-gray-200 px-2.5 py-1.5 text-sm focus:border-lcs-secondary focus:outline-none"
          :placeholder="__('Type a message…')"
          :disabled="sending"
        />
        <div class="flex items-center justify-between gap-2">
          <span v-if="sendError" class="text-[11px] text-red-600">{{ sendError }}</span>
          <span v-else class="text-[10px] text-gray-400">
            {{ __('Free-form replies are only allowed within the 24-hour service window.') }}
          </span>
          <button
            type="submit"
            class="inline-flex items-center gap-1 rounded-md bg-lcs-primary px-3 py-1.5 text-xs font-semibold text-white transition hover:bg-lcs-primary/90 disabled:cursor-not-allowed disabled:opacity-50"
            :disabled="sending || !draft.trim()"
          >
            <FeatherIcon :name="sending ? 'loader' : 'send'" class="h-3 w-3" :class="sending ? 'animate-spin' : ''" />
            {{ sending ? __('Sending...') : __('Send') }}
          </button>
        </div>
      </form>
      <div v-else class="mt-3 rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-[11px] text-amber-700">
        {{ __('Sending is disabled — configure LCS WhatsApp Settings to enable.') }}
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { call, FeatherIcon } from 'frappe-ui'

const props = defineProps({
  contact: { type: String, default: null },
  phone: { type: String, default: null },
})

const messages = ref([])
const loading = ref(false)
const draft = ref('')
const sending = ref(false)
const sendError = ref('')
const settings = ref({ enabled: false })

const canSend = computed(() => settings.value.enabled && !!props.phone)

async function reload() {
  if (!props.phone && !props.contact) return
  loading.value = true
  try {
    const [list, summary] = await Promise.all([
      call('lcs_integrations.whatsapp.api.list_messages', {
        contact: props.contact || undefined,
        phone: props.phone || undefined,
        limit: 50,
      }),
      call('lcs_integrations.whatsapp.api.settings_summary'),
    ])
    messages.value = (list || []).slice().reverse() // chronological
    settings.value = summary || { enabled: false }
  } catch (err) {
    console.warn('WhatsApp history fetch failed:', err)
  } finally {
    loading.value = false
  }
}

async function send() {
  if (!draft.value.trim() || !props.phone) return
  sendError.value = ''
  sending.value = true
  try {
    await call('lcs_integrations.whatsapp.service.send_text', {
      to: props.phone,
      body: draft.value.trim(),
      contact: props.contact || undefined,
    })
    draft.value = ''
    await reload()
  } catch (err) {
    sendError.value = String(err?.message || err)
  } finally {
    sending.value = false
  }
}

function formatTimestamp(raw) {
  if (!raw) return ''
  try {
    return new Date(raw.replace(' ', 'T')).toLocaleString()
  } catch {
    return raw
  }
}

onMounted(reload)
watch(() => [props.contact, props.phone], reload)
</script>
