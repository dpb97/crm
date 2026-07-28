<!--
  TerritoryMap — real Leaflet world map for the Market Assignment page.
  =====================================================================
  Replaces the stylized PpMap: markers sit on real geography (server-provided
  lat/lon per territory) and are coloured by the responsible sales manager's
  tone (kind). Click a marker → emits marker-click(id). OSM / satellite base
  layers like ProjectMap. Overlapping coordinates fan out in a small spiral.
-->
<template>
  <div class="relative h-full">
    <div v-if="loading" class="absolute inset-0 z-20 flex items-center justify-center rounded-lg bg-white/80">
      <div class="h-6 w-6 animate-spin rounded-full border-2 border-gray-200 border-t-lcs-primary" />
    </div>
    <div ref="mapContainer" :class="['w-full rounded-lg border', heightClass]" />
  </div>
</template>

<script setup>
import { ref, onMounted, watch, onUnmounted, nextTick } from 'vue'

const props = defineProps({
  markers: { type: Array, default: () => [] }, // [{ id, lat, lon, label, kind }]
  // Territory areas drawn as filled country polygons, coloured by sales manager.
  polygons: { type: Array, default: () => [] }, // [{ id, countries:[name], kind, label }]
  // Project locations overlaid on the polygons (Markteinteilung shows projects too).
  pins: { type: Array, default: () => [] }, // [{ t, ll:[lat,lng] }]
  activeId: { type: [String, Number, null], default: null },
  heightClass: { type: String, default: 'h-full' },
})
const emit = defineEmits(['marker-click'])

const mapContainer = ref(null)
const loading = ref(true)
let map = null
let layers = []
let polyLayers = []
let pinLayer = []

// Sales-manager tone → colour. CSS var() resolves inside the divIcon DOM style,
// so markers match the legend tones exactly (SSOT --pp-*).
const TONE_VAR = {
  brand: 'var(--pp-brand-primary)',
  info: 'var(--pp-state-info)',
  success: 'var(--pp-state-success)',
  warning: 'var(--pp-state-warning)',
  danger: 'var(--pp-state-danger)',
  neutral: 'var(--pp-text-tertiary)',
}
function toneColor(kind) {
  return TONE_VAR[kind] || TONE_VAR.neutral
}

async function ensureMap() {
  const L = await import('leaflet')
  if (map) return L
  await import('leaflet/dist/leaflet.css')
  map = L.map(mapContainer.value, { zoomControl: true, attributionControl: true }).setView([30, 10], 2)
  const street = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap',
    maxZoom: 19,
  })
  const satellite = L.tileLayer(
    'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    { attribution: 'Tiles &copy; Esri — World Imagery', maxZoom: 19 },
  )
  street.addTo(map)
  L.control
    .layers({ [__('Map')]: street, [__('Satellite')]: satellite }, {}, { position: 'topright', collapsed: false })
    .addTo(map)
  return L
}

// Frappe country names → the geojson's `name` property where they differ.
const COUNTRY_ALIAS = {
  'United States': 'United States of America',
  'Serbia': 'Republic of Serbia',
  'Tanzania': 'United Republic of Tanzania',
  'North Macedonia': 'Macedonia',
}
let countryIndex = null
async function loadCountryIndex() {
  if (countryIndex) return countryIndex
  const geo = (await import('@/assets/geo/countries.geo.json')).default
  countryIndex = new Map()
  geo.features.forEach((f) => countryIndex.set(f.properties.name, f))
  return countryIndex
}
function featureFor(name, idx) {
  return idx.get(name) || idx.get(COUNTRY_ALIAS[name]) || null
}

// Draw each territory as its member countries' filled polygons, coloured by the
// responsible sales manager's tone. Click → emits marker-click(id) like a marker.
async function renderPolygons(L) {
  polyLayers.forEach((l) => map.removeLayer(l))
  polyLayers = []
  if (!props.polygons?.length) return
  const idx = await loadCountryIndex()
  const bounds = []
  props.polygons.forEach((terr) => {
    const feats = (terr.countries || []).map((c) => featureFor(c, idx)).filter(Boolean)
    if (!feats.length) return
    const color = toneColor(terr.kind)
    const active = props.activeId != null && terr.id === props.activeId
    const base = active ? 0.5 : 0.32
    const gj = L.geoJSON(
      { type: 'FeatureCollection', features: feats },
      { style: { color, weight: active ? 2.5 : 1, opacity: 0.9, fillColor: color, fillOpacity: base } },
    )
    gj.bindTooltip(terr.label || String(terr.id), { sticky: true })
    gj.on('click', () => emit('marker-click', terr.id))
    gj.on('mouseover', () => gj.setStyle({ fillOpacity: 0.55 }))
    gj.on('mouseout', () => gj.setStyle({ fillOpacity: base }))
    gj.addTo(map)
    polyLayers.push(gj)
    bounds.push(gj.getBounds())
  })
  if (bounds.length) {
    let b = bounds[0]
    for (let i = 1; i < bounds.length; i++) b = b.extend(bounds[i])
    map.fitBounds(b, { padding: [30, 30], maxZoom: 6 })
  }
}

// Project locations as small dots over the territory polygons.
function renderPins(L) {
  pinLayer.forEach((l) => map.removeLayer(l))
  pinLayer = []
  props.pins.forEach((p) => {
    const ll = p.ll || (p.lat != null ? [p.lat, p.lon] : null)
    if (!ll) return
    const m = L.circleMarker(ll, {
      radius: 5, weight: 2, color: '#fff',
      fillColor: 'var(--pp-brand-primary)', fillOpacity: 1,
    })
    if (p.t) m.bindTooltip(String(p.t), { direction: 'top' })
    m.addTo(map)
    pinLayer.push(m)
  })
}

function renderMarkers(L) {
  layers.forEach((m) => map.removeLayer(m))
  layers = []

  const coordSeen = {}
  const bounds = []

  props.markers.forEach((mk) => {
    if (mk.lat == null || mk.lon == null) return
    const active = props.activeId != null && mk.id === props.activeId
    const color = toneColor(mk.kind)

    // Fan out markers sharing the exact same coordinate (spiral).
    const key = `${mk.lat},${mk.lon}`
    const dup = coordSeen[key] || 0
    coordSeen[key] = dup + 1
    let lat = mk.lat
    let lon = mk.lon
    if (dup > 0) {
      const angle = dup * 2.4
      const radius = 0.6 * Math.sqrt(dup)
      lat += radius * Math.cos(angle)
      lon += radius * Math.sin(angle)
    }

    const size = active ? 28 : 20
    const ring = active ? '4px solid var(--pp-brand-primary)' : '3px solid white'
    const icon = L.divIcon({
      className: 'lcs-territory-marker',
      html: `<div style="background:${color};width:${size}px;height:${size}px;border-radius:50%;border:${ring};box-shadow:0 2px 6px rgba(0,0,0,.3);transition:transform .15s" onmouseover="this.style.transform='scale(1.35)'" onmouseout="this.style.transform='scale(1)'"></div>`,
      iconSize: [size, size],
    })
    const marker = L.marker([lat, lon], { icon, zIndexOffset: active ? 1000 : 0 })
    marker.bindPopup(
      `<div style="font-family:Inter,system-ui,sans-serif;min-width:120px;padding:2px 0">
         <div style="display:flex;align-items:center;gap:6px">
           <span style="display:inline-block;width:9px;height:9px;border-radius:50%;background:${color}"></span>
           <span style="font-size:13px;font-weight:600;color:var(--pp-text-primary)">${mk.label || mk.id}</span>
         </div>
       </div>`,
    )
    marker.on('click', () => emit('marker-click', mk.id))
    marker.addTo(map)
    layers.push(marker)
    bounds.push([lat, lon])
  })

  if (bounds.length) {
    map.fitBounds(L.latLngBounds(bounds), { padding: [40, 40], maxZoom: 6 })
  }
}

async function build() {
  try {
    const L = await ensureMap()
    await nextTick()
    map.invalidateSize()
    renderMarkers(L)
    await renderPolygons(L)
    renderPins(L)
  } catch (err) {
    console.error('Territory map init failed:', err)
  } finally {
    loading.value = false
  }
}

onMounted(build)

watch(
  () => [props.markers, props.polygons, props.pins],
  async () => {
    if (!map) { await build(); return }
    const L = await import('leaflet')
    map.invalidateSize()
    renderMarkers(L)
    await renderPolygons(L)
    renderPins(L)
  },
  { deep: true },
)
watch(
  () => props.activeId,
  async () => {
    if (!map) return
    const L = await import('leaflet')
    renderMarkers(L)
    await renderPolygons(L)
  },
)

onUnmounted(() => {
  if (map) { map.remove(); map = null }
})
</script>
