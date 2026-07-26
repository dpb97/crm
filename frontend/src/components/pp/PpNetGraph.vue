<!-- PP_REV: PpNetGraph@4 -->
<!--
  PpNetGraph.vue — Beziehungsgeflecht mit Kraft-Layout (SSOT-Baustein).

  Zweite, „lebendige" Netzwerk-Variante neben dem bewusst statischen
  PpNetworkGraph (Ring-Layout). Bildet die CRM-„Netzwerk"-Seite des Klickdummys
  nach (nwHtml/nwInit/nwLayout).

  @4 (23.07.2026, Klickdummy-Nachzug Runde 2, Marco Regel 20) — additiv/rückwärtskompatibel:
    (1) Typisierte Kanten — eine Kante darf ein Objekt {a,b,type,strength,note} sein.
        `type` (arbeitet/berichtet/beziehung/verantwortlich, SSOT EDGE_TYPES) bestimmt
        Farbe + Linienart + Legende; `strength` (1–3) die Linienbreite; `note` den
        Tooltip. ALT-Format (String-/Array-Kante `[a,b]`) wird normalisiert (Typ
        „beziehung", Stärke 1) — keine Breaking Changes.
    (2) Doppelklick auf einen Knoten öffnet den Beziehungsdialog (Typ/Ziel/Stärke/
        Notiz) und meldet die neue Kante per `edge-save`. Der Dialog ist Vue-gesteuert
        (kein DOM-Gebastel); die In-Memory-Demo (Kante anhängen + Re-Mount) macht die
        Host-Seite — der Baustein bleibt kontrolliert.
    (3) Fokus-API für „Im Netzwerk anzeigen": Prop `focus` (Knoten-ID) + exponierte
        Methode `focusNode(id)` zentrieren + selektieren einen Knoten (z. B. Sprung aus
        der Personen-Tabelle/dem Personen-Inspektor).
    Härtere Kollision (Kollisionsradien Person 30 / Projekt 42, 340 Iterationen, 26
    Relaxations-Pässe) — auch dichte Cluster bleiben überlappungsfrei. LINEARE Hooke-
    Feder BLEIBT (nie quadratisch — sonst NaN-Explosion auf Kanten-Ketten); stärkere
    Beziehungen ziehen etwas fester (Cluster bleiben zusammen).

  @3-Fähigkeiten unverändert: (a) Radius-Kollision + finale Relaxation, (b) intelligente
  Label-Plazierung (4 Anker, Halo), (c) gekrümmte Kanten + Beziehungs-Hover, (d) Zoom-
  to-fit + Suche + Legende, (e) sanftes Einschwingen (rAF, prefers-reduced-motion),
  (f) optionale Cluster-Hüllen je Firma.

  Determinismus: Simulation läuft EINMALIG mit fester Iterationszahl aus den prozentualen
  Startkoordinaten — kein Zufall, Endlage reproduzierbar/testbar. `data-settled="1"`,
  sobald Layout + Einschwingen fertig sind (Test-Signal).

  XSS-sicher: alle Labels/Initialen/Notizen über Text-Bindung (SVG <text>/DOM-Text),
  KEIN v-html.

  Props:
    nodes    Array<{ id, t:'person'|'firma'|'projekt', l:Label, firma?, rolle?, st?, x, y }>
             x/y = Startposition in Prozent (0–100) des 1000×620-Feldes.
    edges    Array<[idA,idB] | { a,b, type?, strength?, note? }>   (beide Formen erlaubt)
    selected gesteuerte Auswahl (:selected + @select / v-model:selected)
    focus    Knoten-ID, die nach dem Einschwingen zentriert + selektiert wird
    labelThreshold  ab dieser Knotenzahl Dichte-Modus (Default 24)
    clusters (Boolean, Default false)  Cluster-Hüllen je Firma
    animate  (Boolean, Default true)   Einschwing-Animation
  Emits:
    select(id)                aktiver Knoten geändert
    inspect({ title, rows })  Klick auf einen Knoten → Spezifikation rechts
    edge-save({ a,b,type,strength,note })  Beziehung aus dem Doppelklick-Dialog gespeichert
  Expose:
    focusNode(id), fitView()

  Grenzen: ausgelegt für ~8–60 Knoten. Kein Auto-Relayout bei Kanten-/Knoten-Prop-
  Änderung zur Laufzeit — neue Daten = Re-Mount (key). Der Dialog fügt NICHT selbst an;
  er emittiert `edge-save`, der Host pflegt die Daten (In-Memory-Demo) und re-mountet.
-->
<script setup>
import { ref, reactive, computed, watch, onMounted, onBeforeUnmount } from "vue";

const props = defineProps({
  nodes:    { type: Array, default: () => [] },
  edges:    { type: Array, default: () => [] },
  selected: { type: [String, Number, null], default: null },
  focus:    { type: [String, Number, null], default: null },
  labelThreshold: { type: Number, default: 24 },
  clusters: { type: Boolean, default: false },
  animate:  { type: Boolean, default: true },
});
const emit = defineEmits(["select", "inspect", "edge-save"]);

/* Kantentypen (SSOT) — Label + CSS-Klasse (Farbe/Linienart token-basiert). */
const EDGE_TYPES = {
  arbeitet:       { label: "Arbeitet bei" },
  berichtet:      { label: "Berichtet an" },
  beziehung:      { label: "Beziehung zu" },
  verantwortlich: { label: "Verantwortlich für" },
};
const EDGE_KEYS = Object.keys(EDGE_TYPES);

const W = 1000, H = 620;
const svgEl = ref(null);
const pos = reactive({});
const target = {};
const vb = reactive({ x: 0, y: 0, w: W, h: H });
const internalSel = ref(null);
const hoverId = ref(null);
const query = ref("");
const settled = ref(false);
const sel = computed(() => internalSel.value ?? props.selected);

/* (1) Kanten normalisieren: Array/String → Objekt mit Typ/Stärke/Notiz. */
const edgeList = computed(() =>
  props.edges.map((e) => {
    if (Array.isArray(e)) return { a: e[0], b: e[1], type: "beziehung", strength: 1, note: "" };
    return { a: e.a, b: e.b, type: EDGE_TYPES[e.type] ? e.type : "beziehung", strength: e.strength || 1, note: e.note || "" };
  }),
);

/* Kollisionsradius je Knoten (Projekt = Rechteck → großzügiger; härter als @3). */
function nodeR(n) { return n.t === "projekt" ? 42 : 30; }

function neighbors(id) {
  const set = new Set([id]);
  for (const e of edgeList.value) { if (e.a === id) set.add(e.b); if (e.b === id) set.add(e.a); }
  return set;
}

/* ---------- Kraft-Layout inkl. Radius-Kollision (einmalig) ---------- */
function runLayout() {
  const nodes = props.nodes;
  const edges = edgeList.value;
  const rep0 = 34000;
  const iters = 340;
  const P = {};
  nodes.forEach((n) => { P[n.id] = { x: (n.x ?? 50) * W / 100, y: (n.y ?? 50) * H / 100 }; });

  for (let it = 0; it < iters; it++) {
    nodes.forEach((a) => {
      const pa = P[a.id]; let fx = 0, fy = 0;
      nodes.forEach((o) => {
        if (o.id === a.id) return;
        const po = P[o.id], dx = pa.x - po.x, dy = pa.y - po.y;
        const d2 = dx * dx + dy * dy || 1, d = Math.sqrt(d2);
        const rep = rep0 / d2; fx += dx / d * rep; fy += dy / d * rep;
      });
      // Federn: LINEARE Hooke-Kraft (Ruhelänge 175). KEIN zusätzliches `* d` (das
      // machte die Feder quadratisch → NaN-Explosion). Stärkere Beziehungen ziehen fester.
      edges.forEach((e) => {
        const other = e.a === a.id ? e.b : (e.b === a.id ? e.a : null);
        if (!other || !P[other]) return;
        const po = P[other], dx = po.x - pa.x, dy = po.y - pa.y, d = Math.sqrt(dx * dx + dy * dy) || 1;
        const f = (d - 175) * (0.035 + (e.strength || 1) * 0.006); fx += dx / d * f; fy += dy / d * f;
      });
      fx += (W / 2 - pa.x) * 0.004; fy += (H / 2 - pa.y) * 0.004;
      const mag = Math.sqrt(fx * fx + fy * fy);
      if (mag > 48) { fx = fx / mag * 48; fy = fy / mag * 48; }
      pa.x += fx; pa.y += fy;
    });
    collide(P, nodes, 3);
    nodes.forEach((a) => { const pa = P[a.id]; pa.x = Math.max(78, Math.min(W - 78, pa.x)); pa.y = Math.max(64, Math.min(H - 52, pa.y)); });
  }
  for (let pass = 0; pass < 26; pass++) {
    collide(P, nodes, 1);
    nodes.forEach((a) => { const pa = P[a.id]; pa.x = Math.max(78, Math.min(W - 78, pa.x)); pa.y = Math.max(64, Math.min(H - 52, pa.y)); });
  }
  nodes.forEach((n) => { target[n.id] = { x: P[n.id].x, y: P[n.id].y }; });
}

function collide(P, nodes, passes) {
  for (let pass = 0; pass < passes; pass++) {
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const a = nodes[i], b = nodes[j], pa = P[a.id], pb = P[b.id];
        let dx = pb.x - pa.x, dy = pb.y - pa.y;
        let d = Math.sqrt(dx * dx + dy * dy);
        if (d < 0.01) { dx = 1; dy = 0; d = 0.01; }
        const min = nodeR(a) + nodeR(b) + 8;
        if (d < min) {
          const push = (min - d) / 2; dx /= d; dy /= d;
          pa.x -= dx * push; pa.y -= dy * push; pb.x += dx * push; pb.y += dy * push;
        }
      }
    }
  }
}

/* ---------- Einschwing-Animation ---------- */
let raf = 0;
let pendingFocus = null;
function afterSettle() { settled.value = true; if (pendingFocus != null) { focusNode(pendingFocus); pendingFocus = null; } }
function startIntro() {
  const nodes = props.nodes;
  const reduce = typeof window !== "undefined" && window.matchMedia
    && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (!props.animate || reduce) {
    nodes.forEach((n) => { pos[n.id] = { x: target[n.id].x, y: target[n.id].y }; });
    afterSettle();
    return;
  }
  const start = {};
  nodes.forEach((n) => { start[n.id] = { x: (n.x ?? 50) * W / 100, y: (n.y ?? 50) * H / 100 }; pos[n.id] = { x: start[n.id].x, y: start[n.id].y }; });
  const DUR = 680, t0 = performance.now();
  const ease = (t) => 1 - Math.pow(1 - t, 3);
  function frame(now) {
    const t = Math.min(1, (now - t0) / DUR), k = ease(t);
    nodes.forEach((n) => {
      pos[n.id].x = start[n.id].x + (target[n.id].x - start[n.id].x) * k;
      pos[n.id].y = start[n.id].y + (target[n.id].y - start[n.id].y) * k;
    });
    if (t < 1) { raf = requestAnimationFrame(frame); }
    else { nodes.forEach((n) => { pos[n.id] = { ...target[n.id] }; }); afterSettle(); }
  }
  raf = requestAnimationFrame(frame);
}
onMounted(() => { pendingFocus = props.focus; runLayout(); startIntro(); });
onBeforeUnmount(() => { if (raf) cancelAnimationFrame(raf); });
watch(() => props.focus, (id) => { if (id != null && settled.value) focusNode(id); });

/* ---------- abgeleitete Geometrie ---------- */
const viewBox = computed(() => `${vb.x} ${vb.y} ${vb.w} ${vb.h}`);

// Kanten als leicht gekrümmte quadratische Bézier + Typ/Stärke.
const linkEls = computed(() =>
  edgeList.value
    .map((e, i) => {
      const a = pos[e.a], b = pos[e.b];
      if (!a || !b) return null;
      if (!Number.isFinite(a.x) || !Number.isFinite(a.y) || !Number.isFinite(b.x) || !Number.isFinite(b.y)) return null;
      const mx = (a.x + b.x) / 2, my = (a.y + b.y) / 2;
      const dx = b.x - a.x, dy = b.y - a.y, len = Math.sqrt(dx * dx + dy * dy) || 1;
      const bow = Math.min(26, len * 0.12);
      const cx = mx - (dy / len) * bow, cy = my + (dx / len) * bow;
      const tt = (EDGE_TYPES[e.type] ? EDGE_TYPES[e.type].label : "Beziehung") + (e.note ? " — " + e.note : "");
      return { i, a: e.a, b: e.b, type: e.type, width: 1.2 + (e.strength || 1) * 0.7,
               d: `M${a.x} ${a.y} Q${cx} ${cy} ${b.x} ${b.y}`, title: tt };
    })
    .filter(Boolean),
);
function initials(l) { return String(l || "").split(" ").map((w) => w[0]).join("").slice(0, 3); }
function badge(n) { return n.t === "projekt" ? String(n.l).split("-").slice(2).join("-") : initials(n.l); }
const typLabel = (t) => (t === "person" ? "Person" : t === "firma" ? "Firma" : "Projekt");

function isDim(id) { const focus = hoverId.value ?? sel.value; if (focus == null) return false; return !neighbors(focus).has(id); }
function edgeHi(e) { const focus = hoverId.value ?? sel.value; if (focus == null) return false; return e.a === focus || e.b === focus; }
function isEdgeDim(e) { const focus = hoverId.value ?? sel.value; if (focus == null) return false; return !edgeHi(e); }

/* ---------- Dichte-Modus: Label-Sichtbarkeit ---------- */
const dense = computed(() => props.nodes.length >= props.labelThreshold);
const zoomedIn = computed(() => vb.w <= 660);
function showLabel(id) {
  if (!dense.value || zoomedIn.value) return true;
  const focus = hoverId.value;
  if (focus != null && neighbors(focus).has(id)) return true;
  return sel.value === id;
}

/* ---------- (b) intelligente Label-Plazierung ---------- */
const anchors = computed(() => {
  const m = {};
  for (const n of props.nodes) {
    const p = pos[n.id]; if (!p) continue;
    const off = n.t === "projekt" ? 30 : 26;
    const cands = [
      { x: 0, y: off, anchor: "middle", dir: "b" }, { x: 0, y: -off, anchor: "middle", dir: "t" },
      { x: off, y: 4, anchor: "start", dir: "r" }, { x: -off, y: 4, anchor: "end", dir: "l" },
    ];
    let best = cands[0], bestScore = -Infinity;
    for (const c of cands) {
      const ax = p.x + c.x, ay = p.y + c.y; let nearest = Infinity;
      for (const o of props.nodes) {
        if (o.id === n.id) continue;
        const po = pos[o.id]; if (!po) continue;
        const dx = po.x - ax, dy = po.y - ay, d = dx * dx + dy * dy; if (d < nearest) nearest = d;
      }
      const bias = c.dir === "b" ? 1.15 : 1;
      if (nearest * bias > bestScore) { bestScore = nearest * bias; best = c; }
    }
    m[n.id] = best;
  }
  return m;
});

/* ---------- (f) Cluster-Hüllen je Firma ---------- */
const HULL_TONES = ["--pp-brand-primary", "--pp-accent-violet", "--pp-accent-amber",
                    "--pp-accent-emerald", "--pp-accent-rose", "--pp-accent-teal"];
function convexHull(pts) {
  if (pts.length < 3) return pts.slice();
  const p = pts.slice().sort((a, b) => a.x - b.x || a.y - b.y);
  const cross = (o, a, b) => (a.x - o.x) * (b.y - o.y) - (a.y - o.y) * (b.x - o.x);
  const lower = [];
  for (const q of p) { while (lower.length >= 2 && cross(lower[lower.length - 2], lower[lower.length - 1], q) <= 0) lower.pop(); lower.push(q); }
  const upper = [];
  for (let i = p.length - 1; i >= 0; i--) { const q = p[i]; while (upper.length >= 2 && cross(upper[upper.length - 2], upper[upper.length - 1], q) <= 0) upper.pop(); upper.push(q); }
  lower.pop(); upper.pop();
  return lower.concat(upper);
}
const hulls = computed(() => {
  if (!props.clusters) return [];
  const firmen = props.nodes.filter((n) => n.t === "firma");
  const out = [];
  const grow = 34;
  firmen.forEach((f, idx) => {
    const nb = neighbors(f.id);
    const raw = [...nb].map((id) => pos[id]).filter(Boolean).map((p) => ({ x: p.x, y: p.y }));
    const pts = raw.filter((p, i) => raw.findIndex((q) => Math.abs(q.x - p.x) < 0.5 && Math.abs(q.y - p.y) < 0.5) === i);
    if (pts.length < 1) return;
    const cx = pts.reduce((s, p) => s + p.x, 0) / pts.length;
    const cy = pts.reduce((s, p) => s + p.y, 0) / pts.length;
    let ring;
    const hull = convexHull(pts);
    if (hull.length >= 3) {
      ring = hull.map((p) => { const dx = p.x - cx, dy = p.y - cy, d = Math.sqrt(dx * dx + dy * dy) || 1; return { x: p.x + dx / d * grow, y: p.y + dy / d * grow }; });
    } else if (pts.length >= 2) {
      const a = pts[0], b = pts[pts.length - 1];
      const dx = b.x - a.x, dy = b.y - a.y, d = Math.sqrt(dx * dx + dy * dy) || 1;
      const nx = -dy / d * grow, ny = dx / d * grow;
      ring = [{ x: a.x + nx, y: a.y + ny }, { x: b.x + nx, y: b.y + ny }, { x: b.x - nx, y: b.y - ny }, { x: a.x - nx, y: a.y - ny }];
    } else {
      const p = pts[0];
      ring = [{ x: p.x - grow, y: p.y - grow }, { x: p.x + grow, y: p.y - grow }, { x: p.x + grow, y: p.y + grow }, { x: p.x - grow, y: p.y + grow }];
    }
    out.push({ id: f.id, tone: `var(${HULL_TONES[idx % HULL_TONES.length]})`, points: ring.map((p) => `${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(" ") });
  });
  return out;
});

/* ---------- Interaktion ---------- */
function pick(n) {
  internalSel.value = n.id;
  emit("select", n.id);
  emit("inspect", {
    title: n.l,
    rows: [["Typ", typLabel(n.t)], ["Firma", n.firma || "—"], ["Rolle / Inhalt", n.rolle || "—"], ["Status", n.st || "—"]],
  });
}
function scale() { const r = svgEl.value ? svgEl.value.getBoundingClientRect().width : W; return vb.w / (r || W); }

function onNodePointerdown(n, ev) {
  ev.stopPropagation();
  let moved = false;
  const sx = ev.clientX, sy = ev.clientY, ox = pos[n.id].x, oy = pos[n.id].y, sc = scale();
  function mv(e2) { const dx = (e2.clientX - sx) * sc, dy = (e2.clientY - sy) * sc; if (Math.abs(dx) + Math.abs(dy) > 3) moved = true; pos[n.id].x = ox + dx; pos[n.id].y = oy + dy; }
  function up() { window.removeEventListener("pointermove", mv); window.removeEventListener("pointerup", up); if (!moved) pick(n); }
  window.addEventListener("pointermove", mv); window.addEventListener("pointerup", up);
}

const panning = ref(false);
function onSvgPointerdown(ev) {
  panning.value = true;
  const sx = ev.clientX, sy = ev.clientY, ox = vb.x, oy = vb.y, sc = scale();
  function mv(e2) { vb.x = ox - (e2.clientX - sx) * sc; vb.y = oy - (e2.clientY - sy) * sc; }
  function up() { panning.value = false; window.removeEventListener("pointermove", mv); window.removeEventListener("pointerup", up); }
  window.addEventListener("pointermove", mv); window.addEventListener("pointerup", up);
}
function onWheel(ev) {
  ev.preventDefault();
  const f = ev.deltaY > 0 ? 1.15 : 0.87;
  const aspect = vb.h / vb.w;
  const nw = Math.max(360, Math.min(1600, vb.w * f));
  const nh = nw * aspect;
  vb.x += (vb.w - nw) / 2; vb.y += (vb.h - nh) / 2; vb.w = nw; vb.h = nh;
}

function fitView() {
  const ns = props.nodes.map((n) => pos[n.id]).filter(Boolean);
  if (!ns.length) return;
  let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
  ns.forEach((p) => { minX = Math.min(minX, p.x); minY = Math.min(minY, p.y); maxX = Math.max(maxX, p.x); maxY = Math.max(maxY, p.y); });
  const pad = 80;
  vb.x = minX - pad; vb.y = minY - pad;
  vb.w = Math.max(360, (maxX - minX) + 2 * pad);
  vb.h = Math.max(240, (maxY - minY) + 2 * pad);
}

// (3) Fokus-API: Knoten zentrieren + selektieren („Im Netzwerk anzeigen").
function focusNode(id) {
  const p = pos[id]; if (!p) return;
  const w = 520, h = w * (vb.h / vb.w || 0.62);
  vb.x = p.x - w / 2; vb.y = p.y - h / 2; vb.w = w; vb.h = h;
  const n = props.nodes.find((x) => x.id === id);
  if (n) pick(n);
}
function doSearch() {
  const q = query.value.trim().toLowerCase();
  if (!q) return;
  const hit = props.nodes.find((n) => String(n.l).toLowerCase().includes(q) || String(n.firma || "").toLowerCase().includes(q));
  if (hit) focusNode(hit.id);
}
defineExpose({ focusNode, fitView });

/* ---------- (2) Doppelklick-Beziehungsdialog ---------- */
const dialog = reactive({ open: false, from: null, type: "arbeitet", targetId: "", strength: 2, note: "" });
const dialogTargets = computed(() => (dialog.from ? props.nodes.filter((n) => n.id !== dialog.from.id) : []));
function openDialog(n) {
  dialog.from = n; dialog.type = "arbeitet";
  dialog.targetId = (dialogTargets.value[0] || {}).id || "";
  dialog.strength = 2; dialog.note = ""; dialog.open = true;
}
function closeDialog() { dialog.open = false; dialog.from = null; }
function saveDialog() {
  if (!dialog.from || !dialog.targetId) { closeDialog(); return; }
  emit("edge-save", {
    a: dialog.from.id, b: dialog.targetId, type: dialog.type,
    strength: Number(dialog.strength), note: dialog.note.trim() || EDGE_TYPES[dialog.type].label,
  });
  closeDialog();
}
</script>

<template>
  <div class="pp-ng">
    <div class="pp-ng__toolbar">
      <div class="pp-ng__search">
        <input type="search" v-model="query" placeholder="Knoten suchen…"
               aria-label="Knoten suchen" @keydown.enter.prevent="doSearch" />
        <button type="button" class="pp-ng__search-go" aria-label="Suchen" @click="doSearch">→</button>
      </div>
      <button type="button" class="pp-ng__fit" @click="fitView">Ansicht einpassen</button>
    </div>

    <svg ref="svgEl" class="pp-ng__svg" :class="{ 'is-panning': panning }" :viewBox="viewBox"
         :data-settled="settled ? '1' : '0'"
         role="img" aria-label="Beziehungsgeflecht (Kraft-Layout)"
         @pointerdown="onSvgPointerdown" @wheel="onWheel">
      <polygon v-for="hu in hulls" :key="'h' + hu.id" class="pp-ng__hull"
               :points="hu.points" :style="{ fill: hu.tone, stroke: hu.tone }" />
      <!-- (1)+(c) Kanten: typisiert, gekrümmt, Beziehungs-Hover -->
      <path v-for="l in linkEls" :key="'e' + l.i" class="pp-ng__edge" :class="['e-' + l.type,
            { 'is-dim': isEdgeDim(l), 'is-hi': edgeHi(l) }]" :d="l.d"
            :style="{ strokeWidth: l.width + 'px' }"><title>{{ l.title }}</title></path>
      <!-- Knoten -->
      <g v-for="n in nodes" :key="n.id" class="pp-ng__node" :class="['t-' + n.t,
           { 'is-sel': sel === n.id, 'is-dim': isDim(n.id) }]"
         :transform="`translate(${(pos[n.id] || {}).x || 0},${(pos[n.id] || {}).y || 0})`"
         role="button" tabindex="0" :aria-label="n.l"
         @pointerdown="onNodePointerdown(n, $event)"
         @dblclick.stop.prevent="openDialog(n)"
         @mouseenter="hoverId = n.id" @mouseleave="hoverId = null"
         @keydown.enter.prevent="pick(n)" @keydown.space.prevent="pick(n)">
        <rect v-if="n.t === 'projekt'" class="pp-ng__shape" x="-34" y="-15" width="68" height="30" rx="3" />
        <circle v-else class="pp-ng__shape" r="19" />
        <text class="pp-ng__ini" y="4">{{ badge(n) }}</text>
        <template v-if="showLabel(n.id) && anchors[n.id]">
          <text class="pp-ng__lbl" :text-anchor="anchors[n.id].anchor" :x="anchors[n.id].x" :y="anchors[n.id].y">{{ n.l }}</text>
          <text v-if="n.rolle" class="pp-ng__sub" :text-anchor="anchors[n.id].anchor" :x="anchors[n.id].x" :y="anchors[n.id].y + 12">{{ n.rolle }}</text>
        </template>
      </g>
    </svg>

    <div class="pp-ng__legend">
      <div class="pp-ng__legend-row">
        <span><i class="t-person"></i>Person</span>
        <span><i class="t-firma"></i>Firma</span>
        <span><i class="t-projekt"></i>Projekt</span>
      </div>
      <div class="pp-ng__legend-row pp-ng__legend-edges">
        <span v-for="k in EDGE_KEYS" :key="k"><i class="ln" :class="'e-' + k"></i>{{ EDGE_TYPES[k].label }}</span>
      </div>
    </div>
    <p class="pp-ng__foot">Ziehen = anordnen · Rad = zoomen · Hover = Beziehung · Klick = Details · Doppelklick = Beziehung hinzufügen</p>

    <!-- (2) Beziehungsdialog (Vue-gesteuert, In-Memory-Demo macht der Host) -->
    <div v-if="dialog.open" class="pp-ng__dialog" role="dialog" aria-label="Beziehung hinzufügen">
      <div class="pp-ng__dialog-head">Beziehung von <b>{{ dialog.from && dialog.from.l }}</b></div>
      <label>Beziehungstyp
        <select v-model="dialog.type">
          <option v-for="k in EDGE_KEYS" :key="k" :value="k">{{ EDGE_TYPES[k].label }}</option>
        </select>
      </label>
      <label>Ziel
        <select v-model="dialog.targetId">
          <option v-for="t in dialogTargets" :key="t.id" :value="t.id">{{ t.l }}{{ t.rolle ? ' — ' + t.rolle : '' }}</option>
        </select>
      </label>
      <label>Stärke
        <select v-model="dialog.strength">
          <option :value="1">schwach</option><option :value="2">mittel</option><option :value="3">stark</option>
        </select>
      </label>
      <label>Notiz
        <input type="text" v-model="dialog.note" placeholder="z. B. Arbeitet bei, Rahmenvertrag …" />
      </label>
      <div class="pp-ng__dialog-btns">
        <button type="button" class="pp-ng__btn" @click="closeDialog">Abbrechen</button>
        <button type="button" class="pp-ng__btn is-pri" @click="saveDialog">Speichern</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.pp-ng { position: relative; background: var(--pp-bg-surface); border: 1px solid var(--pp-border-subtle);
  border-radius: var(--pp-radius-ui); overflow: hidden; }
.pp-ng__svg { display: block; width: 100%; height: min(58vh, 560px); cursor: grab;
  background: var(--pp-bg-base); touch-action: none; }
.pp-ng__svg.is-panning { cursor: grabbing; }

/* Werkzeugleiste */
.pp-ng__toolbar { position: absolute; left: 10px; top: 10px; z-index: 2; display: flex; gap: var(--pp-space-2); align-items: center; }
.pp-ng__search { display: inline-flex; align-items: center; background: var(--pp-bg-surface);
  border: 1px solid var(--pp-border-default); border-radius: var(--pp-radius-ui); overflow: hidden; }
.pp-ng__search input { border: 0; outline: none; background: transparent; font-family: inherit;
  font-size: var(--pp-fs-12); color: var(--pp-text-primary); padding: 5px 8px; width: 140px; }
.pp-ng__search-go { border: 0; cursor: pointer; background: var(--pp-bg-hover); color: var(--pp-text-secondary);
  font-family: inherit; font-size: var(--pp-fs-13); padding: 5px 9px; }
.pp-ng__search-go:hover { color: var(--pp-text-primary); }
.pp-ng__fit { border: 1px solid var(--pp-border-default); cursor: pointer; background: var(--pp-bg-surface);
  color: var(--pp-text-secondary); font-family: inherit; font-size: var(--pp-fs-12);
  font-weight: var(--pp-weight-semibold); border-radius: var(--pp-radius-ui); padding: 5px 10px; }
.pp-ng__fit:hover { background: var(--pp-bg-hover); color: var(--pp-text-primary); }

/* (f) Cluster-Hüllen */
.pp-ng__hull { fill-opacity: 0.06; stroke-opacity: 0.26; stroke-width: 1.5; stroke-linejoin: round; }

/* (1)+(c) Kanten — Typ = Farbe/Linienart (token-basiert), Breite = Stärke (inline) */
.pp-ng__edge { fill: none; stroke: var(--pp-border-strong); transition: opacity .15s ease; }
.pp-ng__edge.e-arbeitet { stroke: var(--pp-text-secondary); }
.pp-ng__edge.e-berichtet { stroke: var(--pp-accent-teal); stroke-dasharray: 3 5; }
.pp-ng__edge.e-beziehung { stroke: var(--pp-text-tertiary); stroke-dasharray: 1 6; stroke-linecap: round; }
.pp-ng__edge.e-verantwortlich { stroke: var(--pp-brand-primary); }
.pp-ng__edge.is-dim { opacity: 0.14; }
.pp-ng__edge.is-hi { opacity: 1; }

.pp-ng__node { cursor: pointer; outline: none; transition: opacity .15s ease; }
.pp-ng__node.is-dim { opacity: 0.16; }
.pp-ng__shape { stroke-width: 2; transition: stroke-width .12s ease; }
.pp-ng__node.t-person .pp-ng__shape  { fill: var(--pp-bg-surface); stroke: var(--pp-brand-primary); }
.pp-ng__node.t-firma  .pp-ng__shape  { fill: var(--pp-brand-primary); stroke: var(--pp-brand-primary); }
.pp-ng__node.t-projekt .pp-ng__shape { fill: var(--pp-state-success);
  stroke: color-mix(in oklab, var(--pp-state-success) 70%, oklch(0 0 0)); }
.pp-ng__node.is-sel .pp-ng__shape { stroke: var(--pp-text-primary); stroke-width: 3; }

.pp-ng__ini { font-size: 11px; font-weight: var(--pp-weight-bold); text-anchor: middle; pointer-events: none; font-family: var(--pp-font-body); }
.pp-ng__node.t-person .pp-ng__ini  { fill: var(--pp-brand-primary); }
.pp-ng__node.t-firma  .pp-ng__ini  { fill: var(--pp-text-on-accent); }
.pp-ng__node.t-projekt .pp-ng__ini { fill: var(--pp-text-on-accent); }
.pp-ng__lbl { font-size: 11px; font-weight: var(--pp-weight-semibold); fill: var(--pp-text-primary);
  pointer-events: none; font-family: var(--pp-font-body); paint-order: stroke; stroke: var(--pp-bg-base); stroke-width: 3px; }
.pp-ng__sub { font-size: 9.5px; fill: var(--pp-text-secondary); pointer-events: none; font-family: var(--pp-font-body);
  paint-order: stroke; stroke: var(--pp-bg-base); stroke-width: 3px; }

/* Legende (Knotentypen + Kantentypen) */
.pp-ng__legend { position: absolute; right: 10px; top: 10px; display: flex; flex-direction: column; gap: 5px;
  background: var(--pp-bg-surface); border: 1px solid var(--pp-border-default); border-radius: var(--pp-radius-ui);
  padding: 7px 10px; font-size: 10.5px; font-weight: var(--pp-weight-semibold); color: var(--pp-text-secondary); }
.pp-ng__legend-row { display: flex; flex-wrap: wrap; gap: 10px; }
.pp-ng__legend-edges { border-top: 1px solid var(--pp-border-subtle); padding-top: 5px; }
.pp-ng__legend span { display: inline-flex; align-items: center; }
.pp-ng__legend i { display: inline-block; width: 10px; height: 10px; border-radius: var(--pp-radius-full);
  margin-right: 5px; vertical-align: -1px; border: 2px solid var(--pp-brand-primary); }
.pp-ng__legend i.t-person  { background: var(--pp-bg-surface); }
.pp-ng__legend i.t-firma   { background: var(--pp-brand-primary); }
.pp-ng__legend i.t-projekt { background: var(--pp-state-success); border-color: var(--pp-state-success); border-radius: 2px; }
.pp-ng__legend i.ln { width: 16px; height: 0; border: 0; border-radius: 0; border-top: 3px solid var(--pp-text-secondary); }
.pp-ng__legend i.ln.e-arbeitet { border-top-color: var(--pp-text-secondary); }
.pp-ng__legend i.ln.e-berichtet { border-top-color: var(--pp-accent-teal); border-top-style: dashed; }
.pp-ng__legend i.ln.e-beziehung { border-top-color: var(--pp-text-tertiary); border-top-style: dotted; }
.pp-ng__legend i.ln.e-verantwortlich { border-top-color: var(--pp-brand-primary); }

.pp-ng__foot { position: absolute; left: 10px; bottom: 8px; margin: 0; font-size: 10px; color: var(--pp-text-tertiary); pointer-events: none; }

/* (2) Beziehungsdialog */
.pp-ng__dialog { position: absolute; right: 14px; bottom: 14px; z-index: 5; width: 280px;
  background: var(--pp-bg-surface); border: 1px solid var(--pp-border-default); border-radius: var(--pp-radius-ui);
  box-shadow: var(--pp-shadow-lg); padding: 12px 13px; display: flex; flex-direction: column; gap: 8px; }
.pp-ng__dialog-head { font-size: 12.5px; font-weight: var(--pp-weight-semibold); color: var(--pp-text-primary); margin-bottom: 2px; }
.pp-ng__dialog label { display: flex; flex-direction: column; gap: 3px; font-size: 9.5px; font-weight: var(--pp-weight-bold);
  letter-spacing: 0.05em; text-transform: uppercase; color: var(--pp-text-tertiary); }
.pp-ng__dialog select, .pp-ng__dialog input { border: 1px solid var(--pp-border-default); border-radius: 3px;
  background: var(--pp-bg-base); padding: 5px 7px; font-family: inherit; font-size: var(--pp-fs-12);
  font-weight: var(--pp-weight-regular); text-transform: none; letter-spacing: 0; color: var(--pp-text-primary); }
.pp-ng__dialog-btns { display: flex; justify-content: flex-end; gap: 8px; margin-top: 4px; }
.pp-ng__btn { border: 1px solid var(--pp-border-default); cursor: pointer; background: var(--pp-bg-surface);
  color: var(--pp-text-secondary); font-family: inherit; font-size: var(--pp-fs-12); font-weight: var(--pp-weight-semibold);
  border-radius: var(--pp-radius-ui); padding: 5px 11px; }
.pp-ng__btn:hover { background: var(--pp-bg-hover); color: var(--pp-text-primary); }
.pp-ng__btn.is-pri { background: var(--pp-brand-primary); border-color: var(--pp-brand-primary); color: var(--pp-text-on-accent); }
.pp-ng__btn.is-pri:hover { background: var(--pp-brand-600, var(--pp-brand-primary)); color: var(--pp-text-on-accent); }
</style>
