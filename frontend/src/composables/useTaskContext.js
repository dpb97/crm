// Shell-wide "current task context": the element a task should link back to
// when created from the inspector's global „Neue Aufgabe" action. A detail page
// sets its document; when nothing is set, the global action falls back to a link
// to the current page (place of creation). Singleton module-level state.
import { ref } from 'vue'

const context = ref(null) // { doctype, name, title } | null

export function useTaskContext() {
  // ctx = { doctype, name, title }; pass null to clear.
  function setTaskContext(ctx) {
    context.value = ctx && (ctx.name || ctx.title) ? ctx : null
  }
  return { context, setTaskContext }
}
