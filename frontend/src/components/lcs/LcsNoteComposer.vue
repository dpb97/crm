<!--
  LcsNoteComposer — „Neue Notiz"-Formular (Modal-Inhalt der Notizen-Seite).
  Tippen oder sprechen; die Notiz wird auf ein Projekt/Lead gemappt (ZUORDNUNG-
  Dropdown mit Trefferquote) und erst per „Notiz speichern" abgelegt.
    · Matching/Ablage → lcs_integrations.notes.api.dispatch_note
    · Voice           → upload_file + retranscribe_audio (Transkriptions-Job)
  Emits `saved` nach erfolgreicher Ablage.
-->
<template>
  <div class="qn" :class="{ 'qn--mobile': isMobile }">
    <p v-if="!isMobile" class="qn-banner">{{ __('Type — dictate additionally in the ERP (server-side transcription)') }}</p>

    <PpSpeakOrType
      class="qn-composer"
      v-model="draft"
      :disabled="busy"
      :rows="isMobile ? 10 : 3"
      :lang="language"
      :placeholder="__('e.g. “Grimsel: KWO wants to push the build phase to 2027, budget stays …”')"
      @error="onError"
    />

    <p v-if="lastError" class="qn-error" role="alert">
      <FeatherIcon name="alert-triangle" class="qn-error-ico" />{{ lastError }}
    </p>

    <!-- All strongly-matched projects (auto-linked on save) — so the user sees
         every project the note will hang on, not only the one in the dropdown. -->
    <div v-if="autoLinked.length" class="qn-autolinks">
      <span class="qn-assign-cap">{{ __('Auto-linked') }}</span>
      <span v-for="c in autoLinked" :key="c.name" class="qn-chip">{{ stripV(c.project_name) }}</span>
    </div>

    <!-- Assignment + save. On the phone this is a fixed bottom bar (thumb zone). -->
    <!-- Manually link the note to any entities (Projekt/Lead/Chance/Kontakt/Firma),
         same as in the editor afterwards. Adds on top of the auto-linked projects. -->
    <div v-if="selectedLinks.length" class="qn-autolinks">
      <span class="qn-assign-cap">{{ __('Linked to') }}</span>
      <span v-for="l in selectedLinks" :key="l.link_doctype + l.link_name" class="qn-chip qn-chip--rm">
        {{ l.title }}<button type="button" class="qn-chip-x" @click="removeLink(l)">×</button>
      </span>
    </div>

    <div class="qn-assign">
      <select v-model="pickDt" class="qn-pickdt">
        <option v-for="e in ENTITIES" :key="e.dt" :value="e.dt">{{ __(e.label) }}</option>
      </select>
      <div class="qn-search">
        <input v-model="q" type="text" class="qn-select" :placeholder="__('Search to link') + ' …'" @input="search" />
        <div v-if="results.length" class="qn-results">
          <button v-for="r in results" :key="r.name" type="button" class="qn-result" @click="addLink(r)">{{ r.label }}</button>
        </div>
      </div>
      <Button class="qn-save" variant="solid" :label="__('Save note')" :loading="busy" :disabled="!draft.trim()" @click="save" />
    </div>

    <p v-if="!isMobile" class="qn-note">
      {{ __('ONE filing: the note hangs on the chosen project/lead, travels with it (Chance → Lead → Projekt) and appears in the list at once.') }}
    </p>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { FeatherIcon, Button, call, toast } from 'frappe-ui'
import PpSpeakOrType from '@/components/pp/PpSpeakOrType.vue'
import { useUserPreferences } from '@/composables/useUserPreferences'
import { useViewport } from '@/composables/useViewport'

const { isMobile } = useViewport()

const emit = defineEmits(['saved'])

const userPrefs = useUserPreferences()
const language = ref(userPrefs.state.prefs.voice_input_language || 'de-DE')

const draft = ref('')
const busy = ref(false)
const matching = ref(false)
const lastError = ref('')
const candidates = ref([])

// Every strong match (>= 0.8) is auto-linked on save — show them all so the
// user sees exactly which projects the note will hang on (not just one).
const autoLinked = computed(() => candidates.value.filter((c) => (c.score || 0) >= 0.8))

// --- Manual multi-entity link picker (mirrors LcsNoteEditor) ----------------
const ENTITIES = [
  { dt: 'LCS Project', label: 'Project', title: 'project_name' },
  { dt: 'CRM Lead', label: 'Lead', title: 'lead_name' },
  { dt: 'LCS Chance', label: 'Chance', title: 'title' },
  { dt: 'Contact', label: 'Contact', title: 'full_name' },
  { dt: 'CRM Organization', label: 'Organization', title: 'organization_name' },
]
const pickDt = ref('LCS Project')
const q = ref('')
const results = ref([])
const selectedLinks = ref([]) // [{ link_doctype, link_name, title }]

let searchTimer = null
function search() {
  clearTimeout(searchTimer)
  const needle = q.value.trim()
  if (needle.length < 2) { results.value = []; return }
  const ent = ENTITIES.find((e) => e.dt === pickDt.value)
  searchTimer = setTimeout(async () => {
    try {
      const rows = await call('frappe.client.get_list', {
        doctype: pickDt.value,
        filters: [[ent.title, 'like', `%${needle}%`]],
        fields: ['name', ent.title],
        limit_page_length: 10,
      })
      results.value = (rows || []).map((r) => ({ name: r.name, label: r[ent.title] || r.name }))
    } catch { results.value = [] }
  }, 250)
}
function addLink(r) {
  if (!selectedLinks.value.some((l) => l.link_doctype === pickDt.value && l.link_name === r.name)) {
    selectedLinks.value.push({ link_doctype: pickDt.value, link_name: r.name, title: r.label })
  }
  q.value = ''
  results.value = []
}
function removeLink(l) {
  selectedLinks.value = selectedLinks.value.filter((x) => !(x.link_doctype === l.link_doctype && x.link_name === l.link_name))
}

// Display helper: drop the "V_" sales-prefix from a project code (V_SB-… → SB-…).
function stripV(s) { return String(s || '').replace(/^V_/i, '') }

function onError(msg) { lastError.value = msg }

// Debounced matching → fill the ZUORDNUNG dropdown with candidates + score.
let matchTimer = null
watch(draft, (v) => {
  clearTimeout(matchTimer)
  const text = (v || '').trim()
  if (text.length < 3) { candidates.value = []; return }
  matchTimer = setTimeout(() => matchNote(text), 500)
})
async function matchNote(text) {
  matching.value = true
  try {
    const res = await call('lcs_integrations.notes.api.dispatch_note', { text, dry_run: 1 })
    const payload = res?.message || res || {}
    candidates.value = payload.candidates || []
  } catch { /* stiller Match-Fehler — Speichern versucht es erneut */ } finally {
    matching.value = false
  }
}

// Ablage: dispatch_note mit gewähltem (oder Auto-)Ziel.
async function save() {
  const text = draft.value.trim()
  if (!text) return
  lastError.value = ''
  busy.value = true
  try {
    const args = { text, dry_run: 0 }
    if (selectedLinks.value.length) {
      args.links = JSON.stringify(selectedLinks.value.map((l) => ({ link_doctype: l.link_doctype, link_name: l.link_name })))
    }
    const res = await call('lcs_integrations.notes.api.dispatch_note', args)
    const payload = res?.message || res || {}
    if (payload.note) {
      const projs = (payload.target_projects || []).map(stripV)
      const others = selectedLinks.value.filter((l) => l.link_doctype !== 'LCS Project').map((l) => l.title)
      const all = [...projs, ...others]
      toast.success(__('Note saved') + (all.length ? ' — ' + all.join(', ') : ''))
      reset()
      emit('saved')
    } else {
      lastError.value = __('Could not save the note.')
    }
  } catch (err) {
    lastError.value = err?.messages?.[0] || err?.message || __('Analysis failed. Please try again.')
  } finally {
    busy.value = false
  }
}
function reset() { draft.value = ''; candidates.value = []; selectedLinks.value = []; q.value = ''; results.value = [] }

// Voice: upload + retranscribe (Transkriptions-Job).
async function onAudio(a) {
  lastError.value = ''
  busy.value = true
  try {
    const fileUrl = await uploadAudio(a)
    if (!fileUrl) return
    await call('lcs_integrations.notes.api.retranscribe_audio', { file_url: fileUrl, language: language.value })
    toast.success(__('Voice note uploaded — transcription queued'))
    emit('saved')
  } catch (err) {
    lastError.value = err?.message || __('Audio could not be uploaded.')
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
    method: 'POST', credentials: 'include',
    headers: csrf ? { 'X-Frappe-CSRF-Token': csrf } : {},
    body: form,
  })
  if (!res.ok) throw new Error(__('Upload failed:') + ' ' + res.status)
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
</script>

<style scoped>
.qn { display: flex; flex-direction: column; gap: var(--pp-space-3); }
.qn-banner { margin: 0; padding: var(--pp-space-2) var(--pp-space-3); font-size: var(--pp-fs-13, 13px);
  color: var(--pp-brand-primary); background: var(--pp-accent-soft); border-radius: var(--pp-radius-ui); }
.qn-assign { display: flex; align-items: center; gap: var(--pp-space-3); flex-wrap: wrap; }
.qn-assign-cap { font-size: 10px; font-weight: var(--pp-weight-bold); letter-spacing: 0.04em;
  text-transform: uppercase; color: var(--pp-text-tertiary); }
.qn-autolinks { display: flex; flex-wrap: wrap; align-items: center; gap: 6px; }
.qn-chip { display: inline-flex; align-items: center; padding: 2px 9px;
  border-radius: var(--pp-radius-full, 999px); border: 1px solid var(--pp-accent-soft, #cdeaea);
  background: var(--pp-accent-soft, #e6f6f6); color: var(--pp-brand-primary, #008b8b);
  font-size: 11px; font-weight: var(--pp-weight-semibold, 600); white-space: nowrap; }
.qn-chip--rm { padding-right: 4px; }
.qn-chip-x { appearance: none; border: none; background: transparent; cursor: pointer;
  margin-left: 4px; color: var(--pp-brand-primary); font-size: 13px; line-height: 1; }
.qn-pickdt { appearance: none; font-family: inherit; font-size: var(--pp-fs-13, 13px);
  padding: 7px var(--pp-space-3); border: 1px solid var(--pp-border-default);
  border-radius: var(--pp-radius-ui); background: var(--pp-bg-base); color: var(--pp-text-primary); }
.qn-search { position: relative; flex: 1; min-width: 180px; }
.qn-search .qn-select { width: 100%; min-width: 0; }
.qn-results { position: absolute; bottom: calc(100% + 4px); left: 0; z-index: 50; width: 100%;
  max-height: 220px; overflow-y: auto; background: var(--pp-bg-surface);
  border: 1px solid var(--pp-border-default); border-radius: var(--pp-radius-ui); box-shadow: var(--pp-shadow-xl); }
.qn-result { display: block; width: 100%; text-align: left; padding: 7px var(--pp-space-3);
  font-size: var(--pp-fs-13, 13px); background: transparent; border: none; cursor: pointer; color: var(--pp-text-primary); }
.qn-result:hover { background: var(--pp-bg-hover); }
.qn-select { flex: 1; min-width: 220px; appearance: none; font-family: inherit; font-size: var(--pp-fs-13, 13px);
  color: var(--pp-text-primary); padding: 7px var(--pp-space-3); border: 1px solid var(--pp-border-default);
  border-radius: var(--pp-radius-ui); background: var(--pp-bg-base); }
.qn-error { margin: 0; display: inline-flex; align-items: center; gap: 6px; font-size: var(--pp-fs-12, 12px); color: var(--pp-state-danger); }
.qn-error-ico { width: 14px; height: 14px; }
.qn-note { margin: 0; font-size: 11px; color: var(--pp-text-tertiary); line-height: 1.5; }

/* --- Mobile: full-height Notion-clean "note page" — a calm, borderless writing
   surface fills the screen; the assignment + save sit in a bottom bar (thumb
   zone). The mic (speak-to-text) stays reachable at the bottom-right. --------- */
.qn--mobile { height: 100%; padding: 0; gap: 0; }
.qn--mobile .qn-composer { flex: 1 1 auto; min-height: 0; }
/* Strip the boxed control chrome so the note reads as a plain page, not a form
   field: no border/background/shadow, roomy padding, larger body text. */
.qn--mobile .qn-composer :deep(.pp-sot) { height: 100%; border: 0; background: transparent;
  box-shadow: none; padding: var(--pp-space-4) var(--pp-space-4) var(--pp-space-2); gap: var(--pp-space-2); }
.qn--mobile .qn-composer :deep(.pp-sot.is-recording) { box-shadow: none; }
.qn--mobile .qn-composer :deep(.pp-sot__composer) { flex: 1 1 auto; min-height: 0; align-items: stretch; }
.qn--mobile .qn-composer :deep(.pp-sot__input) { flex: 1 1 auto; min-height: 0; resize: none;
  border: 0; background: transparent; padding: 0; font-size: var(--pp-fs-17, 17px); line-height: 1.6; }
.qn--mobile .qn-composer :deep(.pp-sot__input:focus) { box-shadow: none; }
/* Notion has no helper line under the field — drop it on the phone to declutter. */
.qn--mobile .qn-composer :deep(.pp-sot__hint) { display: none; }
.qn--mobile .qn-composer :deep(.pp-sot__actions) { align-items: flex-end; }
.qn--mobile .qn-assign { flex: 0 0 auto; flex-direction: column; align-items: stretch;
  gap: 6px; padding: var(--pp-space-3) var(--pp-space-4) var(--pp-space-4);
  border-top: 1px solid var(--pp-border-subtle); background: var(--pp-bg-surface); }
.qn--mobile .qn-select { min-width: 0; width: 100%; padding: 10px var(--pp-space-3); font-size: var(--pp-fs-14, 14px); }
.qn--mobile .qn-save { width: 100%; }
.qn--mobile .qn-save :deep(button) { width: 100%; height: 44px; font-size: var(--pp-fs-14, 14px); }
</style>
