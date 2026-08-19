<!--
  LcsNoteComposer — „Neue Notiz"-Formular (Modal-Inhalt der Notizen-Seite).
  Tippen oder sprechen; die Notiz wird auf ein Projekt/Lead gemappt (ZUORDNUNG-
  Dropdown mit Trefferquote) und erst per „Notiz speichern" abgelegt.
    · Matching/Ablage → lcs_integrations.notes.api.dispatch_note
    · Voice           → upload_file + retranscribe_audio (Transkriptions-Job)
  Emits `saved` nach erfolgreicher Ablage.
-->
<template>
  <div class="qn">
    <p class="qn-banner">{{ __('Type — dictate additionally in the ERP (server-side transcription)') }}</p>

    <PpSpeakOrType
      v-model="draft"
      :disabled="busy"
      :placeholder="__('e.g. “Grimsel: KWO wants to push the build phase to 2027, budget stays …”')"
      @audio="onAudio"
      @error="onError"
    />

    <div class="qn-assign">
      <label class="qn-assign-cap" for="qn-assign">{{ __('Assignment') }}</label>
      <select id="qn-assign" v-model="target" class="qn-select" :disabled="matching">
        <option value="">{{ matching ? __('Matching …') : __('Auto (best match)') }}</option>
        <option v-for="c in candidates" :key="c.name" :value="c.name">
          {{ c.project_number }} · {{ stripV(c.project_name) }} ({{ Math.min(100, Math.round((c.score || 0) * 100)) }} % {{ __('match') }})
        </option>
      </select>
      <Button variant="solid" :label="__('Save note')" :loading="busy" :disabled="!draft.trim()" @click="save" />
    </div>

    <p v-if="lastError" class="qn-error" role="alert">
      <FeatherIcon name="alert-triangle" class="qn-error-ico" />{{ lastError }}
    </p>
    <p class="qn-note">
      {{ __('ONE filing: the note hangs on the chosen project/lead, travels with it (Chance → Lead → Projekt) and appears in the list at once.') }}
    </p>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { FeatherIcon, Button, call, toast } from 'frappe-ui'
import PpSpeakOrType from '@/components/pp/PpSpeakOrType.vue'
import { useUserPreferences } from '@/composables/useUserPreferences'

const emit = defineEmits(['saved'])

const userPrefs = useUserPreferences()
const language = ref(userPrefs.state.prefs.voice_input_language || 'de-DE')

const draft = ref('')
const busy = ref(false)
const matching = ref(false)
const lastError = ref('')
const candidates = ref([])
const target = ref('') // '' = auto (best match)

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
    if (!target.value && candidates.value.length) {
      // Several strong matches (>= auto-dispatch) → keep "Auto" so the note is
      // filed in ALL of them (a note that names two projects lands in both);
      // otherwise pre-select the single best match.
      const strong = candidates.value.filter((c) => (c.score || 0) >= 0.8)
      target.value = strong.length >= 2 ? '' : candidates.value[0].name
    }
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
    if (target.value) args.project = target.value
    const res = await call('lcs_integrations.notes.api.dispatch_note', args)
    const payload = res?.message || res || {}
    const targets = (payload.target_projects && payload.target_projects.length)
      ? payload.target_projects
      : [payload.target_project || target.value].filter(Boolean)
    if (payload.auto_dispatched || targets.length) {
      toast.success(__('Note matched to') + ' ' + targets.map(stripV).join(', '))
      reset()
      emit('saved')
    } else {
      lastError.value = __('No project detected automatically — please choose manually.')
    }
  } catch (err) {
    lastError.value = err?.messages?.[0] || err?.message || __('Analysis failed. Please try again.')
  } finally {
    busy.value = false
  }
}
function reset() { draft.value = ''; candidates.value = []; target.value = '' }

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
.qn-select { flex: 1; min-width: 220px; appearance: none; font-family: inherit; font-size: var(--pp-fs-13, 13px);
  color: var(--pp-text-primary); padding: 7px var(--pp-space-3); border: 1px solid var(--pp-border-default);
  border-radius: var(--pp-radius-ui); background: var(--pp-bg-base); }
.qn-error { margin: 0; display: inline-flex; align-items: center; gap: 6px; font-size: var(--pp-fs-12, 12px); color: var(--pp-state-danger); }
.qn-error-ico { width: 14px; height: 14px; }
.qn-note { margin: 0; font-size: 11px; color: var(--pp-text-tertiary); line-height: 1.5; }
</style>
