// Shell-wide function bar (klickdummy „Funktionsbar"): a page registers its
// action groups; the burger in the PpInspector header (v-model:funcbarOpen)
// toggles the bar, which DesktopLayout renders over the top of the canvas.
// Singleton module-level state so the inspector burger, the bar and the page
// all share ONE reactive source.
import { ref, computed } from 'vue'

const open = ref(false)
// { aktionen?, werkzeuge?, ausgabe?, abstiege? } — arrays of { id?, label, primary? }
const groups = ref(null)
let handler = null // (id) => void

const available = computed(() =>
  !!(groups.value && Object.values(groups.value).some((a) => Array.isArray(a) && a.length)),
)

export function usePilandaFuncbar() {
  // A page registers its bar on mount and clears it on unmount.
  function registerFuncbar(pageGroups, onAction) {
    groups.value = pageGroups || null
    handler = typeof onAction === 'function' ? onAction : null
    open.value = false
  }
  function clearFuncbar() {
    groups.value = null
    handler = null
    open.value = false
  }
  // Called by the rendered PpFunctionBar; runs the page handler then closes.
  function runAction(id) {
    if (handler) handler(id)
    open.value = false
  }
  return { open, groups, available, registerFuncbar, clearFuncbar, runAction }
}
