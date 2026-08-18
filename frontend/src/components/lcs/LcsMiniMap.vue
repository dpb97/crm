<!--
  LcsMiniMap — a lightweight, non-interactive map thumbnail for the Pilot cards.
  Renders static OpenStreetMap tiles centered on lat/lon with a pin, WITHOUT a
  Leaflet instance per card (the Pilot list can show 20+ cards). Pure <img>
  tiles positioned by slippy-map math + a centered marker. Decorative zoom/expand
  chrome mirrors the klickdummy look; expand emits "open".
-->
<template>
  <div ref="box" class="lmm">
    <div v-if="!hasCoords" class="lmm-empty">{{ __('No geodata') }}</div>
    <template v-else>
      <img
        v-for="t in tiles"
        :key="t.key"
        class="lmm-tile"
        :src="t.url"
        :style="{ left: t.left + 'px', top: t.top + 'px' }"
        alt=""
        loading="lazy"
        draggable="false"
      />
      <span class="lmm-pin" :style="{ left: size.w / 2 + 'px', top: size.h / 2 + 'px' }" />
      <div class="lmm-zoom">
        <button type="button" class="lmm-zbtn" @click.stop="zoomIn">+</button>
        <button type="button" class="lmm-zbtn" @click.stop="zoomOut">−</button>
      </div>
      <button type="button" class="lmm-expand" :title="__('Open')" @click.stop="$emit('open')">
        <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M15 3h6v6M9 21H3v-6M21 3l-7 7M3 21l7-7"/></svg>
      </button>
    </template>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount, watch } from 'vue'

const props = defineProps({
  lat: { type: [Number, String], default: null },
  lon: { type: [Number, String], default: null },
  zoom: { type: Number, default: 6 },
})
defineEmits(['open'])

const TILE = 256
const box = ref(null)
const size = reactive({ w: 300, h: 180 })
const z = ref(props.zoom)
let ro = null

const latN = computed(() => Number(props.lat))
const lonN = computed(() => Number(props.lon))
const hasCoords = computed(() => Number.isFinite(latN.value) && Number.isFinite(lonN.value) && !(latN.value === 0 && lonN.value === 0))

function project(lat, lon, zoom) {
  const s = TILE * 2 ** zoom
  const x = ((lon + 180) / 360) * s
  const rad = (lat * Math.PI) / 180
  const y = ((1 - Math.log(Math.tan(rad) + 1 / Math.cos(rad)) / Math.PI) / 2) * s
  return { x, y }
}

const tiles = computed(() => {
  if (!hasCoords.value) return []
  const zoom = z.value
  const n = 2 ** zoom
  const { x: cx, y: cy } = project(latN.value, lonN.value, zoom)
  const originX = cx - size.w / 2
  const originY = cy - size.h / 2
  const tx0 = Math.floor(originX / TILE)
  const tx1 = Math.floor((originX + size.w) / TILE)
  const ty0 = Math.floor(originY / TILE)
  const ty1 = Math.floor((originY + size.h) / TILE)
  const out = []
  for (let tx = tx0; tx <= tx1; tx++) {
    for (let ty = ty0; ty <= ty1; ty++) {
      if (ty < 0 || ty >= n) continue
      const wrappedX = ((tx % n) + n) % n
      out.push({
        key: `${zoom}/${tx}/${ty}`,
        url: `https://tile.openstreetmap.org/${zoom}/${wrappedX}/${ty}.png`,
        left: Math.round(tx * TILE - originX),
        top: Math.round(ty * TILE - originY),
      })
    }
  }
  return out
})

function zoomIn() { z.value = Math.min(15, z.value + 1) }
function zoomOut() { z.value = Math.max(2, z.value - 1) }

function measure() {
  if (!box.value) return
  size.w = box.value.clientWidth || 300
  size.h = box.value.clientHeight || 180
}
onMounted(() => {
  measure()
  ro = new ResizeObserver(measure)
  ro.observe(box.value)
})
watch(() => [props.lat, props.lon, props.zoom], () => { z.value = props.zoom })
onBeforeUnmount(() => { if (ro) ro.disconnect() })
</script>

<style scoped>
.lmm { position: relative; width: 100%; height: 100%; min-height: 150px; overflow: hidden;
  background: var(--pp-bg-sunken, #e6e9ee); border-radius: var(--pp-radius-ui); }
.lmm-tile { position: absolute; width: 256px; height: 256px; user-select: none; }
.lmm-empty { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center;
  font-size: 11px; color: var(--pp-text-tertiary); }
.lmm-pin { position: absolute; width: 14px; height: 14px; transform: translate(-50%, -100%);
  border-radius: 50% 50% 50% 0; background: var(--pp-brand-primary); border: 2px solid #fff;
  box-shadow: 0 1px 3px rgba(0,0,0,0.4); rotate: 45deg; }
.lmm-zoom { position: absolute; left: 8px; top: 8px; display: flex; flex-direction: column;
  border-radius: 4px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.3); }
.lmm-zbtn { appearance: none; width: 26px; height: 26px; border: 0; cursor: pointer;
  background: #fff; color: #333; font-size: 16px; line-height: 1; font-weight: 600; }
.lmm-zbtn + .lmm-zbtn { border-top: 1px solid #ddd; }
.lmm-zbtn:hover { background: #f2f2f2; }
.lmm-expand { position: absolute; right: 8px; bottom: 8px; width: 26px; height: 26px;
  display: flex; align-items: center; justify-content: center; appearance: none; border: 0; cursor: pointer;
  background: #fff; color: #333; border-radius: 4px; box-shadow: 0 1px 3px rgba(0,0,0,0.3); }
.lmm-expand:hover { background: #f2f2f2; }
</style>
