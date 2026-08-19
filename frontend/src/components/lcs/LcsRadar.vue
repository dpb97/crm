<!--
  LcsRadar — kompaktes SVG-Radar (Netzdiagramm) für die Opportunity-Matrix.
  Zeigt N Achsen (0–100) live als gefülltes Polygon. Rein darstellend; die
  Werte kommen als modelValue (key → 0..100) von der Card/dem Dialog.
-->
<template>
  <svg :viewBox="`0 0 ${W} ${H}`" class="lr" role="img">
    <polygon v-for="r in rings" :key="'g' + r" :points="ringPoints(r)" class="lr-grid" />
    <line v-for="(a, i) in axes" :key="'a' + a.key" :x1="cx" :y1="cy" :x2="pt(i, 1).x" :y2="pt(i, 1).y" class="lr-axis" />
    <polygon :points="valuePoints" class="lr-fill" />
    <circle v-for="(a, i) in axes" :key="'d' + a.key" :cx="valPt(i).x" :cy="valPt(i).y" r="3" class="lr-dot" />
    <text
      v-for="(a, i) in axes"
      :key="'l' + a.key"
      :x="labelPt(i).x"
      :y="labelPt(i).y"
      class="lr-label"
      :text-anchor="anchor(i)"
    >{{ a.label }}<tspan class="lr-lval" :x="labelPt(i).x" dy="12">{{ val(a.key) }}</tspan></text>
  </svg>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  axes: { type: Array, required: true },        // [{ key, label }]
  modelValue: { type: Object, default: () => ({}) },
})

const W = 260, H = 220
const cx = W / 2, cy = H / 2, R = 66
const rings = [0.25, 0.5, 0.75, 1]

const n = computed(() => props.axes.length || 1)
function angle(i) { return (-90 + (i * 360) / n.value) * (Math.PI / 180) }
function pt(i, frac) { return { x: cx + R * frac * Math.cos(angle(i)), y: cy + R * frac * Math.sin(angle(i)) } }
function val(key) { const v = Number(props.modelValue?.[key]); return Number.isFinite(v) ? Math.max(0, Math.min(100, v)) : 0 }
function valPt(i) { return pt(i, val(props.axes[i].key) / 100) }
function labelPt(i) { return pt(i, 1.28) }
function anchor(i) {
  const c = Math.cos(angle(i))
  return c > 0.3 ? 'start' : c < -0.3 ? 'end' : 'middle'
}
function ringPoints(frac) { return props.axes.map((_, i) => { const p = pt(i, frac); return `${p.x},${p.y}` }).join(' ') }
const valuePoints = computed(() => props.axes.map((_, i) => { const p = valPt(i); return `${p.x},${p.y}` }).join(' '))
</script>

<style scoped>
.lr { width: 100%; height: auto; display: block; overflow: visible; }
.lr-grid { fill: none; stroke: var(--pp-border-subtle); stroke-width: 1; }
.lr-axis { stroke: var(--pp-border-default); stroke-width: 1; }
.lr-fill { fill: color-mix(in oklab, var(--pp-brand-primary) 22%, transparent); stroke: var(--pp-brand-primary); stroke-width: 1.5; }
.lr-dot { fill: var(--pp-brand-primary); }
.lr-label { font-size: 10px; font-weight: var(--pp-weight-medium); fill: var(--pp-text-secondary); }
.lr-lval { font-size: 10px; font-weight: var(--pp-weight-bold); fill: var(--pp-brand-primary); }
</style>
