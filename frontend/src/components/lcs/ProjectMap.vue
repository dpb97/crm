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
  <!-- h-full lets a page pass heightClass="h-full" to fill available space;
       with an indefinite parent height it harmlessly falls back to content. -->
  <div class="relative h-full">
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
    <div v-show="projects.length" class="relative h-full">
      <div ref="mapContainer" :class="['w-full rounded-lg border', heightClass]" />

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
      <div class="absolute bottom-3 right-3 z-10 rounded-md bg-white/90 px-2 py-1 text-xs text-gray-500 shadow-sm backdrop-blur-sm">
        {{ projects.length }} {{ __('locations') }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, onUnmounted, nextTick } from 'vue'
import { FeatherIcon } from 'frappe-ui'

const props = defineProps({
  projects: { type: Array, default: () => [] },
  // Tailwind height class for the map container. Default keeps the
  // embedded-widget size; pages can pass e.g. `h-[calc(100vh-12rem)]`
  // for a full-bleed map.
  heightClass: { type: String, default: 'h-96' },
})

const mapContainer = ref(null)
const loading = ref(true)
let map = null
let markers = []

// Diverging Phasen-Palette (unterscheidbare Datentoene, bewusst als Hex).
// Alle Werte landen in Style-Bindings bzw. inline-style-HTML-Strings der
// Leaflet-Marker/Popups (DOM-Elemente) -> var() loest hier auf, daher der
// Marken-Ton 'Execution' als var() auf Brand-Cyan (SSOT --pp-brand-primary;
// vormals Alt-Navy).
const phaseColors = {
  Qualified: '#0ea5e9',
  Budget: '#14b8a6',
  Richtpreis: '#8b5cf6',
  Offer: '#f59e0b',
  Negotiation: '#f97316',
  Won: '#22c55e',
  Execution: 'var(--pp-brand-primary)',
  Completed: '#6b7280',
  Lost: '#ef4444',
}

// Create the Leaflet map once. Safe to call before projects arrive — the
// container lives under v-show (kept in the DOM), so the map can be built and
// resized once it becomes visible.
async function ensureMap() {
  const L = await import('leaflet')
  if (map) return L
  await import('leaflet/dist/leaflet.css')
  map = L.map(mapContainer.value, {
    zoomControl: true,
    attributionControl: true,
  }).setView([47.0, 13.0], 3)
  // Base layers — switchable (street map vs. satellite imagery).
  const street = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap',
    maxZoom: 19,
  })
  const satellite = L.tileLayer(
    'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    { attribution: 'Tiles &copy; Esri — World Imagery', maxZoom: 19 },
  )
  street.addTo(map) // default = street map
  L.control
    .layers({ [__('Map')]: street, [__('Satellite')]: satellite }, {}, { position: 'topright', collapsed: false })
    .addTo(map)
  return L
}

onMounted(async () => {
  try {
    if (props.projects.length) {
      const L = await ensureMap()
      await nextTick()
      map.invalidateSize()
      renderMarkers(L)
    }
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

  // Coordinates are country centroids — spread markers sharing the exact
  // same point in a small spiral so all of them stay visible/clickable
  const coordSeen = {}

  props.projects.forEach((p) => {
    if (!p.latitude || !p.longitude) return
    const color = phaseColors[p.phase] || '#6b7280'

    const coordKey = `${p.latitude},${p.longitude}`
    const dupIndex = coordSeen[coordKey] || 0
    coordSeen[coordKey] = dupIndex + 1
    let lat = p.latitude
    let lng = p.longitude
    if (dupIndex > 0) {
      const angle = dupIndex * 2.4 // golden-angle spiral
      const radius = 0.25 * Math.sqrt(dupIndex)
      lat += radius * Math.cos(angle)
      lng += radius * Math.sin(angle)
    }

    const icon = L.divIcon({
      className: 'lcs-map-marker',
      html: `<div style="background:${color};width:22px;height:22px;border-radius:50%;border:3px solid white;box-shadow:0 2px 6px rgba(0,0,0,.3);transition:transform 0.15s" onmouseover="this.style.transform='scale(1.45)'" onmouseout="this.style.transform='scale(1)'"></div>`,
      iconSize: [22, 22],
    })

    const marker = L.marker([lat, lng], { icon })

    // H3: Feedback — rich popup with clear information hierarchy
    const valueStr = p.estimated_value
      ? `<div style="margin-top:6px;font-weight:600;color:var(--pp-brand-primary)">&euro; ${Number(p.estimated_value).toLocaleString('de-DE')}</div>`
      : ''
    const probStr = p.probability
      ? `<div style="margin-top:2px;font-size:11px;color:var(--pp-text-secondary)">Probability: ${Math.round(p.probability)}%</div>`
      : ''

    marker.bindPopup(`
      <div style="font-family:Inter,system-ui,sans-serif;min-width:160px;padding:4px 0">
        <div style="font-weight:600;font-size:13px;color:var(--pp-text-primary)">${p.project_name || ''}</div>
        <div style="font-size:11px;color:var(--pp-text-tertiary);margin-top:2px">${p.project_number || ''} &middot; ${p.project_type || ''}</div>
        <div style="margin-top:6px;display:flex;align-items:center;gap:4px">
          <span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:${color}"></span>
          <span style="font-size:12px;color:var(--pp-text-secondary)">${p.phase || ''}</span>
        </div>
        ${valueStr}
        ${probStr}
        <a href="/crm/projects/${p.name}" style="display:block;margin-top:8px;font-size:11px;color:var(--pp-text-link);text-decoration:none;font-weight:500">${__('Open project')} &rarr;</a>
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
    try {
      // Build the map now if it wasn't created at mount (data loaded late).
      const L = await ensureMap()
      await nextTick()
      map.invalidateSize()
      renderMarkers(L)
    } catch (err) {
      console.error('Map render failed:', err)
    } finally {
      loading.value = false
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
