<!--
  PullToRefresh — mobile-only "pull down from the top to refresh" gesture.
  Mounted once globally (App.vue). When the active list page exposes a shell
  "refresh" action (useListFuncbar), pulling the scroll container down while it
  is already at the top shows a spinner and triggers that page's reload.
  No-op on desktop and on pages without a refresh action.
-->
<template>
  <transition name="ptr-fade">
    <div v-if="pull > 0 || refreshing" class="ptr" :style="{ transform: `translate(-50%, ${indicatorY}px)` }" aria-hidden="true">
      <span class="ptr-spinner" :class="{ 'is-spinning': refreshing }" :style="{ transform: `rotate(${pull * 3}deg)` }">
        <FeatherIcon name="refresh-cw" class="ptr-ic" />
      </span>
    </div>
  </transition>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { FeatherIcon } from 'frappe-ui'
import { useViewport } from '@/composables/useViewport'
import { usePilandaFuncbar } from '@/composables/usePilandaFuncbar'

const { isMobile } = useViewport()
const { groups, runAction } = usePilandaFuncbar()

// Only arm the gesture on the phone AND when the current page offers a refresh.
const hasRefresh = computed(() => !!groups.value?.aktionen?.some((a) => a.id === 'refresh'))
const active = computed(() => isMobile.value && hasRefresh.value)

const THRESHOLD = 70   // px pull needed to trigger a refresh
const MAX = 120        // px max visual pull
const pull = ref(0)
const refreshing = ref(false)
const indicatorY = computed(() => (refreshing.value ? 52 : Math.min(pull.value, MAX)) )

let startY = 0
let pulling = false
let scroller = null

function findScroller(el) {
  while (el && el !== document.body && el !== document.documentElement) {
    const s = getComputedStyle(el)
    if (/(auto|scroll)/.test(s.overflowY) && el.scrollHeight > el.clientHeight + 1) return el
    el = el.parentElement
  }
  return document.scrollingElement || document.documentElement
}

function onStart(e) {
  if (!active.value || refreshing.value || e.touches.length !== 1) { pulling = false; return }
  scroller = findScroller(e.target)
  startY = e.touches[0].clientY
  pulling = (scroller?.scrollTop || 0) <= 0
  pull.value = 0
}
function onMove(e) {
  if (!pulling) return
  const dy = e.touches[0].clientY - startY
  if (dy <= 0) { pull.value = 0; return }
  if ((scroller?.scrollTop || 0) > 0) { pulling = false; pull.value = 0; return }
  // Resist: the indicator moves slower than the finger.
  pull.value = Math.min(dy * 0.5, MAX)
  if (dy > 6 && e.cancelable) e.preventDefault() // suppress native overscroll while pulling
}
function onEnd() {
  if (!pulling) return
  pulling = false
  if (pull.value >= THRESHOLD) {
    refreshing.value = true
    try { runAction('refresh') } catch (_) { /* no-op */ }
    window.setTimeout(() => { refreshing.value = false; pull.value = 0 }, 900)
  } else {
    pull.value = 0
  }
}

onMounted(() => {
  window.addEventListener('touchstart', onStart, { passive: true })
  window.addEventListener('touchmove', onMove, { passive: false })
  window.addEventListener('touchend', onEnd, { passive: true })
  window.addEventListener('touchcancel', onEnd, { passive: true })
})
onBeforeUnmount(() => {
  window.removeEventListener('touchstart', onStart)
  window.removeEventListener('touchmove', onMove)
  window.removeEventListener('touchend', onEnd)
  window.removeEventListener('touchcancel', onEnd)
})
</script>

<style scoped>
.ptr {
  position: fixed; top: 8px; left: 50%; z-index: 2500;
  pointer-events: none; will-change: transform;
}
.ptr-spinner {
  display: inline-flex; align-items: center; justify-content: center;
  width: 38px; height: 38px; border-radius: var(--pp-radius-full);
  background: var(--pp-bg-surface); color: var(--pp-brand-primary);
  border: 1px solid var(--pp-border-default); box-shadow: var(--pp-shadow-md, 0 4px 12px rgba(0,0,0,0.15));
}
.ptr-ic { width: 18px; height: 18px; }
.ptr-spinner.is-spinning { animation: ptr-spin 0.7s linear infinite; }
@keyframes ptr-spin { to { transform: rotate(360deg); } }
.ptr-fade-enter-active, .ptr-fade-leave-active { transition: opacity .2s; }
.ptr-fade-enter-from, .ptr-fade-leave-to { opacity: 0; }
</style>
