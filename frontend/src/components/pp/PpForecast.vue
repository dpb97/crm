<!-- PP_REV: PpForecast@1 -->
<!--
  PpForecast.vue — Ist/Plan/Prognose-Verlaufschart (SSOT-Baustein, Regel 19).

  Marco 23.07.2026: „Prognosen = echte Charts, nie Fortschrittsbalken." Bildet den
  Klickdummy-Renderer `svgForecast` als echten, props-getriebenen Vue-Baustein nach:
    · Ist-Fläche (Vergangenheit) + Ist-Linie mit Punkten
    · Plan-Linie (gestrichelt, ganze Breite)
    · Prognose-Korridor (best..worst) als getönte Fläche ab dem Split
    · Prognose-Erwartungslinie (gestrichelt) mit Punkten ab dem Split
    · Trennlinie „Ist | Prognose"
    · Gitter + Y-Achsen-Ticks + X-Beschriftung + Legende

  Selbst gezeichnetes SVG (KEIN v-html, KEINE Chart-Lib): das Modell wird in einer
  computed-Property zu SVG-Primitiven aufgelöst und deklarativ per v-for gerendert.
  Responsive über viewBox (preserveAspectRatio); Farben ausschließlich aus --pp-*-
  Tokens (scoped CSS-Klassen); hell/dunkel gratis. A11y: role="img" + aria-label.
  Tooltips: native <title> an den Datenpunkten.

  Props:
    title    String   Kartentitel
    meta     String   feine Kopfzeile rechts (Einheit/Erläuterung)
    note     String   Fußnote unter dem Chart
    cats     String[] X-Kategorien (Pflicht)
    splitAt  Number   Index der Trennung Ist|Prognose (0-basiert)
    ist      Number[] Ist-Reihe (bis splitAt)          — optional
    plan     Number[] Plan-Reihe (ganze Breite)        — optional (null-Lücken erlaubt)
    exp      Number[] Prognose erwartet (ab splitAt)   — optional
    best     Number[] Korridor-Oberkante (ab splitAt)  — optional
    worst    Number[] Korridor-Unterkante (ab splitAt) — optional
    unit     String   Einheit für die „Ist"-Legende (z. B. „(M€)")
    ymax     Number   feste Y-Obergrenze (sonst 1,15× Maximum)
    yfmt     Function optionaler Formatter für die Y-Ticks (v → String/Number)
  Emits: keine (reine Darstellung).
-->
<script setup>
import { computed } from "vue";

const props = defineProps({
  title:   { type: String, default: "Prognose" },
  meta:    { type: String, default: "" },
  note:    { type: String, default: "" },
  cats:    { type: Array, required: true },
  splitAt: { type: Number, default: 0 },
  ist:     { type: Array, default: null },
  plan:    { type: Array, default: null },
  exp:     { type: Array, default: null },
  best:    { type: Array, default: null },
  worst:   { type: Array, default: null },
  unit:    { type: String, default: "" },
  ymax:    { type: Number, default: 0 },
  yfmt:    { type: Function, default: null },
});

const W = 760, Ht = 320, x0 = 52, x1 = 742, y0 = 18, y1 = 272;

const model = computed(() => {
  const cats = props.cats, N = cats.length, sp = props.splitAt;
  let ymax = props.ymax;
  if (!ymax) {
    ymax = 0;
    [props.ist, props.plan, props.best, props.exp, props.worst].forEach((a) =>
      (a || []).forEach((v) => { if (v != null && v > ymax) ymax = v; }));
    ymax = ymax * 1.15 || 1;
  }
  const xs = (i) => x0 + (x1 - x0) * (N <= 1 ? 0 : i / (N - 1));
  const ys = (v) => y1 - (v / ymax) * (y1 - y0);
  const fmt = (v) => (props.yfmt ? props.yfmt(v) : Math.round(v));

  const grid = [];
  for (let gi = 0; gi <= 4; gi++) {
    const yv = ymax * gi / 4, yy = ys(yv);
    grid.push({ y: +yy.toFixed(1), label: String(fmt(yv)) });
  }

  // Korridor best..worst (geschlossenes Polygon)
  let band = "";
  if (props.best && props.worst) {
    let p = "";
    for (let i = sp; i < N; i++) p += (i === sp ? "M" : "L") + xs(i).toFixed(1) + " " + ys(props.best[i]).toFixed(1) + " ";
    for (let j = N - 1; j >= sp; j--) p += "L" + xs(j).toFixed(1) + " " + ys(props.worst[j]).toFixed(1) + " ";
    band = p + "Z";
  }

  // Ist-Fläche + Ist-Linie
  let area = "", istLine = "";
  const istDots = [];
  if (props.ist) {
    let ar = "M" + xs(0).toFixed(1) + " " + y1 + " ";
    for (let a = 0; a <= sp; a++) ar += "L" + xs(a).toFixed(1) + " " + ys(props.ist[a]).toFixed(1) + " ";
    area = ar + "L" + xs(sp).toFixed(1) + " " + y1 + " Z";
    let il = "";
    for (let b = 0; b <= sp; b++) il += (b === 0 ? "M" : "L") + xs(b).toFixed(1) + " " + ys(props.ist[b]).toFixed(1) + " ";
    istLine = il;
    for (let f = 0; f <= sp; f++) istDots.push({ x: +xs(f).toFixed(1), y: +ys(props.ist[f]).toFixed(1), v: props.ist[f], cat: cats[f] });
  }

  // Plan-Linie (Lücken erlaubt)
  let planLine = "";
  if (props.plan) {
    let pl = "";
    for (let c = 0; c < N; c++) { if (props.plan[c] == null) continue; pl += (pl ? "L" : "M") + xs(c).toFixed(1) + " " + ys(props.plan[c]).toFixed(1) + " "; }
    planLine = pl;
  }

  // Prognose erwartet
  let expLine = "";
  const expDots = [];
  if (props.exp) {
    let el = "";
    for (let d = sp; d < N; d++) { if (props.exp[d] == null) continue; el += (el ? "L" : "M") + xs(d).toFixed(1) + " " + ys(props.exp[d]).toFixed(1) + " "; }
    expLine = el;
    for (let e = sp; e < N; e++) if (props.exp[e] != null) expDots.push({ x: +xs(e).toFixed(1), y: +ys(props.exp[e]).toFixed(1), v: props.exp[e], cat: cats[e] });
  }

  const splitX = +xs(sp).toFixed(1);
  const xticks = cats.map((ct, i) => ({ x: +xs(i).toFixed(1), label: ct }));

  return { N, sp, grid, band, area, istLine, istDots, planLine, expLine, expDots, splitX, xticks, y0, y1 };
});
</script>

<template>
  <div class="pp-fc pg-card">
    <div class="pp-fc__head">
      <span class="pp-fc__title">{{ title }}</span>
      <span v-if="meta" class="pp-fc__meta">{{ meta }}</span>
    </div>
    <div class="pp-fc__wrap">
      <svg class="pp-fc__svg" :viewBox="`0 0 ${W} ${Ht}`" preserveAspectRatio="xMidYMid meet"
           role="img" :aria-label="title">
        <!-- Gitter + Y-Ticks -->
        <g v-for="(g, i) in model.grid" :key="'g' + i">
          <line class="pp-fc__grid" :x1="x0" :y1="g.y" :x2="x1" :y2="g.y" />
          <text class="pp-fc__ytick" :x="x0 - 6" :y="g.y + 3">{{ g.label }}</text>
        </g>
        <!-- Prognose-Korridor -->
        <path v-if="model.band" class="pp-fc__band" :d="model.band" />
        <!-- Ist-Fläche + Linie -->
        <path v-if="model.area" class="pp-fc__area" :d="model.area" />
        <path v-if="model.istLine" class="pp-fc__ln pp-fc__ist" :d="model.istLine" />
        <!-- Plan-Linie -->
        <path v-if="model.planLine" class="pp-fc__ln pp-fc__plan" :d="model.planLine" />
        <!-- Prognose erwartet -->
        <path v-if="model.expLine" class="pp-fc__ln pp-fc__exp" :d="model.expLine" />
        <circle v-for="(d, i) in model.expDots" :key="'ed' + i" class="pp-fc__dot pp-fc__exp"
                :cx="d.x" :cy="d.y" r="3.2"><title>{{ d.cat }}: {{ d.v }}</title></circle>
        <circle v-for="(d, i) in model.istDots" :key="'id' + i" class="pp-fc__dot pp-fc__ist"
                :cx="d.x" :cy="d.y" r="3.2"><title>{{ d.cat }}: {{ d.v }}</title></circle>
        <!-- Trennlinie Ist | Prognose -->
        <line class="pp-fc__split" :x1="model.splitX" :y1="model.y0" :x2="model.splitX" :y2="model.y1" />
        <text class="pp-fc__split-lbl" :x="model.splitX + 4" :y="model.y0 + 10">Ist | Prognose</text>
        <!-- X-Beschriftung -->
        <text v-for="(t, i) in model.xticks" :key="'x' + i" class="pp-fc__xtick" :x="t.x" :y="model.y1 + 16">{{ t.label }}</text>
      </svg>
      <div class="pp-fc__legend">
        <span><i class="sw-ist"></i>Ist {{ unit }}</span>
        <span><i class="sw-plan"></i>Plan</span>
        <span><i class="sw-exp"></i>Prognose (erwartet)</span>
        <span><i class="sw-band"></i>Korridor (best–worst)</span>
      </div>
    </div>
    <p v-if="note" class="pp-fc__note">{{ note }}</p>
  </div>
</template>

<style scoped>
.pp-fc { background: var(--pp-bg-surface); border: 1px solid var(--pp-border-subtle);
  border-radius: var(--pp-radius-ui); overflow: hidden; }
.pp-fc__head { display: flex; align-items: baseline; gap: var(--pp-space-3);
  padding: var(--pp-space-3) var(--pp-space-4); border-bottom: 1px solid var(--pp-border-subtle); }
.pp-fc__title { font-size: var(--pp-fs-14); font-weight: var(--pp-weight-semibold); color: var(--pp-text-primary); }
.pp-fc__meta { font-size: var(--pp-fs-12); color: var(--pp-text-tertiary); }
.pp-fc__wrap { padding: var(--pp-space-3) var(--pp-space-4); }
.pp-fc__svg { width: 100%; height: auto; display: block; }

.pp-fc__grid { stroke: var(--pp-border-subtle); stroke-width: 1; }
.pp-fc__ytick { font-size: 9px; fill: var(--pp-text-tertiary); text-anchor: end; font-family: var(--pp-font-body); }
.pp-fc__xtick { font-size: 9.5px; fill: var(--pp-text-secondary); text-anchor: middle; font-family: var(--pp-font-body); }

.pp-fc__ln { fill: none; stroke-width: 2.4; stroke-linejoin: round; stroke-linecap: round; }
.pp-fc__ist { stroke: var(--pp-brand-primary); }
.pp-fc__area { fill: var(--pp-brand-primary); opacity: 0.13; stroke: none; }
.pp-fc__plan { stroke: var(--pp-text-tertiary); stroke-width: 1.8; stroke-dasharray: 5 4; }
.pp-fc__exp { stroke: var(--pp-accent-amber); stroke-dasharray: 6 3; }
.pp-fc__band { fill: var(--pp-accent-amber); opacity: 0.12; stroke: none; }
.pp-fc__dot { stroke: var(--pp-bg-surface); stroke-width: 1.5; }
.pp-fc__dot.pp-fc__ist { fill: var(--pp-brand-primary); }
.pp-fc__dot.pp-fc__exp { fill: var(--pp-accent-amber); }
.pp-fc__split { stroke: var(--pp-border-strong); stroke-width: 1.2; stroke-dasharray: 3 3; }
.pp-fc__split-lbl { font-size: 9px; font-weight: var(--pp-weight-semibold); fill: var(--pp-text-tertiary); font-family: var(--pp-font-body); }

.pp-fc__legend { display: flex; flex-wrap: wrap; gap: 8px 16px; margin-top: 10px;
  font-size: 10.5px; font-weight: var(--pp-weight-semibold); color: var(--pp-text-tertiary); }
.pp-fc__legend span { display: inline-flex; align-items: center; gap: 6px; }
.pp-fc__legend i { display: inline-block; width: 16px; height: 10px; border-radius: 2px; flex: none; }
.pp-fc__legend i.sw-ist { background: var(--pp-brand-primary); }
.pp-fc__legend i.sw-plan { height: 0; border-top: 2px dashed var(--pp-text-tertiary); border-radius: 0; }
.pp-fc__legend i.sw-exp { height: 0; border-top: 2px dashed var(--pp-accent-amber); border-radius: 0; }
.pp-fc__legend i.sw-band { background: var(--pp-accent-amber); opacity: 0.3; }

.pp-fc__note { margin: 0; padding: 0 var(--pp-space-4) var(--pp-space-4);
  font-size: var(--pp-fs-12); color: var(--pp-text-secondary); line-height: var(--pp-lh-normal, 1.5); }
</style>
