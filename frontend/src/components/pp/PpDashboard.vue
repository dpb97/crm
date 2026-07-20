<!-- PP_REV: PpDashboard@2 -->
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

  STRIKT --pp-*-Tokens · Radius ≤ 3 px · Hellgrau-Klima hell+dunkel ·
  Skalierungsstufen ≥1700 / ≥2500 (wie die Shell) · Mobile 1-spaltig · A11y
  (Karten = section+h2, klickbare KPIs = button, Raster = role="list").
-->
<script setup>
import { computed } from "vue";

const props = defineProps({
  eyebrow:  { type: String, default: "" },
  title:    { type: String, default: "" },
  kpis:     { type: Array,  default: () => [] },
  cards:    { type: Array,  default: () => [] },
  maxWidth: { type: Number, default: 0 },
});
const emit = defineEmits(["kpi-click", "card-action"]);

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

      <!-- Karten-Raster -->
      <div v-if="cards.length" class="ppd__grid" role="list">
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
  </div>
</template>

<style scoped>
.ppd { height: 100%; overflow: auto; background: var(--pp-bg-base); }
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
  gap: var(--pp-space-3); min-width: 0; padding: var(--pp-space-4); }
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
</style>
