<!-- PP_REV: PpDashboard@5 -->
<!-- @3 (20.07.2026): Karten-Chrome (Fläche/Rand/Radius/Schatten) wandert additiv
     in .ppd-card selbst — der Baustein ist damit SELBST-TRAGEND und rendert seine
     Karten auch dort als echte Karten, wo der Host die globale .pp-card-Utility
     NICHT bereitstellt (CRM-SPA pilanda_sales, Desk-Bundle). Bisher lieferte die
     Fläche allein die showcase-lokale .pp-card (ThemePreview) → Kopien in echten
     Apps rendern nackte Inhalte auf grauem Grund (Marco-Sichttest 20.07.). Werte
     = exakt die .pp-card-Tokens; wo .pp-card existiert, bleibt es visuell gleich. -->
<!-- @5 (26.07.2026): personalisierbares Karten-Registry-FRAMEWORK, additiver
     Nachzug des Klickdummy-A4 (DASH_DEFS/dashGrid/dashMax/dashCatalog/dashSizePop/
     dashReorder). Setzt der Verbraucher die Prop `registry`, schaltet der Baustein
     in den Framework-Modus: 4 Größen (S=1×1 · M=2×1 · L=2×2 · XL=4×2), Karten-Katalog
     (Mehrfach-Picker im PpModal), HTML5-DnD-Umsortierung, Größen-Menü je Karte,
     Doppelklick-Maximieren (Vollflächen-Overlay + Detail-Slot + Abstiegs-Emits) und
     einfacher Picker-Modus (`simple`: nur an/aus). Ohne `registry` bleibt ALLES beim
     @4-Verhalten (cards/#card-<id>-Slots) — voll rückwärtskompatibel. Layout-
     Persistenz via `modelValue` (v-model) beim Verbraucher; serverseitige Pro-User-
     Persistenz ist der Folge-AP (Demo = reaktiver State beim Host). -->
<!--
  PpDashboard.vue — komponierbares Dashboard-LAYOUT (SSOT-Baustein, N9/§6.2).

  „Ein Dashboard soll auch wirklich wie ein Dashboard aussehen" (Marco 14.07.):
  der Baustein liefert die Bühne — Kopf → KPI-Zeile → responsives Karten-Raster —
  und bleibt inhaltlich neutral. Inhalte kommen props-getrieben (KPI-Reihe) bzw.
  über BENANNTE Karten-Slots (`#card-<id>`), sodass jede App (Home, Modul-
  Dashboards) frei komponiert und die Feinheiten dort adaptiert.

  Props:
    · eyebrow / title      — Seitenkopf (PpPageHead-Idiom, hier eingebettet)
    · kpis:  [{ key, label, value, hint, delta, dir, spark[], tone, clickable }]
             tone ∈ neutral|info|success|warning|danger ; dir ∈ up|down|""
    · cards: [{ id, title, meta, span, action:{label} }]
             span = Rasterbreite in 12-Spalten (Default 6 = halb); Karteninhalt
             rendert der Slot `#card-<id>` (Fallback: leerer Zustand).
    · maxWidth (px, Default 0 = volle Canvas-Breite; ERP-Standard seit
              19.07. — Marco: „ERP, kein zentrierter Blog"). Wert > 0 begrenzt
              und zentriert die Bühne (opt-in, z. B. Lese-Layouts).
  Events:
    · kpi-click(kpi)    — Klick auf eine als `clickable` markierte KPI-Kachel
    · card-action(card) — Klick auf die Kopf-Aktion einer Karte
  Slots:
    · #actions          — Aktionen rechts im Seitenkopf
    · #kpis-extra       — hinter der KPI-Reihe (optional)
    · #card-<id>        — Inhalt der jeweiligen Karte
    · #head-<id>        — optionaler Ersatz für den Kartenkopf

  Framework-Modus (@5, opt-in über `registry`):
    · registry: { [id]: { title, size:'s'|'m'|'l'|'xl', fix?, noMax?, abst?:[{t,go,s?}] } }
               Karten-Definitionen; gesetzt = Framework-Modus AN.
    · modelValue (v-model): [{ id, size }] — aktives Layout (sichtbar/Reihenfolge/
               Größe). Ohne v-model hält der Baustein einen internen Stand.
    · defaultLayout: [{ id, size }] — Basis für „Karten zurücksetzen".
    · simple: nur an/aus (kein DnD, keine Größe, feste Reihenfolge).
    · catalogOpen (v-model:catalogOpen): öffnet das Karten-Katalog-Modal.
    Slots: #card-<id> (Karteninhalt) · #detail-<id> (Maximier-Ansicht, Fallback
    #card-<id>). Events: update:modelValue · update:catalogOpen · descend(go).

  STRIKT --pp-*-Tokens · Radius ≤ 3 px · Hellgrau-Klima hell+dunkel ·
  Skalierungsstufen ≥1700 / ≥2500 (wie die Shell) · Mobile 1-spaltig · A11y
  (Karten = section+h2, klickbare KPIs = button, Raster = role="list").
-->
<script setup>
import { computed, ref, watch, onBeforeUnmount } from "vue";
import PpModal from "./PpModal.vue";

const props = defineProps({
  eyebrow:  { type: String, default: "" },
  title:    { type: String, default: "" },
  kpis:     { type: Array,  default: () => [] },
  cards:    { type: Array,  default: () => [] },
  maxWidth: { type: Number, default: 0 },
  // Framework-Modus (@5) — opt-in über registry.
  registry:      { type: Object,  default: null },
  modelValue:    { type: Array,   default: null },  // v-model: [{ id, size }]
  defaultLayout: { type: Array,   default: null },
  simple:        { type: Boolean, default: false },
  catalogOpen:   { type: Boolean, default: false }, // v-model:catalogOpen
});
const emit = defineEmits([
  "kpi-click", "card-action",
  "update:modelValue", "update:catalogOpen", "descend",
]);

/* =============== Framework-Modus (@5) ================================= */
const fw = computed(() => !!props.registry);
const SIZES = [["s", "Klein", "1×1"], ["m", "Mittel", "2×1"], ["l", "Groß", "2×2"], ["xl", "Voll", "4×2"]];

// Registry-Reihenfolge → Basis-Layout (Fallback ohne modelValue/defaultLayout).
const baseLayout = computed(() =>
  Object.keys(props.registry || {}).map((id) => ({ id, size: props.registry[id].size || "m" })));

// Interner Stand, falls der Host KEIN v-model bindet (Demo-Fallback).
const internalLayout = ref(null);
const layout = computed(() => props.modelValue ?? internalLayout.value ?? baseLayout.value);
function setLayout(next) {
  if (props.modelValue != null) emit("update:modelValue", next);
  else internalLayout.value = next;
}
const resetTarget = computed(() =>
  (props.defaultLayout ?? baseLayout.value).map((x) => ({ id: x.id, size: x.size || "m" })));

// Sichtbare Zellen = Layout-Einträge, deren id die Registry kennt.
const cells = computed(() =>
  layout.value
    .filter((ent) => props.registry && props.registry[ent.id])
    .map((ent) => {
      const def = props.registry[ent.id];
      const size = props.simple ? (def.size || "m") : (ent.size || def.size || "m");
      return { id: ent.id, size, def };
    }));

function regOf(id) { return (props.registry && props.registry[id]) || {}; }

/* ---- DnD-Umsortierung: gezogene Karte VOR die Zielkarte ---- */
const dragId = ref(null);
const overId = ref(null);
function onDragStart(id, def) { if (props.simple || def.fix) return; dragId.value = id; }
function onDragOver(id) { if (dragId.value) overId.value = id; }
function onDrop(targetId) {
  const from = dragId.value;
  dragId.value = null; overId.value = null;
  if (!from || from === targetId) return;
  const next = layout.value.map((x) => ({ ...x }));
  const fi = next.findIndex((x) => x.id === from);
  if (fi < 0) return;
  const moved = next.splice(fi, 1)[0];
  let ti = next.findIndex((x) => x.id === targetId);
  if (ti < 0) ti = next.length;
  next.splice(ti, 0, moved);
  setLayout(next);
}
function onDragEnd() { dragId.value = null; overId.value = null; }

/* ---- Größen-Popover je Karte ---- */
const sizePop = ref(null); // id der Karte mit offenem Popover
function toggleSizePop(id) { sizePop.value = sizePop.value === id ? null : id; }
function setSize(id, size) {
  const next = layout.value.map((x) => (x.id === id ? { ...x, size } : { ...x }));
  setLayout(next);
  sizePop.value = null;
}

/* ---- Doppelklick → Karte maximieren (Vollflächen-Overlay) ---- */
const maxId = ref(null);
// Maximieren auch im simple-Modus erlaubt (nur DnD/Größe entfallen dort — wie
// Klickdummy wireDash: dblclick bleibt gebunden). Fixe/noMax-Karten nie.
function openMax(id, def) { if (def.noMax || def.fix) return; maxId.value = id; }
function closeMax() { maxId.value = null; }
function onMaxScrim(e) { if (e.target === e.currentTarget) closeMax(); }
function onDescend(go) { closeMax(); emit("descend", go); }
// ESC schließt das Overlay und konsumiert das Event (PpModal@2-Muster).
function onMaxKey(e) { if (e.key === "Escape" && maxId.value) { e.stopPropagation(); closeMax(); } }
watch(maxId, (v) => {
  if (v) document.addEventListener("keydown", onMaxKey);
  else document.removeEventListener("keydown", onMaxKey);
});
onBeforeUnmount(() => document.removeEventListener("keydown", onMaxKey));

/* ---- Karten-Katalog (Mehrfach-Picker im PpModal) ---- */
const catalogProxy = computed({
  get: () => props.catalogOpen,
  set: (v) => emit("update:catalogOpen", v),
});
const catalogItems = computed(() => {
  const active = new Set(layout.value.map((x) => x.id));
  return Object.keys(props.registry || {}).map((id) => ({
    id, title: props.registry[id].title || id,
    checked: active.has(id),
    disabled: !!(props.registry[id].fix && active.has(id)), // fix + aktiv = nicht abwählbar
  }));
});
function toggleCard(id, on) {
  const cur = layout.value.map((x) => ({ ...x }));
  const idx = cur.findIndex((x) => x.id === id);
  if (on && idx < 0) cur.push({ id, size: regOf(id).size || "m" });
  else if (!on && idx >= 0) cur.splice(idx, 1);
  setLayout(cur);
}
function resetCards() { setLayout(resetTarget.value.map((x) => ({ ...x }))); }

const maxDef = computed(() => (maxId.value ? regOf(maxId.value) : {}));

const TONE = {
  neutral: "var(--pp-brand-primary)",
  info:    "var(--pp-state-info)",
  success: "var(--pp-state-success)",
  warning: "var(--pp-state-warning)",
  danger:  "var(--pp-state-danger)",
};
const toneVar = (t) => TONE[t] || TONE.neutral;

// Sparkline (88×30-ViewBox) — identisch zur PpStatTile-Normalisierung.
function sparkPts(v) {
  if (!v || v.length < 2) return [];
  const min = Math.min(...v), max = Math.max(...v), span = max - min || 1;
  return v.map((y, i) => [
    (i / (v.length - 1)) * 86 + 1,
    28 - ((y - min) / span) * 24,
  ]);
}
const sparks = computed(() => {
  const out = {};
  for (const k of props.kpis) {
    const pts = sparkPts(k.spark);
    out[k.key ?? k.label] = {
      line: pts.map(([x, y]) => `${x},${y}`).join(" "),
      area: pts.length ? `1,29 ${pts.map(([x, y]) => `${x},${y}`).join(" ")} 87,29` : "",
      has: pts.length > 0,
    };
  }
  return out;
});
const sparkOf = (k) => sparks.value[k.key ?? k.label] || { has: false };

function onKpi(k) {
  if (k.clickable) emit("kpi-click", k);
}
</script>

<template>
  <div class="ppd">
    <div class="ppd__inner" :style="maxWidth ? { maxWidth: maxWidth + 'px' } : null">
      <!-- Kopf (PpPageHead-Idiom, eingebettet für die Bühne) -->
      <header v-if="eyebrow || title || $slots.actions" class="ppd__head">
        <div class="ppd__head-meta">
          <span v-if="eyebrow" class="ppd__eyebrow">{{ eyebrow }}</span>
          <h1 v-if="title" class="ppd__title">{{ title }}</h1>
        </div>
        <div v-if="$slots.actions" class="ppd__head-actions"><slot name="actions" /></div>
      </header>

      <!-- KPI-Zeile -->
      <div v-if="kpis.length" class="ppd__kpis">
        <component
          :is="k.clickable ? 'button' : 'div'"
          v-for="k in kpis" :key="k.key ?? k.label"
          class="ppd-kpi" :class="{ 'ppd-kpi--btn': k.clickable }"
          :style="{ '--k': toneVar(k.tone) }"
          :type="k.clickable ? 'button' : undefined"
          @click="onKpi(k)">
          <span class="ppd-kpi__bar" aria-hidden="true"></span>
          <span class="ppd-kpi__body">
            <span class="ppd-kpi__label">{{ k.label }}</span>
            <span class="ppd-kpi__row">
              <span class="ppd-kpi__value">{{ k.value }}</span>
              <svg v-if="sparkOf(k).has" class="pp-spark ppd-kpi__spark"
                   viewBox="0 0 88 30" preserveAspectRatio="none" aria-hidden="true">
                <polygon class="pp-spark__area" :points="sparkOf(k).area" />
                <polyline class="pp-spark__line" :points="sparkOf(k).line" />
              </svg>
            </span>
            <span v-if="k.delta || k.hint" class="ppd-kpi__foot">
              <span v-if="k.delta" class="ppd-kpi__delta"
                    :class="k.dir === 'up' ? 'is-up' : k.dir === 'down' ? 'is-down' : ''">
                <span v-if="k.dir === 'up'">▲</span><span v-else-if="k.dir === 'down'">▼</span>{{ k.delta }}
              </span>
              <span v-if="k.hint" class="ppd-kpi__hint">{{ k.hint }}</span>
            </span>
          </span>
        </component>
      </div>
      <slot name="kpis-extra" />

      <!-- Framework-Raster (@5): Registry + Layout treiben Karten/Größe/Reihenfolge -->
      <div v-if="fw" class="ppd-fw" :class="{ 'ppd-fw--simple': simple }" role="list">
        <section
          v-for="c in cells" :key="c.id"
          class="ppd-cell" :class="['ppd-cell--' + c.size, { 'ppd-cell--drag': dragId === c.id, 'ppd-cell--over': overId === c.id }]"
          :data-card="c.id" :data-size="c.size" role="listitem" tabindex="-1"
          :draggable="!simple && !c.def.fix"
          @dblclick="openMax(c.id, c.def)"
          @dragstart="onDragStart(c.id, c.def)"
          @dragover.prevent="onDragOver(c.id)"
          @drop.prevent="onDrop(c.id)"
          @dragend="onDragEnd">
          <div v-if="!simple && !c.def.fix" class="ppd-cell__tools">
            <button type="button" class="ppd-cell__grip" title="Karte verschieben (ziehen)"
                    aria-label="Karte verschieben">⣿</button>
            <button type="button" class="ppd-cell__size" :aria-expanded="sizePop === c.id"
                    title="Kartengröße ändern" aria-label="Kartengröße ändern"
                    @click.stop="toggleSizePop(c.id)">⤢</button>
            <div v-if="sizePop === c.id" class="ppd-sizepop" @click.stop>
              <button v-for="s in SIZES" :key="s[0]" type="button" :data-size="s[0]"
                      class="ppd-sizepop__opt" :class="{ 'is-on': c.size === s[0] }"
                      @click="setSize(c.id, s[0])">{{ s[1] }}<span class="ppd-sizepop__k">{{ s[2] }}</span></button>
            </div>
          </div>
          <header v-if="c.def.title" class="ppd-cell__head">
            <h2 class="ppd-cell__title">{{ c.def.title }}</h2>
          </header>
          <div class="ppd-cell__body">
            <slot :name="'card-' + c.id" :card="c.def">
              <p class="ppd-card__empty">Kein Inhalt.</p>
            </slot>
          </div>
        </section>
      </div>

      <!-- Karten-Raster (Legacy @4, wenn KEINE registry) -->
      <div v-if="!fw && cards.length" class="ppd__grid" role="list">
        <section v-for="c in cards" :key="c.id" class="pp-card ppd-card" role="listitem"
                 :style="{ '--span': c.span || 6 }">
          <slot :name="'head-' + c.id" :card="c">
            <header v-if="c.title || c.meta || c.action" class="ppd-card__head">
              <h2 class="ppd-card__title">{{ c.title }}</h2>
              <span v-if="c.meta" class="ppd-card__meta">{{ c.meta }}</span>
              <button v-if="c.action" type="button" class="ppd-card__action"
                      @click="emit('card-action', c)">{{ c.action.label }}</button>
            </header>
          </slot>
          <div class="ppd-card__body">
            <slot :name="'card-' + c.id" :card="c">
              <p class="ppd-card__empty">Kein Inhalt.</p>
            </slot>
          </div>
        </section>
      </div>
    </div>

    <!-- Maximieren-Overlay (@5): Vollflächen-Ansicht einer Karte (X + ESC) -->
    <div v-if="fw && maxId" class="ppd-max" role="dialog" aria-modal="true"
         :aria-label="maxDef.title" @click="onMaxScrim">
      <div class="ppd-max__win">
        <header class="ppd-max__head">
          <span class="ppd-max__title">{{ maxDef.title }}</span>
          <button type="button" class="ppd-max__x" aria-label="Schließen (ESC)"
                  title="Schließen (ESC)" @click="closeMax">×</button>
        </header>
        <div class="ppd-max__body">
          <slot :name="'detail-' + maxId" :card="maxDef">
            <slot :name="'card-' + maxId" :card="maxDef" />
          </slot>
        </div>
        <footer v-if="maxDef.abst && maxDef.abst.length" class="ppd-max__foot">
          <span class="ppd-max__foot-lbl">Weiter im Detail</span>
          <div class="ppd-max__jumps">
            <button v-for="a in maxDef.abst" :key="a.go" type="button" class="ppd-max__jump"
                    @click="onDescend(a.go)">
              <span class="ppd-max__jump-t">{{ a.t }} →</span>
              <span v-if="a.s" class="ppd-max__jump-s">{{ a.s }}</span>
            </button>
          </div>
        </footer>
      </div>
    </div>

    <!-- Karten-Katalog (@5): Mehrfach-Picker im zentralen Modal -->
    <PpModal v-if="fw" v-model:open="catalogProxy" title="Karten anpassen" :width="440">
      <div class="ppd-catalog">
        <p class="ppd-catalog__head">Karten dieses Dashboards ein-/ausblenden</p>
        <label v-for="it in catalogItems" :key="it.id" class="ppd-catalog__item"
               :class="{ 'is-disabled': it.disabled }">
          <input type="checkbox" class="ppd-catalog__cb" :checked="it.checked" :disabled="it.disabled"
                 @change="toggleCard(it.id, $event.target.checked)" />
          <span>{{ it.title }}</span>
        </label>
        <p class="ppd-catalog__note">Ausblenden entfernt die Karte nur aus deiner Ansicht —
          „Karten zurücksetzen" stellt den Standard wieder her.</p>
      </div>
      <template #footer>
        <button type="button" class="ppd-catalog__reset" @click="resetCards">Karten zurücksetzen</button>
        <button type="button" class="ppd-catalog__done" @click="catalogProxy = false">Fertig</button>
      </template>
    </PpModal>
  </div>
</template>

<style scoped>
.ppd { position: relative; height: 100%; overflow: auto; background: var(--pp-bg-base); }
.ppd__inner { margin: 0 auto; padding: var(--pp-space-6) var(--pp-space-6) var(--pp-space-10);
  display: flex; flex-direction: column; gap: var(--pp-space-5); }

/* Kopf */
.ppd__head { display: flex; align-items: flex-end; justify-content: space-between;
  gap: var(--pp-space-4); flex-wrap: wrap; }
.ppd__eyebrow { display: block; font-size: var(--pp-fs-12); font-weight: var(--pp-weight-bold);
  letter-spacing: 0.1em; text-transform: uppercase; color: var(--pp-brand-primary); }
.ppd__title { margin: 2px 0 0; font-family: var(--pp-font-heading); font-size: var(--pp-fs-32);
  font-weight: var(--pp-weight-semibold); letter-spacing: -0.02em; color: var(--pp-text-primary); }
.ppd__head-actions { display: inline-flex; align-items: center; gap: var(--pp-space-2); flex-wrap: wrap; }

/* KPI-Zeile — auto-fit, gleiche Kachel-Sprache wie das Portfolio-Dashboard */
.ppd__kpis { display: grid; gap: var(--pp-space-3);
  grid-template-columns: repeat(auto-fit, minmax(clamp(150px, 20%, 220px), 1fr)); }
.ppd-kpi { position: relative; display: flex; gap: var(--pp-space-3); overflow: hidden;
  text-align: left; background: var(--pp-bg-surface); border: 1px solid var(--pp-border-subtle);
  border-radius: var(--pp-radius-ui); box-shadow: var(--pp-shadow-xs);
  padding: var(--pp-space-3) var(--pp-space-3) var(--pp-space-3) 0; }
.ppd-kpi--btn { appearance: none; cursor: pointer; font: inherit; color: inherit;
  transition: border-color var(--pp-duration-fast) var(--pp-ease-standard); }
.ppd-kpi--btn:hover { border-color: var(--k); }
.ppd-kpi--btn:focus-visible { outline: 2px solid var(--pp-brand-primary); outline-offset: 2px; }
.ppd-kpi__bar { flex: 0 0 4px; width: 4px; background: var(--k); align-self: stretch; }
.ppd-kpi__body { display: flex; flex-direction: column; gap: 2px; min-width: 0; flex: 1; }
.ppd-kpi__label { font-size: var(--pp-fs-12); color: var(--pp-text-tertiary);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.ppd-kpi__row { display: flex; align-items: flex-end; justify-content: space-between; gap: var(--pp-space-2); }
.ppd-kpi__value { font-size: var(--pp-fs-32); font-weight: var(--pp-weight-semibold); line-height: 1.05;
  letter-spacing: -0.02em; color: var(--pp-text-primary); font-variant-numeric: tabular-nums; }
.ppd-kpi__spark { width: 72px; height: 26px; flex-shrink: 0; }
.ppd-kpi__foot { display: inline-flex; align-items: center; gap: var(--pp-space-2);
  font-size: var(--pp-fs-12); color: var(--pp-text-tertiary); font-variant-numeric: tabular-nums; }
.ppd-kpi__delta { display: inline-flex; align-items: center; gap: 3px; }
.ppd-kpi__delta.is-up { color: var(--pp-state-success); }
.ppd-kpi__delta.is-down { color: var(--pp-state-danger); }

/* Karten-Raster (12 Spalten, span-gesteuert) */
.ppd__grid { display: grid; grid-template-columns: repeat(12, minmax(0, 1fr));
  gap: var(--pp-space-4); align-items: start; }
.ppd-card { grid-column: span var(--span, 6); display: flex; flex-direction: column;
  gap: var(--pp-space-3); min-width: 0; padding: var(--pp-space-4);
  /* @3: selbst-tragendes Karten-Chrome (identisch zur .pp-card-Utility) */
  background: var(--pp-bg-surface); border: 1px solid var(--pp-border-subtle);
  border-radius: var(--pp-radius-ui); box-shadow: var(--pp-shadow-xs); }
.ppd-card__head { display: flex; align-items: baseline; gap: var(--pp-space-3); }
.ppd-card__title { flex: 1; min-width: 0; margin: 0; font-size: var(--pp-fs-16);
  font-weight: var(--pp-weight-semibold); color: var(--pp-text-primary);
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.ppd-card__meta { font-size: var(--pp-fs-12); color: var(--pp-text-tertiary);
  font-variant-numeric: tabular-nums; white-space: nowrap; }
.ppd-card__action { appearance: none; border: 0; background: none; cursor: pointer;
  font: inherit; font-size: var(--pp-fs-12); color: var(--pp-text-link);
  padding: 0; white-space: nowrap; }
.ppd-card__action:hover { text-decoration: underline; }
.ppd-card__body { display: flex; flex-direction: column; gap: var(--pp-space-2); min-width: 0; }
.ppd-card__empty { margin: 0; font-size: var(--pp-fs-13, 13px); color: var(--pp-text-secondary); }

/* Skalierungsstufen wie die Shell */
@media (min-width: 1700px) {
  .ppd__inner { gap: var(--pp-space-6); }
  .ppd__grid { gap: var(--pp-space-5); }
  .ppd-kpi__value { font-size: var(--pp-fs-36, 34px); }
}
@media (min-width: 2500px) {
  .ppd__inner { padding: var(--pp-space-8) var(--pp-space-8) var(--pp-space-10); }
}

/* Kompaktstufe ≤1500px (Klickdummy-Vorbild): engere Paddings, dichtere KPI-Kacheln. */
@media (max-width: 1500px) {
  .ppd__inner { padding: var(--pp-space-4) var(--pp-space-5) var(--pp-space-8); gap: var(--pp-space-4); }
  .ppd__kpis { grid-template-columns: repeat(auto-fit, minmax(146px, 1fr)); gap: var(--pp-space-2); }
  .ppd-kpi__value { font-size: var(--pp-fs-28, 26px); }
}

/* Responsive: Tablet → 6er-Halbraster, Mobile → 1-spaltig */
@media (max-width: 1080px) {
  .ppd__grid { grid-template-columns: repeat(6, minmax(0, 1fr)); }
  .ppd-card { grid-column: span 6; }
}
@media (max-width: 720px) {
  .ppd__inner { padding: var(--pp-space-4) var(--pp-space-4) var(--pp-space-8); }
  .ppd__kpis { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 480px) {
  .ppd__kpis { grid-template-columns: 1fr; }
}

/* ================= Framework-Modus (@5) ============================== */
/* 4-Spalten-Raster; Größen S=1×1 · M=2×1 · L=2×2 · XL=4×2 (Klickdummy-Parität). */
.ppd-fw { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr));
  grid-auto-rows: minmax(210px, auto); gap: var(--pp-space-4); align-items: stretch; }
.ppd-cell { position: relative; display: flex; flex-direction: column; gap: var(--pp-space-3);
  min-width: 0; padding: var(--pp-space-4); overflow: hidden;
  background: var(--pp-bg-surface); border: 1px solid var(--pp-border-subtle);
  border-radius: var(--pp-radius-ui); box-shadow: var(--pp-shadow-xs); }
.ppd-cell--s  { grid-column: span 1; grid-row: span 1; }
.ppd-cell--m  { grid-column: span 2; grid-row: span 1; }
.ppd-cell--l  { grid-column: span 2; grid-row: span 2; }
.ppd-cell--xl { grid-column: span 4; grid-row: span 2; }
.ppd-cell--drag { opacity: 0.55; }
.ppd-cell--over { box-shadow: inset 3px 0 0 var(--pp-brand-primary), var(--pp-shadow-xs); }

.ppd-cell__tools { position: absolute; top: 6px; right: 6px; z-index: 3;
  display: inline-flex; gap: 2px; opacity: 0; transition: opacity var(--pp-duration-fast) var(--pp-ease-standard); }
.ppd-cell:hover .ppd-cell__tools, .ppd-cell:focus-within .ppd-cell__tools { opacity: 1; }
.ppd-cell__grip, .ppd-cell__size { appearance: none; cursor: pointer; display: inline-grid; place-items: center;
  width: 24px; height: 24px; padding: 0; font: inherit; line-height: 1;
  border: 1px solid var(--pp-border-subtle); border-radius: var(--pp-radius-ui);
  background: var(--pp-bg-surface); color: var(--pp-text-tertiary); }
.ppd-cell__grip { cursor: grab; }
.ppd-cell__size:hover, .ppd-cell__grip:hover { color: var(--pp-brand-primary); border-color: var(--pp-brand-primary); }

.ppd-sizepop { position: absolute; top: 30px; right: 0; z-index: 5; min-width: 128px;
  display: flex; flex-direction: column; gap: 1px; padding: var(--pp-space-1);
  background: var(--pp-bg-surface); border: 1px solid var(--pp-border-default);
  border-radius: var(--pp-radius-ui); box-shadow: var(--pp-shadow-lg); }
.ppd-sizepop__opt { appearance: none; cursor: pointer; font: inherit; font-size: var(--pp-fs-13, 13px);
  display: flex; align-items: center; justify-content: space-between; gap: var(--pp-space-2);
  padding: 5px var(--pp-space-2); border: 0; border-radius: var(--pp-radius-ui);
  background: transparent; color: var(--pp-text-primary); text-align: left; }
.ppd-sizepop__opt:hover { background: var(--pp-bg-hover); }
.ppd-sizepop__opt.is-on { color: var(--pp-brand-primary); font-weight: var(--pp-weight-semibold); }
.ppd-sizepop__k { font-size: var(--pp-fs-11, 11px); color: var(--pp-text-tertiary); font-variant-numeric: tabular-nums; }

.ppd-cell__head { display: flex; align-items: baseline; gap: var(--pp-space-2); padding-right: 56px; }
.ppd-cell__title { margin: 0; font-size: var(--pp-fs-16); font-weight: var(--pp-weight-semibold);
  color: var(--pp-text-primary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.ppd-cell__body { flex: 1 1 auto; min-height: 0; display: flex; flex-direction: column;
  gap: var(--pp-space-2); min-width: 0; }

/* Maximieren-Overlay */
.ppd-max { position: absolute; inset: 0; z-index: var(--pp-z-modal, 1000);
  display: flex; padding: var(--pp-space-5);
  background: rgb(var(--pp-shadow-deep-rgb) / .42); -webkit-backdrop-filter: blur(2px); backdrop-filter: blur(2px); }
.ppd-max__win { display: flex; flex-direction: column; flex: 1 1 auto; min-height: 0;
  background: var(--pp-bg-surface); border: 1px solid var(--pp-border-default);
  border-radius: var(--pp-radius-ui); box-shadow: var(--pp-shadow-xl); overflow: hidden; }
.ppd-max__head { flex: 0 0 auto; display: flex; align-items: center; justify-content: space-between;
  gap: var(--pp-space-2); padding: var(--pp-space-3) var(--pp-space-4);
  border-bottom: 1px solid var(--pp-border-subtle); background: var(--pp-accent-soft);
  color: var(--pp-brand-primary-d, var(--pp-brand-primary)); }
.ppd-max__title { font-size: var(--pp-fs-15, 15px); font-weight: var(--pp-weight-semibold); }
.ppd-max__x { appearance: none; cursor: pointer; width: 28px; height: 28px; padding: 0; font-size: 20px; line-height: 1;
  border: 1px solid transparent; border-radius: var(--pp-radius-ui); background: transparent;
  color: var(--pp-brand-primary-d, var(--pp-brand-primary)); }
.ppd-max__x:hover { background: var(--pp-bg-hover); border-color: var(--pp-border-default); }
.ppd-max__body { flex: 1 1 auto; min-height: 0; overflow: auto; padding: var(--pp-space-4); }
.ppd-max__foot { flex: 0 0 auto; display: flex; flex-direction: column; gap: var(--pp-space-2);
  padding: var(--pp-space-3) var(--pp-space-4); border-top: 1px solid var(--pp-border-subtle);
  background: var(--pp-bg-sunken); }
.ppd-max__foot-lbl { font-size: var(--pp-fs-11, 11px); font-weight: var(--pp-weight-bold);
  letter-spacing: var(--pp-tracking-caps); text-transform: uppercase; color: var(--pp-text-tertiary); }
.ppd-max__jumps { display: flex; flex-wrap: wrap; gap: var(--pp-space-2); }
.ppd-max__jump { appearance: none; cursor: pointer; font: inherit; text-align: left;
  display: flex; flex-direction: column; gap: 1px; padding: var(--pp-space-2) var(--pp-space-3);
  border: 1px solid var(--pp-border-default); border-radius: var(--pp-radius-ui);
  background: var(--pp-bg-surface); color: var(--pp-text-primary); }
.ppd-max__jump:hover { border-color: var(--pp-brand-primary); }
.ppd-max__jump-t { font-size: var(--pp-fs-13, 13px); font-weight: var(--pp-weight-semibold); color: var(--pp-brand-primary); }
.ppd-max__jump-s { font-size: var(--pp-fs-12); color: var(--pp-text-tertiary); }

/* Katalog-Modal-Inhalt */
.ppd-catalog { display: flex; flex-direction: column; gap: 1px; }
.ppd-catalog__head { margin: 0 0 var(--pp-space-1); font-size: 10px; font-weight: var(--pp-weight-bold);
  letter-spacing: var(--pp-tracking-wide); text-transform: uppercase; color: var(--pp-text-tertiary); }
.ppd-catalog__item { display: flex; align-items: center; gap: var(--pp-space-2); cursor: pointer;
  padding: 5px var(--pp-space-1); border-radius: var(--pp-radius-ui);
  font-size: var(--pp-fs-13, 13px); color: var(--pp-text-primary); }
.ppd-catalog__item:hover { background: var(--pp-bg-hover); }
.ppd-catalog__item.is-disabled { cursor: default; color: var(--pp-text-tertiary); }
.ppd-catalog__cb { width: 15px; height: 15px; accent-color: var(--pp-brand-primary); cursor: pointer; }
.ppd-catalog__note { margin: var(--pp-space-2) 0 0; font-size: var(--pp-fs-12); color: var(--pp-text-tertiary); }
.ppd-catalog__reset { appearance: none; cursor: pointer; font: inherit; font-size: var(--pp-fs-13, 13px);
  margin-right: auto; padding: var(--pp-space-2) var(--pp-space-3);
  border: 1px solid var(--pp-border-default); border-radius: var(--pp-radius-ui);
  background: var(--pp-bg-surface); color: var(--pp-text-secondary); }
.ppd-catalog__reset:hover { border-color: var(--pp-brand-primary); color: var(--pp-brand-primary); }
.ppd-catalog__done { appearance: none; cursor: pointer; font: inherit; font-size: var(--pp-fs-13, 13px);
  font-weight: var(--pp-weight-semibold); padding: var(--pp-space-2) var(--pp-space-4);
  border: 1px solid var(--pp-brand-primary); border-radius: var(--pp-radius-ui);
  background: var(--pp-brand-primary); color: var(--pp-text-on-accent); }
.ppd-max { animation: ppd-max-in var(--pp-duration-base) var(--pp-ease-decelerate); }
@keyframes ppd-max-in { from { opacity: 0; } to { opacity: 1; } }

@media (max-width: 1080px) {
  .ppd-fw { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .ppd-cell--xl { grid-column: span 2; }
}
@media (max-width: 620px) {
  .ppd-fw { grid-template-columns: 1fr; }
  .ppd-cell--m, .ppd-cell--l, .ppd-cell--xl { grid-column: span 1; grid-row: span 1; }
}
</style>
