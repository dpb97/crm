<!-- PP_REV: PpModal@2 -->
<!--
  PpModal.vue — zentrales Erfassungs-/Dialog-Fenster (SSOT-Baustein).

  Verbindliche Layout-Regel (Marco 24.07.2026, Pilanda-weit): Erfassungs-
  formulare und Entscheid-Dialoge schieben sich NIE in den Canvas-Fluss —
  sie öffnen als eigenes Fenster ZENTRAL über der Arbeitsfläche. Vue-Nachzug
  der Klickdummy-Funktion `openModal` (pilanda-navigation.html): Scrim, und
  ESC / X / Außenklick schließen. Reine Erfassungs-Seiten mit eigenem
  Nav-Punkt sind davon ausgenommen (dort ist das Formular der Seiteninhalt).

  ECHTE props-in / events-out — kein Store, kein Backend.

  Props:
    open   Boolean (v-model:open)  Sichtbarkeit
    title  String                  Kopfzeile (oder Slot #title)
    width  String|Number           max. Breite (px-Zahl → "…px"), default 640
    closeOnBackdrop Boolean         Außenklick schließt (default true)
    closeOnEsc      Boolean         ESC schließt (default true)

  Slots: (default) Fensterinhalt · #title Kopf · #footer Fußleiste
  Emits: update:open · close

  @2 (26.07.2026): ESC konsumiert das Event (stopPropagation) — ein offenes
  Modal darf beim Schließen den ESC nicht weiterreichen, sonst schließt eine
  darunterliegende Cockpit-ESC-Bindung (PpInspector/PpModuleLayout/PiAssistant)
  gleich mit (Preview-Cockpit-Konflikt). Der Listener hängt jetzt — wie das
  Präzedenz-Muster PpFunctionBar@2 („gleiche Dinge gleich") — auf DOCUMENT und
  nicht auf window: keydown blubbert durch document VOR window, sodass
  stopPropagation die window-Listener der Shell zuverlässig stoppt (auf window
  wäre stopPropagation gegen gleichrangige window-Listener wirkungslos).

  STRIKT --pp-*-Tokens, hell + dunkel; kein v-html mit Nutzdaten.
-->
<script setup>
import { computed, ref, watch, nextTick, onMounted, onBeforeUnmount } from "vue";
import X from "~icons/lucide/x";

const props = defineProps({
  open:            { type: Boolean, default: false },
  title:           { type: String,  default: "" },
  width:           { type: [String, Number], default: 640 },
  closeOnBackdrop: { type: Boolean, default: true },
  closeOnEsc:      { type: Boolean, default: true },
});
const emit = defineEmits(["update:open", "close"]);

const closeBtn = ref(null);
const maxWidth = computed(() =>
  typeof props.width === "number" ? props.width + "px" : props.width);

function close() { emit("update:open", false); emit("close"); }
function onBackdrop() { if (props.closeOnBackdrop) close(); }
function onKey(e) {
  if (props.open && props.closeOnEsc && e.key === "Escape") {
    e.preventDefault();
    e.stopPropagation(); // @2: nicht an die Cockpit-ESC-Bindungen weiterreichen
    close();
  }
}
watch(() => props.open, (v) => {
  document.body.style.overflow = v ? "hidden" : "";
  if (v) nextTick(() => closeBtn.value && closeBtn.value.focus());
});
// document (nicht window): keydown blubbert durch document VOR window, sodass
// stopPropagation die window-Listener der Shell zuverlässig stoppt (@2).
onMounted(() => document.addEventListener("keydown", onKey));
onBeforeUnmount(() => { document.removeEventListener("keydown", onKey); document.body.style.overflow = ""; });
</script>

<template>
  <transition name="pp-modal-t">
    <div v-if="open" class="pp-modal-scrim" @click.self="onBackdrop">
      <div class="pp-modal" role="dialog" aria-modal="true"
           :aria-label="title || undefined" :style="{ maxWidth }">
        <div class="pp-modal__head">
          <span class="pp-modal__title"><slot name="title">{{ title }}</slot></span>
          <button ref="closeBtn" type="button" class="pp-modal__x"
                  aria-label="Schließen" title="Schließen" @click="close"><X /></button>
        </div>
        <div class="pp-modal__body"><slot /></div>
        <div v-if="$slots.footer" class="pp-modal__foot"><slot name="footer" /></div>
      </div>
    </div>
  </transition>
</template>

<style scoped>
.pp-modal-scrim { position: fixed; inset: 0; z-index: var(--pp-z-modal);
  display: flex; align-items: center; justify-content: center; padding: var(--pp-space-6);
  background: rgb(var(--pp-shadow-deep-rgb) / .42);
  -webkit-backdrop-filter: blur(2px); backdrop-filter: blur(2px); }
.pp-modal { display: flex; flex-direction: column; width: 100%; max-height: 86%;
  background: var(--pp-bg-surface); border: 1px solid var(--pp-border-default);
  border-radius: var(--pp-radius-ui); box-shadow: var(--pp-shadow-xl); overflow: hidden; }

.pp-modal__head { display: flex; align-items: center; justify-content: space-between; gap: var(--pp-space-2);
  flex: 0 0 auto; padding: var(--pp-space-3) var(--pp-space-4);
  border-bottom: 1px solid var(--pp-border-subtle); background: var(--pp-accent-soft);
  color: var(--pp-brand-primary-d, var(--pp-brand-primary)); }
.pp-modal__title { font-size: var(--pp-fs-13, 13px); font-weight: var(--pp-weight-semibold);
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.pp-modal__x { appearance: none; cursor: pointer; flex: 0 0 auto; display: inline-flex;
  align-items: center; justify-content: center; width: 26px; height: 26px; padding: 0;
  border: 1px solid transparent; border-radius: var(--pp-radius-ui); background: transparent;
  color: var(--pp-brand-primary-d, var(--pp-brand-primary));
  transition: background var(--pp-duration-fast) var(--pp-ease-standard),
    border-color var(--pp-duration-fast) var(--pp-ease-standard); }
.pp-modal__x:hover { background: var(--pp-bg-hover); border-color: var(--pp-border-default); }
.pp-modal__x:focus-visible { outline: none; box-shadow: var(--pp-shadow-focus-ring); }
.pp-modal__x :deep(svg) { width: 15px; height: 15px; display: block; }

.pp-modal__body { flex: 1 1 auto; min-height: 0; overflow: auto; padding: var(--pp-space-4);
  color: var(--pp-text-primary); font-size: var(--pp-fs-13, 13px); }
.pp-modal__foot { flex: 0 0 auto; display: flex; align-items: center; justify-content: flex-end;
  gap: var(--pp-space-2); padding: var(--pp-space-3) var(--pp-space-4);
  border-top: 1px solid var(--pp-border-subtle); background: var(--pp-bg-sunken); }

/* Ein-/Ausblenden: Scrim faded, Fenster steigt leicht auf. */
.pp-modal-t-enter-active, .pp-modal-t-leave-active { transition: opacity var(--pp-duration-base) var(--pp-ease-standard); }
.pp-modal-t-enter-active .pp-modal, .pp-modal-t-leave-active .pp-modal {
  transition: transform var(--pp-duration-base) var(--pp-ease-decelerate); }
.pp-modal-t-enter-from, .pp-modal-t-leave-to { opacity: 0; }
.pp-modal-t-enter-from .pp-modal, .pp-modal-t-leave-to .pp-modal { transform: translateY(12px) scale(.98); }
</style>
