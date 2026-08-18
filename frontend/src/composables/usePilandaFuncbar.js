// Shell-wide function bar (klickdummy „Funktionsbar"): a page registers its
// action groups; the burger in the PpInspector header (v-model:funcbarOpen)
// toggles the bar, which DesktopLayout renders over the top of the canvas.
// Singleton module-level state so the inspector burger, the bar and the page
// all share ONE reactive source.
//
// A global „Neue Aufgabe" action is always injected, so a task can be created
// from the inspector on EVERY page — regardless of what the page registers.
import { ref, computed } from 'vue'
import { useCreateTask } from './useCreateTask'
import { useTaskContext } from './useTaskContext'

const GLOBAL_NEW_TASK_ID = '__new_task'

const open = ref(false)
// { aktionen?, werkzeuge?, ausgabe?, abstiege? } — arrays of { id?, label, primary? }
const groups = ref(null)
let handler = null // (id) => void

// The page groups plus the always-present global „Neue Aufgabe" action.
const mergedGroups = computed(() => {
  const g = groups.value ? { ...groups.value } : {}
  const aktionen = Array.isArray(g.aktionen) ? [...g.aktionen] : []
  // Skip if the page already offers a task action (useListFuncbar uses 'new-task').
  if (!aktionen.some((a) => a.id === GLOBAL_NEW_TASK_ID || a.id === 'new-task')) {
    aktionen.push({ id: GLOBAL_NEW_TASK_ID, label: __('New task') })
  }
  g.aktionen = aktionen
  return g
})

// Always available: the global new-task action is always there.
const available = computed(() => true)

// Build a fallback ref to the current page (place of creation) when no element
// is selected — a plain URL link the task can carry back.
function currentPageRef() {
  const url = (typeof window !== 'undefined' && window.location && window.location.href) || ''
  let title = (typeof document !== 'undefined' && document.title) || ''
  title = title.replace(/\s*[|·—–-]\s*.*$/, '').trim() // strip " | CRM" suffixes
  return { title: title || __('Page'), url }
}

export function usePilandaFuncbar() {
  const { openTask } = useCreateTask()
  const { context } = useTaskContext()

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
  // Called by the rendered PpFunctionBar; runs the global handler or the page
  // handler, then closes the bar.
  function runAction(id) {
    if (id === GLOBAL_NEW_TASK_ID) {
      // Link the task to the selected element, else to the current page.
      openTask(context.value || currentPageRef())
    } else if (handler) {
      handler(id)
    }
    open.value = false
  }
  return { open, groups: mergedGroups, available, registerFuncbar, clearFuncbar, runAction }
}
