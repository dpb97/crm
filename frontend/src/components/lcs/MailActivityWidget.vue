<!--
  MailActivityWidget
  ==================
  Recent email Communications for one CRM entity (contact / organization
  / project / raw email). Renders a compact timeline with collapsed
  HTML preview, sender/recipient and direction tag.

  Pair this with the Outlook delta sync — every message that lands in
  Frappe Communication via outlook_sync.delta_service shows up here.

  Click a row to expand the body inline; the FrappeCRM email modal can
  be wired in later if richer reply UX is needed.
-->

<template>
  <div class="rounded-xl border bg-white p-4">
    <div class="mb-3 flex items-center justify-between">
      <h3 class="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-gray-400">
        <FeatherIcon name="mail" class="h-3.5 w-3.5" />
        {{ __('Mail activity') }}
        <span class="rounded-full bg-gray-100 px-1.5 py-0.5 text-[10px] text-gray-500">
          {{ messages.length }}
        </span>
      </h3>
      <button
        class="flex items-center gap-1 text-xs text-gray-400 transition hover:text-gray-600 disabled:opacity-50"
        @click="reload"
        :disabled="loading"
        :aria-label="__('Refresh mail activity')"
      >
        <FeatherIcon name="refresh-cw" class="h-3 w-3" :class="loading ? 'animate-spin' : ''" />
        {{ __('Refresh') }}
      </button>
    </div>

    <!-- No selectors -->
    <div
      v-if="!hasSelector"
      class="rounded-lg border border-dashed border-gray-200 px-3 py-4 text-center text-xs text-gray-500"
    >
      {{ __('Pass a contact, organization, project, or email to load activity.') }}
    </div>

    <!-- Loading -->
    <div v-else-if="loading && !messages.length" class="space-y-2">
      <div v-for="i in 3" :key="i" class="h-12 animate-pulse rounded-md bg-gray-50" />
    </div>

    <!-- Empty -->
    <div
      v-else-if="!messages.length"
      class="rounded-lg border border-dashed border-gray-200 px-3 py-4 text-center text-xs text-gray-500"
    >
      {{ __('No emails on file yet.') }}
    </div>

    <!-- Timeline -->
    <ul v-else class="max-h-96 divide-y divide-gray-50 overflow-y-auto" data-testid="mail-list">
      <li v-for="m in messages" :key="m.name" class="px-2 py-2">
        <button
          type="button"
          class="flex w-full items-start gap-2 text-left"
          @click="toggle(m.name)"
        >
          <span
            class="mt-1 inline-flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-full text-[10px] font-bold"
            :class="
              m.sent_or_received === 'Received'
                ? 'bg-blue-100 text-blue-700'
                : 'bg-lcs-primary/10 text-lcs-primary'
            "
            :title="m.sent_or_received"
          >
            {{ m.sent_or_received === 'Received' ? '↓' : '↑' }}
          </span>
          <div class="min-w-0 flex-1">
            <div class="flex items-baseline justify-between gap-2">
              <span class="truncate text-xs font-semibold text-gray-900">
                {{ m.subject || __('(no subject)') }}
              </span>
              <span class="flex-shrink-0 text-[10px] text-gray-400">
                {{ formatTimestamp(m.communication_date || m.creation) }}
              </span>
            </div>
            <div class="mt-0.5 truncate text-[11px] text-gray-500">
              <template v-if="m.sent_or_received === 'Received'">
                {{ __('From') }}: {{ m.sender }}
              </template>
              <template v-else>
                {{ __('To') }}: {{ m.recipients }}
              </template>
            </div>
          </div>
          <FeatherIcon
            :name="expanded === m.name ? 'chevron-up' : 'chevron-down'"
            class="mt-1 h-3 w-3 text-gray-400"
          />
        </button>

        <div
          v-if="expanded === m.name"
          class="mt-2 ml-7 max-h-56 overflow-y-auto rounded border border-gray-100 bg-gray-50 p-2 text-[12px] text-gray-700"
          v-html="sanitizedBody(m.content)"
        />
      </li>
    </ul>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { call, FeatherIcon } from 'frappe-ui'

const props = defineProps({
  contact: { type: String, default: null },
  organization: { type: String, default: null },
  project: { type: String, default: null },
  email: { type: String, default: null },
  limit: { type: Number, default: 50 },
})

const messages = ref([])
const loading = ref(false)
const expanded = ref('')

const hasSelector = computed(
  () => !!(props.contact || props.organization || props.project || props.email),
)

async function reload() {
  if (!hasSelector.value) return
  loading.value = true
  try {
    messages.value =
      (await call('lcs_integrations.outlook_sync.api.list_communications', {
        contact: props.contact || undefined,
        organization: props.organization || undefined,
        project: props.project || undefined,
        email: props.email || undefined,
        limit: props.limit,
      })) || []
  } catch (err) {
    console.warn('Mail activity fetch failed:', err)
  } finally {
    loading.value = false
  }
}

function toggle(name) {
  expanded.value = expanded.value === name ? '' : name
}

function formatTimestamp(raw) {
  if (!raw) return ''
  try {
    return new Date(raw.replace(' ', 'T')).toLocaleString()
  } catch {
    return raw
  }
}

// Strip <script>/<style> tags + on* attributes — Frappe stores already-
// sanitised HTML in Communication.content, but we belt-and-braces here
// in case third-party editors slip through.
function sanitizedBody(html) {
  if (!html) return ''
  return String(html)
    .replace(/<script[\s\S]*?<\/script>/gi, '')
    .replace(/<style[\s\S]*?<\/style>/gi, '')
    .replace(/\son\w+="[^"]*"/gi, '')
    .replace(/\son\w+='[^']*'/gi, '')
}

onMounted(reload)
watch(
  () => [props.contact, props.organization, props.project, props.email, props.limit],
  reload,
)
</script>
