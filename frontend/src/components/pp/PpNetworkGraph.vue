<!-- PP_REV: PpNetworkGraph@1 -->
<!--
  PpNetworkGraph.vue — Beziehungsgraph (Token-SVG, SSOT-Baustein).

  Für CRM-„Netzwerk" u. ä.: Knoten (z. B. Kunde, Betreiber, Behörde, Kontakt) und
  gerichtete/ungerichtete Kanten. Bewusst KEINE Graph-Lib (kein d3-force/vis.js) und
  KEIN Zufall zur Laufzeit — das Layout ist DETERMINISTISCH aus dem Knoten-Index
  berechnet (Kreis-Layout; optional ein zentraler Knoten). Damit ist die Darstellung
  reproduzierbar und pixel-regressionsfähig.

  Grenzen (Wahrheit ist Pflicht): reines Kreis-/Radial-Layout, keine Kraft-Simulation
  und keine Kantenentflechtung — bei sehr dichten Graphen überlagern sich Kanten.
  Für Übersichts-Netze (bis ~20 Knoten) gedacht.

  Props:
    nodes    Array<{ id, label, kind?:String, center?:Boolean }>
             kind ∈ "brand"|"success"|"warning"|"danger"|"info"|"neutral" (Default "brand")
             center:true → Knoten in die Mitte statt auf den Ring
    edges    Array<{ from, to, label?:String }>
    selected gesteuerte Auswahl (:selected + @node-click)
  Emits:
    node-click(id)
-->
<script setup>
import { ref, computed } from "vue";

const props = defineProps({
  nodes:    { type: Array, default: () => [] },
  edges:    { type: Array, default: () => [] },
  selected: { type: [String, Number], default: null },
});
const emit = defineEmits(["node-click"]);

const VB_W = 440;
const VB_H = 320;
const CX = VB_W / 2;
const CY = VB_H / 2;
const R = Math.min(VB_W, VB_H) * 0.38;

const tone = (k) =>
  ["brand", "success", "warning", "danger", "info", "neutral"].includes(k) ? k : "brand";

// Deterministisches Layout: Ring-Knoten gleichverteilt (Start oben, im Uhrzeigersinn),
// zentrale Knoten in die Mitte. Position ergibt sich ausschließlich aus dem Index.
const layout = computed(() => {
  const ring = props.nodes.filter((n) => !n.center);
  const map = new Map();
  props.nodes.forEach((n) => {
    if (n.center) {
      map.set(n.id, { n, x: CX, y: CY, tone: tone(n.kind), center: true });
    } else {
      const i = ring.indexOf(n);
      const a = -Math.PI / 2 + (i / Math.max(ring.length, 1)) * Math.PI * 2;
      map.set(n.id, { n, x: CX + R * Math.cos(a), y: CY + R * Math.sin(a), tone: tone(n.kind), center: false });
    }
  });
  return map;
});

const internalSel = ref(null);
const sel = computed(() => internalSel.value ?? props.selected);

const links = computed(() =>
  props.edges
    .map((e, i) => {
      const a = layout.value.get(e.from);
      const b = layout.value.get(e.to);
      if (!a || !b) return null;
      return { e, i, x1: a.x, y1: a.y, x2: b.x, y2: b.y, mx: (a.x + b.x) / 2, my: (a.y + b.y) / 2 };
    })
    .filter(Boolean),
);

const isEdgeActive = (e) => sel.value != null && (e.from === sel.value || e.to === sel.value);
const isNodeDim = (id) => {
  if (sel.value == null) return false;
  if (id === sel.value) return false;
  return !props.edges.some((e) => (e.from === sel.value && e.to === id) || (e.to === sel.value && e.from === id));
};

const nodesLaid = computed(() => [...layout.value.values()]);

function pick(id) {
  internalSel.value = id;
  emit("node-click", id);
}
</script>

<template>
  <div class="pp-net">
    <svg class="pp-net__svg" :viewBox="`0 0 ${VB_W} ${VB_H}`" role="img"
         aria-label="Beziehungsgraph" preserveAspectRatio="xMidYMid meet">
      <!-- Kanten zuerst (liegen unter den Knoten) -->
      <g class="pp-net__edges">
        <g v-for="l in links" :key="'e' + l.i" class="pp-net__edge" :class="{ 'is-active': isEdgeActive(l.e) }">
          <line :x1="l.x1" :y1="l.y1" :x2="l.x2" :y2="l.y2" />
          <text v-if="l.e.label" class="pp-net__edge-label" :x="l.mx" :y="l.my - 3">{{ l.e.label }}</text>
        </g>
      </g>

      <!-- Knoten -->
      <g class="pp-net__nodes">
        <g v-for="p in nodesLaid" :key="p.n.id"
           class="pp-net__node"
           :class="[{ 'is-selected': sel === p.n.id, 'is-dim': isNodeDim(p.n.id), 'is-center': p.center }]"
           role="button" tabindex="0" :aria-label="p.n.label"
           @click="pick(p.n.id)"
           @keydown.enter.prevent="pick(p.n.id)"
           @keydown.space.prevent="pick(p.n.id)">
          <circle class="pp-net__ring" :cx="p.x" :cy="p.y" :r="p.center ? 24 : 18" />
          <circle class="pp-net__dot" :class="'is-' + p.tone" :cx="p.x" :cy="p.y" :r="p.center ? 15 : 11" />
          <text class="pp-net__label" :x="p.x" :y="p.y + (p.center ? 40 : 32)">{{ p.n.label }}</text>
        </g>
      </g>
    </svg>
  </div>
</template>

<style scoped>
.pp-net { background: var(--pp-bg-surface); border: 1px solid var(--pp-border-subtle);
  border-radius: var(--pp-radius-ui); padding: var(--pp-space-3); }
.pp-net__svg { display: block; width: 100%; height: auto; }

.pp-net__edge line { stroke: var(--pp-border-strong); stroke-width: 1.2;
  transition: stroke var(--pp-duration-fast, 120ms) ease, stroke-width var(--pp-duration-fast, 120ms) ease; }
.pp-net__edge.is-active line { stroke: var(--pp-brand-primary); stroke-width: 2; }
.pp-net__edge-label { fill: var(--pp-text-tertiary); font-size: 10px; text-anchor: middle;
  font-family: var(--pp-font-body); paint-order: stroke; stroke: var(--pp-bg-surface); stroke-width: 3px; }

.pp-net__node { cursor: pointer; outline: none; transition: opacity var(--pp-duration-fast, 120ms) ease; }
.pp-net__node.is-dim { opacity: 0.4; }
.pp-net__ring { fill: transparent; stroke: transparent; stroke-width: 2.5; }
.pp-net__node.is-selected .pp-net__ring,
.pp-net__node:focus-visible .pp-net__ring { stroke: color-mix(in oklab, var(--pp-brand-primary) 55%, transparent); }
.pp-net__dot { stroke: var(--pp-bg-surface); stroke-width: 2;
  transition: r var(--pp-duration-fast, 120ms) ease; }
.pp-net__dot.is-brand   { fill: var(--pp-brand-primary); }
.pp-net__dot.is-success { fill: var(--pp-state-success); }
.pp-net__dot.is-warning { fill: var(--pp-state-warning); }
.pp-net__dot.is-danger  { fill: var(--pp-state-danger); }
.pp-net__dot.is-info    { fill: var(--pp-state-info); }
.pp-net__dot.is-neutral { fill: var(--pp-text-tertiary); }
.pp-net__label { fill: var(--pp-text-secondary); font-size: 11px; font-weight: var(--pp-weight-medium);
  text-anchor: middle; font-family: var(--pp-font-body);
  paint-order: stroke; stroke: var(--pp-bg-surface); stroke-width: 3px; }
.pp-net__node.is-selected .pp-net__label { fill: var(--pp-text-primary); font-weight: var(--pp-weight-semibold); }
</style>
