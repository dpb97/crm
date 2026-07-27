<!--
  LCSNotes — Notizen-Seite (Vertrieb-Nav „Notizen", klickdummy „Notizen").
  ============================================================
  Notizen als Tabelle nach dem Klickdummy-Design: Filterleiste (Alle ·
  Sprachnotiz · Textnotiz + Suche), Karte „Notizen" mit Kopf-Notiz (N von M ·
  Zeile = Details im Inspektor) und die Spalten Notiz (+ Objekt) · Art ·
  Verfasser · Zeit. Einfachklick → angedockter Shell-Inspektor (Spec-Stil).

  Die Art-Spalte ist ECHT: FCRM Note = Textnotiz, LCS Audio Transcription Job
  = Sprachnotiz (Union). Daten: lcs_integrations.projects.api.get_notes.
-->
<template>
  <div class="flex min-h-0 flex-1 flex-col">
    <LayoutHeader>
      <template #left-header>
        <Breadcrumbs :items="[{ label: 'Vertrieb' }, { label: 'CRM' }, { label: __('Notes'), route: { name: 'Notes' } }]" />
      </template>
      <template #right-header>
        <Button :label="__('Refresh')" iconLeft="refresh-cw" :loading="board.loading" @click="board.reload()" />
      </template>
    </LayoutHeader>

    <div class="crmn">
      <div class="crmn-inner">
        <!-- Filterleiste: Art-Segmente + Suche -->
        <section class="crmn-filter">
          <span class="crmn-filter-cap">{{ __('Filter') }}</span>
          <div class="crmn-seg" role="tablist">
            <button
              v-for="s in ARTS"
              :key="s.key"
              type="button"
              class="crmn-seg-btn"
              :class="{ 'is-active': art === s.key }"
              :aria-pressed="art === s.key"
              @click="art = s.key"
            >{{ s.label }}</button>
          </div>
          <div class="crmn-search">
            <input v-model="q" type="search" class="crmn-input" :placeholder="__('Search content, object or author') + ' …'" />
          </div>
        </section>

        <!-- Karte „Notizen" -->
        <section class="crmn-card">
          <header class="crmn-ch">
            <span class="crmn-ch-title">{{ __('Notes') }}</span>
            <span class="crmn-ch-note">
              {{ filtered.length }} {{ __('of') }} {{ rows.length }} · {{ __('row = details in the inspector') }}
            </span>
          </header>

          <PpDataGrid v-if="filtered.length" :columns="columns" :rows="filtered" @row-click="openNote">
            <template #cell-title="{ row }">
              <span class="crmn-title">{{ row.title }}</span>
              <span v-if="row.object" class="crmn-object">{{ row.object }}</span>
            </template>
            <template #cell-art="{ value }">
              <span class="crmn-pill" :data-tone="value === 'voice' ? 'brand' : 'success'">
                <i class="crmn-dot" />{{ value === 'voice' ? __('Voice note') : __('Text note') }}
              </span>
            </template>
            <template #cell-author="{ value }">
              <span :class="{ 'crmn-muted': !value }">{{ value || '—' }}</span>
            </template>
            <template #cell-time="{ value }">
              <span class="crmn-muted">{{ relTime(value) }}</span>
            </template>
          </PpDataGrid>

          <PpEmptyState
            v-else
            :icon="IconStickyNote"
            :title="board.loading ? __('Loading notes …') : __('No notes')"
            :hint="board.loading ? '' : (q || art !== 'all' ? __('No matches for the current filter/search.') : __('Notes and voice notes appear here as they are captured.'))"
          />
        </section>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { createResource, Breadcrumbs, Button } from 'frappe-ui'
import LayoutHeader from '@/components/LayoutHeader.vue'
import PpDataGrid from '@/components/pp/PpDataGrid.vue'
import PpEmptyState from '@/components/pp/PpEmptyState.vue'
import IconStickyNote from '~icons/lucide/sticky-note'
import { usePilandaInspect } from '@/composables/usePilandaInspect'

const router = useRouter()
const { inspectNode } = usePilandaInspect()

const board = createResource({ url: 'lcs_integrations.projects.api.get_notes', auto: true })
const rows = computed(() => board.data?.rows || [])

// --- Filter: Art + Freitext ------------------------------------------------
const ARTS = [
  { key: 'all', label: __('All') },
  { key: 'voice', label: __('Voice note') },
  { key: 'text', label: __('Text note') },
]
const art = ref('all')
const q = ref('')
const filtered = computed(() => {
  const needle = q.value.trim().toLowerCase()
  return rows.value.filter((r) => {
    if (art.value !== 'all' && r.art !== art.value) return false
    if (!needle) return true
    return [r.title, r.object, r.author].some((v) => (v || '').toLowerCase().includes(needle))
  })
})

const columns = [
  { key: 'title', label: __('Note'), pin: true, width: 340 },
  { key: 'art', label: __('Type'), width: 160 },
  { key: 'author', label: __('Author'), width: 200 },
  { key: 'time', label: __('Time'), width: 140 },
]

// --- Zeilen-Klick → angedockter Spec-Inspektor -----------------------------
function openNote(id) {
  const r = rows.value.find((x) => x.id === id)
  if (!r) return
  inspectNode({
    title: r.title || __('Note'),
    badge: { label: r.art === 'voice' ? __('Voice note') : __('Text note'), tone: r.art === 'voice' ? 'brand' : 'success' },
    rows: [
      { label: __('Author'), value: r.author || '—' },
      { label: __('Object'), value: r.object || '—' },
      { label: __('Time'), value: relTime(r.time) },
    ],
    action: r.ref_name ? { label: __('Open object'), onClick: () => openRef(r) } : undefined,
  })
}
function openRef(r) {
  if (r.ref_doctype === 'CRM Lead') router.push({ name: 'Lead', params: { leadId: r.ref_name } })
  else if (r.ref_doctype === 'CRM Deal') router.push({ name: 'Deal', params: { dealId: r.ref_name } })
  else if (r.ref_doctype === 'LCS Project') router.push({ name: 'LCS Project', params: { id: r.ref_name } })
}
onBeforeUnmount(() => inspectNode(null))

// --- Relative Zeit (deutsch) -----------------------------------------------
function relTime(v) {
  if (!v) return '—'
  const d = new Date(String(v).replace(' ', 'T'))
  if (isNaN(d)) return String(v)
  const sec = (Date.now() - d.getTime()) / 1000
  if (sec < 60) return __('just now')
  if (sec < 3600) return __('{0} min ago', [Math.round(sec / 60)])
  const today = new Date(); today.setHours(0, 0, 0, 0)
  const day = new Date(d); day.setHours(0, 0, 0, 0)
  const days = Math.round((today.getTime() - day.getTime()) / 86400000)
  if (days <= 0) return sec < 21600 ? __('{0} h ago', [Math.round(sec / 3600)]) : __('today')
  if (days === 1) return __('yesterday')
  if (days < 7) return __('{0} days ago', [days])
  return new Intl.DateTimeFormat('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric' }).format(d)
}
</script>

<style scoped>
.crmn { flex: 1; min-height: 0; overflow: hidden; background: var(--pp-bg-base); display: flex; flex-direction: column; }
.crmn-inner { flex: 1; min-height: 0; padding: var(--pp-space-6);
  display: flex; flex-direction: column; gap: var(--pp-space-4); }

/* Filterleiste */
.crmn-filter { display: flex; align-items: center; gap: var(--pp-space-3); flex-wrap: wrap;
  padding: var(--pp-space-3) var(--pp-space-4); background: var(--pp-bg-surface);
  border: 1px solid var(--pp-border-subtle); border-radius: var(--pp-radius-ui); box-shadow: var(--pp-shadow-xs); }
.crmn-filter-cap { font-size: 10px; font-weight: var(--pp-weight-bold); letter-spacing: var(--pp-tracking-wide, 0.04em);
  text-transform: uppercase; color: var(--pp-text-tertiary); }
.crmn-seg { display: inline-flex; gap: 2px; padding: 2px; border-radius: var(--pp-radius-full);
  background: var(--pp-bg-base); border: 1px solid var(--pp-border-default); }
.crmn-seg-btn { appearance: none; cursor: pointer; font-family: inherit; font-size: var(--pp-fs-13, 13px);
  padding: 4px 14px; border: none; border-radius: var(--pp-radius-full); background: transparent; color: var(--pp-text-secondary); }
.crmn-seg-btn:hover { color: var(--pp-brand-primary); }
.crmn-seg-btn.is-active { background: var(--pp-brand-primary); color: var(--pp-text-on-accent); font-weight: var(--pp-weight-semibold); }
.crmn-search { flex: 1; min-width: 200px; }
.crmn-input { appearance: none; width: 100%; font-family: inherit; font-size: var(--pp-fs-13, 13px); color: var(--pp-text-primary);
  padding: 7px var(--pp-space-3); border: 1px solid var(--pp-border-default); border-radius: var(--pp-radius-ui); background: var(--pp-bg-base); }
.crmn-input:focus { outline: none; border-color: var(--pp-brand-primary); box-shadow: 0 0 0 3px rgb(var(--pp-brand-primary-rgb) / 0.15); }

/* Karte */
.crmn-card { flex: 1; min-height: 0; display: flex; flex-direction: column;
  background: var(--pp-bg-surface); border: 1px solid var(--pp-border-subtle);
  border-radius: var(--pp-radius-ui); box-shadow: var(--pp-shadow-xs); overflow: hidden; }
.crmn-ch { display: flex; align-items: baseline; justify-content: space-between; gap: var(--pp-space-3);
  padding: var(--pp-space-3) var(--pp-space-4); border-bottom: 1px solid var(--pp-border-subtle); }
.crmn-ch-title { font-size: var(--pp-fs-14, 14px); font-weight: var(--pp-weight-bold); color: var(--pp-text-primary); }
.crmn-ch-note { font-size: 11px; color: var(--pp-text-tertiary); }

/* Zellen */
.crmn-title { display: block; font-weight: var(--pp-weight-medium); color: var(--pp-text-primary); }
.crmn-object { display: block; font-size: 11px; color: var(--pp-text-tertiary); font-variant-numeric: tabular-nums; }
.crmn-muted { color: var(--pp-text-tertiary); }

.crmn-pill { display: inline-flex; align-items: center; gap: 5px; font-size: 11px; font-weight: var(--pp-weight-semibold);
  padding: 2px var(--pp-space-2); border-radius: var(--pp-radius-full); white-space: nowrap; }
.crmn-dot { width: 6px; height: 6px; border-radius: var(--pp-radius-full); flex-shrink: 0; background: currentColor; }
.crmn-pill[data-tone="brand"]   { background: color-mix(in oklab, var(--pp-brand-primary) 14%, transparent); color: var(--pp-brand-primary); }
.crmn-pill[data-tone="success"] { background: color-mix(in oklab, var(--pp-state-success) 16%, transparent); color: var(--pp-state-success); }

.crmn-card :deep(.pp-datagrid) { flex: 1; min-height: 0; }
</style>
