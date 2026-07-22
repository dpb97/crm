// Shared state for the Pilanda inspector panel (right side, Pilanda mode).
// Driven by three sources, all feeding the SAME docked panel:
//   1) a sidebar item's @inspect  -> show that nav item's `spec` (built-in
//      "Spezifikation" panel of PpInspector).
//   2) a page calling `inspectNode(view)` -> show a rich, entity-specific
//      `view` (badges/meta/sections/action) rendered via PpInspectorNodeView
//      into PpInspector's default slot. Used e.g. by the Network graph.
//   3) a page calling `inspectPanel({ component, props, on, title })` -> mount
//      an arbitrary (interactive) component into the inspector's default slot.
//      Used e.g. by the Sales Projects list (ProjectInspector) so its editable
//      panel lives in the docked inspector instead of a modal overlay.
//   4) a page dispatching window `pilanda:inspect` with
//      { kind:'spec', item } | { kind:'node', view } | { kind:'close' }.
// Module-level singleton so the setters (sidebar / pages) and the layout
// (renderer) share one reactive panel. `spec`, `view` and `panel` are mutually
// exclusive — setting one clears the others.
import { ref, markRaw } from 'vue'

const spec = ref(null)  // nav-item spec object (built-in panel), or null
const view = ref(null)  // rich node view (custom slot), or null
const panel = ref(null) // { component, props, on, title } dynamic component, or null
const collapsed = ref(true) // starts closed (rail)

let _wired = false

export function usePilandaInspect() {
  // Nav item -> built-in spec panel.
  function inspectItem(item) {
    if (item) {
      spec.value = item
      view.value = null
      panel.value = null
      collapsed.value = false
    } else {
      spec.value = null
      collapsed.value = true
    }
  }

  // Rich entity view -> custom slot renderer (PpInspectorNodeView).
  function inspectNode(v) {
    if (v) {
      view.value = v
      spec.value = null
      panel.value = null
      collapsed.value = false
    } else {
      view.value = null
      collapsed.value = true
    }
  }

  // Arbitrary component -> mounted into the inspector's default slot.
  function inspectPanel(p) {
    if (p && p.component) {
      panel.value = { ...p, component: markRaw(p.component) }
      spec.value = null
      view.value = null
      collapsed.value = false
    } else {
      panel.value = null
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
        view.value = null
        panel.value = null
        collapsed.value = false
      } else if (d.kind === 'node' && d.view) {
        view.value = d.view
        spec.value = null
        panel.value = null
        collapsed.value = false
      } else if (d.kind === 'close') {
        spec.value = null
        view.value = null
        panel.value = null
        collapsed.value = true
      }
    })
  }

  return { spec, view, panel, collapsed, inspectItem, inspectNode, inspectPanel, setCollapsed }
}
