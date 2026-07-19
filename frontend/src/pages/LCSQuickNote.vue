<!--
  LCSQuickNote — Schnellnotizen (V2, Showcase #9 „Speak-or-Type").
  ============================================================
  Reibungsloses Erfassen von Notizen — tippen ODER sprechen — mit dem
  Theme-Baustein PpSpeakOrType. Zwei echte Datenwege, beide produktiv:

    · Text  → lcs_integrations.notes.api.dispatch_note
              (matcht die Notiz auf ein LCS-Projekt und legt sie als Kommentar
               an; bei klarem Treffer automatisch, sonst Vorschläge / manuelle
               Wahl).
    · Audio → upload_file + lcs_integrations.notes.api.retranscribe_audio
              (lädt die Aufnahme hoch und reiht einen „LCS Audio Transcription
               Job" ein; der Hermes-Agent transkribiert serverseitig nach).

  Bewusste Umstellung ggü. V1 (Marco, Welle 2): die frühere Live-Transkription
  im Browser (VoiceInput/WebSpeech) wird durch PpSpeakOrType + serverseitige
  Transkription ersetzt — PpSpeakOrType nimmt nur Audio auf und transkribiert
  NICHT selbst. Die Sprachauswahl (deckt der Baustein nicht ab) bleibt erhalten
  und steuert die Sprache des Transkriptions-Jobs.
-->

<template>
  <div class="flex h-full flex-col">
    <LayoutHeader>
      <template #left-header>
        <Breadcrumbs :items="[{ label: 'Schnellnotiz', route: { name: 'LCS Quick Note' } }]" />
      </template>
    </LayoutHeader>

    <div class="crms">
      <div class="crms-inner">
        <PpPageHead
          eyebrow="Vertrieb / CRM"
          title="Schnellnotiz"
          :subtitle="`Notiz tippen oder sprechen · ${notes.length} ${notes.length === 1 ? 'Notiz' : 'Notizen'} in dieser Sitzung`"
        />

        <!-- Composer: PpSpeakOrType + Sprachauswahl (aus Alt-Seite erhalten) -->
        <section class="crms-composer">
          <div class="crms-lang">
            <label class="crms-lang-cap" for="crms-lang">Sprache der Aufnahme</label>
            <select id="crms-lang" v-model="language" class="crms-select">
              <option v-for="l in LANGS" :key="l.value" :value="l.value">{{ l.label }}</option>
            </select>
          </div>
          <PpSpeakOrType
            v-model="draft"
            :disabled="busy"
            placeholder="Schnellnotiz zum Projekt eintippen — Projektnummer, Name, Kunde oder Ort nennen. Oder Mikrofon für eine Sprachnotiz…"
            @text="onText"
            @audio="onAudio"
            @error="onError"
          />
          <p class="crms-hint">
            Getippte Notizen werden automatisch dem passenden Projekt zugeordnet. Sprachnotizen werden
            hochgeladen und serverseitig transkribiert (Sprache: {{ langLabel }}) — die Zuordnung erfolgt danach.
          </p>
          <p v-if="lastError" class="crms-error" role="alert">
            <FeatherIcon name="alert-triangle" class="crms-error-ico" />{{ lastError }}
          </p>
        </section>

        <!-- Zuordnung wählen (wenn kein eindeutiger Treffer) -->
        <section v-if="pending" class="crms-assign">
          <div class="crms-assign-head">
            <FeatherIcon name="git-branch" class="crms-assign-ico" />
            <div class="crms-assign-titles">
              <span class="crms-assign-title">Projekt zuordnen</span>
              <span class="crms-assign-note">„{{ pending.text }}"</span>
            </div>
            <button type="button" class="crms-assign-x" aria-label="Verwerfen" @click="cancelPending"><FeatherIcon name="x" /></button>
          </div>

          <div v-if="candidates.length" class="crms-cands">
            <span class="crms-cands-cap">Vorgeschlagene Projekte</span>
            <button v-for="c in candidates" :key="c.name" type="button" class="crms-cand" :disabled="busy" @click="dispatchTo(c.name)">
              <div class="crms-cand-main">
                <span class="crms-cand-name">{{ c.project_name }}<span v-if="c.project_type" class="crms-type" :data-type="c.project_type">{{ c.project_type }}</span></span>
                <span class="crms-cand-sub">
                  <span class="crms-mono">{{ c.project_number }}</span>
                  <template v-if="c.organization"> · {{ c.organization }}</template>
                  <template v-if="c.country"> · {{ c.country }}</template>
                </span>
              </div>
              <span class="crms-cand-score" :data-conf="c.confidence">{{ confidenceLabel(c.confidence) }} · {{ Math.round(c.score * 100) }} %</span>
            </button>
          </div>
          <p v-else class="crms-cands-empty">Kein Projekt automatisch erkannt — bitte unten manuell wählen.</p>

          <div class="crms-manual">
            <span class="crms-cands-cap">Manuell zuordnen</span>
            <div class="crms-search">
              <FeatherIcon name="search" class="crms-search-ico" />
              <input v-model="manualQuery" type="search" class="crms-select crms-select--search"
                     placeholder="Projekt nach Nummer oder Name suchen …" @input="onManualSearch" />
              <span v-if="manualSearching" class="crms-spin" />
            </div>
            <div v-if="manualResults.length" class="crms-manual-list">
              <button v-for="p in manualResults" :key="p.name" type="button" class="crms-cand" :disabled="busy" @click="dispatchTo(p.name)">
                <div class="crms-cand-main">
                  <span class="crms-cand-name">{{ p.project_name }}<span v-if="p.project_type" class="crms-type" :data-type="p.project_type">{{ p.project_type }}</span></span>
                  <span class="crms-cand-sub"><span class="crms-mono">{{ p.project_number }}</span><template v-if="p.organization"> · {{ p.organization }}</template></span>
                </div>
              </button>
            </div>
            <p v-else-if="manualQuery.length >= 2 && !manualSearching" class="crms-cands-empty">Keine passenden Projekte.</p>
          </div>
        </section>

        <!-- Abgelegte Notizen (Sitzung) -->
        <section class="crms-list-wrap">
          <h3 class="crms-list-title">Abgelegte Notizen</h3>
          <ol v-if="notes.length" class="crms-list">
            <li v-for="n in notes" :key="n.id" class="crms-note" :class="'is-' + n.type">
              <div class="crms-note-main">
                <p v-if="n.type === 'text'" class="crms-note-text">{{ n.text }}</p>
                <div v-else class="crms-note-audio">
                  <audio class="crms-audio" :src="n.url" controls preload="metadata"></audio>
                  <span class="crms-note-meta">Sprachnotiz · {{ n.seconds }} s · {{ n.kb }} kB · {{ n.mime }}</span>
                </div>
                <div class="crms-note-foot">
                  <span v-if="n.target" class="crms-target">
                    <FeatherIcon name="check" class="crms-target-ico" />
                    <router-link :to="{ name: 'LCS Project', params: { id: n.target } }" class="crms-target-link">{{ n.target }}</router-link>
                  </span>
                  <span v-else-if="n.type === 'audio'" class="crms-queued">
                    <FeatherIcon name="clock" class="crms-target-ico" />Transkription eingereiht<template v-if="n.job"> · {{ n.job }}</template>
                  </span>
                  <span class="crms-note-time">{{ n.time }}</span>
                </div>
              </div>
              <button type="button" class="crms-del" aria-label="Notiz aus der Liste entfernen" title="Aus der Liste entfernen" @click="removeNote(n.id)">
                <FeatherIcon name="trash-2" />
              </button>
            </li>
          </ol>
          <PpEmptyState
            v-else
            :icon="IconStickyNote"
            title="Noch keine Notizen"
            hint="Tippe eine Notiz und drücke Enter oder nimm eine Sprachnotiz auf."
          />
        </section>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { Breadcrumbs, FeatherIcon, call, toast } from 'frappe-ui'
import LayoutHeader from '@/components/LayoutHeader.vue'
import PpPageHead from '@/components/pp/PpPageHead.vue'
import PpSpeakOrType from '@/components/pp/PpSpeakOrType.vue'
import PpEmptyState from '@/components/pp/PpEmptyState.vue'
import IconStickyNote from '~icons/lucide/sticky-note'
import { useUserPreferences } from '@/composables/useUserPreferences'

const LANGS = [
  { label: 'Deutsch (DE)', value: 'de-DE' },
  { label: 'English (US)', value: 'en-US' },
  { label: 'Italiano (IT)', value: 'it-IT' },
  { label: 'Français (FR)', value: 'fr-FR' },
]
const userPrefs = useUserPreferences()
const language = ref(userPrefs.state.prefs.voice_input_language || 'de-DE')
const langLabel = computed(() => LANGS.find((l) => l.value === language.value)?.label || language.value)

const draft = ref('')
const busy = ref(false)
const lastError = ref('')

// Sitzungs-Notizliste (echte Aktionen: dispatch bzw. Transkriptions-Job).
let seq = 0
const notes = ref([])
function now() {
  return new Date().toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' })
}

// Ausstehende Text-Notiz ohne eindeutigen Treffer (Vorschläge / manuelle Wahl).
const pending = ref(null)          // { text }
const candidates = ref([])

function onError(msg) { lastError.value = msg }

// --- Text-Weg: dispatch_note (Matching + Kommentar-Anlage) ------------------
async function onText(text) {
  lastError.value = ''
  busy.value = true
  try {
    const res = await call('lcs_integrations.notes.api.dispatch_note', { text, dry_run: 0 })
    const payload = res?.message || res || {}
    if (payload.auto_dispatched && payload.target_project) {
      addTextNote(text, payload.target_project)
      toast.success('Notiz zugeordnet zu ' + payload.target_project)
      clearPending()
    } else {
      pending.value = { text }
      candidates.value = payload.candidates || []
      manualQuery.value = ''
      manualResults.value = []
      if (!candidates.value.length) toast.info('Kein Projekt automatisch erkannt — bitte manuell wählen.')
    }
  } catch (err) {
    lastError.value = err?.message || 'Analyse fehlgeschlagen. Bitte erneut versuchen.'
  } finally {
    busy.value = false
  }
}

async function dispatchTo(project) {
  if (busy.value || !pending.value) return
  const text = pending.value.text
  busy.value = true
  try {
    await call('lcs_integrations.notes.api.dispatch_note', { text, project })
    addTextNote(text, project)
    toast.success('Notiz angehängt an ' + project)
    clearPending()
  } catch (err) {
    lastError.value = err?.message || 'Konnte nicht speichern. Bitte erneut versuchen.'
  } finally {
    busy.value = false
  }
}

function cancelPending() { clearPending() }
function clearPending() {
  pending.value = null
  candidates.value = []
  manualQuery.value = ''
  manualResults.value = []
}
function addTextNote(text, target) {
  notes.value.unshift({ id: 'n' + ++seq, type: 'text', text, target, time: now() })
}

// --- Audio-Weg: upload_file + retranscribe_audio (Transkriptions-Job) -------
async function onAudio(a) {
  lastError.value = ''
  busy.value = true
  try {
    const fileUrl = await uploadAudio(a)
    if (!fileUrl) return
    let job = ''
    try {
      const res = await call('lcs_integrations.notes.api.retranscribe_audio', { file_url: fileUrl, language: language.value })
      job = (res?.message || res || {}).job || ''
    } catch (err) {
      lastError.value = err?.message || 'Transkriptions-Job konnte nicht eingereiht werden.'
    }
    notes.value.unshift({
      id: 'n' + ++seq, type: 'audio', url: a.url, mime: a.mimeType,
      seconds: Math.round(a.ms / 1000), kb: Math.round(a.blob.size / 1024), job, time: now(),
    })
    if (job) toast.success('Sprachnotiz hochgeladen — Transkription eingereiht')
  } catch (err) {
    lastError.value = err?.message || 'Audio konnte nicht hochgeladen werden.'
  } finally {
    busy.value = false
  }
}

async function uploadAudio(a) {
  const ext = extensionFor(a.mimeType)
  const filename = `quicknote-${new Date().toISOString().replace(/[:.]/g, '-')}.${ext}`
  const form = new FormData()
  form.append('file', a.blob, filename)
  form.append('is_private', '1')
  form.append('folder', 'Home/Attachments')
  const csrf = window.csrf_token || ''
  const res = await window.fetch('/api/method/upload_file', {
    method: 'POST',
    credentials: 'include',
    headers: csrf ? { 'X-Frappe-CSRF-Token': csrf } : {},
    body: form,
  })
  if (!res.ok) throw new Error(`Upload fehlgeschlagen: ${res.status}`)
  const payload = await res.json()
  return payload?.message?.file_url || null
}
function extensionFor(mime) {
  if (!mime) return 'webm'
  if (mime.includes('webm')) return 'webm'
  if (mime.includes('ogg')) return 'ogg'
  if (mime.includes('mp4') || mime.includes('m4a')) return 'm4a'
  if (mime.includes('wav')) return 'wav'
  return 'bin'
}

// --- Manuelle Projektsuche --------------------------------------------------
const manualQuery = ref('')
const manualSearching = ref(false)
const manualResults = ref([])
let manualTimer = null
function onManualSearch() {
  clearTimeout(manualTimer)
  if (manualQuery.value.length < 2) { manualResults.value = []; return }
  manualSearching.value = true
  manualTimer = setTimeout(async () => {
    try {
      const res = await call('lcs_integrations.notes.api.search_projects', { query: manualQuery.value, limit: 20 })
      manualResults.value = res?.message || res || []
    } catch {
      manualResults.value = []
    } finally {
      manualSearching.value = false
    }
  }, 250)
}

function removeNote(id) {
  const n = notes.value.find((x) => x.id === id)
  if (n && n.type === 'audio' && n.url) URL.revokeObjectURL(n.url)
  notes.value = notes.value.filter((x) => x.id !== id)
}

function confidenceLabel(level) {
  return { high: 'Hoher Treffer', medium: 'Wahrscheinlich', low: 'Vielleicht', 'very-low': 'Schwach' }[level] || level || ''
}
</script>

<style scoped>
.crms { flex: 1; min-height: 0; overflow: auto; background: var(--pp-bg-base); }
.crms-inner { max-width: 900px; margin: 0 auto; padding: var(--pp-space-6) var(--pp-space-6) var(--pp-space-12);
  display: flex; flex-direction: column; gap: var(--pp-space-5); }

.crms-composer { display: flex; flex-direction: column; gap: var(--pp-space-2); }
.crms-lang { display: flex; flex-direction: column; gap: 3px; align-self: flex-start; }
.crms-lang-cap { font-size: 10px; font-weight: var(--pp-weight-bold); letter-spacing: var(--pp-tracking-wide, 0.04em);
  text-transform: uppercase; color: var(--pp-text-tertiary); }
.crms-select { appearance: none; font-family: inherit; font-size: var(--pp-fs-13, 13px); color: var(--pp-text-primary);
  padding: 6px var(--pp-space-3); border: 1px solid var(--pp-border-default); border-radius: var(--pp-radius-ui); background: var(--pp-bg-base); }
.crms-select:focus { outline: none; border-color: var(--pp-brand-primary); box-shadow: 0 0 0 3px rgb(var(--pp-brand-primary-rgb) / 0.15); }
.crms-hint { margin: 0; font-size: var(--pp-fs-12, 12px); color: var(--pp-text-tertiary); }
.crms-error { margin: 0; display: flex; align-items: center; gap: 6px; font-size: var(--pp-fs-13, 13px); color: var(--pp-state-danger); }
.crms-error-ico { width: 15px; height: 15px; flex-shrink: 0; }

/* Zuordnungs-Panel */
.crms-assign { display: flex; flex-direction: column; gap: var(--pp-space-3);
  background: var(--pp-bg-surface); border: 1px solid var(--pp-border-default);
  border-radius: var(--pp-radius-ui); box-shadow: var(--pp-shadow-xs); padding: var(--pp-space-4); }
.crms-assign-head { display: flex; align-items: flex-start; gap: var(--pp-space-2); }
.crms-assign-ico { width: 16px; height: 16px; color: var(--pp-brand-primary); flex-shrink: 0; margin-top: 2px; }
.crms-assign-titles { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 1px; }
.crms-assign-title { font-size: var(--pp-fs-13, 13px); font-weight: var(--pp-weight-semibold); color: var(--pp-text-primary); }
.crms-assign-note { font-size: var(--pp-fs-13, 13px); color: var(--pp-text-secondary); font-style: italic; }
.crms-assign-x { appearance: none; cursor: pointer; flex-shrink: 0; display: inline-flex; padding: 4px; border: 0;
  background: transparent; color: var(--pp-text-tertiary); border-radius: var(--pp-radius-ui); }
.crms-assign-x:hover { color: var(--pp-state-danger); background: color-mix(in oklab, var(--pp-state-danger) 10%, transparent); }
.crms-assign-x :deep(svg) { width: 15px; height: 15px; }

.crms-cands, .crms-manual { display: flex; flex-direction: column; gap: var(--pp-space-2); }
.crms-cands-cap { font-size: 10px; font-weight: var(--pp-weight-bold); letter-spacing: var(--pp-tracking-wide, 0.04em);
  text-transform: uppercase; color: var(--pp-text-tertiary); }
.crms-cands-empty { margin: 0; font-size: var(--pp-fs-13, 13px); color: var(--pp-text-secondary); }
.crms-cand { appearance: none; cursor: pointer; text-align: left; font-family: inherit;
  display: flex; align-items: center; justify-content: space-between; gap: var(--pp-space-3);
  padding: var(--pp-space-2) var(--pp-space-3); background: var(--pp-bg-base);
  border: 1px solid var(--pp-border-subtle); border-radius: var(--pp-radius-ui); }
.crms-cand:hover:not(:disabled) { border-color: var(--pp-brand-primary); background: var(--pp-bg-hover); }
.crms-cand:disabled { opacity: 0.6; cursor: not-allowed; }
.crms-cand-main { min-width: 0; display: flex; flex-direction: column; gap: 2px; }
.crms-cand-name { display: flex; align-items: center; gap: 6px; font-size: var(--pp-fs-14, 14px); font-weight: var(--pp-weight-medium); color: var(--pp-text-primary); }
.crms-cand-sub { font-size: var(--pp-fs-12, 12px); color: var(--pp-text-tertiary); }
.crms-mono { font-variant-numeric: tabular-nums; }
.crms-type { font-size: 10px; font-weight: var(--pp-weight-bold); padding: 1px 5px; border-radius: var(--pp-radius-ui);
  background: var(--pp-bg-sunken); color: var(--pp-text-secondary); }
.crms-cand-score { flex-shrink: 0; font-size: 11px; font-weight: var(--pp-weight-semibold); padding: 2px var(--pp-space-2);
  border-radius: var(--pp-radius-full); background: var(--pp-bg-sunken); color: var(--pp-text-secondary); }
.crms-cand-score[data-conf="high"]   { background: color-mix(in oklab, var(--pp-state-success) 16%, transparent); color: var(--pp-state-success); }
.crms-cand-score[data-conf="medium"] { background: color-mix(in oklab, var(--pp-state-warning) 16%, transparent); color: var(--pp-state-warning); }

.crms-search { position: relative; display: flex; align-items: center; }
.crms-search-ico { position: absolute; left: 9px; width: 15px; height: 15px; color: var(--pp-text-tertiary); pointer-events: none; }
.crms-select--search { width: 100%; padding-left: 30px; }
.crms-spin { position: absolute; right: 10px; width: 14px; height: 14px; border-radius: 50%;
  border: 2px solid var(--pp-border-default); border-top-color: var(--pp-brand-primary); animation: crms-spin 0.7s linear infinite; }
@keyframes crms-spin { to { transform: rotate(360deg); } }
@media (prefers-reduced-motion: reduce) { .crms-spin { animation: none; } }
.crms-manual-list { display: flex; flex-direction: column; gap: var(--pp-space-2); max-height: 320px; overflow-y: auto; }

/* Notizliste */
.crms-list-wrap { display: flex; flex-direction: column; gap: var(--pp-space-3); }
.crms-list-title { margin: 0; font-size: var(--pp-fs-12); font-weight: var(--pp-weight-bold);
  letter-spacing: var(--pp-tracking-wide, 0.04em); text-transform: uppercase; color: var(--pp-text-tertiary); }
.crms-list { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: var(--pp-space-2); }
.crms-note { display: flex; align-items: flex-start; gap: var(--pp-space-3);
  background: var(--pp-bg-surface); border: 1px solid var(--pp-border-subtle);
  border-radius: var(--pp-radius-ui); box-shadow: var(--pp-shadow-xs); padding: var(--pp-space-3) var(--pp-space-4); }
.crms-note.is-audio { border-left: 2px solid var(--pp-state-success); }
.crms-note.is-text { border-left: 2px solid var(--pp-brand-primary); }
.crms-note-main { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 6px; }
.crms-note-text { margin: 0; font-size: var(--pp-fs-14); color: var(--pp-text-primary); line-height: var(--pp-lh-normal, 1.5); }
.crms-note-audio { display: flex; flex-direction: column; gap: 4px; }
.crms-audio { width: 100%; max-width: 420px; height: 36px; }
.crms-note-meta { font-size: var(--pp-fs-12, 12px); color: var(--pp-text-tertiary); font-variant-numeric: tabular-nums; }
.crms-note-foot { display: flex; align-items: center; gap: var(--pp-space-3); flex-wrap: wrap; }
.crms-target, .crms-queued { display: inline-flex; align-items: center; gap: 5px; font-size: var(--pp-fs-12, 12px); }
.crms-target { color: var(--pp-state-success); }
.crms-queued { color: var(--pp-text-tertiary); }
.crms-target-ico { width: 13px; height: 13px; flex-shrink: 0; }
.crms-target-link { color: var(--pp-state-success); font-weight: var(--pp-weight-medium); text-decoration: underline; }
.crms-note-time { margin-left: auto; font-size: 11px; color: var(--pp-text-tertiary); font-variant-numeric: tabular-nums; }

.crms-del { appearance: none; cursor: pointer; flex-shrink: 0; display: inline-flex; align-items: center; justify-content: center;
  width: 30px; height: 30px; border-radius: var(--pp-radius-ui); border: 1px solid transparent; background: transparent; color: var(--pp-text-tertiary); }
.crms-del:hover { border-color: var(--pp-state-danger); color: var(--pp-state-danger); background: color-mix(in oklab, var(--pp-state-danger) 10%, transparent); }
.crms-del :deep(svg) { width: 15px; height: 15px; }

@media (max-width: 560px) {
  .crms-inner { padding: var(--pp-space-4) var(--pp-space-4) var(--pp-space-10); }
  .crms-cand { flex-direction: column; align-items: flex-start; }
  .crms-cand-score { align-self: flex-start; }
}
</style>
