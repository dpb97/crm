<!-- PP_REV: PpMap@2 -->
<!--
  PpMap.vue — Marker-Weltkarte (Token-SVG, SSOT-Baustein).

  Generalisierung aus SalesbotMap.vue (Repo-eigener Showcase): dort war die Karte
  fest an die Salesbot-Tender-SSOT gekoppelt. DIESER Baustein ist datenneutral —
  Marker kommen als Prop rein, Färbung über `kind`.

  Bewusst KEINE Karten-Lib (kein Leaflet/WorldWind), keine Kachel-Bilder, kein <img>:
  reines Token-SVG, equirektangulär (x = lon+180, y = 90-lat, viewBox 360×180 — 1:1
  wie in SalesbotMap). Funktioniert hell + dunkel über Tokens.

  Grenzen (Wahrheit ist Pflicht): der Welt-Umriss ist ein STILISIERTER, vereinfachter
  Kontinent-Pfad (keine echte Vektor-Landmasse) — als Orientierung, nicht als
  geodätisch exakte Basemap gedacht. Für exakte Lagen zählt allein die Projektion
  der Marker-Koordinaten.

  Props:
    markers  Array<{ id, lat:Number, lon:Number, label?:String, kind?:String }>
             kind ∈ "brand"|"success"|"warning"|"danger"|"info"|"neutral" (Default "brand")
    activeId für gesteuerte Auswahl (v-model-fähig über :active-id + @marker-click)
    graticule Boolean — Gradnetz zeigen (Default true)
    markerScale Number — Marker-Vergrößerungsfaktor (Default 1; additiv, ändert
             bestehende Verbraucher nicht). Skaliert Pin- und Halo-Radius linear —
             für Karten mit wenigen, prominenten Markern (z. B. Territorien).
  Emits:
    marker-click(id)   Klick/Enter/Space auf einen Marker
-->
<script setup>
import { ref, computed } from "vue";

const props = defineProps({
  markers:     { type: Array,  default: () => [] },
  activeId:    { type: [String, Number], default: null },
  graticule:   { type: Boolean, default: true },
  markerScale: { type: Number, default: 1 },
});
const emit = defineEmits(["marker-click"]);

const VB_W = 360;
const VB_H = 180;
const xOf = (lon) => lon + 180;
const yOf = (lat) => 90 - lat;

const graticuleLng = [-150, -120, -90, -60, -30, 0, 30, 60, 90, 120, 150];
const graticuleLat = [-60, -30, 0, 30, 60];

// Stilisierter, vereinfachter Kontinent-Umriss (viewBox-Koordinaten, x=lon+180 / y=90-lat).
const LAND = [
  "18,38 40,26 70,20 96,24 128,34 122,50 104,56 100,70 88,74 82,60 70,58 58,50 42,48 26,44",     // Nordamerika
  "128,14 148,11 154,22 144,30 130,26",                                                            // Grönland
  "104,80 120,78 132,86 130,104 122,120 114,138 106,146 100,132 98,112 100,94",                    // Südamerika
  "168,34 182,26 200,24 214,30 218,42 206,48 196,54 184,50 174,44",                                // Europa
  "170,60 186,54 206,56 222,66 224,86 216,104 206,122 196,126 188,110 180,92 174,76",              // Afrika
  "222,28 250,18 288,16 322,22 352,30 356,46 340,58 316,60 300,74 284,66 268,72 252,60 236,50",    // Asien
  "296,104 316,100 332,106 334,118 324,128 306,126 298,116",                                       // Australien
];

const hoverId = ref(null);

// Marker-Radien (viewBox-Einheiten). Basiswerte × markerScale — Default 1 hält
// bestehende Verbraucher pixelgleich. Aktiv-Radius wird per Attribut gebunden
// (nicht via CSS `r`), damit die Vergrößerung auch ohne CSS-Geometrie-Support greift.
const R_PIN = computed(() => 3.4 * props.markerScale);
const R_PIN_ACTIVE = computed(() => 4.4 * props.markerScale);
const R_HALO = computed(() => 7.5 * props.markerScale);
const isActiveMarker = (id) => (hoverId.value ?? props.activeId) === id;

const tone = (k) =>
  ["brand", "success", "warning", "danger", "info", "neutral"].includes(k) ? k : "brand";

const points = computed(() =>
  props.markers.map((m) => ({
    m,
    cx: xOf(m.lon),
    cy: yOf(m.lat),
    tone: tone(m.kind),
  })),
);

const activeMarker = computed(() => {
  const id = hoverId.value ?? props.activeId;
  return id == null ? null : points.value.find((p) => p.m.id === id) || null;
});

function pick(id) {
  emit("marker-click", id);
}
</script>

<template>
  <div class="pp-map">
    <div class="pp-map__wrap">
      <svg class="pp-map__svg" :viewBox="`0 0 ${VB_W} ${VB_H}`" role="img"
           aria-label="Weltkarte mit Marker-Standorten" preserveAspectRatio="xMidYMid meet">
        <rect x="0" y="0" :width="VB_W" :height="VB_H" class="pp-map__ocean" />

        <g v-if="graticule" class="pp-map__grat">
          <line v-for="lng in graticuleLng" :key="'x' + lng" :x1="xOf(lng)" y1="0" :x2="xOf(lng)" :y2="VB_H" />
          <line v-for="lat in graticuleLat" :key="'y' + lat" x1="0" :y1="yOf(lat)" :x2="VB_W" :y2="yOf(lat)" />
        </g>

        <g class="pp-map__land">
          <polygon v-for="(pts, i) in LAND" :key="'l' + i" :points="pts" />
        </g>

        <line class="pp-map__grat-main" x1="0" :y1="yOf(0)" :x2="VB_W" :y2="yOf(0)" />
        <line class="pp-map__grat-main" :x1="xOf(0)" y1="0" :x2="xOf(0)" :y2="VB_H" />

        <g class="pp-map__markers">
          <g v-for="p in points" :key="p.m.id"
             class="pp-map__marker" :class="{ 'is-active': (hoverId ?? activeId) === p.m.id }"
             role="button" tabindex="0"
             :aria-label="p.m.label || String(p.m.id)"
             @mouseenter="hoverId = p.m.id" @mouseleave="hoverId = null"
             @focus="hoverId = p.m.id" @blur="hoverId = null"
             @click="pick(p.m.id)"
             @keydown.enter.prevent="pick(p.m.id)"
             @keydown.space.prevent="pick(p.m.id)">
            <circle class="pp-map__halo" :cx="p.cx" :cy="p.cy" :r="R_HALO" />
            <circle class="pp-map__pin" :class="'is-' + p.tone" :cx="p.cx" :cy="p.cy"
                    :r="isActiveMarker(p.m.id) ? R_PIN_ACTIVE : R_PIN" />
          </g>
        </g>
      </svg>

      <!-- HTML-Tooltip (nicht skalierend): SVG ist verzerrungsfrei (2:1), daher
           lineare %-Abbildung von viewBox → Container. -->
      <div v-if="activeMarker && activeMarker.m.label" class="pp-map__tip"
           :style="{ left: (activeMarker.cx / VB_W * 100) + '%', top: (activeMarker.cy / VB_H * 100) + '%' }">
        {{ activeMarker.m.label }}
      </div>
    </div>
    <p class="pp-map__foot">Equirektangulär · stilisierter Umriss, keine Basemap (Token-SVG)</p>
  </div>
</template>

<style scoped>
.pp-map { background: var(--pp-bg-surface); border: 1px solid var(--pp-border-subtle);
  border-radius: var(--pp-radius-ui); padding: var(--pp-space-3); }
.pp-map__wrap { position: relative; min-width: 0; }
.pp-map__svg { display: block; width: 100%; height: auto; }
.pp-map__ocean { fill: color-mix(in oklab, var(--pp-brand-primary) 7%, var(--pp-bg-sunken)); }
.pp-map__land polygon { fill: color-mix(in oklab, var(--pp-border-strong) 34%, transparent);
  stroke: color-mix(in oklab, var(--pp-border-strong) 60%, transparent); stroke-width: 0.4; }
.pp-map__grat line { stroke: color-mix(in oklab, var(--pp-border-strong) 40%, transparent); stroke-width: 0.4; }
.pp-map__grat-main { stroke: color-mix(in oklab, var(--pp-border-strong) 70%, transparent); stroke-width: 0.6; }

.pp-map__marker { cursor: pointer; outline: none; }
.pp-map__halo { fill: transparent; opacity: 0; transition: opacity var(--pp-duration-fast, 120ms) ease; }
.pp-map__marker.is-active .pp-map__halo,
.pp-map__marker:focus-visible .pp-map__halo { fill: color-mix(in oklab, var(--pp-brand-primary) 22%, transparent); opacity: 1; }
.pp-map__pin { stroke: var(--pp-bg-surface); stroke-width: 0.8; transition: r var(--pp-duration-fast, 120ms) ease; }
.pp-map__pin.is-brand   { fill: var(--pp-brand-primary); }
.pp-map__pin.is-success { fill: var(--pp-state-success); }
.pp-map__pin.is-warning { fill: var(--pp-state-warning); }
.pp-map__pin.is-danger  { fill: var(--pp-state-danger); }
.pp-map__pin.is-info    { fill: var(--pp-state-info); }
.pp-map__pin.is-neutral { fill: var(--pp-text-tertiary); }

.pp-map__tip { position: absolute; transform: translate(-50%, -140%); pointer-events: none;
  background: var(--pp-bg-elevated); color: var(--pp-text-primary);
  border: 1px solid var(--pp-border-default); border-radius: var(--pp-radius-ui);
  padding: 3px 8px; font-size: var(--pp-fs-12, 12px); font-weight: var(--pp-weight-medium);
  white-space: nowrap; box-shadow: var(--pp-shadow-md); z-index: 2; }

.pp-map__foot { margin: var(--pp-space-2) 0 0; text-align: right; font-size: 10px;
  letter-spacing: 0.03em; color: var(--pp-text-tertiary); }
</style>
