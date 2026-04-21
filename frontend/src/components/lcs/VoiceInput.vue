<!--
  VoiceInput — Web Speech API wrapper.
  Emits `transcript` with recognized text.
-->

<template>
  <Tooltip :text="supported ? __('Voice input (click to start)') : __('Voice input not supported in this browser')">
    <button
      type="button"
      class="inline-flex h-8 w-8 items-center justify-center rounded-md transition"
      :class="buttonClass"
      :disabled="!supported"
      @click="toggle"
      :aria-label="__('Voice input')"
      :aria-pressed="listening"
    >
      <FeatherIcon :name="listening ? 'mic' : 'mic-off'" class="h-4 w-4" :class="listening ? 'animate-pulse' : ''" />
    </button>
  </Tooltip>
</template>

<script setup>
import { ref, computed, onUnmounted } from 'vue'
import { FeatherIcon, Tooltip, toast } from 'frappe-ui'

const props = defineProps({
  lang: { type: String, default: 'de-DE' },
})

const emit = defineEmits(['transcript', 'start', 'end'])

const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
const supported = !!SpeechRecognition

const listening = ref(false)
let recognition = null

const buttonClass = computed(() => {
  if (!supported) return 'text-gray-300 cursor-not-allowed'
  if (listening.value) return 'bg-red-100 text-red-600 hover:bg-red-200'
  return 'text-gray-400 hover:bg-gray-100 hover:text-gray-700'
})

function toggle() {
  if (listening.value) stop()
  else start()
}

function start() {
  if (!supported) {
    toast({ title: __('Voice input not supported'), icon: 'alert-circle' })
    return
  }
  recognition = new SpeechRecognition()
  recognition.lang = props.lang
  recognition.continuous = true
  recognition.interimResults = true

  let finalTranscript = ''

  recognition.onresult = (e) => {
    let interim = ''
    for (let i = e.resultIndex; i < e.results.length; i++) {
      const result = e.results[i]
      if (result.isFinal) {
        finalTranscript += result[0].transcript + ' '
      } else {
        interim += result[0].transcript
      }
    }
    emit('transcript', { final: finalTranscript, interim })
  }

  recognition.onerror = (e) => {
    toast({ title: __('Voice input error'), text: e.error, icon: 'alert-circle', iconClasses: 'text-red-500' })
    listening.value = false
  }

  recognition.onend = () => {
    listening.value = false
    emit('end')
  }

  recognition.start()
  listening.value = true
  emit('start')
}

function stop() {
  if (recognition) {
    recognition.stop()
    recognition = null
  }
  listening.value = false
}

onUnmounted(() => stop())
</script>
