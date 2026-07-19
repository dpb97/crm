<!-- PP_REV: PpStatTile@1 -->
<!--
  PpStatTile.vue — KPI-Kachel MIT Trend-Delta + Sparkline (SSOT-Baustein).

  Extrahiert 05.07.2026 aus dem theme-preview-Katalog „Daten-Visualisierung"
  (ThemePreviewDataViz, vorher Inline-Markup) — Entscheid Marco: fertige
  Preview-Elemente als Bausteine verwenden. Abgrenzung: `PpKpi` = einfache
  Kachel (Label/Wert/Hint, tonal); DIESER Baustein = Dashboard-Variante
  mit Verlauf (`spark`) + Richtungs-Delta.

  Struktur-CSS global in components.css (.pp-kpi__*/.pp-spark__* — dieselbe
  Familie). spark/delta optional; ohne beides rendert die Kachel schlicht.
-->
<script setup>
import { computed } from "vue";

const props = defineProps({
  label: { type: String, required: true },
  value: { type: String, required: true },
  hint:  { type: String, default: "" },
  delta: { type: String, default: "" },   // z. B. "+12 %"
  dir:   { type: String, default: "" },   // "up" | "down" | ""
  spark: { type: Array,  default: () => [] }, // Zahlenreihe (Verlauf)
});

// Sparkline in 88×30-ViewBox normalisieren (wie die Preview-Helfer).
const pts = computed(() => {
  const v = props.spark;
  if (!v || v.length < 2) return [];
  const min = Math.min(...v), max = Math.max(...v), span = max - min || 1;
  return v.map((y, i) => [
    (i / (v.length - 1)) * 86 + 1,
    28 - ((y - min) / span) * 24,
  ]);
});
const sparkLine = computed(() => pts.value.map(([x, y]) => `${x},${y}`).join(" "));
const sparkArea = computed(() =>
  pts.value.length ? `1,29 ${sparkLine.value} 87,29` : "");
</script>

<template>
  <div class="pp-kpi">
    <span class="pp-kpi__label">{{ label }}</span>
    <div class="pp-kpi__row">
      <span class="pp-kpi__value">{{ value }}</span>
      <svg v-if="pts.length" class="pp-kpi__spark" viewBox="0 0 88 30" preserveAspectRatio="none">
        <polygon class="pp-spark__area" :points="sparkArea" />
        <polyline class="pp-spark__line" :points="sparkLine" />
      </svg>
    </div>
    <div v-if="delta || hint" class="pp-kpi__foot">
      <span v-if="delta" class="pp-kpi__delta"
            :class="dir === 'up' ? 'pp-kpi__delta--up' : dir === 'down' ? 'pp-kpi__delta--down' : ''">
        {{ dir === 'up' ? '▲' : dir === 'down' ? '▼' : '' }} {{ delta }}
      </span>
      <span v-if="hint" class="pp-kpi__hint">{{ hint }}</span>
    </div>
  </div>
</template>
