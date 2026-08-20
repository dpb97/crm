<!--
  OrgEmailsTab
  ============
  LCS addition: lists the mailbox-synced Communications linked to a CRM
  Organization. The upstream Organization page only has Deals + Contacts tabs,
  so customer mail imported by the Outlook sync had no UI surface. Data comes
  from lcs_integrations.projects.api.get_organization_emails; clicking a row
  opens the full message via get_communication_email. A per-row trash button
  removes a single email from the CRM (delete_synced_email).
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

    <template v-else>
      <!-- LCS: filter by sender / recipient / subject / direction / date range -->
      <div class="mb-2 flex flex-wrap items-center gap-2">
        <select v-model="fSender" class="emf-ctrl min-w-[140px] flex-1 rounded-md px-2 py-1.5 text-sm outline-none">
          <option value="">{{ __('All senders') }}</option>
          <option v-for="s in senderOptions" :key="s" :value="s">{{ s }}</option>
        </select>
        <select v-model="fRecipient" class="emf-ctrl min-w-[140px] flex-1 rounded-md px-2 py-1.5 text-sm outline-none">
          <option value="">{{ __('All recipients') }}</option>
          <option v-for="r in recipientOptions" :key="r" :value="r">{{ r }}</option>
        </select>
        <input v-model="fSubject" type="text" :placeholder="__('Subject') + '…'"
          class="emf-ctrl min-w-[140px] flex-1 rounded-md px-3 py-1.5 text-sm outline-none" />
      </div>
      <div class="mb-3 flex flex-wrap items-center gap-2">
        <select v-model="fDirection" class="emf-ctrl rounded-md px-2 py-1.5 text-sm outline-none">
          <option value="">{{ __('All') }}</option>
          <option value="Received">{{ __('Received') }}</option>
          <option value="Sent">{{ __('Sent') }}</option>
        </select>
        <label class="flex items-center gap-1 text-xs text-ink-gray-5">{{ __('From') }}
          <input v-model="fFrom" type="date" class="emf-ctrl rounded-md px-2 py-1.5 text-sm outline-none" />
        </label>
        <label class="flex items-center gap-1 text-xs text-ink-gray-5">{{ __('To') }}
          <input v-model="fTo" type="date" class="emf-ctrl rounded-md px-2 py-1.5 text-sm outline-none" />
        </label>
        <button v-if="anyFilter" type="button" @click="clearFilters"
          class="rounded-md px-2 py-1.5 text-sm text-ink-gray-5 hover:bg-surface-gray-2 hover:text-ink-gray-8">
          {{ __('Reset') }}
        </button>
        <span class="ml-auto text-xs text-ink-gray-4">{{ filtered.length }} / {{ emails.length }}</span>
      </div>
      <div v-if="filtered.length" class="divide-y rounded-lg border">
      <div
        v-for="e in filtered"
        :key="e.name"
        class="group flex w-full items-start gap-3 px-4 py-3 hover:bg-surface-gray-2"
      >
        <button class="flex min-w-0 flex-1 items-start gap-3 text-left" @click="open(e)">
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
        <!-- LCS: remove a single synced email from the CRM -->
        <button
          class="mt-0.5 shrink-0 self-start rounded p-1.5 text-ink-gray-4 opacity-0 transition hover:bg-red-50 hover:text-red-600 focus:opacity-100 group-hover:opacity-100"
          :title="__('Delete email')"
          @click.stop="askRemove(e)"
        >
          <FeatherIcon name="trash-2" class="h-4 w-4" />
        </button>
      </div>
      </div>
      <div v-else class="py-10 text-center text-sm text-ink-gray-4">{{ __('No emails match the filter.') }}</div>
    </template>

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
            <div class="flex shrink-0 items-center gap-1">
              <Button variant="subtle" iconLeft="external-link" :label="__('Open in Outlook')" :disabled="!current?.message_id" @click="openInOutlook(current)" />
              <Button variant="subtle" iconLeft="corner-up-left" :label="__('Reply')" @click="replyOpen = !replyOpen" />
              <Button variant="ghost" icon="trash-2" :title="__('Delete email')" @click="showReader = false; askRemove(current)" />
              <Button variant="ghost" icon="x" @click="showReader = false" />
            </div>
          </div>
          <div class="max-h-[65vh] overflow-y-auto px-5 py-4">
            <div v-if="loading" class="py-10 text-center text-sm text-ink-gray-4">{{ __('Loading…') }}</div>
            <div v-else>
              <!-- LCS: reply straight from the CRM (sent via Graph as the mailbox) -->
              <div v-if="replyOpen" class="mb-3 rounded-lg border border-lcs-secondary/40 p-3">
                <div class="mb-1 text-xs font-semibold uppercase tracking-wide text-ink-gray-4">{{ __('Reply') }}</div>
                <textarea v-model="replyBody" rows="4" class="emf-ctrl w-full rounded-md px-3 py-2 text-sm outline-none" :placeholder="__('Your reply …')" />
                <div class="mt-2 flex flex-wrap items-center gap-2">
                  <label class="flex items-center gap-1 text-xs text-ink-gray-6"><input type="checkbox" v-model="replyAll" /> {{ __('Reply all') }}</label>
                  <span class="ml-auto"></span>
                  <Button variant="ghost" :label="__('Reply in Outlook')" @click="replyMailto(current)" />
                  <Button variant="ghost" :label="__('Cancel')" @click="replyOpen = false" />
                  <Button variant="solid" :label="__('Send')" :loading="replySending" :disabled="!replyBody.trim()" @click="sendReply" />
                </div>
              </div>
              <!-- LCS: whole conversation (same normalized subject) -->
              <div v-if="conversation.length" class="mb-3 rounded-lg border bg-surface-gray-1 p-2">
                <div class="mb-1 px-1 text-xs font-semibold uppercase tracking-wide text-ink-gray-4">
                  {{ __('Conversation') }} ({{ conversation.length + 1 }})
                </div>
                <button v-for="m in conversation" :key="m.name" type="button"
                  class="flex w-full items-center gap-2 rounded px-2 py-1.5 text-left text-xs hover:bg-surface-gray-2"
                  @click="open(m)">
                  <FeatherIcon :name="m.sent_or_received === 'Sent' ? 'arrow-up-right' : 'arrow-down-left'" class="h-3 w-3 shrink-0 text-ink-gray-4" />
                  <span class="min-w-0 flex-1 truncate">{{ m.subject || __('(no subject)') }}</span>
                  <span class="shrink-0 truncate text-ink-gray-4">{{ m.sender }}</span>
                  <span class="shrink-0 text-ink-gray-4">{{ formatDate(m.communication_date) }}</span>
                </button>
              </div>
              <div class="email-body text-sm text-ink-gray-8" v-html="current?.content || ''" />
              <div v-if="current?.attachments?.length" class="mt-4 border-t pt-3">
                <div class="mb-2 text-xs font-semibold uppercase tracking-wide text-ink-gray-4">
                  {{ __('Attachments') }} ({{ current.attachments.length }})
                </div>
                <div class="flex flex-wrap gap-2">
                  <a
                    v-for="(att, i) in current.attachments"
                    :key="i"
                    :href="att.data_url"
                    :download="att.name"
                    target="_blank"
                    rel="noopener"
                    class="flex items-center gap-2 rounded-lg border px-3 py-2 text-xs hover:bg-surface-gray-2"
                    :title="att.name"
                  >
                    <img v-if="att.is_image" :src="att.data_url" class="h-10 w-10 rounded object-cover" :alt="att.name" />
                    <FeatherIcon v-else name="paperclip" class="h-4 w-4 text-ink-gray-5" />
                    <span class="max-w-[12rem] truncate text-ink-gray-8">{{ att.name }}</span>
                  </a>
                </div>
              </div>
            </div>
          </div>
        </div>
      </template>
    </Dialog>

    <!-- LCS: confirm removing a single email -->
    <Dialog
      v-model="showConfirm"
      :options="{
        title: __('Delete email'),
        size: 'sm',
        actions: [
          { label: __('Delete'), variant: 'solid', theme: 'red', loading: deleting, onClick: confirmRemove },
          { label: __('Cancel'), onClick: () => (showConfirm = false) },
        ],
      }"
    >
      <template #body-content>
        <p class="text-sm text-ink-gray-7">{{ __('Delete this email? It will be removed from the CRM.') }}</p>
        <p v-if="pending" class="mt-2 truncate text-sm font-medium text-ink-gray-9">
          {{ pending.subject || __('(no subject)') }}
        </p>
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { FeatherIcon, Dialog, Button, call, toast, createResource } from 'frappe-ui'
import { formatDate } from '@/utils'

const props = defineProps({
  emails: { type: Array, default: () => [] },
})

// LCS: filter the mail list (sender / recipient / subject / direction / date range)
const fSender = ref('')
const fRecipient = ref('')
const fSubject = ref('')
const fDirection = ref('')
const fFrom = ref('')
const fTo = ref('')
const anyFilter = computed(() =>
  !!(fSender.value || fRecipient.value || fSubject.value || fDirection.value || fFrom.value || fTo.value),
)
// Dropdown options: the distinct senders / recipients actually present in the list.
const senderOptions = computed(() => {
  const set = new Set()
  ;(props.emails || []).forEach((e) => {
    const s = (e.sender || '').trim()
    if (s) set.add(s)
  })
  return [...set].sort((a, b) => a.localeCompare(b))
})
const recipientOptions = computed(() => {
  const set = new Set()
  ;(props.emails || []).forEach((e) => {
    ;(e.recipients || '').split(',').forEach((r) => {
      const t = r.trim()
      if (t) set.add(t)
    })
  })
  return [...set].sort((a, b) => a.localeCompare(b))
})
function clearFilters() {
  fSender.value = ''
  fRecipient.value = ''
  fSubject.value = ''
  fDirection.value = ''
  fFrom.value = ''
  fTo.value = ''
}
// LCS: names removed via the trash button (kept out of the list locally)
const removed = ref(new Set())
const filtered = computed(() => {
  const s = fSender.value.trim().toLowerCase()
  const r = fRecipient.value.trim().toLowerCase()
  const subj = fSubject.value.trim().toLowerCase()
  const dir = fDirection.value
  const from = fFrom.value ? new Date(fFrom.value + 'T00:00:00').getTime() : null
  const to = fTo.value ? new Date(fTo.value + 'T23:59:59').getTime() : null
  return (props.emails || []).filter((e) => {
    if (removed.value.has(e.name)) return false
    if (s && !(e.sender || '').toLowerCase().includes(s)) return false
    if (r && !(e.recipients || '').toLowerCase().includes(r)) return false
    if (subj && !(e.subject || '').toLowerCase().includes(subj)) return false
    if (dir && e.sent_or_received !== dir) return false
    if (from != null || to != null) {
      const d = e.communication_date ? new Date(String(e.communication_date).replace(' ', 'T')).getTime() : NaN
      if (isNaN(d)) return false
      if (from != null && d < from) return false
      if (to != null && d > to) return false
    }
    return true
  })
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

// LCS: whole conversation — group by normalized subject (strip Re:/Fw:/AW:/WG:/TR:).
function normSubject(s) {
  return String(s || '').replace(/^((re|fw|fwd|aw|wg|tr)\s*:\s*)+/i, '').trim().toLowerCase()
}
const conversation = computed(() => {
  if (!current.value) return []
  const cid = current.value.lcs_conversation_id
  const base = normSubject(current.value.subject)
  return (props.emails || [])
    .filter((e) => e.name !== current.value.name && !removed.value.has(e.name)
      && (cid ? e.lcs_conversation_id === cid : (base && normSubject(e.subject) === base)))
    .sort((a, b) => String(b.communication_date || '').localeCompare(String(a.communication_date || '')))
})

// LCS: reply — real send via Graph (as the mailbox owner), or open Outlook.
const replyOpen = ref(false)
const replyBody = ref('')
const replyAll = ref(false)
const replySending = ref(false)
const replyRes = createResource({ url: 'lcs_integrations.projects.api.send_mail_reply' })
watch(current, () => { replyOpen.value = false; replyBody.value = '' })
function sendReply() {
  const b = replyBody.value.trim()
  if (!b || !current.value) return
  replySending.value = true
  replyRes.submit({ name: current.value.name, body: b, reply_all: replyAll.value ? 1 : 0 })
    .then(() => { toast.success(__('Reply sent')); replyOpen.value = false; replyBody.value = '' })
    .catch((e) => { toast.error(e?.messages?.[0] || __('Could not send the reply.')) })
    .finally(() => { replySending.value = false })
}
// LCS: open the ORIGINAL message in Outlook on the web (OWA deep link by the
// stored Graph message id). Opens in the viewer's own Outlook — works when the
// message is in their mailbox; otherwise Outlook falls back to a search view.
function openInOutlook(m) {
  if (!m?.message_id) { toast.error(__('No Outlook link for this email.')); return }
  const url = `https://outlook.office.com/mail/deeplink/read/${encodeURIComponent(m.message_id)}`
  window.open(url, '_blank', 'noopener')
}
function replyMailto(m) {
  if (!m) return
  const to = m.sent_or_received === 'Sent'
    ? (m.recipients || '').split(',')[0].trim()
    : (m.sender || '')
  const subject = 'Re: ' + String(m.subject || '').replace(/^((re|fw|fwd|aw|wg|tr)\s*:\s*)+/i, '')
  window.location.href = `mailto:${encodeURIComponent(to)}?subject=${encodeURIComponent(subject)}`
}

// LCS: delete a single synced email from the CRM (with confirmation)
const showConfirm = ref(false)
const deleting = ref(false)
const pending = ref(null)
function askRemove(e) {
  pending.value = e
  showConfirm.value = true
}
async function confirmRemove() {
  if (!pending.value) return
  deleting.value = true
  const name = pending.value.name
  try {
    await call('lcs_integrations.projects.api.delete_synced_email', { name })
    removed.value = new Set([...removed.value, name])
    showConfirm.value = false
    toast.success(__('Email deleted'))
  } catch (err) {
    toast.error(__('Could not delete the email.'))
  } finally {
    deleting.value = false
    pending.value = null
  }
}
</script>

<style scoped>
/* Filter controls: no white boxes — token grey surface + subtle border. */
.emf-ctrl {
  background: var(--pp-bg-base);
  border: 1px solid var(--pp-border-subtle);
  color: var(--pp-text-primary);
}
.emf-ctrl:focus { border-color: var(--pp-brand-primary); }

.email-body :deep(img) {
  max-width: 100%;
  height: auto;
}
.email-body :deep(a) {
  color: var(--pp-text-link);
  text-decoration: underline;
  word-break: break-word;
}
.email-body :deep(table) {
  max-width: 100%;
}
</style>
