<!--
  LCSDeal — CRM-Verkaufschance Detailseite (V2, Pilanda-UX).
  =========================================================
  Pilanda-Theme-Fläche für die Deal-DETAILSEITE (Route name 'Deal',
  /deals/:dealId). Ersetzt Dominiks Deal.vue-Optik durch Pp*-Bausteine;
  Backend/Datenlogik bleiben Dominiks Frappe-CRM (unverändert).

  WICHTIG — Deal = Projekt: Die Route trägt einen beforeEnter-Guard von
  Dominik/lcs_integrations (Redirect auf die LCS-Projektfläche, wenn zum Deal
  ein LCS-Projekt existiert; ?noredirect=1 als Escape). Diese Seite wird also
  regulär nur erreicht, wenn (noch) KEIN Projekt existiert oder der Escape
  gesetzt ist — sie zeigt dann trotzdem defensiv den „Vertriebsprojekt
  öffnen"-Button, falls die Projekt-Abfrage doch einen Treffer liefert.

  Aufbau:
    · PpPageHead (Eyebrow „Sales / CRM" + Titel Organisation/Deal)
    · PpWorkflowStepper@2  — Funnel-Status in position-Reihenfolge, aktueller
      markiert; Aktionsknöpfe = Statuswechsel (Lost → Pflichtgrund-Dialog,
      derselbe geteilte Baustein wie im Kanban).
    · 2-Spalten-Layout (Vollbreite): links Karten (Verkaufschance/Firma/
      Kontakte), rechts read-only Aktivitäts-Timeline + „Vollansicht öffnen".

  Kommentar-EINGABE bewusst NICHT nachgebaut (Dominiks TextEditor-/Mention-/
  Anhang-Flow ist tief mit Activities.vue verwoben) — dafür „Vollansicht
  öffnen" → Upstream-Deal ('Deal Upstream'). Nur AUSSCHLIESSLICH aus echten
  Pp*-Bausteinen komponiert, token-only, Vollbreiten-Canvas.
-->
<template>
  <div class="flex h-full flex-col">
    <LayoutHeader>
      <template #left-header>
        <Breadcrumbs :items="breadcrumbs" />
      </template>
      <template #right-header>
        <Button :label="__('Refresh')" iconLeft="refresh-cw" @click="reloadAll" :loading="dealRes.loading" />
        <Button variant="subtle" :label="__('Open full view')" iconLeft="external-link" @click="openUpstream" />
      </template>
    </LayoutHeader>

    <div class="lcsdl">
      <div v-if="deal.name" class="lcsdl-inner">
        <PpPageHead :eyebrow="__('Sales / CRM')" :title="title" :subtitle="subtitle">
          <template #actions>
            <Button v-if="projectName" variant="solid" iconLeft="folder" :label="__('Open sales project')" @click="openProject" />
          </template>
        </PpPageHead>

        <!-- Funnel prominent: Status in position-Reihenfolge + Statuswechsel -->
        <section class="lcsdl-card lcsdl-funnel">
          <div class="lcsdl-card-head">
            <span class="lcsdl-card-title">{{ __('Change phase') }}</span>
          </div>
          <PpWorkflowStepper
            :steps="steps"
            :current-actions="stepperActions"
            @action="changeStatus"
          />
        </section>

        <div class="lcsdl-grid">
          <!-- LINKS: Karten --------------------------------------------- -->
          <div class="lcsdl-col">
            <!-- Verkaufschance -->
            <section class="lcsdl-card">
              <div class="lcsdl-card-head">
                <span class="lcsdl-card-title">{{ __('Opportunity') }}</span>
                <span class="lcsdl-badge" :class="'is-' + toneOf(deal.status)">{{ statusLabel(deal.status) }}</span>
              </div>
              <div class="lcsdl-figures">
                <div class="lcsdl-figure">
                  <span class="lcsdl-figure-cap">{{ __('Value') }}</span>
                  <span class="lcsdl-figure-val">{{ eur(deal.annual_revenue, deal.currency) }}</span>
                </div>
                <div class="lcsdl-figure">
                  <span class="lcsdl-figure-cap">{{ __('Win probability') }}</span>
                  <span class="lcsdl-figure-val">{{ probability }} %</span>
                </div>
                <div class="lcsdl-figure">
                  <span class="lcsdl-figure-cap">{{ __('Weighted value') }}</span>
                  <span class="lcsdl-figure-val">{{ eur(weighted, deal.currency) }}</span>
                </div>
              </div>
              <dl class="lcsdl-meta">
                <div>
                  <dt>{{ __('Win probability') }}</dt>
                  <dd>
                    <FormControl
                      type="number"
                      size="sm"
                      v-model="probEdit"
                      class="lcsdl-prob"
                      @change="saveProb"
                    />
                  </dd>
                </div>
                <div>
                  <dt>{{ __('Owner') }}</dt>
                  <dd class="lcsdl-owner">
                    <span v-if="deal.deal_owner" class="lcsdl-avatar">{{ initials(ownerName(deal.deal_owner)) }}</span>
                    {{ deal.deal_owner ? ownerName(deal.deal_owner) : '—' }}
                  </dd>
                </div>
                <div v-if="deal.currency"><dt>{{ __('Currency') }}</dt><dd>{{ deal.currency }}</dd></div>
                <div v-if="deal.creation"><dt>{{ __('Created') }}</dt><dd>{{ fmtDateTime(deal.creation) }}</dd></div>
                <div v-if="deal.modified"><dt>{{ __('Last update') }}</dt><dd>{{ fmtDateTime(deal.modified) }}</dd></div>
              </dl>
            </section>

            <!-- Firma -->
            <section class="lcsdl-card">
              <div class="lcsdl-card-head">
                <span class="lcsdl-card-title">{{ __('Company') }}</span>
              </div>
              <div v-if="deal.organization" class="lcsdl-org">
                <button class="lcsdl-link" @click="openOrganization">
                  <FeatherIcon name="briefcase" class="h-4 w-4" />
                  <span>{{ deal.organization }}</span>
                </button>
                <a v-if="deal.website" class="lcsdl-weblink" :href="normalizeUrl(deal.website)" target="_blank" rel="noopener">
                  <FeatherIcon name="external-link" class="h-3.5 w-3.5" />
                  {{ __('Website') }}
                </a>
              </div>
              <div v-else class="lcsdl-empty-sm">—</div>
            </section>

            <!-- Kontakte -->
            <section class="lcsdl-card">
              <div class="lcsdl-card-head">
                <span class="lcsdl-card-title">{{ __('Contacts') }}</span>
                <span v-if="contacts.length" class="lcsdl-count">{{ contacts.length }}</span>
              </div>
              <ul v-if="contacts.length" class="lcsdl-contacts">
                <li v-for="c in contacts" :key="c.name" class="lcsdl-contact">
                  <button class="lcsdl-contact-main" @click="openContact(c.name)">
                    <span class="lcsdl-avatar">{{ initials(c.full_name) }}</span>
                    <span class="lcsdl-contact-txt">
                      <span class="lcsdl-contact-name">
                        {{ c.full_name || c.name }}
                        <span v-if="c.is_primary" class="lcsdl-primary">{{ __('Primary') }}</span>
                      </span>
                      <span v-if="c.email || c.mobile_no" class="lcsdl-contact-sub">{{ c.email || c.mobile_no }}</span>
                    </span>
                  </button>
                </li>
              </ul>
              <div v-else class="lcsdl-empty-sm">{{ __('No contacts added') }}</div>
            </section>
          </div>

          <!-- RECHTS: Aktivitäten (read-only) --------------------------- -->
          <div class="lcsdl-col">
            <section class="lcsdl-card lcsdl-activity">
              <div class="lcsdl-card-head">
                <span class="lcsdl-card-title">{{ __('Activity') }}</span>
                <Button variant="ghost" size="sm" :label="__('Open full view')" iconLeft="external-link" @click="openUpstream" />
              </div>
              <PpTimeline v-if="activityItems.length" :items="activityItems" />
              <div v-else class="lcsdl-empty-sm">
                {{ activitiesRes.loading ? __('Loading …') : __('No activities yet') }}
              </div>
            </section>
          </div>
        </div>
      </div>

      <div v-else class="lcsdl-empty">
        {{ dealRes.loading ? __('Loading …') : __('Document Not Found') }}
      </div>
    </div>

    <!-- Lost: Pflicht-Verlustgrund (geteilter Baustein, wie im Kanban) -->
    <LostReasonDialog v-model="lostOpen" :saving="saving" @confirm="onLostConfirm" />
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { call, createResource, toast, Breadcrumbs, Button, FormControl, FeatherIcon } from 'frappe-ui'
import LayoutHeader from '@/components/LayoutHeader.vue'
import PpPageHead from '@/components/pp/PpPageHead.vue'
import PpWorkflowStepper from '@/components/pp/PpWorkflowStepper.vue'
import PpTimeline from '@/components/pp/PpTimeline.vue'
import LostReasonDialog from '@/components/lcs/LostReasonDialog.vue'
import { statusesStore } from '@/stores/statuses'
import { usersStore } from '@/stores/users'

const props = defineProps({
  dealId: { type: String, required: true },
})

const router = useRouter()
const statusStore = statusesStore()
const { getUser } = usersStore()

/* ---- Formatierung (de-DE, metrisch) --------------------------------- */
function eur(n, currency = 'EUR') {
  if (n == null || n === '') return '—'
  return new Intl.NumberFormat('de-DE', {
    style: 'currency',
    currency: currency || 'EUR',
    maximumFractionDigits: 0,
  }).format(Number(n))
}
function fmtDateTime(v) {
  if (!v) return '—'
  const d = new Date(v)
  return isNaN(d) ? String(v) : d.toLocaleString('de-DE', { dateStyle: 'short', timeStyle: 'short' })
}
function initials(name) {
  return (name || '').split(/\s+/).filter(Boolean).map((w) => w[0]).join('').slice(0, 2).toUpperCase() || '?'
}
function ownerName(email) {
  return getUser(email)?.full_name || email
}
function stripHtml(s) {
  return String(s || '').replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim()
}
function normalizeUrl(u) {
  const s = String(u || '')
  return /^https?:\/\//i.test(s) ? s : `https://${s}`
}

/* ---- Deal LIVE laden (Dominiks CRM, unverändert) -------------------- */
const dealRes = createResource({
  url: 'frappe.client.get',
  params: { doctype: 'CRM Deal', name: props.dealId },
  cache: ['lcs-deal', props.dealId],
  auto: true,
})
const deal = computed(() => dealRes.data || {})

const title = computed(() => deal.value.organization || deal.value.name || props.dealId)

/* ---- Status-SSOT: CRM Deal Status LIVE (position asc) --------------- */
const statuses = computed(() => statusStore.dealStatuses.data || [])
function statusType(name) {
  return statusStore.getDealStatus(name)?.type || 'Open'
}
function statusProb(name) {
  return Number(statusStore.getDealStatus(name)?.probability) || 0
}
function statusPos(name) {
  return Number(statusStore.getDealStatus(name)?.position) || 0
}
function statusLabel(name) {
  return name ? __(name) : '—'
}
function toneOf(name) {
  const t = statusType(name)
  return t === 'Won' ? 'success' : t === 'Lost' ? 'danger' : 'info'
}

const probability = computed(() => {
  const p = deal.value.probability != null && deal.value.probability !== ''
    ? Number(deal.value.probability)
    : statusProb(deal.value.status)
  return Math.round(p || 0)
})
const weighted = computed(() => (Number(deal.value.annual_revenue) || 0) * probability.value / 100)

const subtitle = computed(() => {
  const parts = [statusLabel(deal.value.status), `${eur(deal.value.annual_revenue, deal.value.currency)}`, `${probability.value} %`]
  return parts.filter(Boolean).join(' · ')
})

/* ---- PpWorkflowStepper: Funnel + Statuswechsel ---------------------- */
const steps = computed(() => {
  const curPos = statusPos(deal.value.status)
  const curName = deal.value.status
  return statuses.value.map((s) => {
    let state = 'open'
    if (s.name === curName) state = statusType(s.name) === 'Lost' ? 'blocked' : 'active'
    else if (s.position < curPos) state = 'done'
    return { key: s.name, label: __(s.name), state }
  })
})
// Jede andere Phase als klickbare Aktion (Won = primär, Lost = danger).
const stepperActions = computed(() =>
  statuses.value
    .filter((s) => s.name !== deal.value.status)
    .map((s) => {
      const t = statusType(s.name)
      return { label: __(s.name), event: s.name, kind: t === 'Won' ? 'primary' : t === 'Lost' ? 'danger' : 'default' }
    }),
)

/* ---- Statuswechsel (dieselben Regeln wie im Kanban) ----------------- */
const saving = ref(false)
const lostOpen = ref(false)
const lostTarget = ref(null)

function changeStatus(name) {
  if (!name || name === deal.value.status) return
  if (statusType(name) === 'Lost') {
    lostTarget.value = name
    lostOpen.value = true
    return
  }
  persistStatus({ status: name })
}

async function persistStatus(fields) {
  saving.value = true
  try {
    await call('frappe.client.set_value', { doctype: 'CRM Deal', name: props.dealId, fieldname: fields })
    toast({ title: __('Status updated'), icon: 'check-circle', iconClasses: 'text-green-500' })
    dealRes.reload()
    activitiesRes.reload()
    return true
  } catch (e) {
    toast({ title: __('Could not save. Please try again.'), text: e?.messages?.[0] || e?.message || '', icon: 'alert-circle', iconClasses: 'text-red-500' })
    return false
  } finally {
    saving.value = false
  }
}

async function onLostConfirm({ reason, notes }) {
  const fields = { status: lostTarget.value, lost_reason: reason }
  if (notes) fields.lost_notes = notes
  const ok = await persistStatus(fields)
  if (ok) lostOpen.value = false
}

/* ---- Inline-Edit: Abschlusswahrscheinlichkeit ----------------------- */
const probEdit = ref(null)
watch(
  () => deal.value.probability,
  (v) => { probEdit.value = v ?? statusProb(deal.value.status) },
  { immediate: true },
)
function saveProb() {
  const val = Number(probEdit.value)
  if (isNaN(val)) return
  if (val === Number(deal.value.probability)) return
  saveField('probability', val)
}
async function saveField(fieldname, value) {
  try {
    await call('frappe.client.set_value', { doctype: 'CRM Deal', name: props.dealId, fieldname: { [fieldname]: value } })
    toast({ title: __('Saved'), icon: 'check-circle', iconClasses: 'text-green-500' })
    dealRes.reload()
  } catch (e) {
    toast({ title: __('Could not save. Please try again.'), text: e?.messages?.[0] || e?.message || '', icon: 'alert-circle', iconClasses: 'text-red-500' })
  }
}

/* ---- Kontakte (Dominiks Deal-API, read-only) ------------------------ */
const contactsRes = createResource({
  url: 'crm.fcrm.doctype.crm_deal.api.get_deal_contacts',
  params: { name: props.dealId },
  cache: ['lcs-deal-contacts', props.dealId],
  auto: true,
})
const contacts = computed(() => contactsRes.data || [])

/* ---- Aktivitäten (Dominiks get_activities, read-only) --------------- */
const activitiesRes = createResource({
  url: 'crm.api.activities.get_activities',
  params: { name: props.dealId },
  cache: ['lcs-deal-activities', props.dealId],
  auto: true,
  transform: ([versions, calls, notes, tasks, attachments]) => ({ versions, calls, notes, tasks, attachments }),
})

const activityItems = computed(() => {
  const a = activitiesRes.data
  if (!a) return []
  const items = []
  for (const v of a.versions || []) {
    let kind = 'info'
    let dir = null
    let subject = ''
    const t = v.activity_type
    if (t === 'communication') {
      kind = 'email'
      dir = v.data?.sent_or_received === 'Received' ? 'in' : 'out'
      subject = v.data?.subject || __('Email')
    } else if (t === 'comment') {
      kind = 'note'
      subject = stripHtml(v.content) || __('Comment')
    } else if (t === 'incoming_call') {
      kind = 'call'; dir = 'in'; subject = __('Call')
    } else if (t === 'outgoing_call') {
      kind = 'call'; dir = 'out'; subject = __('Call')
    } else {
      subject = stripHtml(v.content || v.data?.field || v.activity_type || '')
    }
    items.push({ kind, dir, subject, who: v.owner_name || v.owner || '', ago: fmtDateTime(v.creation), _t: v.creation })
  }
  for (const c of a.calls || []) {
    items.push({ kind: 'call', dir: c.type === 'Incoming' ? 'in' : 'out', subject: c.status || __('Call'), who: c.caller || c.owner || '', ago: fmtDateTime(c.creation), _t: c.creation })
  }
  for (const n of a.notes || []) {
    items.push({ kind: 'note', subject: stripHtml(n.title || n.content) || __('Note'), who: n.owner || '', ago: fmtDateTime(n.modified || n.creation), _t: n.modified || n.creation })
  }
  for (const tk of a.tasks || []) {
    items.push({ kind: 'task', subject: tk.title || __('Task'), who: tk.assigned_to || tk.owner || '', ago: fmtDateTime(tk.modified || tk.creation), _t: tk.modified || tk.creation })
  }
  return items.sort((x, y) => new Date(y._t) - new Date(x._t)).slice(0, 40)
})

/* ---- LCS-Projekt (dieselbe Abfrage wie der beforeEnter-Guard) ------- */
const projectRes = createResource({
  url: 'lcs_integrations.projects.api.find_project_for',
  params: { doctype: 'CRM Deal', name: props.dealId },
  auto: true,
})
const projectName = computed(() => projectRes.data?.name || null)

/* ---- Navigation / Aktionen ------------------------------------------ */
const breadcrumbs = computed(() => [
  { label: __('Deals'), route: { name: 'Deals' } },
  { label: title.value, route: { name: 'Deal', params: { dealId: props.dealId } } },
])

function openUpstream() {
  router.push({ name: 'Deal Upstream', params: { dealId: props.dealId } })
}
function openProject() {
  if (projectName.value) router.push({ name: 'LCS Project', params: { id: projectName.value } })
}
function openOrganization() {
  if (deal.value.organization) router.push({ name: 'Organization', params: { organizationId: deal.value.organization } })
}
function openContact(name) {
  router.push({ name: 'Contact', params: { contactId: name } })
}
function reloadAll() {
  dealRes.reload()
  contactsRes.reload()
  activitiesRes.reload()
}
</script>

<style scoped>
/* Vollbreiten-Canvas (kein max-width-Zentrieren), token-only. */
.lcsdl { flex: 1; min-height: 0; overflow: auto; background: var(--pp-bg-base); }
.lcsdl-inner {
  display: flex;
  flex-direction: column;
  gap: var(--pp-space-5);
  padding: var(--pp-space-6) var(--pp-space-6) var(--pp-space-12);
}

.lcsdl-empty {
  padding: var(--pp-space-8);
  text-align: center;
  color: var(--pp-text-tertiary);
  font-size: var(--pp-fs-14);
}
.lcsdl-empty-sm {
  padding: var(--pp-space-4);
  text-align: center;
  color: var(--pp-text-tertiary);
  font-size: var(--pp-fs-14);
}

/* Karten */
.lcsdl-card {
  background: var(--pp-bg-surface);
  border: 1px solid var(--pp-border-subtle);
  border-radius: var(--pp-radius-ui);
  padding: var(--pp-space-4);
  display: flex;
  flex-direction: column;
  gap: var(--pp-space-3);
}
.lcsdl-card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--pp-space-3);
}
.lcsdl-card-title {
  font-size: var(--pp-fs-12);
  font-weight: var(--pp-weight-bold);
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--pp-text-tertiary);
}
.lcsdl-count {
  display: inline-flex; align-items: center; justify-content: center;
  min-width: 20px; height: 20px; padding: 0 6px;
  border-radius: var(--pp-radius-full);
  background: var(--pp-bg-sunken); color: var(--pp-text-secondary);
  font-size: 11px; font-weight: var(--pp-weight-bold);
}

.lcsdl-funnel { gap: var(--pp-space-4); }

.lcsdl-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.5fr) minmax(0, 1fr);
  gap: var(--pp-space-5);
  align-items: start;
}
.lcsdl-col { display: flex; flex-direction: column; gap: var(--pp-space-5); min-width: 0; }

/* Kennzahlen */
.lcsdl-figures {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--pp-space-2);
  padding: var(--pp-space-3);
  background: var(--pp-bg-sunken);
  border: 1px solid var(--pp-border-subtle);
  border-radius: var(--pp-radius-ui);
}
.lcsdl-figure { display: flex; flex-direction: column; gap: 3px; }
.lcsdl-figure-cap {
  font-size: 10px; font-weight: var(--pp-weight-bold); letter-spacing: 0.04em;
  text-transform: uppercase; color: var(--pp-text-tertiary);
}
.lcsdl-figure-val {
  font-size: var(--pp-fs-15, 15px); font-weight: var(--pp-weight-semibold);
  color: var(--pp-text-primary); font-variant-numeric: tabular-nums;
}

.lcsdl-badge {
  display: inline-flex; align-items: center;
  padding: 2px 10px; border-radius: var(--pp-radius-full);
  font-size: var(--pp-fs-12); font-weight: var(--pp-weight-semibold);
}
.lcsdl-badge.is-info { background: color-mix(in oklab, var(--pp-brand-primary) 14%, transparent); color: var(--pp-brand-primary); }
.lcsdl-badge.is-success { background: color-mix(in oklab, var(--pp-state-success) 16%, transparent); color: var(--pp-state-success); }
.lcsdl-badge.is-danger { background: color-mix(in oklab, var(--pp-state-danger) 14%, transparent); color: var(--pp-state-danger); }

.lcsdl-meta { display: grid; grid-template-columns: 1fr 1fr; gap: var(--pp-space-3) var(--pp-space-4); margin: 0; }
.lcsdl-meta dt { font-size: var(--pp-fs-12); color: var(--pp-text-tertiary); margin-bottom: 2px; }
.lcsdl-meta dd { margin: 0; font-size: var(--pp-fs-14); color: var(--pp-text-primary); }
.lcsdl-prob { max-width: 96px; }

.lcsdl-owner { display: inline-flex; align-items: center; gap: var(--pp-space-2); }
.lcsdl-avatar {
  display: inline-flex; align-items: center; justify-content: center; flex-shrink: 0;
  width: 22px; height: 22px; border-radius: var(--pp-radius-full);
  background: color-mix(in oklab, var(--pp-brand-primary) 16%, transparent);
  color: var(--pp-brand-primary); font-size: 9px; font-weight: var(--pp-weight-bold);
}

/* Firma */
.lcsdl-org { display: flex; flex-direction: column; gap: var(--pp-space-2); }
.lcsdl-link {
  display: inline-flex; align-items: center; gap: var(--pp-space-2);
  appearance: none; border: 0; background: transparent; cursor: pointer; padding: 0;
  font-family: inherit; font-size: var(--pp-fs-15, 15px); font-weight: var(--pp-weight-semibold);
  color: var(--pp-text-primary);
}
.lcsdl-link:hover { color: var(--pp-brand-primary); }
.lcsdl-weblink {
  display: inline-flex; align-items: center; gap: var(--pp-space-1);
  align-self: flex-start; font-size: var(--pp-fs-13, 13px);
  color: var(--pp-brand-primary); text-decoration: none;
}
.lcsdl-weblink:hover { text-decoration: underline; }

/* Kontakte */
.lcsdl-contacts { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: var(--pp-space-1); }
.lcsdl-contact-main {
  display: flex; align-items: center; gap: var(--pp-space-3); width: 100%;
  appearance: none; border: 0; background: transparent; cursor: pointer; text-align: left;
  padding: var(--pp-space-2); border-radius: var(--pp-radius-ui); font-family: inherit;
}
.lcsdl-contact-main:hover { background: var(--pp-bg-hover); }
.lcsdl-contact-txt { display: flex; flex-direction: column; gap: 1px; min-width: 0; }
.lcsdl-contact-name {
  display: inline-flex; align-items: center; gap: var(--pp-space-2);
  font-size: var(--pp-fs-14); font-weight: var(--pp-weight-medium, 500); color: var(--pp-text-primary);
}
.lcsdl-contact-sub { font-size: var(--pp-fs-12); color: var(--pp-text-tertiary); overflow: hidden; text-overflow: ellipsis; }
.lcsdl-primary {
  padding: 1px 6px; border-radius: var(--pp-radius-full);
  background: color-mix(in oklab, var(--pp-state-success) 16%, transparent); color: var(--pp-state-success);
  font-size: 10px; font-weight: var(--pp-weight-bold); text-transform: uppercase; letter-spacing: 0.04em;
}

.lcsdl-activity { min-height: 200px; }

@media (max-width: 1080px) {
  .lcsdl-grid { grid-template-columns: minmax(0, 1fr); }
}
</style>
