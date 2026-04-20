<!--
  ProjectMap — redesigned per Shneiderman & Nielsen heuristics
  =============================================================
  H1: Visibility — loading state, marker count, legend
  H3: Feedback — hover highlights, click shows popup
  H5: Error prevention — graceful fallback for missing coords
  H6: Recognition — color legend always visible
  H8: Aesthetic & minimalist — clean map with minimal chrome
  H10: Help — empty state explains what's needed
-->

<template>
  <div class="relative">
    <!-- H1: Visibility — loading overlay -->
    <div v-if="loading" class="absolute inset-0 z-20 flex items-center justify-center rounded-lg bg-white/80">
      <div class="flex flex-col items-center gap-2">
        <div class="h-6 w-6 animate-spin rounded-full border-2 border-gray-200 border-t-lcs-secondary" />
        <span class="text-xs text-gray-500">{{ __('Loading map...') }}</span>
      </div>
    </div>

    <!-- H10: Help — empty state with guidance -->
    <div v-if="!loading && !projects.length" class="flex flex-col items-center justify-center rounded-lg border border-dashed border-gray-200 bg-gray-50/50 py-12">
      <FeatherIcon name="map-pin" class="h-8 w-8 text-gray-300" />
      <p class="mt-3 text-sm text-gray-500">{{ __('No projects with location data available.') }}</p>
      <p class="mt-1 text-xs text-gray-400">{{ __('Assign countries to projects to see them on the map.') }}</p>
    </div>

    <!-- Map container -->
    <div v-show="projects.length" class="relative">
      <div ref="mapContainer" class="h-96 w-full rounded-lg border" />

      <!-- H6: Recognition — phase color legend overlay -->
      <div class="absolute bottom-3 left-3 z-10 rounded-lg border bg-white/95 px-3 py-2 shadow-sm backdrop-blur-sm">
        <div class="mb-1 text-[10px] font-semibold uppercase tracking-wide text-gray-400">{{ __('Phase') }}</div>
        <div class="flex flex-wrap gap-x-3 gap-y-1">
          <span
            v-for="(color, phase) in phaseColors"
            :key="phase"
            class="flex items-center gap-1 text-[11px] text-gray-600"
          >
            <span class="h-2.5 w-2.5 rounded-full border border-white shadow-sm" :style="{ backgroundColor: color }" />
            {{ __(phase) }}
          </span>
        </div>
      </div>

      <!-- H1: Visibility — marker count -->
      <div class="absolute right-3 top-3 z-10 rounded-md bg-white/90 px-2 py-1 text-xs text-gray-500 shadow-sm backdrop-blur-sm">
        {{ projects.length }} {{ __('locations') }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, onUnmounted } from 'vue'
import { FeatherIcon } from 'frappe-ui'

const props = defineProps({
  projects: { type: Array, default: () => [] },
})

const mapContainer = ref(null)
const loading = ref(true)
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
  if (!props.projects.length) {
    loading.value = false
    return
  }
  try {
    const L = await import('leaflet')
    await import('leaflet/dist/leaflet.css')

    map = L.map(mapContainer.value, {
      zoomControl: true,
      attributionControl: true,
    }).setView([47.0, 13.0], 3)

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap',
      maxZoom: 18,
    }).addTo(map)

    renderMarkers(L)
  } catch (err) {
    console.error('Map initialization failed:', err)
  } finally {
    loading.value = false
  }
})

function renderMarkers(L) {
  // Clean existing markers
  markers.forEach((m) => map.removeLayer(m))
  markers = []

  props.projects.forEach((p) => {
    if (!p.latitude || !p.longitude) return
    const color = phaseColors[p.phase] || '#6b7280'

    const icon = L.divIcon({
      className: 'lcs-map-marker',
      html: `<div style="background:${color};width:14px;height:14px;border-radius:50%;border:2.5px solid white;box-shadow:0 1px 4px rgba(0,0,0,.25);transition:transform 0.15s" onmouseover="this.style.transform='scale(1.3)'" onmouseout="this.style.transform='scale(1)'"></div>`,
      iconSize: [14, 14],
    })

    const marker = L.marker([p.latitude, p.longitude], { icon })

    // H3: Feedback — rich popup with clear information hierarchy
    const valueStr = p.estimated_value
      ? `<div style="margin-top:6px;font-weight:600;color:#0B3A6F">&euro; ${Number(p.estimated_value).toLocaleString('de-DE')}</div>`
      : ''
    const probStr = p.probability
      ? `<div style="margin-top:2px;font-size:11px;color:#666">Probability: ${Math.round(p.probability)}%</div>`
      : ''

    marker.bindPopup(`
      <div style="font-family:Inter,system-ui,sans-serif;min-width:160px;padding:4px 0">
        <div style="font-weight:600;font-size:13px;color:#111">${p.project_name || ''}</div>
        <div style="font-size:11px;color:#888;margin-top:2px">${p.project_number || ''} &middot; ${p.project_type || ''}</div>
        <div style="margin-top:6px;display:flex;align-items:center;gap:4px">
          <span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:${color}"></span>
          <span style="font-size:12px;color:#444">${p.phase || ''}</span>
        </div>
        ${valueStr}
        ${probStr}
        <a href="/crm/projects/${p.name}" style="display:block;margin-top:8px;font-size:11px;color:#1E78C2;text-decoration:none;font-weight:500">${__('Open project')} &rarr;</a>
      </div>
    `, { maxWidth: 240 })

    marker.addTo(map)
    markers.push(marker)
  })

  // Auto-fit bounds with padding
  if (markers.length) {
    const group = L.featureGroup(markers)
    map.fitBounds(group.getBounds().pad(0.15))
  }
}

watch(
  () => props.projects,
  async (newProjects) => {
    if (!newProjects.length) {
      loading.value = false
      return
    }
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
