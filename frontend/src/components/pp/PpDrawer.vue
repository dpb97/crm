<!-- PP_REV: PpDrawer@1 -->
<!--
  PpDrawer.vue — Side-Sheet (SSOT-Baustein).

  ECHTE props-in / events-out Komponente. Overlay + von der Seite
  einschiebendes Panel nach dem Kern-Muster .pp-drawer (components.css,
  Abschnitt 11). Backdrop-Klick + Esc schließen; Slide-Transition.

  Props:
    open   Boolean (v-model:open)
    side   'right' (default) | 'left'
    width  String|Number — Panelbreite (px-Zahl → "…px"), default 400
    title  String — Kopfzeile (oder Slot #title)

  Slots: (default) Inhalt · #title Kopf · #footer Fußleiste
  Emits: update:open · close

  STRIKT --pp-*-Tokens, hell + dunkel.
-->
<script setup>
import { computed, watch, onMounted, onBeforeUnmount } from "vue";
import X from "~icons/lucide/x";

const props = defineProps({
  open:  { type: Boolean, default: false },
  side:  { type: String,  default: "right" },
  width: { type: [String, Number], default: 400 },
  title: { type: String,  default: "" },
});
const emit = defineEmits(["update:open", "close"]);

const isLeft = computed(() => props.side === "left");
const panelWidth = computed(() =>
  typeof props.width === "number" ? props.width + "px" : props.width);

function close() { emit("update:open", false); emit("close"); }

function onKey(e) { if (props.open && e.key === "Escape") { e.preventDefault(); close(); } }
watch(() => props.open, (v) => {
  document.body.style.overflow = v ? "hidden" : "";
});
onMounted(() => window.addEventListener("keydown", onKey));
onBeforeUnmount(() => { window.removeEventListener("keydown", onKey); document.body.style.overflow = ""; });
</script>

<template>
  <transition name="pp-drawer-t">
    <div v-if="open" class="pp-drawer-overlay" :class="{ 'pp-drawer-overlay--left': isLeft }"
         @click.self="close">
      <div class="pp-drawer" :class="{ 'pp-drawer--left': isLeft }"
           :style="{ width: panelWidth }" role="dialog" aria-modal="true">
        <div class="pp-drawer__head">
          <span class="pp-drawer__title"><slot name="title">{{ title }}</slot></span>
          <button type="button" class="pp-collapse-btn" aria-label="Schließen"
                  title="Schließen" @click="close"><X /></button>
        </div>
        <div class="pp-drawer__body"><slot /></div>
        <div v-if="$slots.footer" class="pp-drawer__foot"><slot name="footer" /></div>
      </div>
    </div>
  </transition>
</template>

<style scoped>
/* Links andocken (Kern .pp-drawer-overlay dockt rechts an). */
.pp-drawer-overlay--left { justify-content: flex-start; }

/* Slide-Transition (rechts default, links gespiegelt). */
.pp-drawer-t-enter-active, .pp-drawer-t-leave-active { transition: opacity var(--pp-duration-base) var(--pp-ease-standard); }
.pp-drawer-t-enter-active .pp-drawer, .pp-drawer-t-leave-active .pp-drawer {
  transition: transform var(--pp-duration-base) var(--pp-ease-decelerate); }
.pp-drawer-t-enter-from, .pp-drawer-t-leave-to { opacity: 0; }
.pp-drawer-t-enter-from .pp-drawer, .pp-drawer-t-leave-to .pp-drawer { transform: translateX(100%); }
.pp-drawer-t-enter-from .pp-drawer--left, .pp-drawer-t-leave-to .pp-drawer--left { transform: translateX(-100%); }
</style>
