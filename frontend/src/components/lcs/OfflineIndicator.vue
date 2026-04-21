<!--
  OfflineIndicator — offline banner + pending-sync drawer.
  Clicking the banner opens a panel listing queued mutations with
  individual retry / discard controls.
-->

<template>
  <!-- Conflict resolver dialog -->
  <ConflictResolver
    :mutation="resolverMutation"
    @close="resolverMutation = null"
  />

  <!-- Top banner -->
  <Transition
    enter-active-class="transition ease-out duration-200"
    enter-from-class="opacity-0 -translate-y-2"
    enter-to-class="opacity-100 translate-y-0"
    leave-active-class="transition ease-in duration-150"
    leave-from-class="opacity-100"
    leave-to-class="opacity-0"
  >
    <button
      v-if="showBanner"
      class="fixed left-1/2 top-3 z-50 flex -translate-x-1/2 items-center gap-2 rounded-full border px-4 py-1.5 text-xs font-medium shadow-lg"
      :class="bannerClass"
      @click="drawerOpen = !drawerOpen"
    >
      <span class="relative flex h-2 w-2">
        <span class="absolute inline-flex h-full w-full animate-ping rounded-full opacity-75" :class="pingClass" />
        <span class="relative inline-flex h-2 w-2 rounded-full" :class="dotClass" />
      </span>
      <span>{{ bannerMessage }}</span>
      <FeatherIcon :name="drawerOpen ? 'chevron-up' : 'chevron-down'" class="h-3 w-3" />
    </button>
  </Transition>

  <!-- Drawer with queued mutations -->
  <Transition
    enter-active-class="transition ease-out duration-200"
    enter-from-class="opacity-0 translate-y-4"
    enter-to-class="opacity-100 translate-y-0"
    leave-active-class="transition ease-in duration-150"
    leave-from-class="opacity-100"
    leave-to-class="opacity-0"
  >
    <div
      v-if="drawerOpen"
      class="fixed right-4 top-16 z-50 w-96 overflow-hidden rounded-xl border bg-white shadow-2xl"
    >
      <!-- Header -->
      <div class="flex items-center justify-between border-b bg-gray-50 px-4 py-3">
        <div>
          <div class="text-sm font-semibold text-gray-900">{{ __('Offline Queue') }}</div>
          <div class="text-xs text-gray-500">
            {{ pending.length }} {{ __('pending') }}
            <span v-if="failed.length"> · {{ failed.length }} {{ __('failed') }}</span>
          </div>
        </div>
        <button class="rounded-md p-1 hover:bg-gray-200" @click="drawerOpen = false">
          <FeatherIcon name="x" class="h-4 w-4 text-gray-500" />
        </button>
      </div>

      <!-- Mutation list -->
      <div class="max-h-96 overflow-y-auto">
        <div v-if="!mutations.length" class="py-8 text-center text-sm text-gray-400">
          <FeatherIcon name="check-circle" class="mx-auto h-6 w-6 text-green-400" />
          <p class="mt-2">{{ __('All changes synced') }}</p>
        </div>
        <div
          v-for="m in sortedMutations"
          :key="m.id"
          class="border-b px-4 py-3 hover:bg-gray-50"
        >
          <div class="flex items-start justify-between gap-2">
            <div class="min-w-0 flex-1">
              <div class="flex items-center gap-1.5">
                <span class="h-1.5 w-1.5 rounded-full" :class="statusDotClass(m.status)" />
                <span class="text-xs font-semibold uppercase tracking-wide" :class="statusTextClass(m.status)">
                  {{ __(m.status) }}
                </span>
                <span v-if="m.retry_count" class="text-[10px] text-gray-400">
                  {{ __('retry') }} {{ m.retry_count }}
                </span>
                <!-- Conflict field count badge -->
                <span v-if="m.status === 'conflict' && m.conflicts" class="rounded-full bg-orange-100 px-1.5 py-0 text-[10px] font-bold text-orange-800">
                  {{ Object.keys(m.conflicts).length }} {{ __('field(s)') }}
                </span>
              </div>
              <div class="mt-1 truncate text-sm font-medium text-gray-800">{{ m.description }}</div>
              <div class="mt-0.5 truncate font-mono text-[10px] text-gray-400">
                {{ m.doctype }}{{ m.name ? ' · ' + m.name : '' }}
              </div>
              <div v-if="m.error" class="mt-1 rounded-md bg-red-50 px-2 py-1 text-[10px] text-red-700">
                {{ m.error }}
              </div>
              <!-- Conflict summary — click to resolve -->
              <div v-if="m.status === 'conflict'" class="mt-2 rounded-md bg-orange-50 border border-orange-200 px-2 py-1.5">
                <div class="text-[10px] font-semibold text-orange-800">
                  {{ __('Server changed while you were editing') }}
                </div>
                <div class="mt-0.5 text-[10px] text-orange-700">
                  {{ __('Conflicting fields') }}: {{ Object.keys(m.conflicts || {}).join(', ') }}
                </div>
              </div>
            </div>
            <div class="flex shrink-0 flex-col gap-1">
              <!-- Resolve button for conflicts -->
              <button
                v-if="m.status === 'conflict'"
                class="rounded-md bg-orange-500 p-1.5 text-white hover:bg-orange-600"
                @click="openResolver(m)"
                :title="__('Resolve conflict')"
              >
                <FeatherIcon name="git-merge" class="h-3 w-3" />
              </button>
              <button
                v-if="m.status === 'failed' || (m.status === 'pending' && online)"
                class="rounded-md bg-gray-100 p-1.5 text-gray-600 hover:bg-lcs-secondary hover:text-white"
                @click="onRetry(m.id)"
                :title="__('Retry')"
              >
                <FeatherIcon name="refresh-cw" class="h-3 w-3" />
              </button>
              <button
                class="rounded-md bg-gray-100 p-1.5 text-gray-600 hover:bg-red-500 hover:text-white"
                @click="onDiscard(m.id)"
                :title="__('Discard')"
              >
                <FeatherIcon name="trash-2" class="h-3 w-3" />
              </button>
            </div>
          </div>
          <div class="mt-1 text-[10px] text-gray-400">{{ timeAgo(m.timestamp) }}</div>
        </div>
      </div>

      <!-- Footer with sync action -->
      <div v-if="mutations.length" class="flex items-center justify-between border-t bg-gray-50 px-4 py-2.5">
        <span class="text-xs text-gray-500">
          <span v-if="online">{{ __('Online — syncing automatically') }}</span>
          <span v-else>{{ __('Waiting for connection') }}</span>
        </span>
        <button
          v-if="online"
          class="rounded-md bg-lcs-primary px-2.5 py-1 text-xs font-medium text-white hover:bg-lcs-secondary"
          @click="onSyncNow"
          :disabled="syncing"
        >
          {{ syncing ? __('Syncing...') : __('Sync now') }}
        </button>
      </div>
    </div>
  </Transition>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { FeatherIcon } from 'frappe-ui'
import { listMutations, onQueueChange } from '@/utils/offlineDB'
import { drain, retryMutation, discardMutation } from '@/utils/syncEngine'
import ConflictResolver from '@/components/lcs/ConflictResolver.vue'

const online = ref(navigator.onLine)
const mutations = ref([])
const drawerOpen = ref(false)
const syncing = ref(false)
const resolverMutation = ref(null)

function openResolver(mutation) {
  resolverMutation.value = mutation
}

function updateOnline() {
  online.value = navigator.onLine
  refresh()
}

async function refresh() {
  mutations.value = await listMutations()
}

const pending = computed(() => mutations.value.filter(m => m.status === 'pending' || m.status === 'syncing'))
const failed = computed(() => mutations.value.filter(m => m.status === 'failed'))
const conflicts = computed(() => mutations.value.filter(m => m.status === 'conflict'))

const sortedMutations = computed(() =>
  [...mutations.value].sort((a, b) => (b.timestamp || 0) - (a.timestamp || 0))
)

const showBanner = computed(() => !online.value || pending.value.length > 0 || failed.value.length > 0 || conflicts.value.length > 0)

const bannerClass = computed(() => {
  if (!online.value) return 'border-red-200 bg-red-50 text-red-800'
  if (conflicts.value.length) return 'border-orange-200 bg-orange-50 text-orange-800'
  if (failed.value.length) return 'border-red-200 bg-red-50 text-red-800'
  if (pending.value.length) return 'border-amber-200 bg-amber-50 text-amber-800'
  return 'border-green-200 bg-green-50 text-green-800'
})

const pingClass = computed(() => {
  if (!online.value || failed.value.length) return 'bg-red-400'
  if (conflicts.value.length) return 'bg-orange-400'
  return 'bg-amber-400'
})

const dotClass = computed(() => {
  if (!online.value || failed.value.length) return 'bg-red-500'
  if (conflicts.value.length) return 'bg-orange-500'
  return 'bg-amber-500'
})

const bannerMessage = computed(() => {
  if (!online.value) return __('Offline — changes will sync when reconnected')
  if (conflicts.value.length) return `${conflicts.value.length} ${__('conflict(s) — tap to resolve')}`
  if (failed.value.length) return `${failed.value.length} ${__('sync error(s)')}`
  if (pending.value.length) return `${__('Syncing')} ${pending.value.length} ${__('change(s)')}...`
  return __('All synced')
})

function statusDotClass(status) {
  const m = { pending: 'bg-amber-400', syncing: 'bg-blue-500 animate-pulse', failed: 'bg-red-500', conflict: 'bg-orange-500 animate-pulse', done: 'bg-green-500' }
  return m[status] || 'bg-gray-400'
}

function statusTextClass(status) {
  const m = { pending: 'text-amber-700', syncing: 'text-blue-700', failed: 'text-red-700', conflict: 'text-orange-700', done: 'text-green-700' }
  return m[status] || 'text-gray-500'
}

function timeAgo(ts) {
  if (!ts) return ''
  const seconds = Math.floor((Date.now() - ts) / 1000)
  if (seconds < 60) return `${seconds}s ${__('ago')}`
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${__('ago')}`
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ${__('ago')}`
  return `${Math.floor(seconds / 86400)}d ${__('ago')}`
}

async function onRetry(id) {
  await retryMutation(id)
  refresh()
}

async function onDiscard(id) {
  if (!confirm(__('Discard this pending change? It will not be sent to the server.'))) return
  await discardMutation(id)
  refresh()
}

async function onSyncNow() {
  syncing.value = true
  try {
    await drain()
    await refresh()
  } finally {
    syncing.value = false
  }
}

let unsub = null

onMounted(() => {
  window.addEventListener('online', updateOnline)
  window.addEventListener('offline', updateOnline)
  refresh()
  unsub = onQueueChange(() => refresh())
})

onUnmounted(() => {
  window.removeEventListener('online', updateOnline)
  window.removeEventListener('offline', updateOnline)
  if (unsub) unsub()
})
</script>
