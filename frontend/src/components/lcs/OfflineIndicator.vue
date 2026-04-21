<!--
  OfflineIndicator — shows a banner when the browser goes offline.
  Pending mutations are queued in localStorage for replay on reconnect.
-->

<template>
  <Transition
    enter-active-class="transition ease-out duration-200"
    enter-from-class="opacity-0 -translate-y-2"
    enter-to-class="opacity-100 translate-y-0"
    leave-active-class="transition ease-in duration-150"
    leave-from-class="opacity-100"
    leave-to-class="opacity-0"
  >
    <div
      v-if="!online || pendingCount > 0"
      class="fixed left-1/2 top-3 z-50 flex -translate-x-1/2 items-center gap-2 rounded-full border px-4 py-1.5 text-xs font-medium shadow-lg"
      :class="online ? 'border-amber-200 bg-amber-50 text-amber-800' : 'border-red-200 bg-red-50 text-red-800'"
    >
      <span class="relative flex h-2 w-2">
        <span
          class="absolute inline-flex h-full w-full animate-ping rounded-full opacity-75"
          :class="online ? 'bg-amber-400' : 'bg-red-400'"
        />
        <span class="relative inline-flex h-2 w-2 rounded-full" :class="online ? 'bg-amber-500' : 'bg-red-500'" />
      </span>
      <span v-if="!online">{{ __('Offline — changes will sync when reconnected') }}</span>
      <span v-else-if="pendingCount > 0">
        {{ __('Syncing') }} {{ pendingCount }} {{ __('pending change(s)...') }}
      </span>
    </div>
  </Transition>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const online = ref(navigator.onLine)
const pendingCount = ref(0)

function updateOnline() { online.value = navigator.onLine }

function updatePending() {
  try {
    const queue = JSON.parse(localStorage.getItem('lcs-offline-queue') || '[]')
    pendingCount.value = queue.length
  } catch { pendingCount.value = 0 }
}

onMounted(() => {
  window.addEventListener('online', updateOnline)
  window.addEventListener('offline', updateOnline)
  window.addEventListener('storage', updatePending)
  updatePending()

  // Poll for queue changes (storage event only fires cross-tab)
  const interval = setInterval(updatePending, 3000)
  onUnmounted(() => {
    window.removeEventListener('online', updateOnline)
    window.removeEventListener('offline', updateOnline)
    window.removeEventListener('storage', updatePending)
    clearInterval(interval)
  })
})
</script>
