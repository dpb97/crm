<!-- PP_REV: PpGeoMap@4 -->
<!--
  PpGeoMap.vue — echte Landkarte (Leaflet + OpenStreetMap, SSOT-Baustein, Regeln 13/21).

  Projektlandkarte im Seilkranbau: Anlagen/Projekte liegen als Seilbahn-Trasse auf
  der Karte — Endmast Tal (Kontur/offen) + Endmast Berg (gefüllt), verbunden mit der
  gebogenen Seillinie (Spannweite beschriftet). Bildet geoInit/vmapHtml + VMAP/
  VMAP_STATE/VMARKT_GEO des Klickdummys nach.

  @3 (23.07.2026, Klickdummy-Nachzug Runde 2, Marco Regel 21) — additiv/props-kompatibel:
    · Marker-FORM = Anlagentyp (▲ Seilkran „SK" · ● Materialseilbahn „SB" · ◆ Winde „WI"),
      Marker-FARBE = Lebenszyklus-STATUS (bau/betrieb/service/akquise → Token-Farbe).
      Rückwärtskompatibel: fehlt `state`, greift die bisherige Phase→Farbe; `col`
      überschreibt weiterhin explizit. Fehlt `typ`, wird ● gezeichnet.
    · Seillinie gebogen (quadratische Bézier, Parität geoBow) + permanentes Spannweiten-
      Label „≈X km".
    · Cluster bei Zoom-out (3°-Raster): unter Zoom ≤5 Cluster-Bläschen mit Anlagenzahl,
      Klick zoomt auf die Region; darüber die Einzelanlagen.
    · Maßstab (L.control.scale, metrisch), Vollbild-Toggle + „Auf Projekte zoomen"
      (eigene L.Control-Buttons oben links).
    · Marktaufteilungs-Overlay: `markt`-Polygone als eigener Layer im Ebenen-Umschalter
      (L.control.layers Overlay-Checkbox), Flächen-Klick → Markt-`inspect`-Payload.
    · KPI-Segmentierung: Prop `segment` filtert die Marker nach Status (die KPI-Karten
      der Seite steuern ihn; Marker-Layer werden bei Wechsel neu aufgebaut).
    · Reicher Hover-Tooltip (Nr. + Bezeichnung + Firma + Typ + Status + Wert) — XSS-
      sicher als DOM mit textContent, KEIN HTML aus Daten.

  @4 (26.07.2026, Konsistenz-Sweep F29) — Wiederhol-/Bounds-Härtung (der volle
  OSM/Territorien-Umbau folgt in einer späteren Etappe nach Klickdummy-K4):
    · TileLayer `noWrap:true` → keine horizontale Kachel-Wiederholung.
    · `maxBounds [[-85,-180],[85,180]]` + `maxBoundsViscosity:1` → Karte bleibt in
      der einen Welt (kein endloses Panning), `worldCopyJump:false`.

  Bewusste Entscheidungen (Wahrheit ist Pflicht):
    · Leaflet als echte yarn-Dependency (KEIN CDN); CSS lokal importiert.
    · KEINE Marker-PNGs — nur L.circleMarker / L.divIcon / L.polygon / L.polyline.
    · Farben zur Laufzeit aus den --pp-*-Tokens aufgelöst (Probe-Element → computed
      color). Grenze: Auflösung beim Mount — Hell/Dunkel-Wechsel wirkt erst nach
      Re-Mount. Markt-Overlay-Farben kommen als CSS-Werte in `markt[].col` (Token-Vars
      erlaubt) und werden ebenfalls aufgelöst.
    · @2-Robustheit bleibt: `fitBounds` erst bei echter Container-Höhe, ResizeObserver
      → `map.invalidateSize()` (0-hoch/unsichtbar-beim-Mount-Fehler).
    · Kacheln © OpenStreetMap/OpenTopoMap/Esri (Internet nötig); offline bleibt es leer.

  Props:
    pins    Array<{ t:Label, ll:[lat,lng], c?:'ok'|'warn'|'' }>
    routes  Array<{ t:Label, pts:[[lat,lng],…], dash?:Boolean }>
    masten  Array<{ nr, n:Name, firma?, typ?:'SK'|'SB'|'WI', state?, phase?, col?,
                    wert?, wer?, info?, tal:[lat,lng], berg:[lat,lng] }>
    markt   Array<{ t:Label, col:CSS-Farbe, ring:[[lat,lng],…], wer?, laender?,
                    leads?, proj?, pipe?, status? }>  — Marktaufteilungs-Overlay
    segment String  Status-Filter der Masten ('all' | 'bau' | 'betrieb' | 'service' | 'akquise')
    height  String  CSS-Höhe (Default "min(58vh, 640px)")
  Emits:
    inspect({ title, rows })   Klick auf Pin / Seillinie / Mast / Marktfläche → Spezifikation
-->
<script setup>
import { ref, watch, onMounted, onBeforeUnmount } from "vue";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

const props = defineProps({
  pins:    { type: Array, default: () => [] },
  routes:  { type: Array, default: () => [] },
  masten:  { type: Array, default: () => [] },
  markt:   { type: Array, default: () => [] },
  segment: { type: String, default: "all" },
  height:  { type: String, default: "min(58vh, 640px)" },
});
const emit = defineEmits(["inspect"]);

const mapEl = ref(null);
let map = null;
let ro = null;
let didFit = false;
let T = null;                 // aufgelöste Token-Farben
let indivLayer = null;        // Einzel-Anlagen
let clusterLayer = null;      // Cluster-Bläschen
let pinLayer = null;          // Pins + Routen (nachbaubar, s. buildPins)
let projBounds = [];          // alle Mast-Punkte (für „Auf Projekte zoomen")
let allBounds = [];           // alles inkl. Pins/Routes (für initiales fitBounds)

/* Status → Token-Farbe (Lebenszyklus). */
const STATE_META = {
  bau:     { key: "warning", label: "In Bau" },
  betrieb: { key: "success", label: "In Betrieb" },
  service: { key: "danger",  label: "Service fällig" },
  akquise: { key: "brand",   label: "Akquise" },
};
function stateColor(state) { const m = STATE_META[state]; return m ? T[m.key] : T.brand; }
function stateLabel(state) { const m = STATE_META[state]; return m ? m.label : (state || "—"); }
function typName(typ) { return typ === "SK" ? "Seilkran" : typ === "WI" ? "Winde / Vorschub" : typ === "SB" ? "Materialseilbahn" : "Anlage"; }
function typGlyph(typ) { return typ === "SK" ? "▲" : typ === "WI" ? "◆" : "●"; }

function phaseColor(phase) {
  const p = String(phase || "").toLowerCase();
  if (/gewonnen|auftrag|in betrieb|fertig/.test(p)) return T.success;
  if (/verhandlung|angebot/.test(p)) return T.warning;
  if (/projektierung|planung/.test(p)) return T.amber;
  return T.brand;
}
function mastColor(pj) { return pj.col || (pj.state ? stateColor(pj.state) : phaseColor(pj.phase)); }

/* Token → konkrete Farbe (rgb) über ein Probe-Element auflösen. */
function resolveColor(cssValue, host) {
  const probe = document.createElement("span");
  probe.style.color = cssValue; probe.style.display = "none";
  host.appendChild(probe);
  const c = getComputedStyle(probe).color;
  host.removeChild(probe);
  return c;
}

/* Horizontale Seillinien-Länge (Haversine), km, Dezimalkomma. */
function geoKm(a, b) {
  const R = 6371;
  const dl = (b[0] - a[0]) * Math.PI / 180, dg = (b[1] - a[1]) * Math.PI / 180;
  const la = a[0] * Math.PI / 180, lb = b[0] * Math.PI / 180;
  const x = Math.sin(dl / 2), y = Math.sin(dg / 2);
  const h = x * x + Math.cos(la) * Math.cos(lb) * y * y;
  return (2 * R * Math.asin(Math.sqrt(h))).toFixed(1).replace(".", ",");
}
/* Gebogene Seillinie (quadratische Bézier, abgetastet) — Parität geoBow. */
function geoBow(a, b) {
  const mx = (a[0] + b[0]) / 2, my = (a[1] + b[1]) / 2;
  const dx = b[0] - a[0], dy = b[1] - a[1], len = Math.sqrt(dx * dx + dy * dy) || 1, bow = len * 0.16;
  const cx = mx - (dy / len) * bow, cy = my + (dx / len) * bow, pts = [];
  for (let t = 0; t <= 1.0001; t += 0.1) {
    const it = 1 - t;
    pts.push([it * it * a[0] + 2 * it * t * cx + t * t * b[0], it * it * a[1] + 2 * it * t * cy + t * t * b[1]]);
  }
  return pts;
}

/* XSS-sicherer Tooltip: reiner Text als DOM-Element. */
function textTip(s) { const el = document.createElement("span"); el.textContent = s; return el; }
/* Reicher Tooltip (mehrere Zeilen, Nr. fett) — XSS-sicher via DOM. */
function richTip(head, lines) {
  const d = document.createElement("div");
  const b = document.createElement("b"); b.textContent = head; d.appendChild(b);
  lines.forEach((line) => { d.appendChild(document.createElement("br")); d.appendChild(document.createTextNode(line)); });
  return d;
}

function fitOnce() {
  if (didFit || !map || !allBounds.length || !mapEl.value) return;
  if (mapEl.value.offsetHeight > 0 && mapEl.value.offsetWidth > 0) {
    map.invalidateSize();
    map.fitBounds(allBounds, { padding: [40, 40], maxZoom: 11 });
    didFit = true;
  }
}

/* Pins + Routen auf-/neu bauen. Eigener Layer, weil die Daten asynchron
   nachlaufen (createResource): beim Mount sind pins/routes noch leer, ein
   einmaliges Zeichnen dort ließe die Karte dauerhaft leer. */
function buildPins() {
  if (pinLayer) { map.removeLayer(pinLayer); pinLayer = null; }
  pinLayer = L.layerGroup();
  props.pins.forEach((p) => {
    if (!Array.isArray(p.ll) || p.ll.length < 2) return;
    const col = p.c === "ok" ? T.success : (p.c === "warn" ? T.warning : T.brand);
    const rows = [["Position", p.ll[0].toFixed(3) + ", " + p.ll[1].toFixed(3)]];
    (p.rows || []).forEach((r) => rows.unshift(r));
    L.circleMarker(p.ll, { radius: 7, color: col, weight: 2, fillColor: col, fillOpacity: 0.35 })
      .bindTooltip(textTip(p.t))
      .on("click", () => emit("inspect", { title: p.t, rows }))
      .addTo(pinLayer);
    allBounds.push(p.ll);
  });
  props.routes.forEach((r) => {
    L.polyline(r.pts, { color: T.brand, weight: 3, opacity: 0.75, dashArray: r.dash === false ? null : "7 7" })
      .bindTooltip(textTip(r.t))
      .addTo(pinLayer);
    r.pts.forEach((x) => allBounds.push(x));
  });
  pinLayer.addTo(map);
}

/* Einzel-Anlagen + Cluster (segment-gefiltert) auf-/neu bauen. */
function buildMasten() {
  if (indivLayer) { map.removeLayer(indivLayer); indivLayer = null; }
  if (clusterLayer) { map.removeLayer(clusterLayer); clusterLayer = null; }
  projBounds = [];
  const visible = props.segment === "all" ? props.masten : props.masten.filter((m) => m.state === props.segment);
  if (!visible.length) return;

  indivLayer = L.layerGroup();
  visible.forEach((pj) => {
    const col = mastColor(pj), glyph = typGlyph(pj.typ);
    const tipLines = [pj.n, pj.firma || "—", typName(pj.typ) + " · " + stateLabel(pj.state) + " · " + (pj.wert || "—")];
    const line = L.polyline(geoBow(pj.tal, pj.berg), { color: col, weight: 3.5, opacity: 0.95, lineCap: "round" });
    line.bindTooltip("≈" + geoKm(pj.tal, pj.berg) + " km", { permanent: true, direction: "center", className: "pp-geo__span" });
    const mi = (fill) => L.divIcon({
      className: "",
      html: '<span class="pp-geo-mast ' + (fill ? "is-berg" : "is-tal") + '" style="border-color:' + col + ";" +
            (fill ? "background:" + col + ";color:var(--pp-text-on-accent)" : "background:var(--pp-bg-surface);color:" + col) + '">' + glyph + "</span>",
      iconSize: [22, 22], iconAnchor: [11, 11],
    });
    const talM = L.marker(pj.tal, { icon: mi(false) });
    const bergM = L.marker(pj.berg, { icon: mi(true) });
    talM.bindTooltip(richTip("Endmast Tal — " + (pj.nr || pj.n), tipLines));
    bergM.bindTooltip(richTip("Endmast Berg — " + (pj.nr || pj.n), tipLines));
    const det = () => emit("inspect", {
      title: pj.n,
      rows: [
        ["Projekt-Nr.", pj.nr || "—"], ["Bezeichnung", pj.n], ["Firma / Kunde", pj.firma || "—"],
        ["Anlagentyp", typName(pj.typ)], ["Status", stateLabel(pj.state)], ["Auftragswert", pj.wert || "—"],
        ["Verantwortlich", pj.wer || "—"], ["Hinweis", pj.info || "—"],
        ["Endmast Tal", pj.tal[0].toFixed(4) + ", " + pj.tal[1].toFixed(4)],
        ["Endmast Berg", pj.berg[0].toFixed(4) + ", " + pj.berg[1].toFixed(4)],
        ["Spannweite (horiz.)", "≈" + geoKm(pj.tal, pj.berg) + " km"],
      ],
    });
    [line, talM, bergM].forEach((x) => { x.on("click", det); indivLayer.addLayer(x); });
    projBounds.push(pj.tal); projBounds.push(pj.berg);
  });
  indivLayer.addTo(map);

  // Cluster-Bläschen bei Zoom-out (Rasterung ~3°).
  const groups = {};
  visible.forEach((pj) => {
    const mid = [(pj.tal[0] + pj.berg[0]) / 2, (pj.tal[1] + pj.berg[1]) / 2];
    const key = Math.round(mid[0] / 3) + "_" + Math.round(mid[1] / 3);
    (groups[key] = groups[key] || []).push(mid);
  });
  clusterLayer = L.layerGroup();
  Object.keys(groups).forEach((k) => {
    const g = groups[k];
    const cx = g.reduce((s, p) => s + p[0], 0) / g.length, cy = g.reduce((s, p) => s + p[1], 0) / g.length;
    const bubble = L.marker([cx, cy], { icon: L.divIcon({ className: "", html: '<span class="pp-geo-cluster">' + g.length + "</span>", iconSize: [36, 36], iconAnchor: [18, 18] }) });
    bubble.bindTooltip(textTip(g.length + " Anlagen in dieser Region — Klick zum Aufzoomen"));
    bubble.on("click", () => map.flyToBounds(g, { padding: [70, 70], maxZoom: 10 }));
    clusterLayer.addLayer(bubble);
  });
  updCluster();
}

function updCluster() {
  if (!map || !indivLayer || !clusterLayer) return;
  if (map.getZoom() <= 5) {
    if (map.hasLayer(indivLayer)) map.removeLayer(indivLayer);
    if (!map.hasLayer(clusterLayer)) clusterLayer.addTo(map);
  } else {
    if (map.hasLayer(clusterLayer)) map.removeLayer(clusterLayer);
    if (!map.hasLayer(indivLayer)) indivLayer.addTo(map);
  }
}

onMounted(() => {
  if (!mapEl.value) return;
  T = {
    brand:   resolveColor("var(--pp-brand-primary)", mapEl.value),
    success: resolveColor("var(--pp-state-success)", mapEl.value),
    warning: resolveColor("var(--pp-state-warning)", mapEl.value),
    danger:  resolveColor("var(--pp-state-danger)", mapEl.value),
    amber:   resolveColor("var(--pp-accent-amber)", mapEl.value),
  };

  map = L.map(mapEl.value, {
    scrollWheelZoom: true,
    worldCopyJump: false,                    // @4 F29: kein Sprung in die Kachel-Kopie
    maxBounds: [[-85, -180], [85, 180]],     // @4 F29: eine Welt, kein endloses Panning
    maxBoundsViscosity: 1,                   // @4 F29: harte Kante an den Bounds
  });
  const geoBase = {
    "Standard": L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png",
      { maxZoom: 19, noWrap: true, attribution: "© OpenStreetMap-Mitwirkende" }),
    "Gelände (Höhenlinien)": L.tileLayer("https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png",
      { maxZoom: 17, noWrap: true, attribution: "© OpenStreetMap-Mitwirkende, SRTM · Kartendarstellung © OpenTopoMap (CC-BY-SA)" }),
    "Satellit": L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
      { maxZoom: 19, noWrap: true, attribution: "Tiles © Esri — Source: Esri, Maxar, Earthstar Geographics" }),
  };
  geoBase["Standard"].addTo(map);

  // Marktaufteilungs-Overlay (Toggle im Ebenen-Umschalter).
  const overlays = {};
  if (props.markt.length) {
    const mkLayer = L.layerGroup();
    props.markt.forEach((mk) => {
      const col = resolveColor(mk.col || "var(--pp-brand-primary)", mapEl.value);
      const poly = L.polygon(mk.ring, { color: col, weight: 1.6, opacity: 0.6, fillColor: col, fillOpacity: 0.14, dashArray: "5 4" });
      poly.bindTooltip(textTip(mk.t + " — " + (mk.wer || "unbesetzt")), { sticky: true });
      poly.on("mouseover", () => poly.setStyle({ fillOpacity: 0.26 }));
      poly.on("mouseout", () => poly.setStyle({ fillOpacity: 0.14 }));
      poly.on("click", (ev) => {
        if (ev && ev.originalEvent) L.DomEvent.stop(ev.originalEvent);
        emit("inspect", {
          title: "Markt · " + mk.t,
          rows: [
            ["Verantwortlich", mk.wer || "unbesetzt"], ["Länder", mk.laender || "—"],
            ["Aktive Leads", mk.leads || "—"], ["Projekte im Gebiet", mk.proj || "—"],
            ["Pipeline", mk.pipe || "—"],
            ["Gebietsstatus", mk.wer ? "besetzt — Chancen laufen direkt an den Verantwortlichen" : "unbesetzt — eingehende Chancen an die Vertriebsbesprechung"],
          ],
        });
      });
      mkLayer.addLayer(poly);
    });
    overlays["Marktaufteilung"] = mkLayer;
  }
  L.control.layers(geoBase, Object.keys(overlays).length ? overlays : null, { position: "topright" }).addTo(map);
  L.control.scale({ imperial: false, metric: true, position: "bottomleft" }).addTo(map);

  allBounds = [];
  buildPins();
  buildMasten();
  props.masten.forEach((pj) => { allBounds.push(pj.tal); allBounds.push(pj.berg); });

  // Cluster-Umschaltung an den Zoom koppeln.
  map.on("zoomend", updCluster);

  // Steuer-Buttons: Vollbild + „Auf Projekte zoomen".
  const Btns = L.Control.extend({
    options: { position: "topleft" },
    onAdd() {
      const wrap = L.DomUtil.create("div", "leaflet-bar pp-geo-ctl");
      const fs = L.DomUtil.create("a", "pp-geo-ctl__btn", wrap);
      fs.href = "#"; fs.title = "Vollbild ein/aus"; fs.innerHTML = "⤢";
      L.DomEvent.on(fs, "click", (e) => {
        L.DomEvent.stop(e); mapEl.value.classList.toggle("is-fs");
        setTimeout(() => { map.invalidateSize(); if (projBounds.length) map.fitBounds(projBounds, { padding: [40, 40], maxZoom: 12 }); }, 80);
      });
      const zp = L.DomUtil.create("a", "pp-geo-ctl__btn", wrap);
      zp.href = "#"; zp.title = "Auf Projekte zoomen"; zp.innerHTML = "⌖";
      L.DomEvent.on(zp, "click", (e) => { L.DomEvent.stop(e); if (projBounds.length) map.fitBounds(projBounds, { padding: [40, 40], maxZoom: 12 }); });
      return wrap;
    },
  });
  map.addControl(new Btns());

  fitOnce();
  ro = new ResizeObserver(() => { if (!map) return; map.invalidateSize(); fitOnce(); });
  ro.observe(mapEl.value);
});

// KPI-Segmentierung: Status-Filter wechselt → Marker-Layer neu bauen + einpassen.
watch(() => props.segment, () => {
  if (!map) return;
  buildMasten();
  if (projBounds.length) map.fitBounds(projBounds, { padding: [40, 40], maxZoom: 12 });
});

// Nachlaufende Daten (createResource lädt asynchron): alles neu zeichnen und
// erneut einpassen, sonst bleibt die Karte auf dem leeren Mount-Stand stehen.
watch(() => [props.pins, props.routes, props.masten], () => {
  if (!map) return;
  allBounds = [];
  buildPins();
  buildMasten();
  props.masten.forEach((pj) => { allBounds.push(pj.tal); allBounds.push(pj.berg); });
  didFit = false;
  fitOnce();
});

onBeforeUnmount(() => {
  if (ro) { ro.disconnect(); ro = null; }
  if (map) { map.remove(); map = null; }
});
</script>

<template>
  <div class="pp-geo">
    <div ref="mapEl" class="pp-geo__map" :style="{ minHeight: height === '100%' ? '320px' : height }"></div>
    <p class="pp-geo__hint">
      Kartenkacheln &copy; OpenStreetMap-Mitwirkende (Internet erforderlich) &mdash; Rad = zoomen,
      Ziehen = verschieben, Klick auf Seillinie/Mast/Pin/Marktfl&auml;che = Details im Inspektor.
    </p>
  </div>
</template>

<style scoped>
/* Fülle den Elterncontainer: der einzige Consumer (LCSProjectsMap) gibt
   height="100%", das aber an der Karten-div hing und mangels Wrapper-Höhe auf 0
   kollabierte (leere graue Fläche). Als Flex-Spalte trägt der Wrapper die Höhe,
   die Karte nimmt den Rest, der Hinweis bleibt darunter. */
.pp-geo { display: flex; flex-direction: column; height: 100%; min-height: 0;
  border: 1px solid var(--pp-border-subtle); border-radius: var(--pp-radius-ui);
  overflow: hidden; background: var(--pp-bg-surface); }
.pp-geo__map { width: 100%; flex: 1 1 auto; min-height: 0; background: var(--pp-bg-base); z-index: 0; }
.pp-geo__map :deep(.leaflet-container) { font: inherit; background: var(--pp-bg-base); }
.pp-geo__map.is-fs { position: fixed; inset: 0; height: 100vh !important; width: 100vw;
  border-radius: 0; z-index: 2000; }
.pp-geo__hint { margin: 0; padding: var(--pp-space-2) var(--pp-space-3);
  border-top: 1px solid var(--pp-border-subtle); font-size: 10.5px; color: var(--pp-text-tertiary); }

/* Endmast-Marker (divIcon-Inhalt liegt außerhalb des scoped-Bereichs → :deep). */
.pp-geo__map :deep(.pp-geo-mast) { display: flex; align-items: center; justify-content: center;
  width: 22px; height: 22px; border: 2px solid var(--pp-brand-primary); border-radius: var(--pp-radius-full);
  background: var(--pp-bg-surface); font-size: 12px; line-height: 1; color: var(--pp-brand-primary);
  box-shadow: var(--pp-shadow-sm); }
.pp-geo__map :deep(.pp-geo-cluster) { display: flex; align-items: center; justify-content: center;
  width: 36px; height: 36px; border-radius: var(--pp-radius-full); background: var(--pp-brand-primary);
  color: var(--pp-text-on-accent); font-weight: var(--pp-weight-bold); font-size: 14px;
  border: 2px solid var(--pp-text-on-accent); box-shadow: var(--pp-shadow-md); }
.pp-geo__map :deep(.pp-geo__span) { background: color-mix(in srgb, var(--pp-bg-surface) 90%, transparent);
  border: 1px solid var(--pp-border-subtle); border-radius: 3px; padding: 0 4px;
  font-weight: var(--pp-weight-bold); font-size: 9.5px; color: var(--pp-text-primary); box-shadow: none; }
.pp-geo__map :deep(.pp-geo__span::before) { display: none; }
.pp-geo__map :deep(.pp-geo-ctl) { background: transparent; border: 0; box-shadow: none; }
.pp-geo__map :deep(.pp-geo-ctl__btn) { display: flex !important; align-items: center; justify-content: center;
  width: 30px; height: 30px; background: var(--pp-bg-surface); color: var(--pp-brand-primary);
  font-size: 16px; font-weight: var(--pp-weight-bold); text-decoration: none; }
.pp-geo__map :deep(.pp-geo-ctl__btn:hover) { background: var(--pp-bg-hover); }
</style>
