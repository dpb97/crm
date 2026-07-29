// Shared reactive viewport width. The upstream `isMobileView` reads
// `window.innerWidth` inside a computed, which never recomputes on resize
// (no dependency changes) — so the Pilanda shell could not switch between
// desktop and mobile layouts live. This module binds ONE passive resize
// listener for the whole app lifetime and exposes a reactive width, so
// `isMobile` updates on rotation/resize without a reload.
import { ref, computed } from 'vue'

const MOBILE_BREAKPOINT = 768

const width = ref(window.innerWidth)

let _bound = false
function _ensureBound() {
  if (_bound) return
  window.addEventListener('resize', () => { width.value = window.innerWidth }, { passive: true })
  _bound = true
}

export function useViewport() {
  _ensureBound()
  return {
    viewportWidth: width,
    isMobile: computed(() => width.value < MOBILE_BREAKPOINT),
  }
}
