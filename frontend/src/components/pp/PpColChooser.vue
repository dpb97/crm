<!-- PP_REV: PpColChooser@1 -->
<!--
  PpColChooser.vue — gemeinsamer Spalten-Chooser (EIN Baustein).

  Vue-Nachzug der Klickdummy-Funktion `colChooser` (pilanda-navigation.html,
  Welle 25.07.): eine Pillen-Schaltfläche „Spalten" öffnet ein Panel mit
  Checkboxen je Spalte; die Reihenfolge lässt sich per Drag&Drop ändern
  (native HTML5-DnD). Gleiche Optik/Bedienung für Gantt UND Artikel-Grid
  („gleiche Dinge immer gleich lösen"). EIN State-Flag `open` steuert das Panel.

  ECHTE props-in / events-out — kein Store, keine Persistenz (macht der Host).

  Props:
    open   Boolean (v-model:open)     Panel offen
    items  [{ k, l, checked?, disabled? }]  Spalten in AKTUELLER Reihenfolge
    head   String                     Panel-Kopf (default „Spalten einblenden")
    label  String                     Pillen-Text (default „Spalten")
    reorderable Boolean               DnD-Reihenfolge erlauben (default true)
  Emits:
    update:open        Panel auf/zu
    toggle {k,checked} Spalte ein-/ausgeblendet
    reorder [k,…]      neue Schlüssel-Reihenfolge (nach DnD)

  STRIKT --pp-*-Tokens, hell + dunkel.
-->
<script setup>
import { ref } from "vue";
import Columns from "~icons/lucide/columns-3";

const props = defineProps({
  open:        { type: Boolean, default: false },
  items:       { type: Array,   default: () => [] },
  head:        { type: String,  default: "Spalten einblenden" },
  label:       { type: String,  default: "Spalten" },
  reorderable: { type: Boolean, default: true },
});
const emit = defineEmits(["update:open", "toggle", "reorder"]);

function toggleOpen() { emit("update:open", !props.open); }
function onToggle(it, e) { if (it.disabled) return; emit("toggle", { k: it.k, checked: e.target.checked }); }

// --- DnD-Reihenfolge (native HTML5; Persistenz macht der Host) ---
const dragKey = ref(null);
function onDragStart(k) { dragKey.value = k; }
function onDrop(targetK) {
  const from = dragKey.value; dragKey.value = null;
  if (!from || from === targetK) return;
  const order = props.items.map((i) => i.k);
  const fi = order.indexOf(from), ti = order.indexOf(targetK);
  if (fi < 0 || ti < 0) return;
  order.splice(ti, 0, order.splice(fi, 1)[0]);
  emit("reorder", order);
}
</script>

<template>
  <div class="pp-colchooser">
    <button type="button" class="pp-colchooser__pill" :class="{ 'is-open': open }"
            :aria-expanded="open" aria-haspopup="menu" @click="toggleOpen">
      <Columns /><span>{{ label }}</span>
    </button>
    <template v-if="open">
      <div class="pp-colchooser__backdrop" @click="emit('update:open', false)"></div>
      <div class="pp-colchooser__panel" role="menu">
        <div class="pp-colchooser__head">{{ head }}</div>
        <label v-for="it in items" :key="it.k" class="pp-colchooser__row"
               :class="{ 'is-disabled': it.disabled, 'is-drag': dragKey === it.k }"
               :draggable="reorderable && !it.disabled ? 'true' : 'false'"
               @dragstart="onDragStart(it.k)" @dragover.prevent @drop.prevent="onDrop(it.k)">
          <span v-if="reorderable" class="pp-colchooser__grip" aria-hidden="true">⋮⋮</span>
          <input type="checkbox" :checked="it.checked" :disabled="it.disabled" @change="onToggle(it, $event)">
          <span class="pp-colchooser__lbl">{{ it.l }}</span>
        </label>
      </div>
    </template>
  </div>
</template>

<style scoped>
/* Eigener Stapelkontext (z-index) über der Seite: so liegt das Panel garantiert
   ÜBER dem viewport-füllenden Backdrop (sonst gewinnt der fixe Backdrop das
   Cross-Context-Rennen und verdeckt die Checkboxen). */
.pp-colchooser { position: relative; display: inline-flex; z-index: 50; }
.pp-colchooser__pill { display: inline-flex; align-items: center; gap: var(--pp-space-1);
  font-size: var(--pp-fs-12); font-weight: var(--pp-weight-semibold);
  padding: 5px var(--pp-space-2); border: 1px solid var(--pp-border-default);
  border-radius: var(--pp-radius-ui); background: var(--pp-bg-surface); color: var(--pp-text-primary);
  cursor: pointer; transition: background var(--pp-duration-fast) var(--pp-ease-standard); }
.pp-colchooser__pill:hover { background: var(--pp-bg-hover); }
.pp-colchooser__pill.is-open { border-color: var(--pp-brand-primary); color: var(--pp-brand-primary); }
.pp-colchooser__pill :deep(svg) { width: 14px; height: 14px; }

.pp-colchooser__backdrop { position: fixed; inset: 0; z-index: 1; }
.pp-colchooser__panel { position: absolute; top: calc(100% + 4px); right: 0; z-index: 2;
  min-width: 220px; padding: var(--pp-space-2); background: var(--pp-bg-elevated);
  border: 1px solid var(--pp-border-default); border-radius: var(--pp-radius-ui);
  box-shadow: var(--pp-shadow-lg); }
.pp-colchooser__head { font-size: var(--pp-fs-12); font-weight: var(--pp-weight-bold);
  color: var(--pp-text-secondary); padding: 2px var(--pp-space-1) var(--pp-space-1);
  text-transform: uppercase; letter-spacing: .05em; }
.pp-colchooser__row { display: flex; align-items: center; gap: var(--pp-space-2);
  padding: var(--pp-space-1) var(--pp-space-1); border-radius: var(--pp-radius-sm);
  font-size: var(--pp-fs-13, 13px); color: var(--pp-text-primary); cursor: pointer; }
.pp-colchooser__row:hover { background: var(--pp-bg-hover); }
.pp-colchooser__row.is-disabled { opacity: .5; cursor: not-allowed; }
.pp-colchooser__row.is-drag { opacity: .5; }
.pp-colchooser__grip { color: var(--pp-text-tertiary); font-size: 11px; cursor: grab; letter-spacing: -2px; }
.pp-colchooser__lbl { flex: 1; }
.pp-colchooser__row input { accent-color: var(--pp-brand-primary); }
</style>
