<!--
  LCSLead — CRM-Interessenten-DETAILSEITE (V2, Showcase „Lead-Detail").
  ============================================================
  Pilanda-UX für die Detailansicht eines „Interessenten" (CRM Lead). Ersetzt
  Dominiks Lead.vue als Route 'Lead' (/leads/:leadId); die Original-Seite bleibt
  als 'Lead Upstream' (/leads-upstream/:leadId) über den Knopf „Vollansicht
  öffnen" erreichbar — dort leben E-Mail-Composer, Telefonie und WhatsApp,
  die HIER bewusst NICHT nachgebaut werden.

  Aufbau (Vollbreiten-Canvas, token-only, aus echten Pp*-Bausteinen):
    · PpPageHead   — Eyebrow „Sales / CRM" + Titel = Interessenten-Name,
                     daneben Status-Pille MIT Wechsel-Menü (CRM Lead Status,
                     persistiert per frappe.client.set_value, fail-loud).
    · Kopf-Aktionen: „In Verkaufschance umwandeln" (Dominiks ConvertToDealModal,
                     unverändert → convert_to_deal-API + Navigation zum Deal)
                     und „Vollansicht öffnen" (Upstream-Fallback).
    · Links  — Stammdaten-Karten (Person / Firma / Zuordnung). Einfache
               Textfelder inline editierbar (set_value); Links/Meta read-only.
               Felder werden NUR gezeigt, wenn im DocType vorhanden (defensiv).
    · Rechts — Aktivitäts-Verlauf über PpTimeline: Kommentare + Notizen +
               Verlaufs-Ereignisse (Anlage/Feldänderungen), chronologisch,
               LESEND. Darunter ein Kommentar-Eingabefeld, das über Dominiks
               Kommentar-API (crm.api.comment.add_comment) speichert.

  Datenquellen (Dominiks CRM-Backend, unverändert):
    · Lead-Dokument → frappe.client.get            ('CRM Lead')
    · Status-Liste  → CRM Lead Status              (statusesStore)
    · Aktivitäten   → crm.api.activities.get_activities
    · Kommentar neu → crm.api.comment.add_comment
    · Feld ändern   → frappe.client.set_value
-->

<template>
  <div class="flex h-full flex-col">
    <LayoutHeader>
      <template #left-header>
        <Breadcrumbs :items="breadcrumbs" />
      </template>
      <template #right-header>
        <Button :label="__('Refresh')" iconLeft="refresh-cw" @click="reload" :loading="leadRes.loading" />
      </template>
    </LayoutHeader>

    <div class="lcl">
      <!-- Ladezustand / Fehler ehrlich anzeigen -->
      <div v-if="loadError" class="lcl-state">
        <h2 class="lcl-state-title">{{ __('Document not found') }}</h2>
        <p class="lcl-state-hint">{{ loadError }}</p>
        <button class="lcl-btn" @click="goToList">{{ __('Leads') }}</button>
      </div>
      <div v-else-if="!doc.name && leadRes.loading" class="lcl-state">
        <p class="lcl-state-hint">{{ __('Loading …') }}</p>
      </div>

      <div v-else-if="doc.name" class="lcl-inner">
        <PpPageHead :eyebrow="__('Sales / CRM')" :title="title">
          <template #actions>
            <!-- Status-Pille MIT Wechsel-Menü (persistiert per set_value) -->
            <div class="lcl-status">
              <button
                class="lcl-pill"
                :data-tone="statusTone(doc.status)"
                :disabled="savingStatus"
                @click="statusMenuOpen = !statusMenuOpen"
              >
                <i class="lcl-dot"></i>
                <span>{{ doc.status ? __(doc.status) : __('Status') }}</span>
                <IconChevronDown class="lcl-pill-caret" />
              </button>
              <template v-if="statusMenuOpen">
                <div class="lcl-menu-backdrop" @click="statusMenuOpen = false"></div>
                <ul class="lcl-menu" role="menu">
                  <li v-for="s in leadStatusList" :key="s.name">
                    <button
                      class="lcl-menu-item"
                      :class="{ 'is-active': s.name === doc.status }"
                      role="menuitem"
                      @click="changeStatus(s.name)"
                    >
                      <i class="lcl-dot" :data-tone="statusTone(s.name)"></i>
                      <span>{{ __(s.name) }}</span>
                      <IconCheck v-if="s.name === doc.status" class="lcl-menu-check" />
                    </button>
                  </li>
                </ul>
              </template>
            </div>

            <Button
              variant="solid"
              :label="__('Convert to deal')"
              iconLeft="git-pull-request"
              @click="showConvert = true"
            />
            <Button
              :label="__('Open full view')"
              iconLeft="external-link"
              @click="openFullView"
            />
          </template>
        </PpPageHead>

        <div class="lcl-grid">
          <!-- LINKS: Stammdaten -->
          <div class="lcl-col">
            <section v-for="group in fieldGroups" :key="group.title" class="lcl-card">
              <h3 class="lcl-card-title">{{ group.title }}</h3>
              <dl class="lcl-fields">
                <div v-for="f in group.fields" :key="f.key" class="lcl-field">
                  <dt class="lcl-field-label">{{ f.label }}</dt>
                  <dd class="lcl-field-value">
                    <!-- Inline-Edit für einfache Textfelder -->
                    <input
                      v-if="f.editable && editingField === f.key"
                      ref="editInput"
                      v-model="editValue"
                      class="lcl-input"
                      type="text"
                      @keydown.enter.prevent="saveEdit(f.key)"
                      @keydown.esc="cancelEdit"
                      @blur="saveEdit(f.key)"
                    />
                    <button
                      v-else-if="f.editable"
                      class="lcl-edit-trigger"
                      :class="{ 'is-empty': !doc[f.key] }"
                      :title="__('Click to edit')"
                      @click="startEdit(f.key)"
                    >
                      <span>{{ formatValue(f, doc[f.key]) }}</span>
                      <IconPencil class="lcl-edit-ico" />
                    </button>
                    <!-- Read-only (Links / Meta) -->
                    <span v-else :class="{ 'lcl-muted': !doc[f.key] }">
                      {{ formatValue(f, doc[f.key]) }}
                    </span>
                  </dd>
                </div>
              </dl>
            </section>
          </div>

          <!-- RECHTS: Aktivitäts-Verlauf -->
          <div class="lcl-col">
            <section class="lcl-card lcl-activity">
              <div class="lcl-activity-head">
                <h3 class="lcl-card-title">{{ __('Activities') }}</h3>
                <button
                  v-if="hasFullViewOnly"
                  class="lcl-link"
                  @click="openFullView"
                >
                  {{ __('Open full view') }}
                  <IconExternalLink class="lcl-link-ico" />
                </button>
              </div>

              <PpTimeline v-if="timelineItems.length" :items="timelineItems" />
              <p v-else-if="activitiesRes.loading" class="lcl-muted lcl-activity-empty">
                {{ __('Loading …') }}
              </p>
              <p v-else class="lcl-muted lcl-activity-empty">
                {{ __('No activities yet') }}
              </p>

              <p v-if="hasFullViewOnly" class="lcl-activity-note">
                {{ __('Emails, calls and tasks are shown in the full view.') }}
              </p>

              <!-- Kommentar-Eingabe (speichert über Dominiks Kommentar-API) -->
              <div class="lcl-comment">
                <textarea
                  v-model="newComment"
                  class="lcl-comment-input"
                  rows="3"
                  :placeholder="__('Write a comment …')"
                  :disabled="sendingComment"
                  @keydown.ctrl.enter="submitComment"
                  @keydown.meta.enter="submitComment"
                ></textarea>
                <div class="lcl-comment-actions">
                  <button
                    class="lcl-btn lcl-btn--primary"
                    :disabled="commentEmpty || sendingComment"
                    @click="submitComment"
                  >
                    <IconSend class="lcl-btn-ico" />
                    {{ sendingComment ? __('Sending comment...') : __('Add comment') }}
                  </button>
                </div>
              </div>
            </section>
          </div>
        </div>
      </div>
    </div>

    <!-- Dominiks Convert-Flow (unverändert): erzeugt den Deal via
         crm.fcrm.doctype.crm_lead.crm_lead.convert_to_deal und navigiert im
         Erfolgsfall zur Deal-Detailseite. -->
    <ConvertToDealModal v-if="showConvert && doc.name" v-model="showConvert" :lead="doc" />
  </div>
</template>

<script setup>
import { ref, computed, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import { call, createResource, toast, Breadcrumbs, Button } from 'frappe-ui'
import LayoutHeader from '@/components/LayoutHeader.vue'
import PpPageHead from '@/components/pp/PpPageHead.vue'
import PpTimeline from '@/components/pp/PpTimeline.vue'
import ConvertToDealModal from '@/components/Modals/ConvertToDealModal.vue'
import { statusesStore } from '@/stores/statuses'
import { usersStore } from '@/stores/users'
import IconChevronDown from '~icons/lucide/chevron-down'
import IconCheck from '~icons/lucide/check'
import IconPencil from '~icons/lucide/pencil'
import IconSend from '~icons/lucide/send-horizontal'
import IconExternalLink from '~icons/lucide/external-link'

const props = defineProps({
  leadId: { type: String, required: true },
})

const router = useRouter()
const statusStore = statusesStore()
const { getUser } = usersStore()

/* ---- Lead-Dokument LIVE laden (Dominiks Backend, unverändert) -------- */
const leadRes = createResource({
  url: 'frappe.client.get',
  makeParams: () => ({ doctype: 'CRM Lead', name: props.leadId }),
  auto: true,
})
const doc = computed(() => leadRes.data || {})
const loadError = computed(() => {
  const e = leadRes.error
  if (!e) return ''
  return e.messages?.[0] || e.message || __('An error occurred')
})
function reload() {
  leadRes.reload()
  activitiesRes.reload()
}

/* ---- Anzeige-Helfer -------------------------------------------------- */
function displayName(l) {
  return (
    l.lead_name ||
    [l.first_name, l.last_name].filter(Boolean).join(' ') ||
    l.organization ||
    l.name ||
    ''
  )
}
const title = computed(() => displayName(doc.value) || props.leadId)

function userName(email) {
  return email ? getUser(email)?.full_name || email : '—'
}
function fmtDateTime(v) {
  if (!v) return '—'
  const d = new Date(v)
  if (isNaN(d)) return String(v)
  return d.toLocaleString('de-DE', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}
function timeAgo(v) {
  if (!v) return ''
  const d = new Date(v)
  if (isNaN(d)) return String(v)
  const sec = Math.round((Date.now() - d.getTime()) / 1000)
  if (sec < 60) return __('just now')
  const min = Math.round(sec / 60)
  if (min < 60) return __('{0} min ago', [min])
  const hrs = Math.round(min / 60)
  if (hrs < 24) return __('{0} h ago', [hrs])
  const days = Math.round(hrs / 24)
  if (days < 30) return __('{0} d ago', [days])
  return d.toLocaleDateString('de-DE')
}
function stripHtml(html) {
  if (!html) return ''
  try {
    return (new DOMParser().parseFromString(html, 'text/html').body.textContent || '').trim()
  } catch (e) {
    return String(html)
  }
}

/* ---- Stammdaten-Felder (defensiv: nur zeigen, was der DocType hat) ---- */
// Feldkatalog des geladenen Dokuments (Frappe liefert nur vorhandene Felder).
function hasField(key) {
  return Object.prototype.hasOwnProperty.call(doc.value, key)
}
const FIELD_DEFS = {
  first_name:  { label: __('First name'),  editable: true },
  last_name:   { label: __('Last name'),   editable: true },
  job_title:   { label: __('Position'),    editable: true },
  email:       { label: __('Email'),       editable: true, type: 'email' },
  mobile_no:   { label: __('Mobile'),      editable: true },
  phone:       { label: __('Phone'),       editable: true },
  organization:{ label: __('Organization'),editable: true },
  website:     { label: __('Website'),     editable: true },
  territory:   { label: __('Territory'),   editable: true },
  industry:    { label: __('Industry'),    editable: true },
  source:      { label: __('Source'),      editable: false },
  lead_owner:  { label: __('Lead owner'),  editable: false, type: 'user' },
  creation:    { label: __('Created'),     editable: false, type: 'datetime' },
  modified:    { label: __('Last modified'), editable: false, type: 'datetime' },
}
function buildGroup(title, keys) {
  const fields = keys
    .filter((k) => hasField(k))
    .map((k) => ({ key: k, ...FIELD_DEFS[k] }))
  return { title, fields }
}
const fieldGroups = computed(() => {
  return [
    buildGroup(__('Person'), ['first_name', 'last_name', 'job_title', 'email', 'mobile_no', 'phone']),
    buildGroup(__('Company'), ['organization', 'website', 'territory', 'industry']),
    buildGroup(__('Assignment'), ['source', 'lead_owner', 'creation', 'modified']),
  ].filter((g) => g.fields.length)
})
function formatValue(f, value) {
  if (value == null || value === '') return '—'
  if (f.type === 'user') return userName(value)
  if (f.type === 'datetime') return fmtDateTime(value)
  return String(value)
}

/* ---- Inline-Edit einfacher Textfelder (set_value, fail-loud) --------- */
const editingField = ref(null)
const editValue = ref('')
const editInput = ref(null)
function startEdit(key) {
  editingField.value = key
  editValue.value = doc.value[key] ?? ''
  nextTick(() => {
    const el = Array.isArray(editInput.value) ? editInput.value[0] : editInput.value
    el?.focus?.()
    el?.select?.()
  })
}
function cancelEdit() {
  editingField.value = null
  editValue.value = ''
}
async function saveEdit(key) {
  // Blur nach ESC (editingField bereits null) darf nicht doppelt speichern.
  if (editingField.value !== key) return
  const next = editValue.value
  const prev = doc.value[key] ?? ''
  editingField.value = null
  if (next === prev) return
  // Optimistisch anzeigen, dann persistieren.
  const original = { ...leadRes.data }
  leadRes.data[key] = next
  try {
    await call('frappe.client.set_value', {
      doctype: 'CRM Lead',
      name: doc.value.name,
      fieldname: key,
      value: next,
    })
    toast.success(__('Saved'))
    activitiesRes.reload()
  } catch (e) {
    leadRes.data[key] = original[key] // Rollback
    toast.error(e?.messages?.[0] || e?.message || __('Error updating field'))
  }
}

/* ---- Status-Pille + Wechsel-Menü ------------------------------------- */
const statusMenuOpen = ref(false)
const savingStatus = ref(false)
const leadStatusList = computed(() => statusStore.leadStatuses.data || [])

// Frappe-Farbnamen → pp-Tonwert (token-only Pillen, keine Hex). Deckungsgleich
// mit LCSLeads, damit Liste und Detail dieselbe Statusfarbe zeigen.
const COLOR_TONE = {
  green: 'success', teal: 'success', lime: 'success',
  blue: 'info', cyan: 'info', sky: 'info', 'light-blue': 'info',
  indigo: 'brand', purple: 'brand', violet: 'brand',
  red: 'danger', pink: 'danger',
  orange: 'warning', amber: 'warning', yellow: 'warning',
  gray: 'neutral', grey: 'neutral', black: 'neutral',
}
function statusTone(name) {
  const s = leadStatusList.value.find((x) => x.name === name)
  const raw = (s?.color || '').toString().toLowerCase()
  return COLOR_TONE[raw] || 'neutral'
}
async function changeStatus(name) {
  statusMenuOpen.value = false
  if (!name || name === doc.value.status) return
  savingStatus.value = true
  const prev = doc.value.status
  leadRes.data.status = name // optimistisch
  try {
    await call('frappe.client.set_value', {
      doctype: 'CRM Lead',
      name: doc.value.name,
      fieldname: 'status',
      value: name,
    })
    toast.success(__('Status updated'))
    activitiesRes.reload()
  } catch (e) {
    leadRes.data.status = prev // Rollback
    toast.error(e?.messages?.[0] || e?.message || __('Could not save. Please try again.'))
  } finally {
    savingStatus.value = false
  }
}

/* ---- Aktivitäten (LESEND) ------------------------------------------- */
// Dieselbe API wie Dominiks Activities.vue; Rückgabe ist ein Tuple, das wir
// in ein benanntes Objekt transformieren.
const activitiesRes = createResource({
  url: 'crm.api.activities.get_activities',
  makeParams: () => ({ name: props.leadId }),
  auto: true,
  transform: ([versions, calls, notes, tasks, attachments]) => ({
    versions: versions || [],
    calls: calls || [],
    notes: notes || [],
    tasks: tasks || [],
    attachments: attachments || [],
  }),
})

// Timeline = Kommentare + Notizen + Verlaufs-Ereignisse (Anlage/Feldänderung),
// chronologisch (neueste zuerst). E-Mails/Anrufe/Aufgaben/WhatsApp bleiben der
// Vollansicht vorbehalten (nicht nachgebaut).
const timelineItems = computed(() => {
  const data = activitiesRes.data
  if (!data) return []
  const items = []

  for (const v of data.versions) {
    if (v.activity_type === 'comment') {
      items.push({
        kind: 'note',
        subject: stripHtml(v.content) || __('Comment'),
        who: userName(v.owner),
        ago: timeAgo(v.creation),
        _ts: v.creation,
      })
    } else if (v.activity_type === 'creation') {
      items.push({
        kind: 'info',
        subject: typeof v.data === 'string' ? v.data : __('created this lead'),
        who: userName(v.owner),
        ago: timeAgo(v.creation),
        _ts: v.creation,
      })
    } else if (['changed', 'added', 'removed'].includes(v.activity_type)) {
      items.push({
        kind: 'info',
        subject: changeSubject(v),
        who: userName(v.owner),
        ago: timeAgo(v.creation),
        _ts: v.creation,
      })
    }
  }

  for (const n of data.notes) {
    items.push({
      kind: 'note',
      subject: n.title || stripHtml(n.content) || __('Note'),
      who: userName(n.owner),
      ago: timeAgo(n.creation || n.modified),
      _ts: n.creation || n.modified,
    })
  }

  return items.sort((a, b) => new Date(b._ts) - new Date(a._ts))
})
function changeSubject(v) {
  const d = v.data || {}
  const label = d.field_label || d.field || ''
  if (v.activity_type === 'added') return `${label}: ${d.value}`
  if (v.activity_type === 'removed') return `${label} ${__('removed')}`
  return `${label}: ${d.old_value ?? '—'} → ${d.value ?? '—'}`
}
// Gibt es Inhalte (E-Mails/Anrufe/Aufgaben), die nur die Vollansicht zeigt?
const hasFullViewOnly = computed(() => {
  const d = activitiesRes.data
  if (!d) return false
  const emails = (d.versions || []).some((v) => v.activity_type === 'communication')
  return emails || (d.calls?.length || 0) > 0 || (d.tasks?.length || 0) > 0
})

/* ---- Kommentar anlegen (Dominiks Kommentar-API) ---------------------- */
const newComment = ref('')
const sendingComment = ref(false)
const commentEmpty = computed(() => !newComment.value.trim())
async function submitComment() {
  if (commentEmpty.value || sendingComment.value) return
  sendingComment.value = true
  // Plain-Text → einfaches HTML (Zeilenumbrüche erhalten), wie die Kommentar-
  // Mechanik es erwartet (content ist HTML).
  const html = newComment.value
    .trim()
    .split('\n')
    .map((line) => `<div>${escapeHtml(line) || '<br>'}</div>`)
    .join('')
  try {
    await call('crm.api.comment.add_comment', {
      reference_doctype: 'CRM Lead',
      reference_name: doc.value.name,
      content: html,
    })
    newComment.value = ''
    toast.success(__('Comment sent'))
    activitiesRes.reload()
  } catch (e) {
    toast.error(e?.messages?.[0] || e?.message || __('Failed to send comment!'))
  } finally {
    sendingComment.value = false
  }
}
function escapeHtml(s) {
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
}

/* ---- Navigation ------------------------------------------------------ */
const breadcrumbs = computed(() => [
  { label: __('Leads'), route: { name: 'Leads' } },
  { label: title.value },
])
function goToList() {
  router.push({ name: 'Leads' })
}
function openFullView() {
  router.push({ name: 'Lead Upstream', params: { leadId: props.leadId } })
}

/* Menü schließen, wenn das Dokument wechselt. */
const showConvert = ref(false)
watch(() => props.leadId, () => {
  statusMenuOpen.value = false
  editingField.value = null
})
</script>

<style scoped>
/* Vollbreiten-Canvas — kein zentrierendes max-width (Shell-2.0-Vorgabe). */
.lcl { flex: 1; min-height: 0; overflow: auto; background: var(--pp-bg-base); }
.lcl-inner {
  display: flex; flex-direction: column; gap: var(--pp-space-5);
  padding: var(--pp-space-6) var(--pp-space-6) var(--pp-space-12);
}

/* Lade-/Fehlerzustand */
.lcl-state { display: flex; flex-direction: column; align-items: center; gap: var(--pp-space-3);
  padding: var(--pp-space-12) var(--pp-space-6); text-align: center; }
.lcl-state-title { margin: 0; font-family: var(--pp-font-heading); font-size: var(--pp-fs-20);
  font-weight: var(--pp-weight-semibold); color: var(--pp-text-primary); }
.lcl-state-hint { margin: 0; color: var(--pp-text-tertiary); font-size: var(--pp-fs-14); }

/* Buttons */
.lcl-btn { appearance: none; cursor: pointer; font-family: inherit; font-size: var(--pp-fs-13, 13px);
  display: inline-flex; align-items: center; gap: 6px;
  padding: 6px var(--pp-space-3); border-radius: var(--pp-radius-ui);
  border: 1px solid var(--pp-border-default); background: var(--pp-bg-surface); color: var(--pp-text-primary); }
.lcl-btn:hover:not(:disabled) { background: var(--pp-bg-hover); border-color: var(--pp-brand-primary); color: var(--pp-brand-primary); }
.lcl-btn:disabled { opacity: 0.55; cursor: default; }
.lcl-btn--primary { background: var(--pp-brand-primary); border-color: var(--pp-brand-primary); color: var(--pp-text-on-accent); }
.lcl-btn--primary:hover:not(:disabled) { filter: brightness(1.05); color: var(--pp-text-on-accent); }
.lcl-btn-ico { width: 14px; height: 14px; }

.lcl-link { appearance: none; background: none; border: none; cursor: pointer; padding: 0;
  display: inline-flex; align-items: center; gap: 4px; font-family: inherit;
  font-size: var(--pp-fs-12); font-weight: var(--pp-weight-semibold); color: var(--pp-brand-primary); }
.lcl-link:hover { text-decoration: underline; }
.lcl-link-ico { width: 13px; height: 13px; }

/* Status-Pille + Menü */
.lcl-status { position: relative; }
.lcl-pill { appearance: none; cursor: pointer; font-family: inherit;
  display: inline-flex; align-items: center; gap: 6px;
  font-size: var(--pp-fs-13, 13px); font-weight: var(--pp-weight-semibold);
  padding: 5px var(--pp-space-3); border-radius: var(--pp-radius-full);
  border: 1px solid transparent; }
.lcl-pill:disabled { opacity: 0.6; cursor: default; }
.lcl-pill-caret { width: 14px; height: 14px; opacity: 0.7; }
.lcl-dot { width: 7px; height: 7px; border-radius: var(--pp-radius-full); flex-shrink: 0; background: currentColor; }

.lcl-pill[data-tone="info"]    { background: color-mix(in oklab, var(--pp-state-info) 14%, transparent);    color: var(--pp-state-info); }
.lcl-pill[data-tone="brand"]   { background: color-mix(in oklab, var(--pp-brand-primary) 14%, transparent); color: var(--pp-brand-primary); }
.lcl-pill[data-tone="success"] { background: color-mix(in oklab, var(--pp-state-success) 16%, transparent); color: var(--pp-state-success); }
.lcl-pill[data-tone="warning"] { background: color-mix(in oklab, var(--pp-state-warning) 16%, transparent); color: var(--pp-state-warning); }
.lcl-pill[data-tone="danger"]  { background: color-mix(in oklab, var(--pp-state-danger) 16%, transparent);  color: var(--pp-state-danger); }
.lcl-pill[data-tone="neutral"] { background: var(--pp-bg-sunken); color: var(--pp-text-secondary); }

.lcl-menu-backdrop { position: fixed; inset: 0; z-index: 40; }
.lcl-menu { position: absolute; top: calc(100% + 4px); right: 0; z-index: 41; margin: 0; padding: var(--pp-space-1);
  list-style: none; min-width: 200px; max-height: 320px; overflow: auto;
  background: var(--pp-bg-surface); border: 1px solid var(--pp-border-default);
  border-radius: var(--pp-radius-ui); box-shadow: var(--pp-shadow-md, 0 8px 24px rgb(0 0 0 / 0.14)); }
.lcl-menu-item { appearance: none; cursor: pointer; width: 100%; font-family: inherit; text-align: left;
  display: flex; align-items: center; gap: 8px; padding: 7px var(--pp-space-2);
  border: none; background: none; border-radius: var(--pp-radius-ui);
  font-size: var(--pp-fs-13, 13px); color: var(--pp-text-primary); }
.lcl-menu-item:hover { background: var(--pp-bg-hover); }
.lcl-menu-item.is-active { font-weight: var(--pp-weight-semibold); }
.lcl-menu-item .lcl-dot[data-tone="info"]    { color: var(--pp-state-info); }
.lcl-menu-item .lcl-dot[data-tone="brand"]   { color: var(--pp-brand-primary); }
.lcl-menu-item .lcl-dot[data-tone="success"] { color: var(--pp-state-success); }
.lcl-menu-item .lcl-dot[data-tone="warning"] { color: var(--pp-state-warning); }
.lcl-menu-item .lcl-dot[data-tone="danger"]  { color: var(--pp-state-danger); }
.lcl-menu-item .lcl-dot[data-tone="neutral"] { color: var(--pp-text-tertiary); }
.lcl-menu-check { width: 14px; height: 14px; margin-left: auto; color: var(--pp-brand-primary); }

/* Zwei-Spalten-Layout */
.lcl-grid { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: var(--pp-space-5); align-items: start; }
.lcl-col { display: flex; flex-direction: column; gap: var(--pp-space-5); min-width: 0; }

/* Karten */
.lcl-card { background: var(--pp-bg-surface); border: 1px solid var(--pp-border-subtle);
  border-radius: var(--pp-radius-ui); box-shadow: var(--pp-shadow-xs); padding: var(--pp-space-4) var(--pp-space-5); }
.lcl-card-title { margin: 0 0 var(--pp-space-3); font-size: var(--pp-fs-12); font-weight: var(--pp-weight-bold);
  letter-spacing: var(--pp-tracking-wide, 0.04em); text-transform: uppercase; color: var(--pp-text-tertiary); }

.lcl-fields { display: grid; grid-template-columns: max-content minmax(0, 1fr); gap: var(--pp-space-2) var(--pp-space-4); margin: 0; }
.lcl-field { display: contents; }
.lcl-field-label { font-size: var(--pp-fs-13, 13px); color: var(--pp-text-tertiary); padding-top: 5px; }
.lcl-field-value { margin: 0; min-width: 0; font-size: var(--pp-fs-14); color: var(--pp-text-primary); }
.lcl-muted { color: var(--pp-text-tertiary); }

.lcl-input { appearance: none; width: 100%; font-family: inherit; font-size: var(--pp-fs-14); color: var(--pp-text-primary);
  padding: 4px var(--pp-space-2); border: 1px solid var(--pp-brand-primary); border-radius: var(--pp-radius-ui);
  background: var(--pp-bg-base); }
.lcl-input:focus { outline: none; box-shadow: 0 0 0 3px rgb(var(--pp-brand-primary-rgb) / 0.15); }

.lcl-edit-trigger { appearance: none; cursor: text; width: 100%; text-align: left; font-family: inherit;
  display: flex; align-items: center; justify-content: space-between; gap: 6px;
  padding: 4px var(--pp-space-2); border: 1px solid transparent; border-radius: var(--pp-radius-ui);
  background: none; font-size: var(--pp-fs-14); color: var(--pp-text-primary); }
.lcl-edit-trigger:hover { background: var(--pp-bg-hover); border-color: var(--pp-border-subtle); }
.lcl-edit-trigger.is-empty span { color: var(--pp-text-tertiary); }
.lcl-edit-ico { width: 13px; height: 13px; opacity: 0; flex-shrink: 0; color: var(--pp-text-tertiary); }
.lcl-edit-trigger:hover .lcl-edit-ico { opacity: 0.7; }

/* Aktivitäten */
.lcl-activity { display: flex; flex-direction: column; gap: var(--pp-space-4); }
.lcl-activity-head { display: flex; align-items: center; justify-content: space-between; gap: var(--pp-space-3); }
.lcl-activity-head .lcl-card-title { margin: 0; }
.lcl-activity-empty { margin: 0; font-size: var(--pp-fs-14); }
.lcl-activity-note { margin: 0; font-size: var(--pp-fs-12); color: var(--pp-text-tertiary); }

.lcl-comment { display: flex; flex-direction: column; gap: var(--pp-space-2);
  border-top: 1px solid var(--pp-border-subtle); padding-top: var(--pp-space-4); }
.lcl-comment-input { appearance: none; width: 100%; resize: vertical; font-family: inherit;
  font-size: var(--pp-fs-14); color: var(--pp-text-primary);
  padding: var(--pp-space-2) var(--pp-space-3); border: 1px solid var(--pp-border-default);
  border-radius: var(--pp-radius-ui); background: var(--pp-bg-base); }
.lcl-comment-input:focus { outline: none; border-color: var(--pp-brand-primary);
  box-shadow: 0 0 0 3px rgb(var(--pp-brand-primary-rgb) / 0.15); }
.lcl-comment-actions { display: flex; justify-content: flex-end; }

@media (max-width: 1080px) {
  .lcl-grid { grid-template-columns: minmax(0, 1fr); }
}
</style>
