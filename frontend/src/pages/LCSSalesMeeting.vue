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
          <select
            v-if="meetingDates.length"
            v-model="selectedDate"
            class="crmsm-meetpick"
            :title="__('Select meeting (past meetings are read-only)')"
          >
            <option :value="null">{{ __('Current meeting') }}</option>
            <option v-for="m in meetingOptions" :key="m.value" :value="m.value">{{ m.label }}</option>
          </select>
          <Button :label="__('Insights')" iconLeft="bar-chart-2" @click="$router.push({ name: 'LCS Forecasting' })" />
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

        <!-- Tabs: Protokoll + die vier Excel-Listen -->
        <nav class="crmsm-tabs">
          <button v-for="t in TABS" :key="t.key" type="button" class="crmsm-tab"
                  :class="{ 'is-active': tab === t.key }" @click="tab = t.key">
            {{ t.label }}<span v-if="t.count != null" class="crmsm-tabcount">{{ t.count }}</span>
          </button>
        </nav>

        <!-- Actions live in the shell PpFunctionBar (toggled by the inspector
             burger); the page only registers its action groups. -->
        <div class="crmsm-canvas">
          <p v-if="readonly" class="crmsm-robanner" role="status">
            {{ __('Archived meeting') }} {{ meetingDateLabel }} — {{ __('read-only.') }}
            <button type="button" class="crmsm-rolink" @click="selectedDate = null">{{ __('Back to current meeting') }}</button>
          </p>
          <p v-if="flash" class="crmsm-flash" role="status">{{ flash }}</p>

          <template v-if="tab === 'protokoll'">
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
                <PpPill v-if="it.status" tone="info">{{ it.status }}</PpPill>
                <span v-if="it.value" class="crmsm-important-val">{{ money(it.value) }}</span>
              </button>
            </div>
          </section>

          <!-- Agenda: Entscheid direkt am Punkt -->
          <PpTableCard
            :title="`${__('Agenda')} ${meetingDateLabel}`"
            :note="__('Decide at the point · done items are archived manually · row = detail in the inspector')"
          >
            <PpDataGrid v-if="agenda.length" :columns="agendaCols" :rows="agendaRows" @row-click="onAgendaClick">
              <template #cell-status="{ value }">
                <PpPill :tone="statusTone(value)">{{ statusLabel(value) }}</PpPill>
              </template>
              <template #cell-entscheid="{ row }">
                <span v-if="readonly" class="crmsm-ro-dec">{{ row.decision || '—' }}</span>
                <div v-else class="crmsm-rowacts" @click.stop>
                  <button v-if="row.status === 'Decided'" type="button" class="crmsm-btn" @click="archive(row)">
                    {{ __('Archive') }}
                  </button>
                  <button v-else type="button" class="crmsm-btn is-primary" @click="decide(row)">
                    {{ __('Decided') }}
                  </button>
                  <button type="button" class="crmsm-btn crmsm-btn--danger" :title="__('Remove point')" @click="remove(row)">
                    <IconTrash class="crmsm-btn-ic" />
                  </button>
                </div>
              </template>
            </PpDataGrid>

            <PpEmptyState
              v-else
              :icon="IconClipboard"
              :title="board.loading ? __('Loading agenda …') : __('No open agenda points')"
              :hint="board.loading ? '' : __('Add a point via the actions bar to start the meeting.')"
            />

            <template v-if="archivedCount" #footer>
              {{ archivedCount }} {{ __('archived point(s)') }} — {{ __('archive via the “Minutes” action.') }}
            </template>
          </PpTableCard>

          <!-- Drei Stufen (kompakte Karten) -->
          <div class="crmsm-stages">
            <section class="crmsm-card">
              <header class="crmsm-ch">{{ __('Opportunities') }}<span class="crmsm-ch-m">{{ chancen.length }} {{ __('open') }}</span></header>
              <ul class="crmsm-list">
                <li v-for="c in chancen" :key="c.id" class="crmsm-row" tabindex="0"
                    @click="selectStage('deal', c)" @keydown.enter="selectStage('deal', c)">
                  <span class="crmsm-rowname">{{ c.name }}</span>
                  <span class="crmsm-rowval">{{ money(c.value) }}</span>
                  <PpPill :tone="dealTone(c.status)">{{ c.status }}</PpPill>
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
                  <PpPill tone="info">{{ l.status }}</PpPill>
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
                  <PpPill tone="success">{{ p.phase }}</PpPill>
                </li>
                <li v-if="!projekte.length" class="crmsm-row crmsm-row--empty">{{ __('No active sales projects.') }}</li>
              </ul>
            </section>
          </div>
          </template>

          <!-- Angebote in Bearbeitung / Aufträge / Angebote in Evidenz -->
          <template v-else-if="tab === 'offers' || tab === 'orders' || tab === 'evidenz'">
            <PpTableCard :title="tabTitle" :note="__('Row = edit classification · Chance = LCS% × Kunde%')">
              <PpDataGrid v-if="pipeRows.length" :columns="pipeCols" :rows="pipeRows" :page-size="25" @row-click="editOffer">
                <template #cell-chance="{ row }"><b>{{ row.chance }}%</b></template>
                <template #cell-value="{ value }">{{ money(value) }}</template>
                <template #cell-weighted="{ value }">{{ money(value) }}</template>
                <template #cell-offer_status="{ value }">
                  <PpPill v-if="value" :tone="offerStatusTone(value)">{{ value }}</PpPill>
                </template>
              </PpDataGrid>
              <PpEmptyState v-else :icon="IconClipboard"
                :title="board.loading ? __('Loading …') : __('No entries in this list')" />
            </PpTableCard>
          </template>

          <!-- Wartung & Service -->
          <template v-else-if="tab === 'maintenance'">
            <PpTableCard :title="__('Maintenance & Service')" :note="__('Row = edit · trash = remove · add via the actions bar')">
              <PpDataGrid v-if="maintenance.length" :columns="maintCols" :rows="maintenance" :page-size="25" @row-click="editMaint">
                <template #cell-act="{ row }">
                  <button type="button" class="crmsm-btn crmsm-btn--danger" :title="__('Remove')" @click.stop="removeMaint(row)">
                    <IconTrash class="crmsm-btn-ic" />
                  </button>
                </template>
              </PpDataGrid>
              <PpEmptyState v-else :icon="IconClipboard" :title="__('No maintenance items')"
                :hint="__('Add one via the actions bar.')" />
            </PpTableCard>
          </template>
        </div>
      </div>
    </div>

    <!-- Angebot-Klassifizierung bearbeiten -->
    <PpModal v-model:open="offerOpen" :title="offerDraft.project_name || __('Offer')" :width="620">
      <div class="crmsm-form">
        <div class="crmsm-frow">
          <label class="crmsm-fld"><span class="crmsm-fld-cap">{{ __('Solution / Produkt') }}</span>
            <select v-model="offerDraft.solution" class="crmsm-input">
              <option value="">—</option><option v-for="o in opts.solution_options" :key="o" :value="o">{{ o }}</option>
            </select></label>
          <label class="crmsm-fld"><span class="crmsm-fld-cap">{{ __('Sector / Sektor') }}</span>
            <select v-model="offerDraft.sector" class="crmsm-input">
              <option value="">—</option><option v-for="o in opts.sector_options" :key="o" :value="o">{{ o }}</option>
            </select></label>
        </div>
        <div class="crmsm-frow">
          <label class="crmsm-fld"><span class="crmsm-fld-cap">{{ __('Sales Type') }}</span>
            <select v-model="offerDraft.sales_type" class="crmsm-input">
              <option value="">—</option><option v-for="o in opts.sales_type_options" :key="o" :value="o">{{ o }}</option>
            </select></label>
          <label class="crmsm-fld"><span class="crmsm-fld-cap">{{ __('Angebots-Status') }}</span>
            <select v-model="offerDraft.offer_status" class="crmsm-input">
              <option value="">—</option><option v-for="o in opts.offer_status_options" :key="o" :value="o">{{ o }}</option>
            </select></label>
        </div>
        <div class="crmsm-frow">
          <label class="crmsm-fld"><span class="crmsm-fld-cap">{{ __('Chance LCS') }} (%)</span>
            <input v-model.number="offerDraft.chance_lcs" type="number" min="0" max="100" class="crmsm-input" /></label>
          <label class="crmsm-fld"><span class="crmsm-fld-cap">{{ __('Chance Projekt/Kunde') }} (%)</span>
            <input v-model.number="offerDraft.chance_customer" type="number" min="0" max="100" class="crmsm-input" /></label>
          <label class="crmsm-fld"><span class="crmsm-fld-cap">{{ __('Chance') }}</span>
            <input :value="offerChance + ' %'" type="text" class="crmsm-input" readonly /></label>
        </div>
        <div class="crmsm-frow">
          <label class="crmsm-fld"><span class="crmsm-fld-cap">{{ __('Fällig') }}</span>
            <input v-model="offerDraft.due" type="text" class="crmsm-input" placeholder="KW10 …" /></label>
          <label class="crmsm-fld crmsm-fld--chk">
            <input v-model="offerDraft.in_evidenz" type="checkbox" /> {{ __('In Evidenz (geparkt)') }}
          </label>
        </div>
        <label class="crmsm-fld"><span class="crmsm-fld-cap">{{ __('Grund Ablehnung') }}</span>
          <textarea v-model="offerDraft.rejection_reason" rows="2" class="crmsm-input" /></label>

        <!-- Kommentar-Thread (jeder darf) -->
        <div v-if="commentName" class="crmsm-comments">
          <div class="crmsm-fld-cap">{{ __('Kommentare & Bewertungen') }}</div>
          <div class="crmsm-cadd">
            <textarea v-model="commentInput" rows="2" class="crmsm-input" :placeholder="__('Kommentar / Bewertung …')" />
            <button type="button" class="crmsm-btn is-primary" :disabled="!commentInput.trim() || commentBusy" @click="addComment">{{ __('Post') }}</button>
          </div>
          <ul class="crmsm-clist">
            <li v-for="c in comments" :key="c.name" class="crmsm-citem">
              <div class="crmsm-cmeta"><b>{{ c.author }}</b> · {{ cTime(c.creation) }}
                <button v-if="c.mine" type="button" class="crmsm-cdel" :title="__('Delete')" @click="deleteComment(c)">✕</button>
              </div>
              <div class="crmsm-ctext" v-html="c.content" />
            </li>
            <li v-if="!comments.length" class="crmsm-cempty">{{ __('No comments yet.') }}</li>
          </ul>
        </div>

        <div class="crmsm-decide-foot">
          <button type="button" class="crmsm-btn" @click="offerOpen = false">{{ __('Cancel') }}</button>
          <button type="button" class="crmsm-btn is-primary" :disabled="offerSaving" @click="saveOffer">{{ __('Save') }}</button>
        </div>
      </div>
    </PpModal>

    <!-- Wartungspunkt erfassen/bearbeiten -->
    <PpModal v-model:open="maintOpen" :title="maintDraft.name ? __('Edit maintenance item') : __('New maintenance item')" :width="560">
      <div class="crmsm-form">
        <label class="crmsm-fld"><span class="crmsm-fld-cap">{{ __('Projekt / Titel') }}</span>
          <input v-model="maintDraft.title" type="text" class="crmsm-input" required autofocus /></label>
        <div class="crmsm-frow">
          <label class="crmsm-fld"><span class="crmsm-fld-cap">PL/PN</span>
            <input v-model="maintDraft.pl_pn" type="text" class="crmsm-input" /></label>
          <label class="crmsm-fld"><span class="crmsm-fld-cap">{{ __('Fällig') }}</span>
            <input v-model="maintDraft.due" type="text" class="crmsm-input" /></label>
        </div>
        <label class="crmsm-fld"><span class="crmsm-fld-cap">{{ __('Kommentar') }}</span>
          <textarea v-model="maintDraft.comment" rows="2" class="crmsm-input" /></label>
        <label class="crmsm-fld"><span class="crmsm-fld-cap">{{ __('Aktion') }}</span>
          <textarea v-model="maintDraft.action" rows="2" class="crmsm-input" /></label>

        <!-- Kommentar-Thread (jeder darf) -->
        <div v-if="commentName" class="crmsm-comments">
          <div class="crmsm-fld-cap">{{ __('Kommentare & Bewertungen') }}</div>
          <div class="crmsm-cadd">
            <textarea v-model="commentInput" rows="2" class="crmsm-input" :placeholder="__('Kommentar / Bewertung …')" />
            <button type="button" class="crmsm-btn is-primary" :disabled="!commentInput.trim() || commentBusy" @click="addComment">{{ __('Post') }}</button>
          </div>
          <ul class="crmsm-clist">
            <li v-for="c in comments" :key="c.name" class="crmsm-citem">
              <div class="crmsm-cmeta"><b>{{ c.author }}</b> · {{ cTime(c.creation) }}
                <button v-if="c.mine" type="button" class="crmsm-cdel" :title="__('Delete')" @click="deleteComment(c)">✕</button>
              </div>
              <div class="crmsm-ctext" v-html="c.content" />
            </li>
            <li v-if="!comments.length" class="crmsm-cempty">{{ __('No comments yet.') }}</li>
          </ul>
        </div>

        <div class="crmsm-decide-foot">
          <button type="button" class="crmsm-btn" @click="maintOpen = false">{{ __('Cancel') }}</button>
          <button type="button" class="crmsm-btn is-primary" :disabled="maintSaving" @click="saveMaint">{{ __('Save') }}</button>
        </div>
      </div>
    </PpModal>

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

    <!-- Entscheiden: zeigt WAS entschieden werden muss + erfasst den Entscheid -->
    <PpModal v-model:open="decideOpen" :title="__('Take a decision')" :width="520">
      <div v-if="decideItem" class="crmsm-decide">
        <div class="crmsm-decide-cap">{{ __('To be decided') }}</div>
        <div class="crmsm-decide-topic">{{ decideItem.topic }}</div>
        <dl class="crmsm-decide-meta">
          <div v-if="decideItem.object"><dt>{{ __('Object') }}</dt><dd>{{ decideItem.object }}</dd></div>
          <div v-if="decideItem.responsible"><dt>{{ __('Responsible') }}</dt><dd>{{ decideItem.responsible }}</dd></div>
        </dl>
        <label class="crmsm-decide-cap" for="sm-decision">{{ __('Decision') }}</label>
        <textarea id="sm-decision" v-model="decideText" rows="3" class="crmsm-input" :placeholder="__('What was decided?')" autofocus />
        <div class="crmsm-decide-foot">
          <button type="button" class="crmsm-btn" @click="decideOpen = false">{{ __('Cancel') }}</button>
          <button type="button" class="crmsm-btn is-primary" :disabled="mutate.loading" @click="confirmDecide">{{ __('Confirm decision') }}</button>
        </div>
      </div>
    </PpModal>
  </div>
</template>

<script setup>
import { computed, ref, watch, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { createResource, Breadcrumbs, Button } from 'frappe-ui'
import LayoutHeader from '@/components/LayoutHeader.vue'
import PpPageHead from '@/components/pp/PpPageHead.vue'
import PpDataGrid from '@/components/pp/PpDataGrid.vue'
import PpTableCard from '@/components/pp/PpTableCard.vue'
import PpPill from '@/components/pp/PpPill.vue'
import PpEmptyState from '@/components/pp/PpEmptyState.vue'
import PpModal from '@/components/pp/PpModal.vue'
import IconClipboard from '~icons/lucide/clipboard-list'
import IconStar from '~icons/lucide/star'
import IconTrash from '~icons/lucide/trash-2'
import { usePilandaInspect } from '@/composables/usePilandaInspect'
import { usePilandaFuncbar } from '@/composables/usePilandaFuncbar'

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

// --- Meeting-Auswahl (Archiv: alte Meetings schreibgeschützt ansehen) -------
const datesRes = createResource({
  url: 'lcs_integrations.projects.api.get_sales_meeting_dates',
  auto: true,
})
const meetingDates = computed(() => datesRes.data || [])
const latestDate = computed(() => meetingDates.value[0]?.date || null)
// null = aktuelles (jüngstes) Meeting; sonst ein gewähltes Archiv-Datum.
const selectedDate = ref(null)
// Schreibgeschützt, sobald ein Datum gewählt ist, das nicht das jüngste ist.
const readonly = computed(() => !!selectedDate.value && selectedDate.value !== latestDate.value)
const meetingOptions = computed(() =>
  meetingDates.value.map((m, i) => ({
    value: m.date,
    label: (i === 0 ? __('Current') + ' · ' : '') + fmtDate(m.date)
      + (m.total ? ` · ${m.total} ${__('points')}` : ''),
  })),
)
function loadMeeting() {
  board.submit({
    meeting_date: selectedDate.value || null,
    include_archived: readonly.value ? 1 : 0,
  })
}
watch(selectedDate, () => {
  if (readonly.value) tab.value = 'protokoll'
  loadMeeting()
})
// PpDataGrid keys/emits on row.id — the agenda items are keyed by `name`.
const agendaRows = computed(() => agenda.value.map((a) => ({ ...a, id: a.name })))

const agendaCols = [
  { key: 'nr', label: '#', align: 'right', width: 44 },
  { key: 'topic', label: __('Topic'), width: 300 },
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

// Deciding opens a dialog that first shows WHAT has to be decided (topic +
// context) and captures the decision, instead of silently marking it decided.
const decideOpen = ref(false)
const decideItem = ref(null)
const decideText = ref('')
function decide(row) {
  decideItem.value = row
  decideText.value = row.decision || ''
  decideOpen.value = true
}
function confirmDecide() {
  const row = decideItem.value
  if (!row) return
  mutate.submit({ name: row.name, decision: decideText.value.trim() || null }).then(() => {
    flash.value = `${__('Decided')}: „${row.topic}" — ${__('added to the minutes.')}`
    decideOpen.value = false
    board.reload()
  })
}
function archive(row) {
  archiver.submit({ name: row.name }).then(() => {
    flash.value = `„${row.topic}" ${__('archived (manually by the salesperson).')}`
    board.reload()
  })
}

// Delete an agenda point entirely (e.g. added by mistake).
const remover = createResource({ url: 'lcs_integrations.projects.api.sales_meeting_remove' })
function remove(row) {
  remover.submit({ name: row.name }).then(() => {
    flash.value = `${__('Agenda point removed')}: „${row.topic}"`
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
    ref: row.ref_name && row.ref_doctype
      ? { doctype: row.ref_doctype, name: row.ref_name, title: row.topic }
      : { title: row.topic },
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
    ref: { doctype: { deal: 'CRM Deal', lead: 'CRM Lead', project: 'LCS Project' }[kind], name: o.id, title: o.name },
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
// Registered with the shell function bar; the inspector burger toggles it open
// (closed by default). No page-local trigger.
// --- Tabs: Protokoll + die vier Excel-Listen (Angebote/Aufträge/Evidenz/Wartung)
const tab = ref('protokoll')
const smRes = createResource({ url: 'lcs_integrations.projects.api.get_sales_meeting_lists', auto: true })
const offers = computed(() => smRes.data?.offers || [])
const orders = computed(() => smRes.data?.orders || [])
const evidenz = computed(() => smRes.data?.evidenz || [])
const maintenance = computed(() => smRes.data?.maintenance || [])
const opts = computed(() => smRes.data || {})
const TABS = computed(() => {
  const all = [
    { key: 'protokoll', label: __('Protokoll'), count: agenda.value.length },
    { key: 'offers', label: __('Angebote'), count: offers.value.length },
    { key: 'orders', label: __('Aufträge'), count: orders.value.length },
    { key: 'evidenz', label: __('Evidenz'), count: evidenz.value.length },
    { key: 'maintenance', label: __('Wartung'), count: maintenance.value.length },
  ]
  // Archiv-Ansicht: nur das (historische) Protokoll, die Live-Listen sind
  // keine Meeting-Momentaufnahmen.
  return readonly.value ? all.filter((t) => t.key === 'protokoll') : all
})

const pipeRows = computed(() =>
  tab.value === 'orders' ? orders.value : tab.value === 'evidenz' ? evidenz.value : offers.value)
const tabTitle = computed(() =>
  tab.value === 'orders' ? __('Aufträge')
    : tab.value === 'evidenz' ? __('Angebote in Evidenz') : __('Angebote in Bearbeitung'))
const pipeCols = [
  { key: 'project_number', label: 'PL/PN', width: 110 },
  { key: 'project_name', label: __('Projekt'), width: 220 },
  { key: 'solution', label: __('Produkt'), width: 130 },
  { key: 'sector', label: __('Sektor'), width: 130 },
  { key: 'sales_type', label: 'Sales Type', width: 110 },
  { key: 'offer_status', label: __('Status'), width: 120 },
  { key: 'chance', label: 'Chance', align: 'right', width: 80 },
  { key: 'value', label: __('Volumen'), align: 'right', width: 120 },
  { key: 'weighted', label: __('Gewichtet'), align: 'right', width: 120 },
  { key: 'due', label: __('Fällig'), width: 90 },
]
function offerStatusTone(s) {
  if (/auftrag$/i.test(s)) return 'success'
  if (/erwartet/i.test(s)) return 'info'
  if (/konkurrenz|fehler|storniert|gestoppt/i.test(s)) return 'warning'
  return 'info'
}

// Angebot-Klassifizierung bearbeiten (schreibt aufs LCS Project).
const offerOpen = ref(false)
const offerSaving = ref(false)
const offerDraft = ref({})
const offerChance = computed(() => {
  const a = Number(offerDraft.value.chance_lcs) || 0
  const b = Number(offerDraft.value.chance_customer) || 0
  return Math.round((a / 100) * b * 10) / 10
})
function editOffer(id) {
  const r = pipeRows.value.find((x) => x.id === id)
  if (r) { offerDraft.value = { ...r }; offerOpen.value = true; loadComments('LCS Project', r.name) }
}
const offerSaver = createResource({ url: 'lcs_integrations.projects.api.save_project_meeting_fields' })
function saveOffer() {
  offerSaving.value = true
  const d = offerDraft.value
  offerSaver.submit({
    project: d.name,
    values: JSON.stringify({
      lcs_solution: d.solution || null, lcs_sector: d.sector || null,
      lcs_sales_type: d.sales_type || null, lcs_offer_status: d.offer_status || null,
      lcs_chance_lcs: Number(d.chance_lcs) || 0, lcs_chance_customer: Number(d.chance_customer) || 0,
      lcs_meeting_due: d.due || null, lcs_in_evidenz: d.in_evidenz ? 1 : 0,
      lcs_rejection_reason: d.rejection_reason || null,
    }),
  }).then(() => { offerOpen.value = false; smRes.reload() }).finally(() => { offerSaving.value = false })
}

// Wartung
const maintCols = [
  { key: 'title', label: __('Projekt / Titel'), width: 240 },
  { key: 'pl_pn', label: 'PL/PN', width: 100 },
  { key: 'comment', label: __('Kommentar'), width: 260 },
  { key: 'action', label: __('Aktion'), width: 200 },
  { key: 'responsible', label: __('Wer'), width: 120 },
  { key: 'due', label: __('Fällig'), width: 90 },
  { key: 'act', label: '', width: 44 },
]
const maintOpen = ref(false)
const maintSaving = ref(false)
const maintDraft = ref({})
function openMaint(row) {
  maintDraft.value = row ? { ...row } : { title: '', pl_pn: '', comment: '', action: '', due: '' }
  maintOpen.value = true
  loadComments('LCS Maintenance Item', row ? (row.id || row.name) : '')
}
function editMaint(id) { openMaint(maintenance.value.find((x) => x.id === id) || null) }
const maintAdder = createResource({ url: 'lcs_integrations.projects.api.maintenance_add' })
const maintSaver = createResource({ url: 'lcs_integrations.projects.api.maintenance_save' })
const maintRemover = createResource({ url: 'lcs_integrations.projects.api.maintenance_remove' })
function saveMaint() {
  if (!String(maintDraft.value.title || '').trim()) return
  maintSaving.value = true
  const d = maintDraft.value
  const p = d.name
    ? maintSaver.submit({ name: d.name, values: JSON.stringify({ title: d.title, pl_pn: d.pl_pn, comment: d.comment, action: d.action, due: d.due }) })
    : maintAdder.submit({ title: d.title, comment: d.comment, due: d.due })
  p.then(() => { maintOpen.value = false; smRes.reload() }).finally(() => { maintSaving.value = false })
}
function removeMaint(row) { maintRemover.submit({ name: row.id }).then(() => smRes.reload()) }

// --- Kommentar-Thread (offen für alle) -------------------------------------
const comments = ref([])
const commentInput = ref('')
const commentBusy = ref(false)
const commentDoctype = ref('')
const commentName = ref('')
const commentsRes = createResource({ url: 'lcs_integrations.projects.api.get_item_comments' })
const commentAdder = createResource({ url: 'lcs_integrations.projects.api.add_item_comment' })
const commentDeleter = createResource({ url: 'lcs_integrations.projects.api.delete_item_comment' })
function loadComments(doctype, name) {
  commentDoctype.value = doctype
  commentName.value = name || ''
  comments.value = []
  commentInput.value = ''
  if (!name) return
  commentsRes.submit({ doctype, name }).then((r) => { comments.value = r || [] })
}
function addComment() {
  const t = commentInput.value.trim()
  if (!t || !commentName.value) return
  commentBusy.value = true
  commentAdder.submit({ doctype: commentDoctype.value, name: commentName.value, content: t })
    .then((c) => { if (c && c.name) comments.value = [c, ...comments.value]; commentInput.value = '' })
    .finally(() => { commentBusy.value = false })
}
function deleteComment(c) {
  commentDeleter.submit({ name: c.name }).then(() => { comments.value = comments.value.filter((x) => x.name !== c.name) })
}
function cTime(v) {
  if (!v) return ''
  const d = new Date(String(v).replace(' ', 'T'))
  return isNaN(d) ? String(v) : d.toLocaleString('de-DE', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })
}

// --- Funcbar (aktionen tab-abhängig) ---------------------------------------
function currentActions() {
  if (readonly.value) return [{ id: 'refresh', label: __('Refresh') }]
  if (tab.value === 'maintenance')
    return [{ id: 'add-maint', label: __('New maintenance item'), primary: true }, { id: 'refresh', label: __('Refresh') }]
  if (tab.value === 'protokoll')
    return [{ id: 'add', label: __('Add point'), primary: true }, { id: 'protokoll', label: __('Minutes') }, { id: 'refresh', label: __('Refresh') }]
  return [{ id: 'refresh', label: __('Refresh') }]
}
function onAction(id) {
  if (id === 'add') openAdd()
  else if (id === 'protokoll') minutesOpen.value = true
  else if (id === 'add-maint') openMaint(null)
  else if (id === 'refresh') { board.reload(); smRes.reload() }
}
const { registerFuncbar, clearFuncbar } = usePilandaFuncbar()
function syncFuncbar() { registerFuncbar({ aktionen: currentActions() }, onAction) }
onMounted(syncFuncbar)
watch([tab, readonly], syncFuncbar)
onBeforeUnmount(() => clearFuncbar())

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

/* Meeting-Umschalter (Kopf) */
.crmsm-meetpick { appearance: none; font-family: inherit; font-size: var(--pp-fs-13, 13px);
  padding: 5px 26px 5px 10px; border-radius: var(--pp-radius-ui);
  border: 1px solid var(--pp-border-subtle); background: var(--pp-bg-surface); color: var(--pp-text-primary);
  background-image: linear-gradient(45deg, transparent 50%, var(--pp-text-tertiary) 50%),
    linear-gradient(135deg, var(--pp-text-tertiary) 50%, transparent 50%);
  background-position: right 12px center, right 7px center; background-size: 5px 5px, 5px 5px;
  background-repeat: no-repeat; cursor: pointer; }
.crmsm-meetpick:focus { outline: none; border-color: var(--pp-brand-primary); }

/* Archiv-Ansicht: Schreibgeschützt-Banner */
.crmsm-robanner { margin: 0; padding: var(--pp-space-2) var(--pp-space-4); font-size: var(--pp-fs-13, 13px);
  color: var(--pp-state-warning); background: color-mix(in oklab, var(--pp-state-warning) 10%, transparent);
  border: 1px solid color-mix(in oklab, var(--pp-state-warning) 30%, transparent); border-radius: var(--pp-radius-ui); }
.crmsm-rolink { appearance: none; border: 0; background: transparent; cursor: pointer; padding: 0 0 0 6px;
  font: inherit; color: var(--pp-brand-primary); text-decoration: underline; }
.crmsm-ro-dec { font-size: var(--pp-fs-13, 13px); color: var(--pp-text-secondary); }

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
.crmsm-rowacts { display: inline-flex; align-items: center; gap: var(--pp-space-2); }
.crmsm-btn--danger { display: inline-flex; align-items: center; justify-content: center; padding: 3px 5px; color: var(--pp-text-tertiary); }
.crmsm-btn--danger:hover { border-color: var(--pp-state-danger); color: var(--pp-state-danger); background: color-mix(in oklab, var(--pp-state-danger) 8%, transparent); }
.crmsm-btn-ic { width: 13px; height: 13px; }

/* Tabs */
.crmsm-tabs { display: flex; flex-wrap: wrap; gap: 2px; border-bottom: 1px solid var(--pp-border-subtle); margin-bottom: var(--pp-space-3); }
.crmsm-tab { appearance: none; cursor: pointer; font-family: inherit; font-size: var(--pp-fs-13, 13px); font-weight: var(--pp-weight-medium);
  padding: 8px 14px; border: 0; background: transparent; color: var(--pp-text-secondary); border-bottom: 2px solid transparent; }
.crmsm-tab:hover { color: var(--pp-brand-primary); }
.crmsm-tab.is-active { color: var(--pp-brand-primary); border-bottom-color: var(--pp-brand-primary); font-weight: var(--pp-weight-semibold); }
.crmsm-tabcount { margin-left: 6px; font-size: 11px; padding: 1px 6px; border-radius: var(--pp-radius-full);
  background: var(--pp-bg-sunken); color: var(--pp-text-tertiary); font-variant-numeric: tabular-nums; }
.crmsm-tab.is-active .crmsm-tabcount { background: color-mix(in oklab, var(--pp-brand-primary) 14%, transparent); color: var(--pp-brand-primary); }

/* Modal-Formularzeilen (mehrspaltig) */
.crmsm-frow { display: flex; flex-wrap: wrap; gap: var(--pp-space-3); }
.crmsm-frow .crmsm-fld { flex: 1; min-width: 140px; }
.crmsm-fld--chk { flex-direction: row; align-items: center; gap: 8px; font-size: var(--pp-fs-13, 13px); color: var(--pp-text-secondary); }

/* Kommentar-Thread */
.crmsm-comments { margin-top: var(--pp-space-3); border-top: 1px solid var(--pp-border-subtle); padding-top: var(--pp-space-2); }
.crmsm-cadd { display: flex; gap: var(--pp-space-2); align-items: flex-start; margin: var(--pp-space-2) 0; }
.crmsm-cadd .crmsm-input { flex: 1; }
.crmsm-clist { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: var(--pp-space-2); max-height: 240px; overflow-y: auto; }
.crmsm-citem { background: var(--pp-bg-base); border: 1px solid var(--pp-border-subtle); border-radius: var(--pp-radius-ui); padding: var(--pp-space-2) var(--pp-space-3); }
.crmsm-cmeta { font-size: 11px; color: var(--pp-text-tertiary); display: flex; align-items: center; gap: 6px; }
.crmsm-cmeta b { color: var(--pp-text-secondary); }
.crmsm-cdel { margin-left: auto; appearance: none; border: 0; background: transparent; cursor: pointer; color: var(--pp-text-tertiary); font-size: 12px; }
.crmsm-cdel:hover { color: var(--pp-state-danger); }
.crmsm-ctext { font-size: var(--pp-fs-13, 13px); color: var(--pp-text-primary); margin-top: 2px; word-break: break-word; }
.crmsm-cempty { font-size: var(--pp-fs-12, 12px); color: var(--pp-text-tertiary); }
/* Phone: comfortable ≥40px touch targets for Decide / Archive (the meeting's
   primary decide flow). Desktop stays compact in the dense agenda grid. */
@media (max-width: 767px) {
  .crmsm-btn { min-height: 40px; display: inline-flex; align-items: center; justify-content: center; padding: 8px 14px; }
}


/* Modal-Formular */
.crmsm-form { display: flex; flex-direction: column; gap: var(--pp-space-4); }
.crmsm-fld { display: flex; flex-direction: column; gap: 4px; }
.crmsm-fld-cap { font-size: 10px; font-weight: var(--pp-weight-bold); letter-spacing: 0.04em;
  text-transform: uppercase; color: var(--pp-text-tertiary); }
.crmsm-input { appearance: none; font-family: inherit; font-size: var(--pp-fs-13, 13px); color: var(--pp-text-primary);
  padding: 7px var(--pp-space-3); border: 1px solid var(--pp-border-default); border-radius: var(--pp-radius-ui);
  background: var(--pp-bg-base); }
.crmsm-input:focus { outline: none; border-color: var(--pp-brand-primary); box-shadow: 0 0 0 3px rgb(var(--pp-brand-primary-rgb) / 0.15); }
.crmsm-input { width: 100%; }

/* Entscheid-Dialog */
.crmsm-decide { display: flex; flex-direction: column; gap: var(--pp-space-2); }
.crmsm-decide-cap { font-size: 10px; font-weight: var(--pp-weight-bold); letter-spacing: 0.05em; text-transform: uppercase; color: var(--pp-text-tertiary); }
.crmsm-decide-topic { font-size: var(--pp-fs-16, 16px); font-weight: var(--pp-weight-semibold); color: var(--pp-text-primary); }
.crmsm-decide-meta { display: flex; flex-wrap: wrap; gap: var(--pp-space-2) var(--pp-space-5); margin: 0 0 var(--pp-space-2);
  padding: var(--pp-space-2) var(--pp-space-3); background: var(--pp-bg-sunken); border-radius: var(--pp-radius-ui); }
.crmsm-decide-meta dt { font-size: 10px; text-transform: uppercase; letter-spacing: 0.05em; color: var(--pp-text-tertiary); }
.crmsm-decide-meta dd { margin: 2px 0 0; font-size: var(--pp-fs-13, 13px); color: var(--pp-text-primary); }
.crmsm-decide-foot { display: flex; justify-content: flex-end; gap: var(--pp-space-2); margin-top: var(--pp-space-2); }

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
