<!--
  LCSOfferDetail — standalone page for a single LCS Offer.

  Routed from /crm/offers/:id. Complements the Offers-tab inside the
  project detail (which is compact cards) by offering the full view:
  inline-editable fields, status timeline, ERPNext backlinks, attachment
  list, full notes editor (with voice input).
-->

<template>
  <LayoutHeader>
    <template #left-header>
      <Breadcrumbs :items="breadcrumbs" />
    </template>
    <template v-if="doc.name" #right-header>
      <div class="flex items-center gap-2">
        <span class="text-xs text-gray-400">{{ __('Modified') }} {{ modifiedAgo }}</span>
        <Dropdown :options="statusDropdownOptions" placement="right">
          <template #default="{ open }">
            <Button :iconRight="open ? 'chevron-up' : 'chevron-down'">
              <template #prefix>
                <span class="h-2 w-2 rounded-full" :class="statusDotClass(doc.status)" />
              </template>
              {{ __(doc.status || 'Set Status') }}
            </Button>
          </template>
        </Dropdown>
      </div>
    </template>
  </LayoutHeader>

  <!-- Loading -->
  <div v-if="offer.loading && !doc.name" class="flex h-full items-center justify-center">
    <div class="h-8 w-8 animate-spin rounded-full border-2 border-gray-200 border-t-lcs-secondary" />
  </div>

  <!-- Not found -->
  <div v-else-if="!doc.name && !offer.loading" class="flex h-full items-center justify-center">
    <div class="text-center">
      <FeatherIcon name="alert-circle" class="mx-auto h-8 w-8 text-red-400" />
      <h2 class="mt-4 text-lg font-medium text-gray-900">{{ __('Offer Not Found') }}</h2>
      <Button class="mt-4" variant="outline" @click="$router.push({ name: 'LCS Projects' })" :label="__('Back to Projects')" iconLeft="arrow-left" />
    </div>
  </div>

  <!-- Main content -->
  <div v-else class="flex-1 overflow-y-auto">
    <div class="mx-auto max-w-5xl p-5 space-y-5">

      <!-- Status Hero -->
      <div class="rounded-xl border bg-gradient-to-r from-white to-gray-50 p-5">
        <div class="flex flex-wrap items-start justify-between gap-4">
          <div class="min-w-0">
            <div class="flex items-center gap-2">
              <h1 class="truncate text-xl font-bold text-gray-900">{{ doc.offer_title }}</h1>
              <span class="rounded-full bg-gray-100 px-2 py-0.5 font-mono text-xs font-bold text-gray-700">v{{ doc.version }}</span>
            </div>
            <div class="mt-1 flex flex-wrap items-center gap-2 text-sm">
              <router-link
                v-if="doc.project"
                :to="{ name: 'LCS Project', params: { id: doc.project } }"
                class="font-mono text-gray-500 hover:text-lcs-primary hover:underline"
              >
                {{ doc.project }}
              </router-link>
              <span class="text-gray-300">·</span>
              <span class="font-mono text-xs text-gray-400">{{ doc.name }}</span>
            </div>
          </div>
          <div class="flex flex-col items-end gap-2">
            <span :class="statusClass(doc.status)" class="inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-sm font-semibold">
              <span class="h-2 w-2 rounded-full" :class="statusDotClass(doc.status)" />
              {{ __(doc.status) }}
            </span>
            <div class="text-right">
              <div class="text-2xl font-bold tabular-nums text-gray-900">
                {{ doc.value ? formatCurrency(doc.value) : '—' }}
              </div>
              <div v-if="doc.probability" class="text-[10px] uppercase text-gray-400">
                {{ Math.round(doc.probability) }}% {{ __('probability') }}
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Commercial grid -->
      <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <InlineField :label="__('Value (€)')" :value="doc.value" type="number" @save="save('value', $event)" :format="formatCurrency" />
        <InlineField :label="__('Win Probability (%)')" :value="doc.probability" type="number" @save="save('probability', $event)" :suffix="'%'" />
        <InlineField :label="__('Offer Date')" :value="doc.offer_date" type="date" @save="save('offer_date', $event)" :format="formatDate" />
        <InlineField :label="__('Valid Until')" :value="doc.valid_until" type="date" @save="save('valid_until', $event)" :format="formatDate" :warning="isExpired(doc.valid_until)" />
      </div>

      <!-- Status timeline -->
      <div class="rounded-xl border bg-white p-4">
        <div class="mb-3 text-xs font-semibold uppercase tracking-wide text-gray-500">
          <FeatherIcon name="activity" class="mr-1 inline h-3 w-3" />
          {{ __('Status Flow') }}
        </div>
        <div class="flex items-center gap-1 overflow-x-auto">
          <template v-for="(s, i) in statusFlow" :key="s">
            <button
              class="flex shrink-0 flex-col items-center gap-1 px-2"
              @click="changeStatus(s)"
              :disabled="s === doc.status"
            >
              <div class="h-8 w-8 rounded-full flex items-center justify-center"
                   :class="statusFlowClass(s)">
                <FeatherIcon v-if="statusFlowIdx(s) <= statusFlowIdx(doc.status)" name="check" class="h-4 w-4" />
                <span v-else class="text-[10px]">{{ i + 1 }}</span>
              </div>
              <span class="text-[10px] font-medium" :class="s === doc.status ? 'text-gray-900' : 'text-gray-400'">
                {{ __(s) }}
              </span>
            </button>
            <div v-if="i < statusFlow.length - 1" class="h-px w-6 shrink-0 bg-gray-200" />
          </template>
        </div>
      </div>

      <!-- ERPNext links -->
      <div v-if="doc.erpnext_quotation || doc.erpnext_sales_order" class="rounded-xl border bg-white p-4">
        <div class="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-500">
          <FeatherIcon name="git-branch" class="mr-1 inline h-3 w-3" />
          {{ __('ERPNext Artefacts') }}
        </div>
        <div class="flex flex-wrap gap-2">
          <ErpNextDeepLink v-if="doc.erpnext_quotation" doctype="Quotation" :name="doc.erpnext_quotation" :label="__('Quotation') + ': ' + doc.erpnext_quotation" />
          <ErpNextDeepLink v-if="doc.erpnext_sales_order" doctype="Sales Order" :name="doc.erpnext_sales_order" :label="__('Sales Order') + ': ' + doc.erpnext_sales_order" />
        </div>
      </div>

      <!-- Notes -->
      <div class="rounded-xl border bg-amber-50/30 border-amber-200 p-4">
        <div class="mb-2 flex items-center justify-between">
          <div class="flex items-center gap-2 text-sm font-semibold text-amber-900">
            <FeatherIcon name="edit-3" class="h-4 w-4" />
            {{ __('Notes') }}
          </div>
          <Button v-if="!editingNotes" variant="ghost" size="sm" @click="startNotesEdit" :label="__('Edit')" iconLeft="edit-2" />
        </div>
        <div v-if="editingNotes" class="space-y-2">
          <div class="relative">
            <textarea
              v-model="editNotesValue"
              ref="notesInput"
              class="w-full rounded-lg border border-amber-300 bg-white px-3 py-2 pr-10 text-sm"
              rows="5"
              :placeholder="__('Terms, reminders, outcome...')"
            />
            <div class="absolute right-2 top-2">
              <VoiceInput :record-audio="true" @transcript="onVoiceNote" />
            </div>
          </div>
          <div class="flex gap-2">
            <Button variant="solid" size="sm" @click="saveNotes" :label="__('Save')" iconLeft="check" />
            <Button variant="ghost" size="sm" @click="cancelNotesEdit" :label="__('Cancel')" />
          </div>
        </div>
        <div v-else-if="doc.notes" class="whitespace-pre-wrap text-sm text-gray-800" v-html="doc.notes" />
        <div v-else class="text-sm italic text-amber-700/70">{{ __('No notes yet.') }}</div>
      </div>

      <!-- Won/Lost reason — only shown when relevant -->
      <div v-if="doc.status === 'Rejected' || doc.status === 'Accepted'" class="rounded-xl border bg-white p-4">
        <InlineField
          :label="doc.status === 'Accepted' ? __('Won Notes') : __('Lost Reason')"
          :value="doc.won_lost_reason"
          type="textarea"
          @save="save('won_lost_reason', $event)"
        />
      </div>

      <!-- Attachments -->
      <div v-if="attachments.data?.length" class="rounded-xl border bg-white p-4">
        <div class="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-500">
          <FeatherIcon name="paperclip" class="mr-1 inline h-3 w-3" />
          {{ __('Attachments') }} ({{ attachments.data.length }})
        </div>
        <ul class="space-y-1 text-sm">
          <li v-for="f in attachments.data" :key="f.name" class="flex items-center gap-2">
            <FeatherIcon name="file" class="h-3.5 w-3.5 text-gray-400" />
            <a :href="f.file_url" target="_blank" rel="noopener" class="text-lcs-secondary hover:underline">
              {{ f.file_name || f.file_url }}
            </a>
            <span class="text-xs text-gray-400">{{ (f.file_size / 1024).toFixed(0) }} KB</span>
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  createDocumentResource, createListResource, createResource,
  Breadcrumbs, Button, Dropdown, FeatherIcon, toast,
} from 'frappe-ui'
import LayoutHeader from '@/components/LayoutHeader.vue'
import VoiceInput from '@/components/lcs/VoiceInput.vue'
import ErpNextDeepLink from '@/components/lcs/ErpNextDeepLink.vue'

// Inline-editable field — click to edit, blur to save
const InlineField = {
  props: ['label', 'value', 'type', 'format', 'suffix', 'warning'],
  emits: ['save'],
  template: `
    <div class="rounded-lg border bg-white p-3 transition hover:shadow-sm" :class="warning ? 'border-red-200 bg-red-50' : ''">
      <div class="text-[10px] font-bold uppercase tracking-wider text-gray-400">{{ label }}</div>
      <div v-if="!editing" @click="startEdit" class="mt-1 cursor-pointer text-sm font-medium text-gray-900" :class="!value ? 'text-gray-300 italic' : ''">
        {{ value ? displayValue : '— click to set —' }}
      </div>
      <div v-else class="mt-1 flex gap-1">
        <input
          ref="input"
          v-model="editValue"
          :type="type || 'text'"
          class="w-full rounded border border-gray-300 px-2 py-1 text-sm"
          @keydown.enter="commit"
          @keydown.escape="cancel"
          @blur="commit"
        />
      </div>
    </div>
  `,
  data() {
    return { editing: false, editValue: this.value }
  },
  computed: {
    displayValue() {
      if (this.format) return this.format(this.value) + (this.suffix || '')
      return String(this.value) + (this.suffix || '')
    },
  },
  methods: {
    startEdit() {
      this.editValue = this.value
      this.editing = true
      this.$nextTick(() => this.$refs.input?.focus())
    },
    commit() {
      if (this.editValue !== this.value) this.$emit('save', this.editValue)
      this.editing = false
    },
    cancel() { this.editing = false },
  },
}

const route = useRoute()
const router = useRouter()
const props = defineProps({ id: { type: String, required: true } })

const offer = createDocumentResource({
  doctype: 'LCS Offer',
  name: props.id,
  onError: (err) => {
    if (err.exc_type === 'DoesNotExistError') {
      toast({ title: __('Offer not found'), icon: 'alert-circle', iconClasses: 'text-red-500' })
    }
  },
})
if (!offer.doc) offer.get.fetch()
const doc = computed(() => offer.doc || {})

const breadcrumbs = computed(() => {
  const crumbs = [{ label: __('Projects'), route: { name: 'LCS Projects' } }]
  if (doc.value.project) {
    crumbs.push({ label: doc.value.project, route: { name: 'LCS Project', params: { id: doc.value.project } } })
  }
  crumbs.push({ label: doc.value.offer_title || props.id, route: { name: 'LCS Offer', params: { id: props.id } } })
  return crumbs
})

const modifiedAgo = computed(() => doc.value.modified ? _relTime(doc.value.modified) : '')

// Status flow
const statusFlow = ['Draft', 'Sent', 'In Review', 'Accepted']
const statusFlowIdx = (s) => statusFlow.indexOf(s)

const statusDropdownOptions = computed(() => {
  const all = ['Draft', 'Sent', 'In Review', 'Accepted', 'Rejected', 'Expired', 'Revised']
  return all.map(s => ({
    label: __(s),
    icon: doc.value.status === s ? 'check' : undefined,
    onClick: () => changeStatus(s),
  }))
})

function changeStatus(newStatus) {
  if (newStatus === doc.value.status) return
  save('status', newStatus)
}

// Notes edit
const editingNotes = ref(false)
const editNotesValue = ref('')
const notesInput = ref(null)
function startNotesEdit() {
  editNotesValue.value = doc.value.notes || ''
  editingNotes.value = true
  nextTick(() => notesInput.value?.focus())
}
function cancelNotesEdit() { editingNotes.value = false }
function saveNotes() {
  save('notes', editNotesValue.value)
  editingNotes.value = false
}
let voiceBaseline = ''
function onVoiceNote({ final, interim }) {
  if (final && voiceBaseline === '') voiceBaseline = editNotesValue.value || ''
  const separator = voiceBaseline ? (voiceBaseline.endsWith('\n') ? '' : '\n') : ''
  editNotesValue.value = voiceBaseline + separator + (final || '') + (interim || '')
}

// Save
function save(fieldname, value) {
  offer.setValue.submit({ [fieldname]: value }).then(() => {
    toast({ title: __('Saved'), icon: 'check-circle', iconClasses: 'text-green-500' })
  }).catch((err) => {
    toast({ title: __('Save failed'), text: err.messages?.[0] || err.message, icon: 'alert-circle', iconClasses: 'text-red-500' })
  })
}

// Attachments
const attachments = createListResource({
  doctype: 'File',
  filters: { attached_to_doctype: 'LCS Offer', attached_to_name: props.id },
  fields: ['name', 'file_url', 'file_name', 'file_size'],
  orderBy: 'creation desc',
  pageLength: 20,
  auto: true,
})

// --- Style helpers ---
function statusClass(s) {
  const m = {
    Draft: 'bg-gray-50 text-gray-700 border border-gray-200',
    Sent: 'bg-blue-50 text-blue-700 border border-blue-200',
    'In Review': 'bg-purple-50 text-purple-700 border border-purple-200',
    Accepted: 'bg-green-50 text-green-700 border border-green-200',
    Rejected: 'bg-red-50 text-red-700 border border-red-200',
    Expired: 'bg-gray-50 text-gray-500 border border-gray-200',
    Revised: 'bg-amber-50 text-amber-700 border border-amber-200',
  }
  return m[s] || 'bg-gray-50 text-gray-600 border border-gray-200'
}

function statusDotClass(s) {
  const m = {
    Draft: 'bg-gray-400', Sent: 'bg-blue-500', 'In Review': 'bg-purple-500',
    Accepted: 'bg-green-500', Rejected: 'bg-red-500',
    Expired: 'bg-gray-300', Revised: 'bg-amber-500',
  }
  return m[s] || 'bg-gray-400'
}

function statusFlowClass(s) {
  const idx = statusFlowIdx(s)
  const currentIdx = statusFlowIdx(doc.value.status)
  if (s === doc.value.status) return 'bg-lcs-primary text-white ring-2 ring-lcs-secondary/40'
  if (idx < currentIdx) return 'bg-green-500 text-white'
  return 'bg-gray-100 text-gray-400'
}

function formatCurrency(v) {
  return new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(v || 0)
}
function formatDate(d) {
  if (!d) return ''
  return new Intl.DateTimeFormat('de-DE', { day: '2-digit', month: 'short', year: 'numeric' }).format(new Date(d))
}
function isExpired(d) {
  if (!d) return false
  return new Date(d) < new Date()
}
function _relTime(iso) {
  const s = Math.floor((Date.now() - new Date(iso).getTime()) / 1000)
  if (s < 60) return `${s}s ${__('ago')}`
  if (s < 3600) return `${Math.floor(s / 60)}m ${__('ago')}`
  if (s < 86400) return `${Math.floor(s / 3600)}h ${__('ago')}`
  return `${Math.floor(s / 86400)}d ${__('ago')}`
}
</script>
