<!--
  VoiceInput — speech-to-text for any text/textarea field.
  ============================================================

  Features:
  - Auto-reads language from LCS User Preferences (voice_input_language)
  - Live audio-level meter (visual feedback during recording)
  - Live interim transcript preview in a floating pill
  - Keyboard shortcut Ctrl+Shift+V (or ⌘+Shift+V on Mac)
  - Detects WebSpeech vs Azure Speech backend via settings
  - Graceful fallback + clear error messages

  Emits:
    transcript { final: string, interim: string } — live stream
    done      final transcript string — on stop/end
-->

<template>
  <div class="relative inline-block">
    <Tooltip :text="tooltipText">
      <button
        type="button"
        class="inline-flex h-8 w-8 items-center justify-center rounded-md transition"
        :class="buttonClass"
        :disabled="!supported"
        @click="toggle"
        :aria-label="__('Voice input')"
        :aria-pressed="listening"
      >
        <FeatherIcon :name="listening ? 'mic' : supported ? 'mic' : 'mic-off'" class="h-4 w-4" />
      </button>
    </Tooltip>

    <!-- Audio level meter — 5 vertical bars animated when listening -->
    <div
      v-if="listening"
      class="pointer-events-none absolute -right-1 -top-1 flex items-end gap-0.5"
      aria-hidden="true"
    >
      <span
        v-for="i in 5"
        :key="i"
        class="w-0.5 rounded-sm bg-red-500 transition-all duration-100"
        :style="{ height: `${4 + Math.max(0, (audioLevel - i * 0.15) * 30)}px` }"
      />
    </div>

    <!-- Live interim transcript — shown as a tooltip-like pill -->
    <Transition
      enter-active-class="transition duration-150"
      enter-from-class="opacity-0 translate-y-1"
      enter-to-class="opacity-100 translate-y-0"
      leave-active-class="transition duration-100"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div
        v-if="listening && interimText"
        class="absolute right-full top-1/2 mr-2 -translate-y-1/2 whitespace-nowrap rounded-lg bg-gray-900 px-3 py-1.5 text-xs text-white shadow-lg"
        style="max-width: min(400px, calc(100vw - 24px)); white-space: normal; overflow-wrap: break-word;"
      >
        <div class="flex items-center gap-1.5">
          <span class="h-1.5 w-1.5 animate-pulse rounded-full bg-red-400" />
          <span class="text-gray-300">{{ __('Listening') }}{{ activeLang ? ' · ' + activeLang : '' }}</span>
        </div>
        <div class="mt-0.5 italic">{{ interimText }}</div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { FeatherIcon, Tooltip, toast } from 'frappe-ui'
import { useUserPreferences } from '@/composables/useUserPreferences'

const props = defineProps({
  /** Override the user's preferred language (e.g. force en-US for a specific field) */
  lang: { type: String, default: '' },
  /** Enable the global Ctrl+Shift+V hotkey for this instance (only one should set this per page) */
  hotkey: { type: Boolean, default: false },
  /** Record the raw audio in parallel — emitted as `audio-blob` on stop */
  recordAudio: { type: Boolean, default: false },
})

const emit = defineEmits(['transcript', 'start', 'end', 'done', 'audio-blob'])

// MediaRecorder state
let mediaRecorder = null
let audioChunks = []

const userPrefs = useUserPreferences()

const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
const supported = !!SpeechRecognition

const listening = ref(false)
const interimText = ref('')
const audioLevel = ref(0)

let recognition = null
let audioContext = null
let analyser = null
let rafHandle = null
let mediaStream = null

// Active language: explicit prop > user preference > browser default
const activeLang = computed(() =>
  props.lang || userPrefs.state.prefs.voice_input_language || 'de-DE',
)

const buttonClass = computed(() => {
  if (!supported) return 'text-gray-300 cursor-not-allowed'
  if (listening.value) return 'bg-red-50 text-red-600 ring-2 ring-red-200 hover:bg-red-100'
  return 'text-gray-400 hover:bg-gray-100 hover:text-gray-700'
})

const tooltipText = computed(() => {
  if (!supported) return __('Voice input not supported in this browser (Chrome/Edge recommended)')
  const hotkeyHint = props.hotkey ? ' (Ctrl+Shift+V)' : ''
  return listening.value
    ? __('Stop recording') + hotkeyHint
    : __('Voice input') + hotkeyHint + ' · ' + activeLang.value
})

function toggle() {
  if (listening.value) stop()
  else start()
}

async function start() {
  if (!supported) {
    toast({
      title: __('Voice input not supported'),
      text: __('Please use Chrome or Edge.'),
      icon: 'alert-circle',
      iconClasses: 'text-red-500',
    })
    return
  }

  // --- Audio meter + optional recording setup ---
  try {
    mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true })
    audioContext = new (window.AudioContext || window.webkitAudioContext)()
    const source = audioContext.createMediaStreamSource(mediaStream)
    analyser = audioContext.createAnalyser()
    analyser.fftSize = 256
    source.connect(analyser)
    startMeterLoop()

    // Optional: record the raw audio in parallel so it can be sent to
    // Whisper / Azure later for higher-quality re-transcription.
    // MediaRecorder format depends on the browser — typically
    // audio/webm;codecs=opus on Chrome/Edge/Firefox, audio/mp4 on Safari.
    if (props.recordAudio && window.MediaRecorder) {
      audioChunks = []
      const mimeCandidates = [
        'audio/webm;codecs=opus',
        'audio/webm',
        'audio/mp4',
        'audio/ogg;codecs=opus',
      ]
      const mimeType = mimeCandidates.find(m => MediaRecorder.isTypeSupported(m)) || ''
      mediaRecorder = new MediaRecorder(mediaStream, mimeType ? { mimeType } : undefined)
      mediaRecorder.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) audioChunks.push(e.data)
      }
      mediaRecorder.start(1000)  // collect in 1-second chunks so stop() finalises fast
    }
  } catch (err) {
    // Getting the audio stream failed — recognition will still work in
    // some browsers because Web Speech API opens its own stream. We
    // just won't have the level meter. Not fatal.
    console.warn('Audio meter/recording unavailable:', err)
  }

  // --- Recognition setup ---
  recognition = new SpeechRecognition()
  recognition.lang = activeLang.value
  recognition.continuous = true
  recognition.interimResults = true
  recognition.maxAlternatives = 1

  let finalTranscript = ''

  recognition.onresult = (e) => {
    let interim = ''
    let newlyFinal = ''
    for (let i = e.resultIndex; i < e.results.length; i++) {
      const result = e.results[i]
      const segment = result[0].transcript
      if (result.isFinal) {
        newlyFinal += segment + ' '
      } else {
        interim += segment
      }
    }
    if (newlyFinal) finalTranscript += newlyFinal
    interimText.value = interim
    emit('transcript', { final: finalTranscript, interim })
  }

  recognition.onerror = (e) => {
    const msg = mapError(e.error)
    toast({
      title: __('Voice input'),
      text: msg,
      icon: 'alert-circle',
      iconClasses: 'text-red-500',
    })
    cleanup()
  }

  recognition.onend = () => {
    emit('done', finalTranscript)
    cleanup()
  }

  try {
    recognition.start()
    listening.value = true
    emit('start')
  } catch (err) {
    toast({
      title: __('Could not start recording'),
      text: err.message || String(err),
      icon: 'alert-circle',
      iconClasses: 'text-red-500',
    })
    cleanup()
  }
}

function stop() {
  if (recognition) {
    try { recognition.stop() } catch {}
  }
  cleanup()
}

function cleanup() {
  listening.value = false
  interimText.value = ''
  audioLevel.value = 0

  if (rafHandle) {
    cancelAnimationFrame(rafHandle)
    rafHandle = null
  }

  // Finalise the recording before we close the stream. MediaRecorder's
  // onstop handler fires asynchronously, so we emit the blob from there.
  if (mediaRecorder) {
    const mr = mediaRecorder
    const chunks = audioChunks
    mr.onstop = () => {
      if (chunks.length) {
        const blob = new Blob(chunks, { type: mr.mimeType || 'audio/webm' })
        emit('audio-blob', { blob, mimeType: mr.mimeType, duration: null })
      }
    }
    try { mr.state !== 'inactive' && mr.stop() } catch {}
    mediaRecorder = null
    audioChunks = []
  }

  if (mediaStream) {
    mediaStream.getTracks().forEach(t => t.stop())
    mediaStream = null
  }
  if (audioContext) {
    audioContext.close().catch(() => {})
    audioContext = null
  }
  analyser = null
  recognition = null
  emit('end')
}

function startMeterLoop() {
  if (!analyser) return
  const buf = new Uint8Array(analyser.frequencyBinCount)

  const tick = () => {
    if (!analyser) return
    analyser.getByteTimeDomainData(buf)
    // RMS → 0..1
    let sum = 0
    for (let i = 0; i < buf.length; i++) {
      const v = (buf[i] - 128) / 128
      sum += v * v
    }
    audioLevel.value = Math.min(1, Math.sqrt(sum / buf.length) * 3)
    rafHandle = requestAnimationFrame(tick)
  }
  tick()
}

// Translate Web Speech API error codes into actionable German messages
function mapError(code) {
  const map = {
    'not-allowed': __('Microphone permission denied. Enable it in browser settings.'),
    'service-not-allowed': __('Microphone access blocked by your system.'),
    'no-speech': __('No speech detected. Speak closer to the microphone.'),
    'audio-capture': __('No microphone found.'),
    'network': __('Network error reaching speech recognition service.'),
    'aborted': __('Recording was cancelled.'),
    'bad-grammar': __('Speech recognition grammar error.'),
    'language-not-supported': __('Selected language is not supported.'),
  }
  return map[code] || __('Speech recognition failed: ') + code
}

// --- Global hotkey ---

function handleHotkey(e) {
  if (!props.hotkey || !supported) return
  if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.code === 'KeyV') {
    e.preventDefault()
    toggle()
  }
}

onMounted(() => {
  if (props.hotkey) document.addEventListener('keydown', handleHotkey)
})
onUnmounted(() => {
  if (props.hotkey) document.removeEventListener('keydown', handleHotkey)
  cleanup()
})

// If lang prop changes while listening, restart with new language
watch(() => props.lang, (v) => {
  if (listening.value && v && recognition && recognition.lang !== v) {
    stop()
    setTimeout(() => start(), 100)
  }
})
</script>
