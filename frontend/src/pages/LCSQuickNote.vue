<!--
  LCSQuickNote
  ============
  A frictionless capture page for voice / typed notes. The user can:
  1. Speak or type a note
  2. Click "Analyze" → backend ranks LCS Projects by match score,
     returns top candidates
  3. Auto-dispatched if one candidate is clearly better than the
     rest (score >= 0.8 and not tied), otherwise user picks from
     suggestions
  4. Manual fallback: searchable dropdown at the bottom for any
     project (also usable when matching finds no good candidate)

  Keyboard: Ctrl+Shift+V toggles voice input; Ctrl+Enter dispatches.
-->

<template>
  <LayoutHeader>
    <template #left-header>
      <Breadcrumbs :items="[{ label: __('Quick Note'), route: { name: 'LCS Quick Note' } }]" />
    </template>
    <template #right-header>
      <div class="flex items-center gap-2 text-xs text-gray-500">
        <kbd class="rounded border bg-white px-1.5 py-0.5 font-mono">Ctrl+Enter</kbd>
        {{ __('to dispatch') }}
      </div>
    </template>
  </LayoutHeader>

  <div class="flex-1 overflow-y-auto p-5">
    <div class="mx-auto max-w-3xl space-y-5">

      <!-- Intro -->
      <div class="rounded-lg border border-blue-200 bg-blue-50 p-3 text-sm text-blue-900">
        <div class="flex items-start gap-2">
          <FeatherIcon name="mic" class="mt-0.5 h-4 w-4 shrink-0" />
          <div>
            <div class="font-semibold">{{ __('Speak or type — we match it to the right project automatically.') }}</div>
            <div class="mt-0.5 text-xs text-blue-700">
              {{ __('Mention a project number, name, customer, or location and the system picks the best fit. You can always assign manually.') }}
            </div>
          </div>
        </div>
      </div>

      <!-- Text area -->
      <div class="relative">
        <textarea
          v-model="noteText"
          ref="noteInput"
          class="w-full rounded-xl border border-gray-300 bg-white px-4 py-3 pr-14 text-sm text-gray-900 shadow-sm focus:border-lcs-secondary focus:ring-1 focus:ring-lcs-secondary"
          rows="8"
          :placeholder="__('e.g. Heute Call mit Techint Chile zu SB-SADDN, Liefertermin 30.06. bestätigt')"
          @keydown.ctrl.enter.prevent="analyze"
          @keydown.meta.enter.prevent="analyze"
          @input="onInput"
        />
        <div class="absolute right-3 top-3">
          <VoiceInput
            :hotkey="true"
            :record-audio="true"
            @transcript="onVoiceTranscript"
            @done="onVoiceDone"
            @audio-blob="onAudioBlob"
          />
        </div>
        <!-- Audio captured indicator -->
        <div
          v-if="capturedAudio"
          class="absolute bottom-2 right-3 flex items-center gap-1.5 rounded-full bg-purple-50 border border-purple-200 px-2 py-0.5 text-[10px] font-medium text-purple-700"
          :title="__('Audio saved — can be re-transcribed later with better AI')"
        >
          <FeatherIcon name="headphones" class="h-2.5 w-2.5" />
          {{ capturedAudio.sizeKb }} KB {{ capturedAudio.mime.split('/')[1] }}
          <button class="ml-1 text-purple-500 hover:text-red-500" @click="capturedAudio = null" :title="__('Discard audio')">×</button>
        </div>
        <!-- Character counter -->
        <div class="mt-1 flex items-center justify-between text-[11px] text-gray-400">
          <span>{{ noteText.length }} {{ __('characters') }}</span>
          <span v-if="noteText.trim()">
            {{ __('Press') }}
            <kbd class="rounded border bg-white px-1 font-mono">Ctrl+Shift+V</kbd>
            {{ __('for voice') }}
          </span>
        </div>
      </div>

      <!-- Actions -->
      <div class="flex items-center justify-between gap-2">
        <div class="flex gap-2">
          <Button
            variant="solid"
            :label="__('Analyze & Dispatch')"
            iconLeft="target"
            @click="analyze"
            :loading="analyzing"
            :disabled="!noteText.trim() || analyzing"
          />
          <Button
            variant="ghost"
            :label="__('Clear')"
            iconLeft="x"
            @click="reset"
            :disabled="!noteText && !result"
          />
        </div>
        <span v-if="lastDispatched" class="text-xs text-green-600">
          <FeatherIcon name="check" class="inline h-3 w-3" />
          {{ __('Saved to') }} {{ lastDispatched }}
        </span>
      </div>

      <!-- Auto-dispatched banner -->
      <div v-if="result && result.auto_dispatched" class="rounded-xl border border-green-200 bg-green-50 p-4">
        <div class="flex items-start gap-3">
          <FeatherIcon name="check-circle" class="mt-0.5 h-5 w-5 text-green-600" />
          <div class="flex-1">
            <div class="font-semibold text-green-900">
              {{ __('Note saved — auto-matched to') }}
              <router-link
                :to="{ name: 'LCS Project', params: { id: result.target_project } }"
                class="underline hover:text-green-700"
              >
                {{ result.target_project }}
              </router-link>
            </div>
            <div class="mt-1 text-xs text-green-700">
              {{ __('If this is wrong:') }}
              <button @click="undoAndShowCandidates" class="font-medium underline">{{ __('reassign manually') }}</button>
            </div>
          </div>
        </div>
      </div>

      <!-- Candidate suggestions -->
      <div v-if="result && !result.auto_dispatched && result.candidates?.length" class="space-y-3">
        <div class="text-xs font-semibold uppercase tracking-wide text-gray-500">
          <FeatherIcon name="git-branch" class="mr-1 inline h-3 w-3" />
          {{ __('Suggested projects') }}
        </div>
        <button
          v-for="c in result.candidates"
          :key="c.name"
          class="group flex w-full items-start justify-between gap-3 rounded-xl border bg-white p-4 text-left transition hover:border-lcs-secondary hover:shadow-sm"
          @click="dispatchToProject(c.name)"
          :disabled="dispatching"
        >
          <div class="min-w-0 flex-1">
            <div class="flex items-center gap-2">
              <span class="font-semibold text-gray-900">{{ c.project_name }}</span>
              <span :class="typeClass(c.project_type)" class="rounded-full px-1.5 py-0.5 text-[10px] font-bold">{{ c.project_type }}</span>
            </div>
            <div class="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-gray-500">
              <span class="font-mono">{{ c.project_number }}</span>
              <span v-if="c.organization">· {{ c.organization }}</span>
              <span v-if="c.country">· {{ c.country }}</span>
              <span v-if="c.phase">· {{ c.phase }}</span>
            </div>
          </div>
          <div class="flex flex-col items-end gap-1">
            <span :class="confidenceClass(c.confidence)" class="rounded-full px-2 py-0.5 text-[10px] font-bold uppercase">
              {{ confidenceLabel(c.confidence) }} · {{ Math.round(c.score * 100) }}%
            </span>
            <span class="text-[10px] text-gray-400 group-hover:text-lcs-primary">
              {{ __('Click to assign') }} →
            </span>
          </div>
        </button>
      </div>

      <!-- No candidates -->
      <div v-if="result && !result.auto_dispatched && !result.candidates?.length" class="rounded-xl border border-dashed border-gray-200 bg-gray-50 p-6 text-center">
        <FeatherIcon name="search" class="mx-auto h-6 w-6 text-gray-400" />
        <p class="mt-2 text-sm text-gray-600">{{ __('No project matched automatically.') }}</p>
        <p class="mt-1 text-xs text-gray-400">{{ __('Pick one manually below.') }}</p>
      </div>

      <!-- Manual picker — always available -->
      <div v-if="result" class="rounded-xl border bg-white p-4">
        <div class="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-500">
          <FeatherIcon name="edit-2" class="mr-1 inline h-3 w-3" />
          {{ __('Pick manually') }}
        </div>
        <div class="relative">
          <input
            v-model="manualQuery"
            type="search"
            class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:border-lcs-secondary focus:ring-1 focus:ring-lcs-secondary"
            :placeholder="__('Search any project by number or name...')"
            @input="onManualSearch"
          />
          <div v-if="manualSearching" class="absolute right-3 top-2.5">
            <div class="h-4 w-4 animate-spin rounded-full border-2 border-gray-200 border-t-lcs-secondary" />
          </div>
        </div>

        <div v-if="manualResults.length" class="mt-2 max-h-60 overflow-y-auto rounded-md border">
          <button
            v-for="p in manualResults"
            :key="p.name"
            class="flex w-full items-start justify-between gap-2 border-b px-3 py-2 text-left hover:bg-blue-50"
            @click="dispatchToProject(p.name)"
            :disabled="dispatching"
          >
            <div class="min-w-0 flex-1">
              <div class="text-sm font-medium text-gray-900">{{ p.project_name }}</div>
              <div class="text-xs text-gray-500">
                <span class="font-mono">{{ p.project_number }}</span>
                <span v-if="p.organization"> · {{ p.organization }}</span>
              </div>
            </div>
            <span :class="typeClass(p.project_type)" class="shrink-0 rounded px-1.5 py-0.5 text-[10px] font-bold">
              {{ p.project_type }}
            </span>
          </button>
        </div>
        <div v-else-if="manualQuery.length >= 2 && !manualSearching" class="mt-2 rounded-md bg-gray-50 p-3 text-center text-xs text-gray-500">
          {{ __('No matching projects.') }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { Breadcrumbs, Button, FeatherIcon, call, toast } from 'frappe-ui'
import LayoutHeader from '@/components/LayoutHeader.vue'
import VoiceInput from '@/components/lcs/VoiceInput.vue'

const router = useRouter()
const noteText = ref('')
const noteInput = ref(null)
const result = ref(null)
const analyzing = ref(false)
const dispatching = ref(false)
const lastDispatched = ref('')
const capturedAudio = ref(null)  // { blob, mime, sizeKb }
const uploadingAudio = ref(false)

// --- Voice input — append streamed transcript to noteText ---
let voiceBaseline = ''
function onVoiceTranscript({ final, interim }) {
  if (final && voiceBaseline === '') voiceBaseline = noteText.value || ''
  const separator = voiceBaseline ? (voiceBaseline.endsWith('\n') ? '' : '\n') : ''
  noteText.value = voiceBaseline + separator + (final || '') + (interim || '')
}
function onVoiceDone() {
  voiceBaseline = ''  // next recording starts fresh
}
function onInput() {
  voiceBaseline = ''  // manual edit also resets the baseline
}

// Audio captured in parallel with the recognition. Kept in memory
// until dispatch; then uploaded as a File and attached to the Comment.
function onAudioBlob({ blob, mimeType }) {
  if (!blob) return
  capturedAudio.value = {
    blob,
    mime: mimeType || blob.type || 'audio/webm',
    sizeKb: Math.round(blob.size / 1024),
  }
}

async function uploadAudioIfPresent() {
  if (!capturedAudio.value) return null
  uploadingAudio.value = true
  try {
    const ext = _extensionFor(capturedAudio.value.mime)
    const filename = `quicknote-${new Date().toISOString().replace(/[:.]/g, '-')}.${ext}`
    const form = new FormData()
    form.append('file', capturedAudio.value.blob, filename)
    form.append('is_private', '1')
    form.append('folder', 'Home/Attachments')
    const csrf = window.csrf_token || ''
    const res = await window.fetch('/api/method/upload_file', {
      method: 'POST',
      credentials: 'include',
      headers: csrf ? { 'X-Frappe-CSRF-Token': csrf } : {},
      body: form,
    })
    if (!res.ok) throw new Error(`Upload failed: ${res.status}`)
    const payload = await res.json()
    return payload?.message?.file_url || null
  } catch (err) {
    toast({
      title: __('Audio upload failed'),
      text: err.message || String(err),
      icon: 'alert-circle',
      iconClasses: 'text-amber-500',
    })
    return null
  } finally {
    uploadingAudio.value = false
  }
}

function _extensionFor(mime) {
  if (!mime) return 'webm'
  if (mime.includes('webm')) return 'webm'
  if (mime.includes('ogg')) return 'ogg'
  if (mime.includes('mp4') || mime.includes('m4a')) return 'm4a'
  if (mime.includes('wav')) return 'wav'
  return 'bin'
}

// --- Analyze + dispatch ---
async function analyze() {
  if (!noteText.value.trim() || analyzing.value) return
  analyzing.value = true
  try {
    // Upload the captured audio first so its file_url can travel with
    // the dispatch call — keeps the Comment + File tied to the right
    // project in a single transaction server-side.
    const audioUrl = await uploadAudioIfPresent()

    const res = await call('lcs_integrations.notes.api.dispatch_note', {
      text: noteText.value,
      dry_run: 0,
      audio_file_url: audioUrl || '',
    })
    result.value = res.message || res
    if (result.value.auto_dispatched) {
      lastDispatched.value = result.value.target_project
      // Audio has been re-parented to the target project — clear the local
      // blob so it doesn't get re-uploaded if the user dispatches another note
      capturedAudio.value = null
      toast({
        title: __('Saved'),
        text: `${__('Note matched to')} ${result.value.target_project}${audioUrl ? ' (+ audio)' : ''}`,
        icon: 'check-circle',
        iconClasses: 'text-green-500',
      })
    } else if (!result.value.candidates?.length) {
      toast({
        title: __('No match'),
        text: __('Pick a project manually below.'),
        icon: 'info',
        iconClasses: 'text-blue-500',
      })
    }
  } catch (err) {
    toast({
      title: __('Analysis failed'),
      text: err.message || __('Please try again.'),
      icon: 'alert-circle',
      iconClasses: 'text-red-500',
    })
  } finally {
    analyzing.value = false
  }
}

async function dispatchToProject(projectName) {
  if (dispatching.value || !noteText.value.trim()) return
  dispatching.value = true
  try {
    // If audio is still sitting in memory (user picked manually before analyze),
    // upload it now so it gets attached to the chosen project too.
    const audioUrl = await uploadAudioIfPresent()

    const res = await call('lcs_integrations.notes.api.dispatch_note', {
      text: noteText.value,
      project: projectName,
      audio_file_url: audioUrl || '',
    })
    const payload = res.message || res
    lastDispatched.value = payload.target_project || projectName
    toast({
      title: __('Saved'),
      text: `${__('Note attached to')} ${lastDispatched.value}${audioUrl ? ' (+ audio)' : ''}`,
      icon: 'check-circle',
      iconClasses: 'text-green-500',
    })
    // Reset for the next note
    noteText.value = ''
    voiceBaseline = ''
    result.value = null
    capturedAudio.value = null
    manualQuery.value = ''
    manualResults.value = []
    noteInput.value?.focus()
  } catch (err) {
    toast({
      title: __('Could not save'),
      text: err.message || __('Please try again.'),
      icon: 'alert-circle',
      iconClasses: 'text-red-500',
    })
  } finally {
    dispatching.value = false
  }
}

function reset() {
  noteText.value = ''
  result.value = null
  voiceBaseline = ''
  capturedAudio.value = null
  manualQuery.value = ''
  manualResults.value = []
  lastDispatched.value = ''
  noteInput.value?.focus()
}

// If auto-dispatch was wrong, let the user pick a different target
function undoAndShowCandidates() {
  // Keep the note text, clear the auto-dispatch state so user gets candidates + manual picker
  if (result.value) {
    result.value = { ...result.value, auto_dispatched: false, comment: null, target_project: null }
  }
  // Optionally: could also delete the already-created comment — left for a future "undo" flow
}

// --- Manual project picker ---
const manualQuery = ref('')
const manualSearching = ref(false)
const manualResults = ref([])
let manualTimer = null

function onManualSearch() {
  clearTimeout(manualTimer)
  if (manualQuery.value.length < 2) {
    manualResults.value = []
    return
  }
  manualSearching.value = true
  manualTimer = setTimeout(async () => {
    try {
      const res = await call('lcs_integrations.projects.api.get_project_list', {
        filters: {
          project_name: ['like', `%${manualQuery.value}%`],
        },
        limit: 20,
      })
      const rows = res.message || res || []
      // Also search by number — second query, merged
      const res2 = await call('lcs_integrations.projects.api.get_project_list', {
        filters: {
          project_number: ['like', `%${manualQuery.value}%`],
        },
        limit: 20,
      })
      const byNumber = res2.message || res2 || []
      const merged = [...rows]
      for (const p of byNumber) {
        if (!merged.find(m => m.name === p.name)) merged.push(p)
      }
      manualResults.value = merged.slice(0, 20)
    } catch (err) {
      console.warn('manual search failed:', err)
      manualResults.value = []
    } finally {
      manualSearching.value = false
    }
  }, 250)
}

// --- Style helpers ---
function typeClass(type) {
  const m = {
    SB: 'bg-blue-100 text-blue-800',
    WI: 'bg-purple-100 text-purple-800',
    LL: 'bg-emerald-100 text-emerald-800',
    SK: 'bg-amber-100 text-amber-800',
    Other: 'bg-gray-100 text-gray-700',
  }
  return m[type] || 'bg-gray-100 text-gray-700'
}

function confidenceClass(level) {
  const m = {
    high: 'bg-green-100 text-green-800',
    medium: 'bg-amber-100 text-amber-800',
    low: 'bg-gray-100 text-gray-600',
    'very-low': 'bg-gray-100 text-gray-400',
  }
  return m[level] || 'bg-gray-100 text-gray-700'
}

function confidenceLabel(level) {
  const m = {
    high: __('High match'),
    medium: __('Likely'),
    low: __('Maybe'),
    'very-low': __('Weak'),
  }
  return m[level] || level
}
</script>
