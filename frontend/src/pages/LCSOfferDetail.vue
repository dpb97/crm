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
                <span class="h-2 w-2 rounded-full" :style="statusDotStyle(doc.status)" />
              </template>
              {{ __(doc.status || 'Set Status') }}
            </Button>
          </template>
        </Dropdown>
      </div>
    </template>
  </LayoutHeader>

  <!-- Loading -->
  <div v-if="offer.loading && !doc.name" class="lcsod-center">
    <div class="lcsod-spinner" />
  </div>

  <!-- Not found -->
  <div v-else-if="!doc.name && !offer.loading" class="lcsod-center">
    <PpEmptyState :icon="IconAlertCircle" :title="__('Offer Not Found')">
      <template #action>
        <Button variant="outline" @click="$router.push({ name: 'LCS Projects' })" :label="__('Back to Projects')" iconLeft="arrow-left" />
      </template>
    </PpEmptyState>
  </div>

  <!-- Main content -->
  <div v-else class="lcsod flex-1 overflow-y-auto">
    <div class="lcsod-inner">

      <!-- Status Hero -->
      <div class="lcsod-hero">
        <div class="flex flex-wrap items-start justify-between gap-4">
          <div class="min-w-0">
            <div class="flex items-center gap-2">
              <h1 class="lcsod-title">{{ doc.offer_title }}</h1>
              <span class="lcsod-ver">v{{ doc.version }}</span>
            </div>
            <div class="mt-1 flex flex-wrap items-center gap-2 text-sm">
              <router-link
                v-if="doc.project"
                :to="{ name: 'LCS Project', params: { id: doc.project } }"
                class="lcsod-project"
              >
                {{ doc.project }}
              </router-link>
              <span class="lcsod-sep">·</span>
              <span class="lcsod-id">{{ doc.name }}</span>
            </div>
          </div>
          <div class="flex flex-col items-end gap-2">
            <span class="lcsod-pill" :data-tone="statusTone(doc.status)">
              <i class="lcsod-dot" />{{ __(doc.status) }}
            </span>
            <div class="text-right">
              <MoneyDual
                v-if="doc.value"
                class="items-end"
                :amount="doc.value"
                :currency="doc.currency"
                :value-eur="doc.value_eur"
                :rate="doc.exchange_rate_to_eur || liveRateValue"
                :frozen-at="doc.rate_frozen_at"
                size="lg"
              />
              <div v-else class="lcsod-nomoney">—</div>
              <div v-if="doc.probability" class="lcsod-prob">
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

      <!-- FX Snapshot — frozen-at-save vs. live (Frankfurter.dev, ECB) -->
      <div v-if="doc.value && doc.currency && doc.currency !== 'EUR'" class="lcsod-card">
        <div class="mb-3 flex items-center justify-between">
          <div class="lcsod-card-title">
            <FeatherIcon name="repeat" class="h-3 w-3" />
            {{ __('Currency Conversion') }}
          </div>
          <Button
            variant="ghost"
            size="sm"
            :loading="liveRate.loading"
            @click="liveRate.reload()"
            :label="__('Refresh live rate')"
            iconLeft="refresh-cw"
          />
        </div>

        <div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <!-- Frozen card -->
          <div class="lcsod-fx lcsod-fx--frozen">
            <div class="lcsod-fx-cap">{{ __('Frozen at save') }}</div>
            <div class="lcsod-fx-val">
              {{ doc.value_eur ? formatCurrency(doc.value_eur) : '—' }}
              <span class="lcsod-fx-ccy">EUR</span>
            </div>
            <div class="lcsod-fx-note">
              {{ doc.exchange_rate_to_eur
                  ? `1 ${doc.currency} = ${Number(doc.exchange_rate_to_eur).toFixed(4)} EUR`
                  : __('Not yet frozen — save the offer to capture a rate.') }}
            </div>
            <div v-if="doc.rate_frozen_at" class="lcsod-fx-stamp">
              {{ __('Captured') }} {{ formatDateTime(doc.rate_frozen_at) }}
            </div>
          </div>

          <!-- Live card -->
          <div class="lcsod-fx lcsod-fx--live">
            <div class="flex items-center justify-between">
              <div class="lcsod-fx-cap lcsod-fx-cap--live">
                {{ __('Live (Frankfurter.dev · ECB)') }}
              </div>
              <span
                v-if="fxDeltaPct != null"
                class="lcsod-delta"
                :data-tone="fxDeltaPct >= 0 ? 'success' : 'danger'"
              >
                {{ fxDeltaPct >= 0 ? '+' : '' }}{{ fxDeltaPct.toFixed(2) }}%
              </span>
            </div>
            <div class="lcsod-fx-val">
              {{ liveValueEur != null ? formatCurrency(liveValueEur) : '—' }}
              <span class="lcsod-fx-ccy">EUR</span>
            </div>
            <div class="lcsod-fx-note">
              {{ liveRateValue != null
                  ? `1 ${doc.currency} = ${Number(liveRateValue).toFixed(4)} EUR`
                  : (liveRate.loading ? __('Fetching…') : __('Live rate unavailable.')) }}
            </div>
          </div>
        </div>
      </div>

      <!-- Status timeline -->
      <div class="lcsod-card">
        <div class="lcsod-card-title mb-3">
          <FeatherIcon name="activity" class="h-3 w-3" />
          {{ __('Status Flow') }}
        </div>
        <div class="flex items-center gap-1 overflow-x-auto">
          <template v-for="(s, i) in statusFlow" :key="s">
            <button
              class="flex shrink-0 flex-col items-center gap-1 px-2"
              @click="changeStatus(s)"
              :disabled="s === doc.status"
            >
              <div class="lcsod-node" :data-state="statusFlowState(s)">
                <FeatherIcon v-if="statusFlowIdx(s) <= statusFlowIdx(doc.status)" name="check" class="h-4 w-4" />
                <span v-else class="text-[10px]">{{ i + 1 }}</span>
              </div>
              <span class="lcsod-node-label" :data-current="s === doc.status ? 'true' : 'false'">
                {{ __(s) }}
              </span>
            </button>
            <div v-if="i < statusFlow.length - 1" class="lcsod-node-link" />
          </template>
        </div>
      </div>

      <!-- ERPNext links -->
      <div v-if="doc.erpnext_quotation || doc.erpnext_sales_order" class="lcsod-card">
        <div class="lcsod-card-title mb-2">
          <FeatherIcon name="git-branch" class="h-3 w-3" />
          {{ __('ERPNext Artefacts') }}
        </div>
        <div class="flex flex-wrap gap-2">
          <ErpNextDeepLink v-if="doc.erpnext_quotation" doctype="Quotation" :name="doc.erpnext_quotation" :label="__('Quotation') + ': ' + doc.erpnext_quotation" />
          <ErpNextDeepLink v-if="doc.erpnext_sales_order" doctype="Sales Order" :name="doc.erpnext_sales_order" :label="__('Sales Order') + ': ' + doc.erpnext_sales_order" />
        </div>
      </div>

      <!-- Notes -->
      <div class="lcsod-card lcsod-notes">
        <div class="mb-2 flex items-center justify-between">
          <div class="lcsod-notes-title">
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
              class="lcsod-textarea"
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
        <div v-else-if="doc.notes" class="lcsod-notes-body" v-html="doc.notes" />
        <div v-else class="lcsod-notes-empty">{{ __('No notes yet.') }}</div>
      </div>

      <!-- Won/Lost reason — only shown when relevant -->
      <div v-if="doc.status === 'Rejected' || doc.status === 'Accepted'" class="lcsod-card">
        <InlineField
          :label="doc.status === 'Accepted' ? __('Won Notes') : __('Lost Reason')"
          :value="doc.won_lost_reason"
          type="textarea"
          @save="save('won_lost_reason', $event)"
        />
      </div>

      <!-- Angebot-Versionen (PDF-Upload + Versionshistorie) -->
      <div class="lcsod-card">
        <div class="lcsod-card-title mb-2 flex items-center justify-between">
          <span class="flex items-center gap-1">
            <FeatherIcon name="file-text" class="h-3 w-3" />
            {{ __('Offer versions') }} ({{ attachments.data?.length || 0 }})
          </span>
          <button class="lcsod-upl" :disabled="uploading" @click="triggerOfferUpload">
            <FeatherIcon name="upload" class="h-3.5 w-3.5" />
            {{ uploading ? __('Uploading …') : __('Upload PDF') }}
          </button>
          <input ref="offerFileInput" type="file" accept="application/pdf" class="hidden" @change="onOfferFile" />
        </div>
        <ul v-if="attachments.data?.length" class="lcsod-files">
          <li v-for="f in attachments.data" :key="f.name">
            <span class="lcsod-ver">v{{ versionOf(f) }}</span>
            <a :href="f.file_url" target="_blank" rel="noopener" class="lcsod-file-link">
              {{ f.file_name || f.file_url }}
            </a>
            <span class="lcsod-file-size">{{ (f.file_size / 1024).toFixed(0) }} KB · {{ formatDate(f.creation) }}</span>
          </li>
        </ul>
        <p v-else class="text-xs text-gray-400">{{ __('No offer PDF uploaded yet.') }}</p>
      </div>

      <!-- Kommentare -->
      <div class="lcsod-card">
        <div class="lcsod-card-title mb-2">
          <FeatherIcon name="message-square" class="h-3 w-3" />
          {{ __('Comments') }} ({{ comments.data?.length || 0 }})
        </div>
        <ul v-if="comments.data?.length" class="lcsod-comments">
          <li v-for="c in comments.data" :key="c.name" class="lcsod-comment">
            <div class="lcsod-comment-meta">{{ c.comment_by || c.owner }} · {{ relTime(c.creation) }}</div>
            <div class="lcsod-comment-body" v-html="c.content" />
          </li>
        </ul>
        <div class="mt-2 flex gap-2">
          <textarea v-model="newComment" rows="2" class="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm" :placeholder="__('Write a comment …')" />
          <button class="lcsod-upl self-end" :disabled="!newComment.trim() || postingComment" @click="postComment">{{ __('Post') }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  createDocumentResource, createListResource, createResource,
  Breadcrumbs, Button, Dropdown, FeatherIcon, toast,
} from 'frappe-ui'
import LayoutHeader from '@/components/LayoutHeader.vue'
import VoiceInput from '@/components/lcs/VoiceInput.vue'
import ErpNextDeepLink from '@/components/lcs/ErpNextDeepLink.vue'
import MoneyDual from '@/components/lcs/MoneyDual.vue'
import PpEmptyState from '@/components/pp/PpEmptyState.vue'
import IconAlertCircle from '~icons/lucide/alert-circle'

// Inline-editable field — click to edit, blur to save
const InlineField = {
  props: ['label', 'value', 'type', 'format', 'suffix', 'warning'],
  emits: ['save'],
  template: `
    <div class="lcsod-ifield" :class="{ 'lcsod-ifield--warn': warning }">
      <div class="lcsod-ifield-cap">{{ label }}</div>
      <div v-if="!editing" @click="startEdit" class="lcsod-ifield-val" :class="{ 'lcsod-ifield-val--empty': !value }">
        {{ value ? displayValue : '— click to set —' }}
      </div>
      <div v-else class="mt-1 flex gap-1">
        <input
          ref="input"
          v-model="editValue"
          :type="type || 'text'"
          class="lcsod-ifield-input"
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

// Live FX rate via Frankfurter.dev (cached server-side, 6h TTL).
// Re-fetches whenever the document's currency changes.
const liveRate = createResource({
  url: 'lcs_integrations.currency.api.get_live_rate',
  makeParams: () => ({ from_ccy: doc.value.currency || 'EUR', to_ccy: 'EUR' }),
  auto: false,
})
watch(
  () => doc.value.currency,
  (ccy) => {
    if (ccy && ccy !== 'EUR') liveRate.reload()
  },
  { immediate: true },
)
const liveRateValue = computed(() => liveRate.data?.rate ?? null)
const liveValueEur = computed(() => {
  if (liveRateValue.value == null || doc.value.value == null) return null
  return Math.round(Number(doc.value.value) * liveRateValue.value * 100) / 100
})
const fxDeltaPct = computed(() => {
  const frozen = doc.value.value_eur
  const live = liveValueEur.value
  if (!frozen || live == null) return null
  return ((live - frozen) / frozen) * 100
})

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

// Attachments = Angebot-Versionen (PDF-Upload + Versionshistorie)
const attachments = createListResource({
  doctype: 'File',
  filters: { attached_to_doctype: 'LCS Offer', attached_to_name: props.id },
  fields: ['name', 'file_url', 'file_name', 'file_size', 'creation'],
  orderBy: 'creation desc',
  pageLength: 50,
  auto: true,
})
// Version number = position in creation-ascending order (oldest = v1).
const versionMap = computed(() => {
  const asc = [...(attachments.data || [])].sort((a, b) => String(a.creation).localeCompare(String(b.creation)))
  const m = {}
  asc.forEach((f, i) => { m[f.name] = i + 1 })
  return m
})
function versionOf(f) { return versionMap.value[f.name] || '?' }

const offerFileInput = ref(null)
const uploading = ref(false)
function triggerOfferUpload() { offerFileInput.value?.click() }
async function onOfferFile(ev) {
  const file = ev.target.files?.[0]
  ev.target.value = ''
  if (!file) return
  uploading.value = true
  try {
    const form = new FormData()
    form.append('file', file, file.name)
    form.append('is_private', '1')
    form.append('folder', 'Home/Attachments')
    form.append('doctype', 'LCS Offer')
    form.append('docname', props.id)
    form.append('attached_to_doctype', 'LCS Offer')
    form.append('attached_to_name', props.id)
    const csrf = window.csrf_token || ''
    const res = await window.fetch('/api/method/upload_file', {
      method: 'POST', credentials: 'include',
      headers: csrf ? { 'X-Frappe-CSRF-Token': csrf } : {},
      body: form,
    })
    if (!res.ok) throw new Error(__('Upload failed:') + ' ' + res.status)
    toast({ title: __('Offer PDF uploaded'), icon: 'check-circle', iconClasses: 'text-green-500' })
    attachments.reload()
  } catch (err) {
    toast({ title: __('Could not attach PDF'), text: err?.message || '', icon: 'alert-circle', iconClasses: 'text-red-500' })
  } finally {
    uploading.value = false
  }
}

// Kommentare (echtes Frappe-Comment-System)
const comments = createListResource({
  doctype: 'Comment',
  filters: { reference_doctype: 'LCS Offer', reference_name: props.id, comment_type: 'Comment' },
  fields: ['name', 'content', 'comment_by', 'owner', 'creation'],
  orderBy: 'creation desc',
  pageLength: 50,
  auto: true,
})
const newComment = ref('')
const postingComment = ref(false)
async function postComment() {
  const text = newComment.value.trim()
  if (!text) return
  postingComment.value = true
  try {
    await createResource({ url: 'frappe.client.insert' }).submit({
      doc: {
        doctype: 'Comment', comment_type: 'Comment',
        reference_doctype: 'LCS Offer', reference_name: props.id,
        content: text,
      },
    })
    newComment.value = ''
    comments.reload()
  } catch (err) {
    toast({ title: __('Could not post comment'), text: err?.messages?.[0] || '', icon: 'alert-circle', iconClasses: 'text-red-500' })
  } finally {
    postingComment.value = false
  }
}
function relTime(v) {
  if (!v) return ''
  const d = new Date(String(v).replace(' ', 'T')).getTime()
  if (isNaN(d)) return String(v)
  const min = Math.floor((Date.now() - d) / 60000)
  if (min < 1) return __('just now')
  if (min < 60) return `vor ${min} Min.`
  const h = Math.floor(min / 60)
  if (h < 24) return `vor ${h} Std.`
  return new Intl.DateTimeFormat('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric' }).format(d)
}

// --- Style helpers (token-based tones) ---
const TONE_VAR = {
  neutral: 'var(--pp-text-tertiary)', info: 'var(--pp-state-info)', brand: 'var(--pp-brand-primary)',
  success: 'var(--pp-state-success)', warning: 'var(--pp-state-warning)', danger: 'var(--pp-state-danger)',
}
function statusTone(s) {
  return {
    Draft: 'neutral', Sent: 'info', 'In Review': 'brand', Accepted: 'success',
    Rejected: 'danger', Expired: 'neutral', Revised: 'warning',
  }[s] || 'neutral'
}
function statusDotStyle(s) {
  return { background: TONE_VAR[statusTone(s)] }
}
function statusFlowState(s) {
  const idx = statusFlowIdx(s)
  const cur = statusFlowIdx(doc.value.status)
  if (s === doc.value.status) return 'current'
  if (idx < cur) return 'done'
  return 'todo'
}

function formatCurrency(v) {
  return new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(v || 0)
}
function formatDate(d) {
  if (!d) return ''
  return new Intl.DateTimeFormat('de-DE', { day: '2-digit', month: 'short', year: 'numeric' }).format(new Date(d))
}
function formatDateTime(d) {
  if (!d) return ''
  return new Intl.DateTimeFormat('de-DE', {
    day: '2-digit', month: 'short', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  }).format(new Date(d))
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

<style scoped>
/* ---- Pilanda design system (token-only) ------------------------------- */
.lcsod { background: var(--pp-bg-base); }
.lcsod-inner { max-width: 64rem; margin: 0 auto; padding: var(--pp-space-5);
  display: flex; flex-direction: column; gap: var(--pp-space-5); }
.lcsod-center { display: flex; height: 100%; align-items: center; justify-content: center; }
.lcsod-spinner { width: 32px; height: 32px; border-radius: var(--pp-radius-full);
  border: 2px solid var(--pp-border-subtle); border-top-color: var(--pp-brand-primary);
  animation: lcsod-spin 0.7s linear infinite; }
@keyframes lcsod-spin { to { transform: rotate(360deg); } }

/* Hero */
.lcsod-hero { border: 1px solid var(--pp-border-subtle); border-radius: var(--pp-radius-ui);
  background: linear-gradient(90deg, var(--pp-bg-surface), var(--pp-bg-sunken));
  padding: var(--pp-space-5); box-shadow: var(--pp-shadow-xs); }
.lcsod-title { margin: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
  font-size: var(--pp-fs-20); font-weight: var(--pp-weight-bold); color: var(--pp-text-primary);
  font-family: var(--pp-font-heading); }
.lcsod-ver { border-radius: var(--pp-radius-full); background: var(--pp-bg-sunken);
  padding: 2px var(--pp-space-2); font-size: 11px; font-weight: var(--pp-weight-bold);
  color: var(--pp-text-secondary); font-variant-numeric: tabular-nums; }
.lcsod-project { font-family: ui-monospace, monospace; color: var(--pp-text-tertiary); text-decoration: none; }
.lcsod-project:hover { color: var(--pp-brand-primary); text-decoration: underline; }
.lcsod-sep { color: var(--pp-border-strong); }
.lcsod-id { font-family: ui-monospace, monospace; font-size: var(--pp-fs-12); color: var(--pp-text-tertiary); }
.lcsod-nomoney { font-size: var(--pp-fs-24); font-weight: var(--pp-weight-bold); color: var(--pp-text-tertiary); }
.lcsod-prob { font-size: 10px; text-transform: uppercase; color: var(--pp-text-tertiary); }

/* Token pill (status) */
.lcsod-pill { display: inline-flex; align-items: center; gap: 6px; font-size: var(--pp-fs-13, 13px);
  font-weight: var(--pp-weight-semibold); padding: 4px var(--pp-space-3); border-radius: var(--pp-radius-full); }
.lcsod-dot { width: 8px; height: 8px; border-radius: var(--pp-radius-full); flex-shrink: 0; background: currentColor; }
.lcsod-pill[data-tone="info"]    { background: color-mix(in oklab, var(--pp-state-info) 14%, transparent);    color: var(--pp-state-info); }
.lcsod-pill[data-tone="brand"]   { background: color-mix(in oklab, var(--pp-brand-primary) 14%, transparent); color: var(--pp-brand-primary); }
.lcsod-pill[data-tone="success"] { background: color-mix(in oklab, var(--pp-state-success) 16%, transparent); color: var(--pp-state-success); }
.lcsod-pill[data-tone="warning"] { background: color-mix(in oklab, var(--pp-state-warning) 16%, transparent); color: var(--pp-state-warning); }
.lcsod-pill[data-tone="danger"]  { background: color-mix(in oklab, var(--pp-state-danger) 16%, transparent);  color: var(--pp-state-danger); }
.lcsod-pill[data-tone="neutral"] { background: var(--pp-bg-sunken); color: var(--pp-text-secondary); }

/* Cards */
.lcsod-card { background: var(--pp-bg-surface); border: 1px solid var(--pp-border-subtle);
  border-radius: var(--pp-radius-ui); box-shadow: var(--pp-shadow-xs); padding: var(--pp-space-4); }
.lcsod-card-title { display: flex; align-items: center; gap: var(--pp-space-2); font-size: var(--pp-fs-12);
  font-weight: var(--pp-weight-bold); letter-spacing: 0.04em; text-transform: uppercase; color: var(--pp-text-tertiary); }

/* FX subcards */
.lcsod-fx { border-radius: var(--pp-radius-ui); padding: var(--pp-space-3); border: 1px solid var(--pp-border-subtle); }
.lcsod-fx--frozen { background: var(--pp-bg-sunken); }
.lcsod-fx--live { border-color: color-mix(in oklab, var(--pp-brand-primary) 30%, transparent);
  background: color-mix(in oklab, var(--pp-brand-primary) 6%, transparent); }
.lcsod-fx-cap { font-size: 10px; font-weight: var(--pp-weight-bold); letter-spacing: 0.06em;
  text-transform: uppercase; color: var(--pp-text-tertiary); }
.lcsod-fx-cap--live { color: var(--pp-brand-primary); }
.lcsod-fx-val { margin-top: var(--pp-space-1); font-size: var(--pp-fs-18); font-weight: var(--pp-weight-semibold);
  color: var(--pp-text-primary); font-variant-numeric: tabular-nums; }
.lcsod-fx-ccy { margin-left: var(--pp-space-1); font-size: var(--pp-fs-12); font-weight: var(--pp-weight-regular); color: var(--pp-text-tertiary); }
.lcsod-fx-note { margin-top: var(--pp-space-1); font-size: var(--pp-fs-12); color: var(--pp-text-secondary); }
.lcsod-fx-stamp { margin-top: 2px; font-size: 10px; color: var(--pp-text-tertiary); }
.lcsod-delta { border-radius: var(--pp-radius-full); padding: 2px var(--pp-space-2); font-size: 10px;
  font-weight: var(--pp-weight-semibold); font-variant-numeric: tabular-nums; }
.lcsod-delta[data-tone="success"] { background: color-mix(in oklab, var(--pp-state-success) 18%, transparent); color: var(--pp-state-success); }
.lcsod-delta[data-tone="danger"]  { background: color-mix(in oklab, var(--pp-state-danger) 18%, transparent);  color: var(--pp-state-danger); }

/* Status flow nodes */
.lcsod-node { width: 32px; height: 32px; border-radius: var(--pp-radius-full);
  display: flex; align-items: center; justify-content: center; }
.lcsod-node[data-state="current"] { background: var(--pp-brand-primary); color: var(--pp-text-on-accent);
  box-shadow: 0 0 0 3px color-mix(in oklab, var(--pp-brand-primary) 30%, transparent); }
.lcsod-node[data-state="done"] { background: var(--pp-state-success); color: var(--pp-text-on-accent); }
.lcsod-node[data-state="todo"] { background: var(--pp-bg-sunken); color: var(--pp-text-tertiary); }
.lcsod-node-label { font-size: 10px; font-weight: var(--pp-weight-medium); color: var(--pp-text-tertiary); }
.lcsod-node-label[data-current="true"] { color: var(--pp-text-primary); }
.lcsod-node-link { height: 1px; width: 24px; flex-shrink: 0; background: var(--pp-border-default); }

/* Notes */
.lcsod-notes { border-color: color-mix(in oklab, var(--pp-state-warning) 30%, transparent);
  background: color-mix(in oklab, var(--pp-state-warning) 7%, transparent); }
.lcsod-notes-title { display: flex; align-items: center; gap: var(--pp-space-2); font-size: var(--pp-fs-14);
  font-weight: var(--pp-weight-semibold); color: var(--pp-state-warning); }
.lcsod-textarea { width: 100%; border-radius: var(--pp-radius-ui);
  border: 1px solid color-mix(in oklab, var(--pp-state-warning) 40%, transparent);
  background: var(--pp-bg-surface); padding: var(--pp-space-2) var(--pp-space-3); padding-right: 40px;
  font-size: var(--pp-fs-14); color: var(--pp-text-primary); }
.lcsod-textarea:focus { outline: none; border-color: var(--pp-brand-primary); }
.lcsod-notes-body { white-space: pre-wrap; font-size: var(--pp-fs-14); color: var(--pp-text-primary); }
.lcsod-notes-empty { font-size: var(--pp-fs-14); font-style: italic; color: color-mix(in oklab, var(--pp-state-warning) 70%, var(--pp-text-tertiary)); }

/* Attachments */
.lcsod-files { margin: 0; padding: 0; list-style: none; display: flex; flex-direction: column; gap: 4px; font-size: var(--pp-fs-14); }
.lcsod-files li { display: flex; align-items: center; gap: var(--pp-space-2); }
.lcsod-file-ico { width: 14px; height: 14px; color: var(--pp-text-tertiary); }
.lcsod-file-link { color: var(--pp-brand-primary); text-decoration: none; }
.lcsod-file-link:hover { text-decoration: underline; }
.lcsod-file-size { font-size: var(--pp-fs-12); color: var(--pp-text-tertiary); }
.lcsod-upl { appearance: none; cursor: pointer; font-family: inherit; font-size: var(--pp-fs-12);
  display: inline-flex; align-items: center; gap: 5px; padding: 5px 10px; border-radius: var(--pp-radius-ui);
  border: 1px solid var(--pp-brand-primary); background: var(--pp-brand-primary); color: var(--pp-text-on-accent); }
.lcsod-upl:hover:not(:disabled) { filter: brightness(1.05); }
.lcsod-upl:disabled { opacity: 0.6; cursor: default; }
.lcsod-ver { flex-shrink: 0; font-size: 11px; font-weight: var(--pp-weight-bold); font-variant-numeric: tabular-nums;
  color: var(--pp-text-on-accent); background: var(--pp-brand-primary); padding: 1px 7px; border-radius: var(--pp-radius-full); }
.lcsod-comments { margin: 0 0 var(--pp-space-2); padding: 0; list-style: none; display: flex; flex-direction: column; gap: var(--pp-space-3); }
.lcsod-comment { border-bottom: 1px solid var(--pp-border-subtle); padding-bottom: var(--pp-space-2); }
.lcsod-comment:last-child { border-bottom: 0; }
.lcsod-comment-meta { font-size: 11px; color: var(--pp-text-tertiary); margin-bottom: 2px; }
.lcsod-comment-body { font-size: var(--pp-fs-13, 13px); color: var(--pp-text-primary); }
</style>

<style>
/* InlineField renders from a runtime string template, so scoped CSS can't
   reach it — these rules are intentionally global (namespaced lcsod-ifield). */
.lcsod-ifield { border-radius: var(--pp-radius-ui); border: 1px solid var(--pp-border-subtle);
  background: var(--pp-bg-surface); padding: var(--pp-space-3); transition: box-shadow 0.15s ease; }
.lcsod-ifield:hover { box-shadow: var(--pp-shadow-sm); }
.lcsod-ifield--warn { border-color: color-mix(in oklab, var(--pp-state-danger) 40%, transparent);
  background: color-mix(in oklab, var(--pp-state-danger) 8%, transparent); }
.lcsod-ifield-cap { font-size: 10px; font-weight: var(--pp-weight-bold); letter-spacing: 0.06em;
  text-transform: uppercase; color: var(--pp-text-tertiary); }
.lcsod-ifield-val { margin-top: var(--pp-space-1); cursor: pointer; font-size: var(--pp-fs-14);
  font-weight: var(--pp-weight-medium); color: var(--pp-text-primary); }
.lcsod-ifield-val--empty { color: var(--pp-text-tertiary); font-style: italic; }
.lcsod-ifield-input { width: 100%; border-radius: var(--pp-radius-ui); border: 1px solid var(--pp-border-default);
  padding: 4px var(--pp-space-2); font-size: var(--pp-fs-14); background: var(--pp-bg-base); color: var(--pp-text-primary); }
.lcsod-ifield-input:focus { outline: none; border-color: var(--pp-brand-primary); }
</style>
