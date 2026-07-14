<!--
  OrgEmailsTab
  ============
  LCS addition: lists the mailbox-synced Communications linked to a CRM
  Organization. The upstream Organization page only has Deals + Contacts tabs,
  so customer mail imported by the Outlook sync had no UI surface. Data comes
  from lcs_integrations.projects.api.get_organization_emails; clicking a row
  opens the full message via get_communication_email.
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
        @click="open(e)"
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
          <div class="mt-1 line-clamp-2 text-xs text-ink-gray-5">{{ e.preview }}</div>
        </div>
      </button>
    </div>

    <!-- Reader modal -->
    <Dialog v-model="showReader" :options="{ size: '3xl' }">
      <template #body>
        <div class="p-1">
          <div class="flex items-start justify-between gap-4 border-b px-5 py-4">
            <div class="min-w-0">
              <h3 class="text-lg font-semibold text-ink-gray-9">{{ current?.subject || __('(no subject)') }}</h3>
              <div class="mt-1 text-sm text-ink-gray-6">
                <span class="font-medium">{{ __('From') }}:</span> {{ current?.sender }}
              </div>
              <div v-if="current?.recipients" class="text-sm text-ink-gray-6">
                <span class="font-medium">{{ __('To') }}:</span> {{ current?.recipients }}
              </div>
              <div class="mt-0.5 text-xs text-ink-gray-4">{{ current && formatDate(current.communication_date) }}</div>
            </div>
            <Button variant="ghost" icon="x" @click="showReader = false" />
          </div>
          <div class="max-h-[65vh] overflow-y-auto px-5 py-4">
            <div v-if="loading" class="py-10 text-center text-sm text-ink-gray-4">{{ __('Loading…') }}</div>
            <div v-else class="email-body text-sm text-ink-gray-8" v-html="current?.content || ''" />
          </div>
        </div>
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { FeatherIcon, Dialog, Button, call } from 'frappe-ui'
import { formatDate } from '@/utils'

defineProps({
  emails: { type: Array, default: () => [] },
})

const showReader = ref(false)
const loading = ref(false)
const current = ref(null)

async function open(e) {
  current.value = { ...e, content: '' }
  showReader.value = true
  loading.value = true
  try {
    current.value = await call(
      'lcs_integrations.projects.api.get_communication_email',
      { name: e.name },
    )
  } catch (err) {
    current.value = { ...e, content: `<p>${__('Could not load the email.')}</p>` }
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.email-body :deep(img) {
  max-width: 100%;
  height: auto;
}
.email-body :deep(a) {
  color: var(--ink-blue-600, #2563eb);
  text-decoration: underline;
  word-break: break-word;
}
.email-body :deep(table) {
  max-width: 100%;
}
</style>
