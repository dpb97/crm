<!--
  ProjectMap
  ==========
  Interactive Leaflet map showing project markers colored by phase.
  Click a marker popup link to navigate to the project detail page.

  Props: `projects` — array of project objects with latitude, longitude,
         project_name, project_number, project_type, phase, estimated_value, name.
-->

<template>
  <div ref="mapContainer" class="h-96 w-full rounded-lg border" />
</template>

<script setup>
import { ref, onMounted, watch, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  projects: { type: Array, default: () => [] },
})

const router = useRouter()
const mapContainer = ref(null)
let map = null
let markers = []

const phaseColors = {
  Inquiry: '#0ea5e9',
  Offer: '#f59e0b',
  Negotiation: '#f97316',
  Order: '#22c55e',
  Execution: '#0B3A6F',
  Completed: '#6b7280',
  Lost: '#ef4444',
}

onMounted(async () => {
  const L = await import('leaflet')
  await import('leaflet/dist/leaflet.css')

  map = L.map(mapContainer.value).setView([47.0, 13.0], 3)
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap',
    maxZoom: 18,
  }).addTo(map)

  renderMarkers(L)
})

function renderMarkers(L) {
  markers.forEach((m) => map.removeLayer(m))
  markers = []

  props.projects.forEach((p) => {
    if (!p.latitude || !p.longitude) return
    const color = phaseColors[p.phase] || '#6b7280'
    const icon = L.divIcon({
      className: 'lcs-map-marker',
      html: `<div style="background:${color};width:12px;height:12px;border-radius:50%;border:2px solid white;box-shadow:0 1px 3px rgba(0,0,0,.3)"></div>`,
      iconSize: [12, 12],
    })
    const marker = L.marker([p.latitude, p.longitude], { icon })
    const valueStr = p.estimated_value
      ? `<div class="mt-1 font-medium">&euro; ${Number(p.estimated_value).toLocaleString('de-DE')}</div>`
      : ''
    marker.bindPopup(`
      <div class="text-sm">
        <div class="font-semibold">${p.project_name || ''}</div>
        <div class="text-xs text-gray-500">${p.project_number || ''} &middot; ${p.project_type || ''}</div>
        <div class="mt-1"><span style="color:${color}">&bull;</span> ${p.phase || ''}</div>
        ${valueStr}
        <a href="/crm/projects/${p.name}" class="mt-2 block text-xs text-blue-600 hover:underline">${__('Open')} &rarr;</a>
      </div>
    `)
    marker.addTo(map)
    markers.push(marker)
  })

  if (markers.length) {
    const group = L.featureGroup(markers)
    map.fitBounds(group.getBounds().pad(0.1))
  }
}

watch(
  () => props.projects,
  async () => {
    if (map) {
      const L = await import('leaflet')
      renderMarkers(L)
    }
  },
  { deep: true },
)

onUnmounted(() => {
  if (map) {
    map.remove()
    map = null
  }
})
</script>

<style>
.lcs-map-marker {
  background: transparent !important;
  border: none !important;
}
</style>
