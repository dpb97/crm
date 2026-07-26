<!--
  LCSSalesMeeting — Sales Meeting (Gremiums-Sicht, Theme-Referenz
  „ThemePreviewSalesMeeting", Marco 24.07.2026).
  ============================================================
  Die EINZIGE Seite mit allen drei Vertriebsfluss-Stufen nebeneinander:
  · Agenda mit „Entschieden → Archivieren"-Fluss (Entscheid direkt am Punkt;
    Erledigtes wird NICHT durchgestrichen — der Verkäufer archiviert manuell).
  · darunter die drei Stufen (Chancen · Leads · Vertriebsprojekte) als kompakte
    Karten.
  · Seiten-Aktionen leben in der zentralen PpFunctionBar (seiten-lokaler Burger
    im Kopf); Erfassen/Protokoll öffnen als PpModal.
  · „Letzte Entscheide" + „Meeting-Rahmen" stehen als Standardinhalt im
    angedockten Shell-Inspektor (usePilandaInspect); ein Zeilen-Klick
    überschreibt den Inspektor mit der Spezifikation des Punkts.

  Echte Daten: lcs_integrations.projects.api.get_sales_meeting_agenda
  (+ sales_meeting_add / _decide / _archive).
-->

<template>
  <div class="flex h-full flex-col">
    <LayoutHeader>
      <template #left-header>
        <Breadcrumbs :items="[{ label: 'Vertrieb' }, { label: 'CRM' }, { label: __('Sales Meeting'), route: { name: 'LCS Sales Meeting' } }]" />
      </template>
      <template #right-header>
        <div class="flex items-center gap-2">
          <Button :label="__('Insights')" iconLeft="bar-chart-2" @click="$router.push({ name: 'LCS Forecasting' })" />
          <Button :label="__('Actions')" iconLeft="menu" @click="barOpen = !barOpen" />
          <Button :label="__('Refresh')" iconLeft="refresh-cw" :loading="board.loading" @click="board.reload()" />
        </div>
      </template>
    </LayoutHeader>

    <div class="crmsm">
      <div class="crmsm-inner">
        <PpPageHead
          :title="__('Sales Meeting')"
          :subtitle="`${meetingDateLabel} · ${agenda.length} ${__('open points')} · ${stageTotal} ${__('in the pipeline')}`"
        />

        <!-- Positionierter Canvas: die FunctionBar überlagert oben (absolut). -->
        <div class="crmsm-canvas">
          <PpFunctionBar
            v-model:open="barOpen"
            :page-groups="{ aktionen: pageActions }"
            :aria-label="__('Sales meeting actions')"
            @action="onAction"
          />

          <p v-if="flash" class="crmsm-flash" role="status">{{ flash }}</p>

          <!-- Flagged important (entitätsübergreifende Sternflags) -->
          <section v-if="important.length" class="crmsm-card crmsm-important">
            <header class="crmsm-important-head">
              <IconStar class="crmsm-important-star" /> {{ __('Flagged important') }}
              <span class="crmsm-ch-m">{{ important.length }} {{ __('across projects, leads and opportunities') }}</span>
            </header>
            <div class="crmsm-important-list">
              <button
                v-for="it in important"
                :key="it.entity + it.name"
                type="button"
                class="crmsm-important-row"
                @click="openImportant(it)"
              >
                <span class="crmsm-ent" :data-ent="it.entity">{{ entityLabel(it.entity) }}</span>
                <span class="crmsm-important-main">
                  <span class="crmsm-important-title">{{ it.label }}</span>
                  <span class="crmsm-important-sub">{{ it.sub }}<template v-if="it.person"> · {{ shortUser(it.person) }}</template></span>
                </span>
                <span v-if="it.status" class="crmsm-pill" data-tone="info"><i class="crmsm-dot" />{{ it.status }}</span>
                <span v-if="it.value" class="crmsm-important-val">{{ money(it.value) }}</span>
              </button>
            </div>
          </section>

          <!-- Agenda: Entscheid direkt am Punkt -->
          <section class="crmsm-card">
            <header class="crmsm-ch">
              {{ __('Agenda') }} {{ meetingDateLabel }}
              <span class="crmsm-ch-m">{{ __('Decide at the point · done items are archived manually · row = detail in the inspector') }}</span>
            </header>

            <PpDataGrid v-if="agenda.length" :columns="agendaCols" :rows="agendaRows" @row-click="onAgendaClick">
              <template #cell-status="{ value }">
                <span class="crmsm-pill" :data-tone="statusTone(value)"><i class="crmsm-dot" />{{ statusLabel(value) }}</span>
              </template>
              <template #cell-entscheid="{ row }">
                <button v-if="row.status === 'Decided'" type="button" class="crmsm-btn" @click.stop="archive(row)">
                  {{ __('Archive') }}
                </button>
                <button v-else type="button" class="crmsm-btn is-primary" @click.stop="decide(row)">
                  {{ __('Decided') }}
                </button>
              </template>
            </PpDataGrid>

            <PpEmptyState
              v-else
              :icon="IconClipboard"
              :title="board.loading ? __('Loading agenda …') : __('No open agenda points')"
              :hint="board.loading ? '' : __('Add a point via the actions bar to start the meeting.')"
            />

            <p v-if="archivedCount" class="crmsm-note">
              {{ archivedCount }} {{ __('archived point(s)') }} — {{ __('archive via the “Minutes” action.') }}
            </p>
          </section>

          <!-- Drei Stufen (kompakte Karten) -->
          <div class="crmsm-stages">
            <section class="crmsm-card">
              <header class="crmsm-ch">{{ __('Opportunities') }}<span class="crmsm-ch-m">{{ chancen.length }} {{ __('open') }}</span></header>
              <ul class="crmsm-list">
                <li v-for="c in chancen" :key="c.id" class="crmsm-row" tabindex="0"
                    @click="selectStage('deal', c)" @keydown.enter="selectStage('deal', c)">
                  <span class="crmsm-rowname">{{ c.name }}</span>
                  <span class="crmsm-rowval">{{ money(c.value) }}</span>
                  <span class="crmsm-pill" :data-tone="dealTone(c.status)"><i class="crmsm-dot" />{{ c.status }}</span>
                </li>
                <li v-if="!chancen.length" class="crmsm-row crmsm-row--empty">{{ __('No open opportunities.') }}</li>
              </ul>
            </section>

            <section class="crmsm-card">
              <header class="crmsm-ch">{{ __('Leads') }}<span class="crmsm-ch-m">{{ leads.length }} {{ __('active') }}</span></header>
              <ul class="crmsm-list">
                <li v-for="l in leads" :key="l.id" class="crmsm-row" tabindex="0"
                    @click="selectStage('lead', l)" @keydown.enter="selectStage('lead', l)">
                  <span class="crmsm-rowname">{{ l.name }}</span>
                  <span class="crmsm-rowsub">{{ l.org }}</span>
                  <span class="crmsm-pill" data-tone="info"><i class="crmsm-dot" />{{ l.status }}</span>
                </li>
                <li v-if="!leads.length" class="crmsm-row crmsm-row--empty">{{ __('No active leads.') }}</li>
              </ul>
            </section>

            <section class="crmsm-card">
              <header class="crmsm-ch">{{ __('Sales projects') }}<span class="crmsm-ch-m">{{ projekte.length }} {{ __('active') }}</span></header>
              <ul class="crmsm-list">
                <li v-for="p in projekte" :key="p.id" class="crmsm-row" tabindex="0"
                    @click="selectStage('project', p)" @keydown.enter="selectStage('project', p)">
                  <span class="crmsm-rowname">{{ p.name }}</span>
                  <span class="crmsm-rowval">{{ money(p.value) }}</span>
                  <span class="crmsm-pill" data-tone="success"><i class="crmsm-dot" />{{ p.phase }}</span>
                </li>
                <li v-if="!projekte.length" class="crmsm-row crmsm-row--empty">{{ __('No active sales projects.') }}</li>
              </ul>
            </section>
          </div>
        </div>
      </div>
    </div>

    <!-- Erfassen (neuer Agenda-Punkt) -->
    <PpModal v-model:open="addOpen" :title="__('New agenda point')" :width="520">
      <form class="crmsm-form" @submit.prevent="submitAdd">
        <label class="crmsm-fld">
          <span class="crmsm-fld-cap">{{ __('Topic') }}</span>
          <input v-model="addForm.topic" type="text" class="crmsm-input" required autofocus />
        </label>
        <label class="crmsm-fld">
          <span class="crmsm-fld-cap">{{ __('Reference object') }}</span>
          <input v-model="addForm.object" type="text" class="crmsm-input" :placeholder="__('Deal, project, customer …')" />
        </label>
      </form>
      <template #footer>
        <Button :label="__('Cancel')" @click="addOpen = false" />
        <Button variant="solid" :label="__('Add')" :loading="adding" @click="submitAdd" />
      </template>
    </PpModal>

    <!-- Protokoll (Entscheide) -->
    <PpModal v-model:open="minutesOpen" :title="`${__('Minutes')} — ${meetingDateLabel}`" :width="600">
      <ul v-if="decisions.length" class="crmsm-minutes">
        <li v-for="(d, i) in decisions" :key="i" class="crmsm-minute">
          <span class="crmsm-minute-topic">{{ d.topic }}</span>
          <span v-if="d.object" class="crmsm-minute-obj">{{ d.object }}</span>
          <span class="crmsm-minute-dec">{{ d.decision || __('Decided — no note recorded.') }}</span>
          <span v-if="d.on" class="crmsm-minute-on">{{ fmtDate(d.on) }}</span>
        </li>
      </ul>
      <PpEmptyState v-else :icon="IconClipboard" :title="__('No decisions yet')" :hint="__('Decisions taken at the agenda points appear here.')" />
    </PpModal>
  </div>
</template>

<script setup>
import { computed, ref, watch, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { createResource, Breadcrumbs, Button } from 'frappe-ui'
import LayoutHeader from '@/components/LayoutHeader.vue'
import PpPageHead from '@/components/pp/PpPageHead.vue'
import PpDataGrid from '@/components/pp/PpDataGrid.vue'
import PpEmptyState from '@/components/pp/PpEmptyState.vue'
import PpFunctionBar from '@/components/pp/PpFunctionBar.vue'
import PpModal from '@/components/pp/PpModal.vue'
import IconClipboard from '~icons/lucide/clipboard-list'
import IconStar from '~icons/lucide/star'
import { usePilandaInspect } from '@/composables/usePilandaInspect'

const router = useRouter()
const { inspectNode } = usePilandaInspect()

const board = createResource({
  url: 'lcs_integrations.projects.api.get_sales_meeting_agenda',
  auto: true,
  onSuccess: () => { showDefaultInspector() },
})
const agenda = computed(() => board.data?.agenda || [])
const archivedCount = computed(() => board.data?.archived_count || 0)
const chancen = computed(() => board.data?.chancen || [])
const leads = computed(() => board.data?.leads || [])
const projekte = computed(() => board.data?.projekte || [])
const decisions = computed(() => board.data?.decisions || [])
const important = computed(() => board.data?.important || [])
const frame = computed(() => board.data?.frame || {})
const stageTotal = computed(() => chancen.value.length + leads.value.length + projekte.value.length)
const meetingDateLabel = computed(() => board.data?.meeting_date ? fmtDate(board.data.meeting_date) : '')
// PpDataGrid keys/emits on row.id — the agenda items are keyed by `name`.
const agendaRows = computed(() => agenda.value.map((a) => ({ ...a, id: a.name })))

const agendaCols = [
  { key: 'nr', label: '#', align: 'right', width: 44 },
  { key: 'topic', label: __('Topic'), pin: true, width: 300 },
  { key: 'object', label: __('Object'), width: 240 },
  { key: 'responsible', label: __('Responsible'), width: 150 },
  { key: 'status', label: __('Status'), width: 120 },
  { key: 'entscheid', label: __('Decision'), width: 130 },
]

// --- Status-Darstellung ----------------------------------------------------
const STATUS = {
  Open:     { label: __('Open'),     tone: 'info' },
  Decided:  { label: __('Decided'),  tone: 'success' },
  Archived: { label: __('Archived'), tone: 'muted' },
}
function statusLabel(s) { return STATUS[s]?.label || s }
function statusTone(s) { return STATUS[s]?.tone || 'info' }
function dealTone(s) {
  if (/negoti|verhand/i.test(s)) return 'warning'
  if (/won|gewonn/i.test(s)) return 'success'
  return 'info'
}

// --- Entscheiden / Archivieren (echte Mutationen) --------------------------
const flash = ref('')
const mutate = createResource({ url: 'lcs_integrations.projects.api.sales_meeting_decide' })
const archiver = createResource({ url: 'lcs_integrations.projects.api.sales_meeting_archive' })

function decide(row) {
  mutate.submit({ name: row.name }).then(() => {
    flash.value = `${__('Decided')}: „${row.topic}" — ${__('added to the minutes. Archiving stays the salesperson’s manual step.')}`
    board.reload()
  })
}
function archive(row) {
  archiver.submit({ name: row.name }).then(() => {
    flash.value = `„${row.topic}" ${__('archived (manually by the salesperson).')}`
    board.reload()
  })
}

// --- Angedockter Inspektor: Standardinhalt + Zeilen-Spezifikation ----------
function showDefaultInspector() {
  const f = frame.value
  inspectNode({
    title: __('Sales Meeting'),
    badge: { label: meetingDateLabel.value, tone: 'brand' },
    rows: [
      { label: __('Open points'), value: String(f.open_points ?? agenda.value.length) },
      { label: __('Flagged important'), value: String(f.important ?? important.value.length) },
      { label: __('Opportunities'), value: String(f.opportunities ?? chancen.value.length) },
      { label: __('Leads'), value: String(f.leads ?? leads.value.length) },
      { label: __('Sales projects'), value: String(f.projects ?? projekte.value.length) },
    ],
    sections: [
      {
        title: __('Recent decisions'),
        items: decisions.value.map((d) => ({ text: `${d.topic}${d.object ? ' · ' + d.object : ''}`, muted: d.decision || '' })),
        empty: __('No decisions yet.'),
      },
    ],
  })
}

function onAgendaClick(id) {
  const row = agenda.value.find((a) => a.name === id)
  if (!row) return
  inspectNode({
    title: row.topic,
    badge: { label: statusLabel(row.status), tone: statusTone(row.status) },
    rows: [
      { label: __('Object'), value: row.object || '—' },
      { label: __('Responsible'), value: shortUser(row.responsible) || '—' },
    ],
    sections: [
      {
        title: __('Decision'),
        items: row.decision ? [{ text: row.decision }] : [],
        empty: __('Not decided yet.'),
      },
    ],
    action: row.ref_name ? { label: __('Open object'), onClick: () => openRef(row) } : undefined,
  })
}

function selectStage(kind, o) {
  const cfg = {
    deal:    { badge: __('Opportunity'), tone: 'info', rows: [{ label: __('Customer'), value: o.org || '—' }, { label: __('Value'), value: money(o.value) }, { label: __('Status'), value: o.status }] },
    lead:    { badge: __('Lead'), tone: 'warning', rows: [{ label: __('Organization'), value: o.org || '—' }, { label: __('Owner'), value: shortUser(o.owner) || '—' }, { label: __('Status'), value: o.status }] },
    project: { badge: __('Sales project'), tone: 'success', rows: [{ label: __('Number'), value: o.nr || '—' }, { label: __('Phase'), value: o.phase }, { label: __('Value'), value: money(o.value) }] },
  }[kind]
  inspectNode({
    title: o.name,
    badge: { label: cfg.badge, tone: cfg.tone },
    rows: cfg.rows,
    action: { label: __('Open'), onClick: () => openStage(kind, o) },
  })
}

function openRef(row) {
  const dt = row.ref_doctype
  if (dt === 'CRM Deal') router.push({ name: 'Deal', params: { dealId: row.ref_name } })
  else if (dt === 'CRM Lead') router.push({ name: 'Lead', params: { leadId: row.ref_name } })
  else if (dt === 'LCS Project') router.push({ name: 'LCS Project', params: { id: row.ref_name } })
}
function openStage(kind, o) {
  if (kind === 'deal') router.push({ name: 'Deal', params: { dealId: o.id } })
  else if (kind === 'lead') router.push({ name: 'Lead', params: { leadId: o.id } })
  else if (kind === 'project') router.push({ name: 'LCS Project', params: { id: o.id } })
}

// --- Flagged important (cross-entity star flags) ---------------------------
const ENTITY = {
  project: { label: __('Project'), route: 'LCS Project', param: 'id' },
  lead: { label: __('Lead'), route: 'Lead', param: 'leadId' },
  deal: { label: __('Opportunity'), route: 'Deal', param: 'dealId' },
}
function entityLabel(e) { return ENTITY[e]?.label || e }
function openImportant(it) {
  const cfg = ENTITY[it.entity]
  if (cfg) router.push({ name: cfg.route, params: { [cfg.param]: it.name } })
}

// --- FunctionBar-Aktionen + Modals -----------------------------------------
const barOpen = ref(false)
const pageActions = [
  { id: 'add', label: __('Add point'), primary: true },
  { id: 'protokoll', label: __('Minutes') },
  { id: 'refresh', label: __('Refresh') },
]
function onAction(id) {
  if (id === 'add') openAdd()
  else if (id === 'protokoll') minutesOpen.value = true
  else if (id === 'refresh') board.reload()
}

const addOpen = ref(false)
const adding = ref(false)
const addForm = ref({ topic: '', object: '' })
const adder = createResource({ url: 'lcs_integrations.projects.api.sales_meeting_add' })
function openAdd() { addForm.value = { topic: '', object: '' }; addOpen.value = true }
function submitAdd() {
  if (!addForm.value.topic.trim()) return
  adding.value = true
  adder.submit({ topic: addForm.value.topic.trim(), reference_object: addForm.value.object.trim() })
    .then(() => {
      addOpen.value = false
      flash.value = `${__('Agenda point added')}: „${addForm.value.topic.trim()}"`
      board.reload()
    })
    .finally(() => { adding.value = false })
}

const minutesOpen = ref(false)

// Standardinhalt neu setzen, wenn Entscheide/Rahmen sich ändern (nach reload).
watch(decisions, () => { showDefaultInspector() })
onBeforeUnmount(() => inspectNode(null))

// --- Formathelfer ----------------------------------------------------------
function money(v) {
  const n = Number(v) || 0
  if (n >= 1_000_000) return '€' + (n / 1_000_000).toFixed(1) + ' Mio'
  if (n >= 1_000) return '€' + Math.round(n / 1_000) + 'k'
  return '€' + Math.round(n)
}
function shortUser(u) { return (u || '').split('@')[0] }
function fmtDate(d) {
  try {
    return new Intl.DateTimeFormat('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric' }).format(new Date(String(d).replace(' ', 'T')))
  } catch { return String(d) }
}
</script>

<style scoped>
.crmsm { flex: 1; min-height: 0; overflow: auto; background: var(--pp-bg-base); }
.crmsm-inner { width: 100%; margin: 0; padding: var(--pp-space-6) var(--pp-space-6) var(--pp-space-12);
  display: flex; flex-direction: column; gap: var(--pp-space-5); }

/* Positionierter Canvas — die absolute FunctionBar füllt hier den oberen Rand. */
.crmsm-canvas { position: relative; display: flex; flex-direction: column; gap: var(--pp-space-5); }

.crmsm-flash { margin: 0; padding: var(--pp-space-2) var(--pp-space-4); font-size: var(--pp-fs-13, 13px);
  color: var(--pp-brand-primary); background: var(--pp-accent-soft);
  border: 1px solid var(--pp-border-subtle); border-radius: var(--pp-radius-ui); }

.crmsm-card { background: var(--pp-bg-surface); border: 1px solid var(--pp-border-subtle);
  border-radius: var(--pp-radius-ui); box-shadow: var(--pp-shadow-xs); padding: var(--pp-space-2); overflow: hidden; }

/* Flagged important (entitätsübergreifend) */
.crmsm-important { padding: 0; }
.crmsm-important-head { display: flex; align-items: center; gap: 6px; padding: var(--pp-space-2) var(--pp-space-4);
  border-bottom: 1px solid var(--pp-border-subtle); background: color-mix(in oklab, var(--pp-state-warning) 8%, transparent);
  font-size: var(--pp-fs-12, 12px); font-weight: var(--pp-weight-bold); letter-spacing: var(--pp-tracking-wide, 0.04em);
  text-transform: uppercase; color: var(--pp-state-warning); }
.crmsm-important-star { width: 14px; height: 14px; }
.crmsm-important-head .crmsm-ch-m { text-transform: none; letter-spacing: normal; font-weight: var(--pp-weight-regular); }
.crmsm-important-list { display: flex; flex-direction: column; }
.crmsm-important-row { appearance: none; cursor: pointer; text-align: left; font-family: inherit;
  display: flex; align-items: center; gap: var(--pp-space-3); padding: var(--pp-space-2) var(--pp-space-4);
  border: 0; border-top: 1px solid var(--pp-border-subtle); background: transparent; }
.crmsm-important-row:first-child { border-top: 0; }
.crmsm-important-row:hover { background: var(--pp-bg-hover); }
.crmsm-important-main { min-width: 0; flex: 1; display: flex; flex-direction: column; }
.crmsm-important-title { font-size: var(--pp-fs-13, 13px); font-weight: var(--pp-weight-medium); color: var(--pp-text-primary);
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.crmsm-important-sub { font-size: 11px; color: var(--pp-text-tertiary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.crmsm-important-val { flex-shrink: 0; font-size: var(--pp-fs-13, 13px); font-weight: var(--pp-weight-medium);
  color: var(--pp-text-secondary); font-variant-numeric: tabular-nums; }
.crmsm-ent { flex-shrink: 0; font-size: 10px; font-weight: var(--pp-weight-bold); text-transform: uppercase;
  padding: 2px var(--pp-space-2); border-radius: var(--pp-radius-ui); }
.crmsm-ent[data-ent="project"] { background: color-mix(in oklab, var(--pp-state-success) 14%, transparent); color: var(--pp-state-success); }
.crmsm-ent[data-ent="lead"]    { background: color-mix(in oklab, var(--pp-state-warning) 16%, transparent); color: var(--pp-state-warning); }
.crmsm-ent[data-ent="deal"]    { background: color-mix(in oklab, var(--pp-state-info) 14%, transparent); color: var(--pp-state-info); }
.crmsm-ch { display: flex; align-items: baseline; gap: var(--pp-space-2); padding: var(--pp-space-2) var(--pp-space-3) var(--pp-space-3);
  font-size: var(--pp-fs-13, 13px); font-weight: var(--pp-weight-semibold); color: var(--pp-text-primary); }
.crmsm-ch-m { font-size: 11px; font-weight: var(--pp-weight-regular); color: var(--pp-text-tertiary); }
.crmsm-note { margin: 0; padding: var(--pp-space-2) var(--pp-space-3) 0; font-size: 11px; color: var(--pp-text-tertiary); }

/* Drei Stufen nebeneinander (bricht auf schmalen Breiten um) */
.crmsm-stages { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: var(--pp-space-4); }

.crmsm-list { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; }
.crmsm-row { display: flex; align-items: center; gap: var(--pp-space-2); padding: var(--pp-space-2) var(--pp-space-3);
  border-top: 1px solid var(--pp-border-subtle); cursor: pointer; }
.crmsm-row:first-child { border-top: 0; }
.crmsm-row:hover { background: var(--pp-bg-hover); }
.crmsm-row:focus-visible { outline: none; box-shadow: var(--pp-shadow-focus-ring); border-radius: var(--pp-radius-ui); }
.crmsm-row--empty { cursor: default; color: var(--pp-text-tertiary); font-size: var(--pp-fs-12, 12px); font-style: italic; }
.crmsm-row--empty:hover { background: transparent; }
.crmsm-rowname { flex: 1; min-width: 0; font-size: var(--pp-fs-13, 13px); color: var(--pp-text-primary);
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.crmsm-rowsub { flex-shrink: 0; max-width: 40%; font-size: 11px; color: var(--pp-text-tertiary);
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.crmsm-rowval { flex-shrink: 0; font-size: var(--pp-fs-12, 12px); font-weight: var(--pp-weight-medium);
  color: var(--pp-text-secondary); font-variant-numeric: tabular-nums; }

.crmsm-btn { appearance: none; cursor: pointer; font-family: inherit; font-size: 11px; font-weight: var(--pp-weight-medium);
  padding: 3px var(--pp-space-2); border: 1px solid var(--pp-border-default); border-radius: var(--pp-radius-ui);
  background: var(--pp-bg-base); color: var(--pp-text-secondary); white-space: nowrap; }
.crmsm-btn:hover { border-color: var(--pp-brand-primary); color: var(--pp-brand-primary); }
.crmsm-btn.is-primary { background: var(--pp-brand-primary); border-color: var(--pp-brand-primary); color: #fff; }
.crmsm-btn.is-primary:hover { color: #fff; opacity: 0.92; }

.crmsm-pill { display: inline-flex; align-items: center; gap: 5px; font-size: 11px; font-weight: var(--pp-weight-semibold);
  padding: 2px var(--pp-space-2); border-radius: var(--pp-radius-full); white-space: nowrap; flex-shrink: 0; }
.crmsm-dot { width: 6px; height: 6px; border-radius: var(--pp-radius-full); flex-shrink: 0; background: currentColor; }
.crmsm-pill[data-tone="info"]    { background: color-mix(in oklab, var(--pp-state-info) 14%, transparent); color: var(--pp-state-info); }
.crmsm-pill[data-tone="warning"] { background: color-mix(in oklab, var(--pp-state-warning) 16%, transparent); color: var(--pp-state-warning); }
.crmsm-pill[data-tone="success"] { background: color-mix(in oklab, var(--pp-state-success) 16%, transparent); color: var(--pp-state-success); }
.crmsm-pill[data-tone="muted"]   { background: var(--pp-bg-sunken); color: var(--pp-text-tertiary); }

/* Modal-Formular */
.crmsm-form { display: flex; flex-direction: column; gap: var(--pp-space-4); }
.crmsm-fld { display: flex; flex-direction: column; gap: 4px; }
.crmsm-fld-cap { font-size: 10px; font-weight: var(--pp-weight-bold); letter-spacing: 0.04em;
  text-transform: uppercase; color: var(--pp-text-tertiary); }
.crmsm-input { appearance: none; font-family: inherit; font-size: var(--pp-fs-13, 13px); color: var(--pp-text-primary);
  padding: 7px var(--pp-space-3); border: 1px solid var(--pp-border-default); border-radius: var(--pp-radius-ui);
  background: var(--pp-bg-base); }
.crmsm-input:focus { outline: none; border-color: var(--pp-brand-primary); box-shadow: 0 0 0 3px rgb(var(--pp-brand-primary-rgb) / 0.15); }

/* Protokoll */
.crmsm-minutes { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: var(--pp-space-2); }
.crmsm-minute { display: grid; grid-template-columns: 1fr auto; gap: 2px var(--pp-space-3);
  padding: var(--pp-space-3); border: 1px solid var(--pp-border-subtle); border-radius: var(--pp-radius-ui); background: var(--pp-bg-base); }
.crmsm-minute-topic { font-size: var(--pp-fs-13, 13px); font-weight: var(--pp-weight-semibold); color: var(--pp-text-primary); }
.crmsm-minute-obj { grid-column: 1; font-size: 11px; color: var(--pp-text-tertiary); }
.crmsm-minute-dec { grid-column: 1 / -1; font-size: var(--pp-fs-13, 13px); color: var(--pp-text-secondary); }
.crmsm-minute-on { grid-row: 1; grid-column: 2; font-size: 11px; color: var(--pp-text-tertiary); font-variant-numeric: tabular-nums; }

@media (max-width: 1080px) {
  .crmsm-stages { grid-template-columns: 1fr; }
}
@media (max-width: 560px) {
  .crmsm-inner { padding: var(--pp-space-4) var(--pp-space-4) var(--pp-space-10); }
}
</style>
