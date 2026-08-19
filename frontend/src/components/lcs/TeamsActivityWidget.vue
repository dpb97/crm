<!--
  TeamsActivityWidget
  ===================
  Surfaces the Microsoft Teams team for one LCS Project: link to the team,
  the channel that receives notifications, and a live list of channels
  pulled from Graph so the user can deep-link into any of them.

  Empty / error states fall back gracefully — Graph hiccups must never
  break the page, the widget just collapses to a "not provisioned" CTA.
-->

<template>
  <div class="rounded-xl border bg-white p-4">
    <div class="mb-3 flex items-center justify-between">
      <h3 class="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-gray-400">
        <FeatherIcon name="message-square" class="h-3.5 w-3.5" />
        {{ __('Microsoft Teams') }}
      </h3>
      <button
        v-if="info.team_id"
        class="flex items-center gap-1 text-xs text-gray-400 transition hover:text-gray-600 disabled:opacity-50"
        @click="refresh"
        :disabled="loading"
        :aria-label="__('Refresh Teams info')"
      >
        <FeatherIcon name="refresh-cw" class="h-3 w-3" :class="loading ? 'animate-spin' : ''" />
        {{ loading ? __('Refreshing...') : __('Refresh') }}
      </button>
    </div>

    <!-- Loading skeleton -->
    <div v-if="loading && !info.team_id" class="space-y-2">
      <div class="h-12 animate-pulse rounded-lg bg-gray-50" />
      <div class="h-8 animate-pulse rounded-lg bg-gray-50" />
    </div>

    <!-- Not provisioned -->
    <div
      v-else-if="!info.team_id"
      class="flex flex-col items-center rounded-lg border border-dashed border-gray-200 py-6"
    >
      <FeatherIcon name="message-square" class="h-7 w-7 text-gray-300" />
      <p class="mt-2 text-sm font-medium text-gray-700">
        {{ __('No Teams workspace yet') }}
      </p>
      <p class="mt-0.5 max-w-xs text-center text-xs text-gray-500">
        {{ __('Provision a project Team to get a structured workspace with channels and a notifications hub.') }}
      </p>
    </div>

    <!-- Provisioned -->
    <div v-else class="space-y-3">
      <!-- Team link -->
      <a
        :href="info.team_link"
        target="_blank"
        rel="noopener"
        class="flex items-center justify-between rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 transition hover:border-lcs-secondary"
      >
        <div class="flex items-center gap-2">
          <FeatherIcon name="external-link" class="h-3.5 w-3.5 text-lcs-primary" />
          <span class="text-sm font-medium text-gray-900">{{ __('Open Team in Microsoft Teams') }}</span>
        </div>
        <span class="text-[10px] uppercase tracking-wider text-gray-400">{{ stripV(info.project_name) }}</span>
      </a>

      <!-- Notifications channel summary -->
      <div
        class="flex items-center justify-between rounded-lg border bg-white px-3 py-2"
        :class="info.teams_notifications_enabled ? 'border-green-200 bg-green-50/40' : 'border-amber-200 bg-amber-50/40'"
      >
        <div class="flex items-center gap-2">
          <span
            class="inline-flex h-2 w-2 rounded-full"
            :class="info.teams_notifications_enabled ? 'bg-green-500' : 'bg-amber-500'"
          />
          <div>
            <div class="text-xs font-semibold text-gray-900">
              {{ __('Notifications channel') }}: {{ info.notifications_channel_name }}
            </div>
            <div class="text-[11px] text-gray-500">
              {{
                info.teams_notifications_enabled
                  ? __('Phase changes and high-probability alerts post here.')
                  : __('Notifications are globally disabled in LCS Outlook Sync Settings.')
              }}
            </div>
          </div>
        </div>
      </div>

      <!-- Error from Graph (e.g. token expired) -->
      <div v-if="info.error" class="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-[11px] text-red-700">
        {{ info.error }}
      </div>

      <!-- Channel list -->
      <div v-if="info.channels.length" class="rounded-lg border border-gray-100">
        <div class="border-b border-gray-100 px-3 py-1.5 text-[10px] font-bold uppercase tracking-wider text-gray-400">
          {{ __('Channels') }} · {{ info.channels.length }}
        </div>
        <ul class="max-h-56 divide-y divide-gray-50 overflow-y-auto">
          <li
            v-for="ch in info.channels"
            :key="ch.id"
            class="flex items-center justify-between px-3 py-1.5 transition hover:bg-gray-50"
          >
            <div class="min-w-0">
              <div class="flex items-center gap-1.5">
                <span class="truncate text-xs font-medium text-gray-800">{{ ch.name }}</span>
                <span
                  v-if="ch.id === info.notifications_channel_id"
                  class="rounded-full bg-lcs-primary/10 px-1.5 py-0.5 text-[9px] font-semibold uppercase tracking-wider text-lcs-primary"
                >
                  {{ __('notify') }}
                </span>
              </div>
              <div v-if="ch.description" class="truncate text-[10px] text-gray-400">
                {{ ch.description }}
              </div>
            </div>
            <a
              v-if="ch.web_url"
              :href="ch.web_url"
              target="_blank"
              rel="noopener"
              class="ml-2 inline-flex items-center text-gray-400 transition hover:text-lcs-primary"
              :aria-label="__('Open channel')"
            >
              <FeatherIcon name="external-link" class="h-3 w-3" />
            </a>
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { call, FeatherIcon } from 'frappe-ui'

const props = defineProps({
  project: { type: String, required: true },
})
// Displayed project code without the "V_" Vertrieb prefix (V_SB-… → SB-…).
function stripV(s) { return String(s || '').replace(/^V_/i, '') }

const loading = ref(false)
const info = ref({
  team_id: null,
  team_link: null,
  notifications_channel_id: null,
  notifications_channel_name: '01-Sales',
  teams_notifications_enabled: false,
  channels: [],
  error: null,
  project_name: '',
})

async function refresh() {
  if (!props.project) return
  loading.value = true
  try {
    const data = await call('lcs_integrations.teams.api.get_project_teams_info', {
      project: props.project,
    })
    info.value = { ...info.value, ...(data || {}) }
  } catch (err) {
    info.value.error = String(err?.message || err)
  } finally {
    loading.value = false
  }
}

onMounted(refresh)
watch(() => props.project, refresh)
</script>
