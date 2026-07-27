// Standard list function bar + default inspector for a Vertrieb list page.
// A page calls useListFuncbar({...}) once; it registers the shell function bar
// (burger in the inspector head) with the common actions and keeps a default
// inspector view so the burger is always present. Selection + export are opt-in.
//
//   useListFuncbar({
//     title, meaning?,            // default inspector head + one-line meaning
//     count: () => number,        // entry count for the inspector
//     reload: () => void,         // „Aktualisieren"
//     exportRows?: () => void,    // „Exportieren" (omit → no export action)
//     selectMode?: Ref<bool>,     // „Auswählen" toggles this (omit → no tool)
//     pickedCount?: () => number, // selected count for the export label
//     actions?: [{ id, label, group?, primary?, run }],  // extra page actions
//   })
import { watch, onMounted, onBeforeUnmount } from 'vue'
import { usePilandaInspect } from './usePilandaInspect'
import { usePilandaFuncbar } from './usePilandaFuncbar'

export function useListFuncbar(opts) {
  const { inspectNode } = usePilandaInspect()
  const { registerFuncbar, clearFuncbar } = usePilandaFuncbar()
  const extra = opts.actions || []

  function buildGroups() {
    const n = opts.pickedCount ? opts.pickedCount() : 0
    const aktionen = []
    if (opts.exportRows) {
      aktionen.push({ id: 'export', label: n ? `${n} ${__('selected')} · ${__('Export')}` : __('Export'), primary: true })
    }
    aktionen.push({ id: 'refresh', label: __('Refresh'), primary: !opts.exportRows })
    const werkzeuge = opts.selectMode ? [{ id: 'select', label: __('Select') }] : []
    extra.forEach((a) => (a.group === 'werkzeuge' ? werkzeuge : aktionen).push({ id: a.id, label: a.label, primary: a.primary }))
    return { aktionen, werkzeuge }
  }

  function onAction(id) {
    if (id === 'export') opts.exportRows && opts.exportRows()
    else if (id === 'refresh') opts.reload && opts.reload()
    else if (id === 'select' && opts.selectMode) opts.selectMode.value = !opts.selectMode.value
    else { const a = extra.find((x) => x.id === id); if (a && a.run) a.run() }
  }

  function sync() { registerFuncbar(buildGroups(), onAction) }

  function showInspector() {
    inspectNode({
      title: opts.title,
      badge: opts.badge,
      rows: [{ label: __('Entries'), value: String(opts.count ? opts.count() : 0) }],
      sections: opts.meaning ? [{ title: __('Meaning'), items: [{ text: opts.meaning }], empty: '—' }] : [],
    })
  }

  // Re-register when the selection count changes (for the „N ausgewählt"-label).
  if (opts.selectMode || opts.pickedCount) {
    watch([opts.selectMode, () => (opts.pickedCount ? opts.pickedCount() : 0)], sync)
  }

  onMounted(() => { sync(); showInspector() })
  onBeforeUnmount(() => { clearFuncbar(); inspectNode(null) })

  return { sync, showInspector }
}
