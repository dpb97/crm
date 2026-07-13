<!--
  OrgEmailsTab
  ============
  LCS addition: lists the mailbox-synced Communications linked to a CRM
  Organization. The upstream Organization page only has Deals + Contacts tabs,
  so customer mail imported by the Outlook sync had no UI surface. Data comes
  from lcs_integrations.projects.api.get_organization_emails.
-->

<template>
  <div class="mt-4 flex w-full flex-col overflow-y-auto px-3 pb-6">
    <div
      v-if="!emails?.length"
      class="flex flex-col items-center justify-center gap-2 py-16 text-ink-gray-4"
    >
      <FeatherIcon name="mail" class="h-8 w-8" />
      <span class="text-sm">{{ __('No emails synced for this company yet.') }}</span>
    </div>

    <div v-else class="divide-y rounded-lg border">
      <button
        v-for="e in emails"
        :key="e.name"
        class="flex w-full items-start gap-3 px-4 py-3 text-left hover:bg-surface-gray-2"
        @click="toggle(e.name)"
      >
        <div
          class="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full"
          :class="e.sent_or_received === 'Sent' ? 'bg-blue-50 text-blue-600' : 'bg-green-50 text-green-600'"
        >
          <FeatherIcon :name="e.sent_or_received === 'Sent' ? 'arrow-up-right' : 'arrow-down-left'" class="h-3.5 w-3.5" />
        </div>
        <div class="min-w-0 flex-1">
          <div class="flex items-center gap-2">
            <span class="truncate text-sm font-medium text-ink-gray-9">{{ e.subject || __('(no subject)') }}</span>
            <span class="ml-auto shrink-0 text-xs text-ink-gray-4">{{ formatDate(e.communication_date) }}</span>
          </div>
          <div class="truncate text-xs text-ink-gray-6">{{ e.sender }}</div>
          <div
            class="mt-1 text-xs text-ink-gray-5"
            :class="expanded.has(e.name) ? '' : 'line-clamp-2'"
          >
            {{ e.preview }}
          </div>
        </div>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { FeatherIcon } from 'frappe-ui'
import { formatDate } from '@/utils'

defineProps({
  emails: { type: Array, default: () => [] },
})

const expanded = ref(new Set())
function toggle(name) {
  const s = new Set(expanded.value)
  s.has(name) ? s.delete(name) : s.add(name)
  expanded.value = s
}
</script>
