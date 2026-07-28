<!--
  LcsNoteComposer — kompakte Schnellerfassung (tippen ODER sprechen) als erster
  Block der Notizen-Seite. Nutzt die produktiven APIs:
    · Text  → lcs_integrations.notes.api.dispatch_note   (Auto-Mapping auf ein
              LCS-Projekt; klarer Treffer → automatisch, sonst Hinweis + Link
              zur vollen Schnellnotiz-Seite mit manueller Wahl)
    · Audio → upload_file + retranscribe_audio           (Transkriptions-Job)
  Emits `saved` nach erfolgreicher Ablage, damit die Liste neu lädt.
-->
<template>
  <section class="qn">
    <header class="qn-head">
      <span class="qn-title">{{ __('Capture quick note') }}</span>
      <div class="qn-lang">
        <label class="qn-lang-cap" for="qn-lang">{{ __('Recording language') }}</label>
        <select id="qn-lang" v-model="language" class="qn-select">
          <option v-for="l in LANGS" :key="l.value" :value="l.value">{{ l.label }}</option>
        </select>
      </div>
    </header>

    <PpSpeakOrType
      v-model="draft"
      :disabled="busy"
      :placeholder="__('Type a quick note about the project — mention the project number, name, customer, or location. Or use the microphone for a voice note…')"
      @text="onText"
      @audio="onAudio"
      @error="onError"
    />

    <p class="qn-hint">
      {{ __('Typed notes are automatically matched to the right project. Voice notes are uploaded and transcribed on the server.') }}
    </p>
    <p v-if="lastError" class="qn-error" role="alert">
      <FeatherIcon name="alert-triangle" class="qn-error-ico" />{{ lastError }}
    </p>
    <p v-if="unmatched" class="qn-unmatched">
      {{ __('No project detected automatically — please choose manually.') }}
      <router-link class="qn-link" :to="{ name: 'LCS Quick Note' }">{{ __('Open quick note') }} →</router-link>
    </p>
  </section>
</template>

<script setup>
import { ref, computed } from 'vue'
import { FeatherIcon, call, toast } from 'frappe-ui'
import PpSpeakOrType from '@/components/pp/PpSpeakOrType.vue'
import { useUserPreferences } from '@/composables/useUserPreferences'

const emit = defineEmits(['saved'])

const LANGS = [
  { label: 'Deutsch (DE)', value: 'de-DE' },
  { label: 'English (US)', value: 'en-US' },
  { label: 'Italiano (IT)', value: 'it-IT' },
  { label: 'Français (FR)', value: 'fr-FR' },
]
const userPrefs = useUserPreferences()
const language = ref(userPrefs.state.prefs.voice_input_language || 'de-DE')

const draft = ref('')
const busy = ref(false)
const lastError = ref('')
const unmatched = ref(false)

function onError(msg) { lastError.value = msg }

// --- Text: dispatch_note (Auto-Mapping) ------------------------------------
async function onText(text) {
  lastError.value = ''
  unmatched.value = false
  busy.value = true
  try {
    const res = await call('lcs_integrations.notes.api.dispatch_note', { text, dry_run: 0 })
    const payload = res?.message || res || {}
    if (payload.auto_dispatched && payload.target_project) {
      toast.success(__('Note matched to') + ' ' + payload.target_project)
      draft.value = ''
      emit('saved')
    } else {
      unmatched.value = true
    }
  } catch (err) {
    lastError.value = err?.message || __('Analysis failed. Please try again.')
  } finally {
    busy.value = false
  }
}

// --- Audio: upload + retranscribe (Transkriptions-Job) ---------------------
async function onAudio(a) {
  lastError.value = ''
  unmatched.value = false
  busy.value = true
  try {
    const fileUrl = await uploadAudio(a)
    if (!fileUrl) return
    try {
      await call('lcs_integrations.notes.api.retranscribe_audio', { file_url: fileUrl, language: language.value })
      toast.success(__('Voice note uploaded — transcription queued'))
      emit('saved')
    } catch (err) {
      lastError.value = err?.message || __('Transcription job could not be queued.')
    }
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
.qn { display: flex; flex-direction: column; gap: var(--pp-space-3);
  background: var(--pp-bg-surface); border: 1px solid var(--pp-border-subtle);
  border-radius: var(--pp-radius-ui); box-shadow: var(--pp-shadow-xs); padding: var(--pp-space-4); }
.qn-head { display: flex; align-items: center; justify-content: space-between; gap: var(--pp-space-3); flex-wrap: wrap; }
.qn-title { font-size: var(--pp-fs-14, 14px); font-weight: var(--pp-weight-bold); color: var(--pp-text-primary); }
.qn-lang { display: inline-flex; align-items: center; gap: var(--pp-space-2); }
.qn-lang-cap { font-size: 10px; font-weight: var(--pp-weight-bold); letter-spacing: 0.04em;
  text-transform: uppercase; color: var(--pp-text-tertiary); }
.qn-select { appearance: none; font-family: inherit; font-size: var(--pp-fs-12, 12px); color: var(--pp-text-primary);
  padding: 4px var(--pp-space-2); border: 1px solid var(--pp-border-default); border-radius: var(--pp-radius-ui); background: var(--pp-bg-base); }
.qn-hint { margin: 0; font-size: 11px; color: var(--pp-text-tertiary); }
.qn-error { margin: 0; display: inline-flex; align-items: center; gap: 6px; font-size: var(--pp-fs-12, 12px); color: var(--pp-state-danger); }
.qn-error-ico { width: 14px; height: 14px; }
.qn-unmatched { margin: 0; font-size: var(--pp-fs-12, 12px); color: var(--pp-text-secondary); }
.qn-link { color: var(--pp-brand-primary); font-weight: var(--pp-weight-semibold); text-decoration: none; }
.qn-link:hover { text-decoration: underline; }
</style>
