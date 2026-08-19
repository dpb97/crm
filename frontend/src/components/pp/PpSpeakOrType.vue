<!-- PP_REV: PpSpeakOrType@1 -->
<!--
  PpSpeakOrType.vue — Eingabe per Text ODER Sprachaufnahme in EINEM Control
  (SSOT-Baustein).

  ECHTE props-in / events-out Komponente. Ein Feld, zwei Wege:
    · Tippen  → Text (v-model); Enter (ohne Shift) sendet, emittiert `text`.
    · Sprechen → echte Audioaufnahme über die MediaRecorder-API. Aufnahme
                 startet/stoppt WIRKLICH; beim Stopp entsteht ein Audio-Blob,
                 emittiert als `audio` (Blob + Object-URL + MIME + Dauer).

  Zustände (echt, sichtbar): idle · recording · error. Fehlt die
  MediaRecorder-/getUserMedia-Unterstützung oder wird der Mikrofonzugriff
  verweigert, geht der Baustein FAIL-LOUD in den sichtbaren error-Zustand
  (kein stiller Fallback, kein Skip) und emittiert `error`.

  Grenzen (Wahrheit ist Pflicht): Dieser Baustein TRANSKRIBIERT NICHT. Er
  liefert nur das rohe Audio-Blob — Spracherkennung/Transkription ist Sache
  der App (Backend/Service). Es gibt bewusst KEIN Fake-Transkript im Baustein.
  Ebenso kein Pegel-Meter/Waveform (nur Laufzeit-Anzeige) und keine
  Format-Konvertierung (das MIME kommt vom Browser bzw. `mimeType`-Prop).

  Props:
    modelValue  String  (v-model)          — aktueller Text im Feld
    placeholder String                     — Platzhalter der Texteingabe
    rows        Number  (default 3)         — Höhe der Texteingabe
    mimeType    String  (default "")        — bevorzugtes Audio-MIME; nur genutzt,
                                              wenn MediaRecorder es unterstützt,
                                              sonst Browser-Default
    maxSeconds  Number  (default 0)         — Auto-Stopp nach n Sekunden (0 = aus)
    disabled    Boolean (default false)     — Feld + Aktionen gesperrt

  Emits:
    update:modelValue (String)              — v-model
    text   (String)                         — gesendeter, getrimmter Text (Feld wird geleert)
    audio  ({ blob, url, mimeType, ms })    — fertige Aufnahme
    error  (String)                         — menschenlesbare Fehlermeldung (fail-loud)
    state  ("idle"|"recording"|"error")     — Zustandswechsel

  STRIKT --pp-*-Tokens, hell + dunkel. Scoped, Prefix `pp-sot`.
-->
<script setup>
import { ref, computed, watch, onBeforeUnmount } from "vue";
import { useViewport } from "@/composables/useViewport";
import IconMic   from "~icons/lucide/mic";
import IconSquare from "~icons/lucide/square";
import IconSend  from "~icons/lucide/send";
import IconAlert from "~icons/lucide/triangle-alert";

const props = defineProps({
  modelValue:  { type: String,  default: "" },
  placeholder: { type: String,  default: "Notiz eintippen…" },
  rows:        { type: Number,  default: 3 },
  mimeType:    { type: String,  default: "" },
  maxSeconds:  { type: Number,  default: 0 },
  disabled:    { type: Boolean, default: false },
});
const emit = defineEmits(["update:modelValue", "text", "audio", "error", "state"]);

// On the phone Enter inserts a line break (send only via the button); on the
// desktop Enter sends as before.
const { isMobile } = useViewport();

/* ---- Zustand ---------------------------------------------------- */
const mode = ref("idle");        // "idle" | "recording" | "error"
const errorMsg = ref("");
const seconds = ref(0);

watch(mode, (m) => emit("state", m));

const hasText = computed(() => (props.modelValue || "").trim().length > 0);
const hintText = computed(() => {
  if (mode.value === "recording") return "Aufnahme läuft… Stop-Knopf zum Beenden.";
  return isMobile.value
    ? "Tippen — Pfeil zum Senden (Enter = neue Zeile) — oder Mikrofon."
    : "Tippen und Enter zum Senden — oder Mikrofon für eine Sprachnotiz.";
});
function fmtTime(s) {
  const m = Math.floor(s / 60), r = s % 60;
  return String(m).padStart(2, "0") + ":" + String(r).padStart(2, "0");
}

/* ---- Text-Weg --------------------------------------------------- */
function onInput(e) { emit("update:modelValue", e.target.value); }
function onKeydown(e) {
  // Phone: Enter = line break (send via the arrow button). Desktop: Enter sends.
  if (e.key === "Enter" && !e.shiftKey && !isMobile.value) { e.preventDefault(); submitText(); }
}
function submitText() {
  const t = (props.modelValue || "").trim();
  if (!t || props.disabled || mode.value === "recording") return;
  emit("text", t);
  emit("update:modelValue", "");
}

/* ---- Audio-Weg (echte MediaRecorder-Integration) ---------------- */
let recorder = null;
let stream = null;
let chunks = [];
let timer = null;

function stopTimer() { if (timer) { clearInterval(timer); timer = null; } }
function releaseStream() {
  if (stream) { stream.getTracks().forEach((t) => t.stop()); stream = null; }
}
function fail(msg) {
  stopTimer();
  releaseStream();
  recorder = null;
  chunks = [];
  seconds.value = 0;
  errorMsg.value = msg;
  mode.value = "error";
  emit("error", msg);
}

async function startRecording() {
  if (props.disabled || mode.value === "recording") return;
  errorMsg.value = "";

  const md = typeof navigator !== "undefined" ? navigator.mediaDevices : null;
  if (!md || typeof md.getUserMedia !== "function" || typeof window.MediaRecorder === "undefined") {
    fail("Audioaufnahme wird in dieser Umgebung nicht unterstützt (MediaRecorder/getUserMedia fehlt).");
    return;
  }

  try {
    stream = await md.getUserMedia({ audio: true });
  } catch (err) {
    fail("Mikrofonzugriff nicht möglich: " + (err && err.name ? err.name : String(err)));
    return;
  }

  try {
    const opts = props.mimeType && window.MediaRecorder.isTypeSupported(props.mimeType)
      ? { mimeType: props.mimeType } : {};
    recorder = new window.MediaRecorder(stream, opts);
  } catch (err) {
    releaseStream();
    fail("Aufnahme-Initialisierung fehlgeschlagen: " + (err && err.message ? err.message : String(err)));
    return;
  }

  chunks = [];
  recorder.ondataavailable = (ev) => { if (ev.data && ev.data.size) chunks.push(ev.data); };
  recorder.onerror = (ev) => fail("Aufnahmefehler: " + (ev.error && ev.error.name ? ev.error.name : "unbekannt"));
  recorder.onstop = finalize;

  try {
    recorder.start();
  } catch (err) {
    releaseStream();
    fail("Aufnahme konnte nicht gestartet werden: " + (err && err.message ? err.message : String(err)));
    return;
  }

  mode.value = "recording";
  seconds.value = 0;
  timer = setInterval(() => {
    seconds.value += 1;
    if (props.maxSeconds > 0 && seconds.value >= props.maxSeconds) stopRecording();
  }, 1000);
}

function stopRecording() {
  stopTimer();
  if (recorder && recorder.state !== "inactive") {
    try { recorder.stop(); } catch { finalize(); }
  }
}

function finalize() {
  const type = (recorder && recorder.mimeType) || (chunks[0] && chunks[0].type) || "audio/webm";
  const ms = seconds.value * 1000;
  const captured = chunks;
  chunks = [];
  releaseStream();
  recorder = null;
  mode.value = "idle";
  const total = captured.reduce((a, c) => a + (c.size || 0), 0);
  seconds.value = 0;
  if (!total) {
    fail("Aufnahme leer — keine Audiodaten empfangen.");
    return;
  }
  const blob = new Blob(captured, { type });
  const url = URL.createObjectURL(blob);
  emit("audio", { blob, url, mimeType: type, ms });
}

function retry() { errorMsg.value = ""; mode.value = "idle"; }

onBeforeUnmount(() => { stopTimer(); if (recorder && recorder.state !== "inactive") { try { recorder.stop(); } catch { /* ignore */ } } releaseStream(); });
</script>

<template>
  <div class="pp-sot" :class="'is-' + mode" :data-state="mode">
    <!-- Fehlerbanner (fail-loud, echter error-Zustand) -->
    <div v-if="mode === 'error'" class="pp-sot__error" role="alert">
      <IconAlert class="pp-sot__error-ico" />
      <span class="pp-sot__error-msg">{{ errorMsg }}</span>
      <button type="button" class="pp-sot__retry" @click="retry">Erneut versuchen</button>
    </div>

    <div class="pp-sot__composer">
      <textarea
        class="pp-sot__input"
        :rows="rows"
        :placeholder="placeholder"
        :disabled="disabled || mode === 'recording'"
        :value="modelValue"
        @input="onInput"
        @keydown="onKeydown"
      ></textarea>

      <div class="pp-sot__actions">
        <div v-if="mode === 'recording'" class="pp-sot__rec" aria-live="polite">
          <span class="pp-sot__rec-dot" aria-hidden="true"></span>
          <span class="pp-sot__rec-time">{{ fmtTime(seconds) }}</span>
        </div>

        <button
          v-if="mode !== 'recording'"
          type="button"
          class="pp-sot__btn pp-sot__mic"
          :disabled="disabled"
          aria-label="Sprachnotiz aufnehmen"
          title="Sprachnotiz aufnehmen"
          @click="startRecording"
        ><IconMic /></button>
        <button
          v-else
          type="button"
          class="pp-sot__btn pp-sot__stop"
          aria-label="Aufnahme stoppen"
          title="Aufnahme stoppen"
          @click="stopRecording"
        ><IconSquare /><span class="pp-sot__stop-label">Stop</span></button>

        <button
          type="button"
          class="pp-sot__btn pp-sot__send"
          :disabled="disabled || mode === 'recording' || !hasText"
          aria-label="Text senden"
          title="Text senden (Enter)"
          @click="submitText"
        ><IconSend /></button>
      </div>
    </div>

    <p class="pp-sot__hint">{{ hintText }}</p>
  </div>
</template>

<style scoped>
.pp-sot { display: flex; flex-direction: column; gap: var(--pp-space-2);
  background: var(--pp-bg-surface); border: 1px solid var(--pp-border-default);
  border-radius: var(--pp-radius-ui); padding: var(--pp-space-3);
  transition: border-color var(--pp-duration-fast, 120ms) ease, box-shadow var(--pp-duration-fast, 120ms) ease; }
.pp-sot.is-recording { border-color: var(--pp-state-danger);
  box-shadow: 0 0 0 3px color-mix(in oklab, var(--pp-state-danger) 16%, transparent); }
.pp-sot.is-error { border-color: var(--pp-state-danger); }

/* Fehlerbanner */
.pp-sot__error { display: flex; align-items: center; gap: var(--pp-space-2);
  padding: var(--pp-space-2) var(--pp-space-3); border-radius: var(--pp-radius-ui);
  background: color-mix(in oklab, var(--pp-state-danger) 12%, transparent);
  color: var(--pp-state-danger); font-size: var(--pp-fs-13, 13px); }
.pp-sot__error-ico { width: 16px; height: 16px; flex-shrink: 0; }
.pp-sot__error-msg { flex: 1; min-width: 0; }
.pp-sot__retry { appearance: none; cursor: pointer; font-family: inherit;
  font-size: var(--pp-fs-12, 12px); font-weight: var(--pp-weight-semibold);
  padding: 3px var(--pp-space-2); border-radius: var(--pp-radius-ui);
  border: 1px solid var(--pp-state-danger); background: transparent; color: var(--pp-state-danger); }
.pp-sot__retry:hover { background: color-mix(in oklab, var(--pp-state-danger) 14%, transparent); }

/* Composer */
.pp-sot__composer { display: flex; align-items: flex-end; gap: var(--pp-space-2); }
.pp-sot__input { flex: 1; min-width: 0; resize: vertical; font-family: inherit;
  font-size: var(--pp-fs-14, 14px); line-height: var(--pp-lh-normal, 1.5); color: var(--pp-text-primary);
  background: var(--pp-bg-base); border: 1px solid var(--pp-border-default);
  border-radius: var(--pp-radius-ui); padding: var(--pp-space-2) var(--pp-space-3); }
.pp-sot__input:focus { outline: none; border-color: var(--pp-brand-primary);
  box-shadow: 0 0 0 3px rgb(var(--pp-brand-primary-rgb) / 0.15); }
.pp-sot__input:disabled { background: var(--pp-bg-sunken); color: var(--pp-text-tertiary); cursor: not-allowed; }

.pp-sot__actions { display: flex; align-items: center; gap: var(--pp-space-2); flex-shrink: 0; }

.pp-sot__btn { appearance: none; cursor: pointer; display: inline-flex; align-items: center; gap: 6px;
  height: 34px; padding: 0 var(--pp-space-3); border-radius: var(--pp-radius-ui);
  border: 1px solid var(--pp-border-default); background: var(--pp-bg-surface); color: var(--pp-text-secondary); }
.pp-sot__btn:hover:not(:disabled) { border-color: var(--pp-brand-primary); color: var(--pp-brand-primary); background: var(--pp-bg-hover); }
.pp-sot__btn:disabled { opacity: 0.5; cursor: not-allowed; }
.pp-sot__btn :deep(svg) { width: 16px; height: 16px; }

.pp-sot__send { background: var(--pp-brand-primary); border-color: var(--pp-brand-primary); color: var(--pp-text-on-accent); }
.pp-sot__send:hover:not(:disabled) { filter: brightness(1.05); color: var(--pp-text-on-accent); background: var(--pp-brand-primary); }
.pp-sot__stop { border-color: var(--pp-state-danger); color: var(--pp-state-danger); }
.pp-sot__stop:hover:not(:disabled) { background: color-mix(in oklab, var(--pp-state-danger) 14%, transparent);
  border-color: var(--pp-state-danger); color: var(--pp-state-danger); }
.pp-sot__stop-label { font-size: var(--pp-fs-13, 13px); font-weight: var(--pp-weight-semibold); }

.pp-sot__rec { display: inline-flex; align-items: center; gap: 6px; color: var(--pp-state-danger);
  font-size: var(--pp-fs-13, 13px); font-weight: var(--pp-weight-semibold); font-variant-numeric: tabular-nums; }
.pp-sot__rec-dot { width: 9px; height: 9px; border-radius: var(--pp-radius-full);
  background: var(--pp-state-danger); animation: pp-sot-pulse 1s ease-in-out infinite; }
@keyframes pp-sot-pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.25; } }
@media (prefers-reduced-motion: reduce) { .pp-sot__rec-dot { animation: none; } }

.pp-sot__hint { margin: 0; font-size: var(--pp-fs-12, 12px); color: var(--pp-text-tertiary); }
</style>
