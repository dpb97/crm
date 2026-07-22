// Shared state for the Pilanda inspector panel (right side, Pilanda mode).
// Driven by two sources, exactly like the Desk shell (PilandaDesk.vue):
//   1) a sidebar item's @inspect  -> show that nav item's spec
//   2) a page dispatching window `pilanda:inspect` with
//      { kind:'spec', item } | { kind:'close' }
// Module-level singleton so the sidebar (setter) and the layout (renderer)
// share one reactive panel.
import { ref } from 'vue'

const spec = ref(null) // nav-item spec object, or null
const collapsed = ref(true) // starts closed (rail)

let _wired = false

export function usePilandaInspect() {
  function inspectItem(item) {
    if (item) {
      spec.value = item
      collapsed.value = false
    } else {
      spec.value = null
      collapsed.value = true
    }
  }
  function setCollapsed(v) {
    collapsed.value = !!v
  }

  if (!_wired && typeof window !== 'undefined') {
    _wired = true
    window.addEventListener('pilanda:inspect', (e) => {
      const d = e?.detail || {}
      if (d.kind === 'spec' && d.item) {
        spec.value = d.item
        collapsed.value = false
      } else if (d.kind === 'close') {
        spec.value = null
        collapsed.value = true
      }
    })
  }

  return { spec, collapsed, inspectItem, setCollapsed }
}
