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
  activeId: { type: [String, Number, null], default: null },
  heightClass: { type: String, default: 'h-full' },
})
const emit = defineEmits(['marker-click'])

const mapContainer = ref(null)
const loading = ref(true)
let map = null
let layers = []

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
  } catch (err) {
    console.error('Territory map init failed:', err)
  } finally {
    loading.value = false
  }
}

onMounted(build)

watch(
  () => props.markers,
  async () => {
    if (!map) { await build(); return }
    const L = await import('leaflet')
    map.invalidateSize()
    renderMarkers(L)
  },
  { deep: true },
)
watch(
  () => props.activeId,
  async () => {
    if (!map) return
    const L = await import('leaflet')
    renderMarkers(L)
  },
)

onUnmounted(() => {
  if (map) { map.remove(); map = null }
})
</script>
