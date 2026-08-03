<!-- PP_REV: PpKanban@4 -->
<!--
  PpKanban.vue — Karten-Board mit ECHTEM Drag & Drop (SSOT-Baustein).

  Für Ticketsystem / Taskmanager: Karten wandern per Zeiger zwischen Status-
  Spalten. Das Drag&Drop ist mit reinen Pointer-Events gebaut (KEIN externes
  npm-Paket): Aufnehmen, freies Ziehen (fixierter Geist-Klon), Einfüge-Position
  live über document.elementFromPoint, Loslassen = Move.

  ECHTE props-in / events-out Komponente — kein Store, kein Backend. Der interne
  Karten-Zustand (localCards) spiegelt die Props und wird beim Ablegen sofort
  aktualisiert (optimistische Anzeige); die App entscheidet via @move, ob sie
  den neuen Stand übernimmt/persistiert.

  @4 (23.07.2026): Aufgaben-Karte nachgezogen aus dem Klickdummy (Batch V).
  Optionale, RÜCKWÄRTSKOMPATIBLE Kartenfelder:
    · ref       String  — Kennung oben links (z. B. „AP-4471")
    · prio      { label, tone }  — Prioritäts-Chip oben rechts, KLICKBAR
                (tone ∈ danger|warning|success) → emit `prio-click`
    · stripe    String  — CSS-Farbe des linken Prioritäts-Streifens der Karte
    · subtitle  String  — Unterzeile unter dem Titel (z. B. Projekt · Bereich)
    · meta      Array<String>  — zusätzliche Meta-Angaben (Stunden, %, Fällig …)
  Neu: Doppelklick auf eine Karte → emit `card-dblclick` (z. B. Deep-Link).
  Ohne die neuen Felder rendert die Karte exakt wie @3.

  Props:
    columns  Array<{ key, label, wip? }>
             · wip  optionale Obergrenze → Zähler wird bei Überschreitung
               als Warnung (rot) markiert
    cards    Array<{ id, col, title, badges?, assignee?, due?,
                     ref?, prio?, stripe?, subtitle?, meta? }>
             · badges   Array<string | { label, tone? }>  tone: neutral|info|
               success|warning|danger
             · assignee String (Kürzel/Name → Avatar-Initialen)
             · due      String (Fälligkeit, frei formatiert)

  Emits:
    move         ({ cardId, fromCol, toCol, index })  nach erfolgreichem Ablegen
    card-click   (cardId)                             Klick ohne Ziehen
    card-dblclick(cardId)                             Doppelklick auf eine Karte
    prio-click   (cardId)                             Klick auf den Prio-Chip

  Slots (@3):
    #column-meta   Optionaler Zusatz je Spaltenkopf, gerendert UNTER dem
                   bestehenden Label + Zähler-Badge. Slot-Props { column }
                   (= das columns-Element). OHNE Slot rendert NICHTS — kein
                   Wrapper, keine Layout-Verschiebung; Default-Rendering exakt
                   wie bisher (voll rückwärtskompatibel). Für dezente
                   Kopf-Kennzahlen wie Phasen-Summen o. Ä.

  Basis-Look über zentrale .pp-kanban*-Klassen (components.css, SSOT); Drag-
  Zustände / WIP / Badges scoped mit --pp-*-Tokens. Hell + dunkel.
-->
<script setup>
import { ref, computed, watch, onBeforeUnmount } from "vue";
import { useViewport } from "@/composables/useViewport";
import ChevronLeft from "~icons/lucide/chevron-left";
import ChevronRight from "~icons/lucide/chevron-right";

const props = defineProps({
  columns: { type: Array, default: () => [] }, // [{ key, label, wip? }]
  cards:   { type: Array, default: () => [] }, // [{ id, col, title, badges?, assignee?, due? }]
  highlightCol: { type: String, default: "" }, // @4: eine Spalte fokussieren (andere gedämpft)
});
const emit = defineEmits(["move", "card-click", "card-dblclick", "prio-click"]);

/* ---- Interner, ablegbarer Karten-Zustand ----------------------- */
const localCards = ref([]);
function syncFromProps() {
  localCards.value = props.cards.map((c) => ({ ...c }));
}
syncFromProps();
watch(() => props.cards, syncFromProps, { deep: true });

/* Karten je Spalte, in aktueller Reihenfolge des internen Arrays. */
const byCol = computed(() => {
  const map = {};
  for (const col of props.columns) map[col.key] = [];
  for (const c of localCards.value) (map[c.col] ??= []).push(c);
  return map;
});

/* ---- Mobile: one lane at a time, swipe between phases ---------------
   On a phone the columns don't fit side by side, so we show a single
   full-width lane and let the user swipe (or tap the ‹ › / dots) through
   the phases. Desktop keeps the full multi-column board. */
const { isMobile } = useViewport();
const activeIdx = ref(0);
watch(
  () => props.columns.length,
  (n) => { if (activeIdx.value > n - 1) activeIdx.value = Math.max(0, n - 1); },
);
const shownColumns = computed(() =>
  isMobile.value
    ? (props.columns[activeIdx.value] ? [props.columns[activeIdx.value]] : [])
    : props.columns,
);
function prevCol() { if (activeIdx.value > 0) activeIdx.value--; }
function nextCol() { if (activeIdx.value < props.columns.length - 1) activeIdx.value++; }
let _swx = 0, _swy = 0;
function onLaneTouchStart(e) { const t = e.changedTouches[0]; _swx = t.clientX; _swy = t.clientY; }
function onLaneTouchEnd(e) {
  const t = e.changedTouches[0];
  const dx = t.clientX - _swx, dy = t.clientY - _swy;
  // Horizontal swipe over ~50px that is clearly not a vertical scroll.
  if (Math.abs(dx) > 50 && Math.abs(dx) > Math.abs(dy) * 1.4) {
    dx < 0 ? nextCol() : prevCol();
  }
}

const TONE_STATE = {
  info:    "var(--pp-state-info)",
  success: "var(--pp-state-success)",
  warning: "var(--pp-state-warning)",
  danger:  "var(--pp-state-danger)",
};
function badgeStyle(b) {
  const tone = typeof b === "object" ? b.tone : null;
  const col = TONE_STATE[tone];
  return col ? { color: col, borderColor: col } : null;
}
const badgeLabel = (b) => (typeof b === "object" ? b.label : b);

/* Prio-Chip (@4): getönter Chip in State-Farbe, klickbar (Zyklus im Host). */
function prioStyle(prio) {
  const col = TONE_STATE[prio?.tone] || "var(--pp-text-secondary)";
  return { color: col, background: `color-mix(in oklab, ${col} 12%, transparent)` };
}
const initials = (name) =>
  (name || "").split(/\s+/).map((w) => w[0]).join("").slice(0, 2).toUpperCase();

/* ---- Drag & Drop per Pointer-Events (ohne Bibliothek) ---------- */
const DRAG_THRESHOLD = 5; // px bis "ziehen" statt "klick"

const drag = ref(null);   // { id, fromCol, startX, startY, x, y, active }
const dropTarget = ref(null); // { col, index }

let downCard = null;      // Kandidat bei pointerdown

function onPointerDown(ev, card) {
  if (ev.button != null && ev.button !== 0) return; // nur primäre Taste
  downCard = card;
  drag.value = {
    id: card.id,
    fromCol: card.col,
    startX: ev.clientX,
    startY: ev.clientY,
    x: ev.clientX,
    y: ev.clientY,
    active: false,
  };
  window.addEventListener("pointermove", onPointerMove);
  window.addEventListener("pointerup", onPointerUp);
}

function onPointerMove(ev) {
  if (!drag.value) return;
  const d = drag.value;
  d.x = ev.clientX;
  d.y = ev.clientY;
  // Mobile: cards are not draggable (one lane visible at a time); horizontal
  // movement is a lane swipe, handled by the container's touch listeners.
  if (isMobile.value) return;
  if (!d.active) {
    const dist = Math.hypot(ev.clientX - d.startX, ev.clientY - d.startY);
    if (dist < DRAG_THRESHOLD) return;
    d.active = true;
    document.body.style.userSelect = "none";
  }
  computeDropTarget(ev.clientX, ev.clientY);
}

/* Einfüge-Ziel bestimmen: Spalte + Index über den Zeiger. Der Geist-Klon
   hat pointer-events:none, daher trifft elementFromPoint die Karten darunter. */
function computeDropTarget(x, y) {
  const el = document.elementFromPoint(x, y);
  const colEl = el && el.closest ? el.closest("[data-kanban-col]") : null;
  if (!colEl) { dropTarget.value = null; return; }
  const colKey = colEl.getAttribute("data-kanban-col");
  const cardEls = [...colEl.querySelectorAll("[data-kanban-card]")].filter(
    (c) => c.getAttribute("data-kanban-card") !== drag.value.id,
  );
  let index = cardEls.length;
  for (let i = 0; i < cardEls.length; i++) {
    const r = cardEls[i].getBoundingClientRect();
    if (y < r.top + r.height / 2) { index = i; break; }
  }
  dropTarget.value = { col: colKey, index };
}

function onPointerUp() {
  const d = drag.value;
  window.removeEventListener("pointermove", onPointerMove);
  window.removeEventListener("pointerup", onPointerUp);
  document.body.style.userSelect = "";

  // Mobile: open the card only on a real tap (barely any movement); a larger
  // movement was a lane swipe and must not open the card.
  if (isMobile.value) {
    if (d && downCard) {
      const dist = Math.hypot((d.x ?? d.startX) - d.startX, (d.y ?? d.startY) - d.startY);
      if (dist < 10) emit("card-click", downCard.id);
    }
    drag.value = null;
    dropTarget.value = null;
    downCard = null;
    return;
  }

  if (d && d.active && dropTarget.value) {
    applyMove(d.id, dropTarget.value.col, dropTarget.value.index);
  } else if (d && !d.active && downCard) {
    emit("card-click", downCard.id);
  }
  drag.value = null;
  dropTarget.value = null;
  downCard = null;
}

/* Karte im internen Array umsetzen (Spalte + Position) und Move melden. */
function applyMove(cardId, toCol, index) {
  const arr = localCards.value;
  const from = arr.findIndex((c) => c.id === cardId);
  if (from < 0) return;
  const card = arr[from];
  const fromCol = card.col;

  // Ziel-Reihenfolge: IDs der Zielspalte ohne die Karte selbst
  const targetIds = arr.filter((c) => c.col === toCol && c.id !== cardId).map((c) => c.id);
  const beforeId = targetIds[index] ?? null; // Karte, VOR die eingefügt wird

  const moved = { ...card, col: toCol };
  const rest = arr.filter((c) => c.id !== cardId);
  let insertAt;
  if (beforeId == null) {
    // ans Ende der Zielspalte: hinter die letzte Karte dieser Spalte
    const lastIdx = rest.map((c) => c.col).lastIndexOf(toCol);
    insertAt = lastIdx < 0 ? rest.length : lastIdx + 1;
  } else {
    insertAt = rest.findIndex((c) => c.id === beforeId);
  }
  rest.splice(insertAt, 0, moved);
  localCards.value = rest;

  emit("move", { cardId, fromCol, toCol, index });
}

function colCount(key) {
  return byCol.value[key]?.length ?? 0;
}
function isOverWip(col) {
  return typeof col.wip === "number" && colCount(col.key) > col.wip;
}

onBeforeUnmount(() => {
  window.removeEventListener("pointermove", onPointerMove);
  window.removeEventListener("pointerup", onPointerUp);
  document.body.style.userSelect = "";
});
</script>

<template>
  <div
    class="pp-kanban pp-kanban--dnd"
    :class="{ 'pp-kanban--mobile': isMobile }"
    @touchstart="isMobile && onLaneTouchStart($event)"
    @touchend="isMobile && onLaneTouchEnd($event)"
  >
    <!-- Mobile: lane switcher (‹ current phase · i/n › + dots) -->
    <div v-if="isMobile && columns.length" class="pp-kanban__mnav">
      <button type="button" class="pp-kanban__mnav-btn" :disabled="activeIdx === 0"
              aria-label="Vorherige Phase" @click="prevCol"><ChevronLeft /></button>
      <div class="pp-kanban__mnav-label">
        <span class="pp-kanban__mnav-name">{{ columns[activeIdx] && columns[activeIdx].label }}</span>
        <span class="pp-kanban__mnav-pos">{{ activeIdx + 1 }} / {{ columns.length }}</span>
      </div>
      <button type="button" class="pp-kanban__mnav-btn" :disabled="activeIdx === columns.length - 1"
              aria-label="Nächste Phase" @click="nextCol"><ChevronRight /></button>
    </div>
    <div v-if="isMobile && columns.length > 1" class="pp-kanban__dots">
      <button v-for="(c, ci) in columns" :key="c.key" type="button" class="pp-kanban__dot"
              :class="{ 'is-active': ci === activeIdx }" :aria-label="c.label" @click="activeIdx = ci"></button>
    </div>
    <div
      v-for="col in shownColumns"
      :key="col.key"
      class="pp-kanban__col"
      :data-kanban-col="col.key"
      :class="{
        'is-dropzone': drag && drag.active && dropTarget && dropTarget.col === col.key,
        'is-dim': highlightCol && col.key !== highlightCol,
        'is-hl':  highlightCol && col.key === highlightCol,
      }"
    >
      <div class="pp-kanban__head">
        <span class="pp-kanban__title">{{ col.label }}</span>
        <span
          class="pp-kanban__count"
          :class="{ 'pp-kanban__count--wip': isOverWip(col) }"
          :title="col.wip != null ? `WIP-Limit ${col.wip}` : null"
        >{{ colCount(col.key) }}<template v-if="col.wip != null"> / {{ col.wip }}</template></span>
      </div>

      <!-- Optionaler Kopf-Zusatz je Spalte (@3): rendert nur, wenn befüllt -->
      <div v-if="$slots['column-meta']" class="pp-kanban__col-meta">
        <slot name="column-meta" :column="col" />
      </div>

      <div class="pp-kanban__body">
        <template v-for="(card, i) in byCol[col.key]" :key="card.id">
          <!-- Einfüge-Markierung vor dieser Karte -->
          <div
            v-if="drag && drag.active && dropTarget && dropTarget.col === col.key && dropTarget.index === i"
            class="pp-kanban__drop"
          ></div>

          <div
            class="pp-kanban__card"
            :class="{ 'is-dragging': drag && drag.active && drag.id === card.id }"
            :style="card.stripe ? { borderLeft: '3px solid ' + card.stripe } : null"
            :data-kanban-card="card.id"
            @pointerdown="onPointerDown($event, card)"
            @dblclick="emit('card-dblclick', card.id)"
          >
            <!-- Kopfzeile (@4): Kennung + klickbarer Prio-Chip -->
            <div v-if="card.ref || card.prio" class="pp-kanban__card-top">
              <span v-if="card.ref" class="pp-kanban__card-ref">{{ card.ref }}</span>
              <button
                v-if="card.prio"
                type="button"
                class="pp-kanban__prio"
                :style="prioStyle(card.prio)"
                :title="'Klick ändert die Dringlichkeit'"
                @pointerdown.stop
                @click.stop="emit('prio-click', card.id)"
              ><span class="pp-kanban__prio-dot"></span>{{ card.prio.label }}</button>
            </div>

            <div class="pp-kanban__card-title">{{ card.title }}</div>
            <div v-if="card.subtitle" class="pp-kanban__card-sub">{{ card.subtitle }}</div>

            <div v-if="card.badges && card.badges.length" class="pp-kanban__badges">
              <span
                v-for="(b, bi) in card.badges"
                :key="bi"
                class="pp-kanban__badge"
                :style="badgeStyle(b)"
              >{{ badgeLabel(b) }}</span>
            </div>

            <div v-if="card.assignee || card.due || (card.meta && card.meta.length)" class="pp-kanban__card-meta">
              <span v-for="(m, mi) in card.meta" :key="'m' + mi" class="pp-kanban__meta-item">{{ m }}</span>
              <span v-if="card.due" class="pp-kanban__due">{{ card.due }}</span>
              <span v-if="card.assignee" class="pp-kanban__who">
                <span class="pp-kanban__avatar" :title="card.assignee">{{ initials(card.assignee) }}</span>
                <span v-if="!card.meta || !card.meta.length" class="pp-kanban__who-name">{{ card.assignee }}</span>
              </span>
            </div>
          </div>
        </template>

        <!-- Einfüge-Markierung am Spaltenende -->
        <div
          v-if="drag && drag.active && dropTarget && dropTarget.col === col.key && dropTarget.index >= colCount(col.key)"
          class="pp-kanban__drop"
        ></div>

        <div v-if="!colCount(col.key)" class="pp-kanban__empty">Keine Karten</div>
      </div>
    </div>

    <!-- Frei ziehender Geist-Klon (folgt dem Zeiger, fängt keine Events) -->
    <div
      v-if="drag && drag.active"
      class="pp-kanban__ghost"
      :style="{ left: drag.x + 12 + 'px', top: drag.y + 8 + 'px' }"
    >
      {{ localCards.find((c) => c.id === drag.id)?.title }}
    </div>
  </div>
</template>

<style scoped>
/* Basis (.pp-kanban*) kommt global aus components.css. Hier nur DnD/WIP/Badges. */
.pp-kanban--dnd { position: relative; min-height: 0; }

.pp-kanban__col.is-dropzone {
  border-color: rgb(var(--pp-brand-primary-rgb) / 0.45);
  background: rgb(var(--pp-brand-primary-rgb) / 0.05);
}
/* Lane-Fokus (@4): eine Spalte hervorheben, die übrigen dämpfen. */
.pp-kanban__col.is-dim { opacity: 0.45; }
.pp-kanban__col.is-hl { box-shadow: 0 0 0 2px var(--pp-brand-primary); }
.pp-kanban__body { min-height: 24px; }

/* Kopf-Zusatz (@3): nur vorhanden, wenn der #column-meta-Slot befüllt ist.
   Dezente Default-Typo; das eigentliche Element gestaltet der Verbraucher. */
.pp-kanban__col-meta {
  margin-top: 2px;
  font-size: var(--pp-fs-12);
  color: var(--pp-text-secondary);
}

.pp-kanban__count--wip {
  color: var(--pp-text-on-accent);
  background: var(--pp-state-danger);
  font-weight: var(--pp-weight-bold);
}

/* Karte: klar greifbar, im Zug gedämpft */
.pp-kanban__card { touch-action: none; user-select: none; }

/* ---- Mobile: single full-width lane + swipe switcher ---------------- */
.pp-kanban--mobile { flex-direction: column; overflow-x: hidden; }
.pp-kanban--mobile .pp-kanban__col { width: 100%; min-width: 0; max-width: 100%; flex: 1 1 auto; }
.pp-kanban__mnav { display: flex; align-items: center; gap: 8px; padding: 2px 0 8px; }
.pp-kanban__mnav-btn {
  flex: 0 0 auto; width: 40px; height: 40px; display: grid; place-items: center;
  border: 1px solid var(--pp-border-default); border-radius: var(--pp-radius-ui);
  background: var(--pp-bg-surface); color: var(--pp-text-secondary); cursor: pointer;
}
.pp-kanban__mnav-btn:disabled { opacity: 0.4; cursor: default; }
.pp-kanban__mnav-btn :deep(svg) { width: 18px; height: 18px; }
.pp-kanban__mnav-label { flex: 1; min-width: 0; display: flex; flex-direction: column; align-items: center; line-height: 1.2; }
.pp-kanban__mnav-name { font-weight: var(--pp-weight-semibold); font-size: 14px; color: var(--pp-text-primary);
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 100%; }
.pp-kanban__mnav-pos { font-size: 11px; color: var(--pp-text-tertiary); font-variant-numeric: tabular-nums; }
.pp-kanban__dots { display: flex; justify-content: center; gap: 6px; padding-bottom: 10px; }
.pp-kanban__dot { width: 7px; height: 7px; padding: 0; border: 0; border-radius: var(--pp-radius-full);
  background: var(--pp-bg-hover); cursor: pointer; transition: background var(--pp-duration-fast) var(--pp-ease-standard); }
.pp-kanban__dot.is-active { background: var(--pp-brand-primary); }
.pp-kanban__card.is-dragging { opacity: 0.4; }

.pp-kanban__badges { display: flex; flex-wrap: wrap; gap: 4px; margin-bottom: var(--pp-space-2); }
.pp-kanban__badge {
  font-size: 10px; font-weight: var(--pp-weight-semibold);
  padding: 1px 6px; border-radius: var(--pp-radius-full);
  border: 1px solid var(--pp-border-default);
  color: var(--pp-text-secondary);
  background: color-mix(in oklab, currentColor 10%, transparent);
}

.pp-kanban__who { display: inline-flex; align-items: center; gap: var(--pp-space-2); min-width: 0; }
.pp-kanban__avatar {
  display: inline-flex; align-items: center; justify-content: center; flex-shrink: 0;
  width: 20px; height: 20px; border-radius: var(--pp-radius-full);
  background: color-mix(in oklab, var(--pp-brand-primary) 16%, transparent);
  color: var(--pp-brand-primary); font-size: 9px; font-weight: var(--pp-weight-bold);
}
.pp-kanban__who-name {
  font-size: var(--pp-fs-12); color: var(--pp-text-secondary);
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.pp-kanban__due { font-size: 11px; color: var(--pp-text-tertiary); flex-shrink: 0; }

/* Karte @4: Kopfzeile / Prio-Chip / Unterzeile / Meta-Items */
.pp-kanban__card-top { display: flex; align-items: center; justify-content: space-between;
  gap: var(--pp-space-2); margin-bottom: 3px; }
.pp-kanban__card-ref { font-size: 10px; font-weight: var(--pp-weight-bold);
  color: var(--pp-brand-primary); font-variant-numeric: tabular-nums; }
.pp-kanban__prio { appearance: none; cursor: pointer; font-family: inherit;
  display: inline-flex; align-items: center; gap: 4px; padding: 1px 8px;
  border: 1px solid transparent; border-radius: var(--pp-radius-full);
  font-size: 10px; font-weight: var(--pp-weight-bold); }
.pp-kanban__prio:hover { border-color: currentColor; }
.pp-kanban__prio-dot { width: 6px; height: 6px; border-radius: var(--pp-radius-full); background: currentColor; }
.pp-kanban__card-sub { font-size: var(--pp-fs-12, 12px); color: var(--pp-text-tertiary);
  margin-top: 1px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.pp-kanban__meta-item { font-size: 10px; color: var(--pp-text-secondary); font-variant-numeric: tabular-nums; }

.pp-kanban__drop {
  height: 2px; margin: 3px 2px;
  background: var(--pp-brand-primary);
  border-radius: var(--pp-radius-full);
  box-shadow: 0 0 0 2px rgb(var(--pp-brand-primary-rgb) / 0.20);
}

.pp-kanban__empty {
  font-size: var(--pp-fs-12); color: var(--pp-text-tertiary);
  padding: var(--pp-space-2); text-align: center;
}

.pp-kanban__ghost {
  position: fixed; z-index: 1000; pointer-events: none;
  max-width: 220px; padding: var(--pp-space-2) var(--pp-space-3);
  background: var(--pp-bg-surface);
  border: 1px solid rgb(var(--pp-brand-primary-rgb) / 0.5);
  border-radius: var(--pp-radius-ui);
  box-shadow: var(--pp-shadow-lg);
  font-size: var(--pp-fs-13, 13px); color: var(--pp-text-primary);
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
  transform: rotate(1.5deg);
}
</style>
