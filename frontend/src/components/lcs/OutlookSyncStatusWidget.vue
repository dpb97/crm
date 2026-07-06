<!--
  OutlookSyncStatusWidget
  =======================
  Admin-facing dashboard for the bench-wide Outlook sync state. Shows:
    · which sync layers are enabled in LCS Outlook Sync Settings
    · every Outlook Mailbox Binding row + its three last-sync timestamps
    · an inline Resync button per row + a global "Resync all" trigger

  Designed for an LCS Admin / Sales Manager — guarded server-side by the
  whitelisted API method, which inherits the DocType's role permissions.
-->

<template>
  <div class="rounded-xl border bg-white p-4">
    <div class="mb-3 flex items-center justify-between">
      <h3 class="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-gray-400">
        <FeatherIcon name="mail" class="h-3.5 w-3.5" />
        {{ __('Outlook sync') }}
      </h3>
      <button
        class="inline-flex items-center gap-1 rounded-md border border-gray-200 px-2 py-1 text-xs text-gray-700 transition hover:border-lcs-secondary hover:text-lcs-primary disabled:opacity-50"
        @click="resyncAll"
        :disabled="busy"
        :aria-label="__('Resync all bindings')"
      >
        <FeatherIcon name="refresh-cw" class="h-3 w-3" :class="busy ? 'animate-spin' : ''" />
        {{ busy ? __('Resyncing...') : __('Resync all') }}
      </button>
    </div>

    <!-- Layer toggles -->
    <div class="mb-3 grid grid-cols-2 gap-1.5 sm:grid-cols-4">
      <LayerChip :on="state.settings?.contact_push" :label="__('Contact push')" />
      <LayerChip :on="state.settings?.inbound_contacts" :label="__('Contacts pull')" />
      <LayerChip :on="state.settings?.calendar" :label="__('Calendar')" />
      <LayerChip :on="state.settings?.teams" :label="__('Teams')" />
    </div>

    <!-- Bindings -->
    <div v-if="loading && !state.bindings.length" class="space-y-2">
      <div v-for="i in 2" :key="i" class="h-10 animate-pulse rounded-md bg-gray-50" />
    </div>

    <div
      v-else-if="!state.bindings.length"
      class="rounded-lg border border-dashed border-gray-200 px-3 py-4 text-center text-xs text-gray-500"
    >
      {{ __('No mailbox bindings — add one in Outlook Mailbox Binding to start syncing.') }}
    </div>

    <ul v-else class="divide-y divide-gray-50 rounded-lg border border-gray-100" data-testid="binding-list">
      <li
        v-for="b in state.bindings"
        :key="b.name"
        class="flex items-center justify-between px-3 py-2"
      >
        <div class="min-w-0">
          <div class="flex items-center gap-1.5">
            <span
              class="inline-flex h-2 w-2 rounded-full"
              :class="b.last_error ? 'bg-red-500' : b.is_active ? 'bg-green-500' : 'bg-gray-300'"
            />
            <span class="truncate text-xs font-semibold text-gray-900">{{ b.user }}</span>
            <span class="truncate text-[11px] text-gray-400">· {{ b.graph_mailbox }}</span>
          </div>
          <div class="mt-0.5 flex flex-wrap gap-x-3 text-[10px] text-gray-500">
            <span>{{ __('Mail') }}: {{ formatTimestamp(b.last_sync) || '—' }}</span>
            <span>{{ __('Cal') }}: {{ formatTimestamp(b.last_calendar_sync) || '—' }}</span>
            <span>{{ __('Cont') }}: {{ formatTimestamp(b.last_contacts_sync) || '—' }}</span>
          </div>
          <div v-if="b.last_error" class="mt-0.5 max-w-md truncate text-[10px] text-red-600">
            {{ b.last_error }}
          </div>
        </div>
        <button
          class="ml-2 inline-flex items-center gap-1 rounded-md border border-gray-200 px-2 py-1 text-[11px] text-gray-700 transition hover:border-lcs-secondary hover:text-lcs-primary disabled:opacity-50"
          @click="resyncOne(b.name)"
          :disabled="busyBinding === b.name || busy"
        >
          <FeatherIcon
            name="refresh-cw"
            class="h-2.5 w-2.5"
            :class="busyBinding === b.name ? 'animate-spin' : ''"
          />
          {{ __('Resync') }}
        </button>
      </li>
    </ul>
  </div>
</template>

<script setup>
import { ref, h, onMounted } from 'vue'
import { call, FeatherIcon } from 'frappe-ui'

// Lightweight inline component for the on/off layer chips — avoids
// pulling in another file for a 6-line render.
const LayerChip = {
  props: { on: Boolean, label: { type: String, required: true } },
  setup(props) {
    return () =>
      h(
        'div',
        {
          class: [
            'flex items-center gap-1.5 rounded-md border px-2 py-1 text-[11px]',
            props.on
              ? 'border-green-200 bg-green-50 text-green-700'
              : 'border-gray-200 bg-gray-50 text-gray-500',
          ],
        },
        [
          h('span', {
            class: ['inline-block h-1.5 w-1.5 rounded-full', props.on ? 'bg-green-500' : 'bg-gray-300'],
          }),
          props.label,
        ],
      )
  },
}

const loading = ref(false)
const busy = ref(false)
const busyBinding = ref('')
const state = ref({ settings: {}, bindings: [] })

async function reload() {
  loading.value = true
  try {
    state.value = await call('lcs_integrations.outlook_sync.api.get_sync_status')
  } catch (err) {
    console.warn('Outlook status fetch failed:', err)
  } finally {
    loading.value = false
  }
}

async function resyncOne(name) {
  busyBinding.value = name
  try {
    await call('lcs_integrations.outlook_sync.api.trigger_resync', { binding: name })
    await reload()
  } catch (err) {
    console.warn('Resync failed:', err)
  } finally {
    busyBinding.value = ''
  }
}

async function resyncAll() {
  busy.value = true
  try {
    await call('lcs_integrations.outlook_sync.api.trigger_resync')
    await reload()
  } catch (err) {
    console.warn('Resync all failed:', err)
  } finally {
    busy.value = false
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
</script>
