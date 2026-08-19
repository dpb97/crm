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
        <Button variant="solid" :label="__('New note')" iconLeft="plus" @click="showNew = true" />
        <Button :label="__('Refresh')" iconLeft="refresh-cw" :loading="board.loading" @click="board.reload()" />
      </template>
    </LayoutHeader>

    <div class="pp-listpage">
      <div class="pp-listpage__inner">
        <!-- Filterleiste: Art-Segmente + Suche -->
        <PpFilterBar
          v-model="art"
          v-model:search="q"
          :segments="ARTS"
          :placeholder="__('Search content, object or author') + ' …'"
        />

        <!-- Karte „Notizen" -->
        <PpTableCard :title="__('Notes')" :shown="filtered.length" :total="rows.length">
          <PpDataGrid table-key="lcs_notes" v-if="filtered.length" :columns="columns" :rows="filtered" :page-size="25" @row-click="openNote">
            <template #cell-title="{ row }">
              <span class="pp-cell-strong">{{ row.title }}</span>
              <span v-if="row.object" class="pp-cell-sub crmn-object">{{ row.object }}</span>
            </template>
            <template #cell-art="{ value }">
              <PpPill :tone="value === 'voice' ? 'brand' : 'success'">
                {{ value === 'voice' ? __('Voice note') : __('Text note') }}
              </PpPill>
            </template>
            <template #cell-author="{ value }">
              <span :class="{ 'pp-cell-muted': !value }">{{ value || '—' }}</span>
            </template>
            <template #cell-time="{ value }">
              <span class="pp-cell-muted">{{ relTime(value) }}</span>
            </template>
          </PpDataGrid>

          <PpEmptyState
            v-else
            :icon="IconStickyNote"
            :title="board.loading ? __('Loading notes …') : __('No notes')"
            :hint="board.loading ? '' : (q || art !== 'all' ? __('No matches for the current filter/search.') : __('Notes and voice notes appear here as they are captured.'))"
          />
        </PpTableCard>
      </div>
    </div>

    <!-- Neue Notiz (nur per Button) -->
    <PpModal v-model:open="showNew" :title="__('New note')" :width="640">
      <LcsNoteComposer @saved="onNoteSaved" />
    </PpModal>
  </div>
</template>

<script setup>
import { ref, computed, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { createResource, Breadcrumbs, Button } from 'frappe-ui'
import LayoutHeader from '@/components/LayoutHeader.vue'
import PpDataGrid from '@/components/pp/PpDataGrid.vue'
import PpEmptyState from '@/components/pp/PpEmptyState.vue'
import PpFilterBar from '@/components/pp/PpFilterBar.vue'
import PpTableCard from '@/components/pp/PpTableCard.vue'
import LcsNoteComposer from '@/components/lcs/LcsNoteComposer.vue'
import PpModal from '@/components/pp/PpModal.vue'
import PpPill from '@/components/pp/PpPill.vue'
import IconStickyNote from '~icons/lucide/sticky-note'
import { usePilandaInspect } from '@/composables/usePilandaInspect'

const router = useRouter()
const { inspectNode } = usePilandaInspect()

const board = createResource({ url: 'lcs_integrations.projects.api.get_notes', auto: true })

// Neue Notiz — nur per Button (Modal).
const showNew = ref(false)
// Keep the window open after saving so several notes can be written in one go
// (the composer clears itself). The user closes it via the ✕ when finished.
function onNoteSaved() { board.reload() }
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
    ref: r.ref_name && r.ref_doctype
      ? { doctype: r.ref_doctype, name: r.ref_name, title: r.title || r.ref_name }
      : { title: r.title || __('Note') },
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
/* Object reference under the note title — tabular digits on top of pp-cell-sub. */
.crmn-object { font-variant-numeric: tabular-nums; }
</style>
