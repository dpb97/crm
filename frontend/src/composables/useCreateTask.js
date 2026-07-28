// Shell-wide "create task" state. The inspector burger / function bar opens a
// task prefilled with the CURRENTLY SELECTED object; a single TaskCreateModal
// mounted in the shell renders it. Singleton module-level state so every page
// and the one modal share ONE reactive source.
import { reactive } from 'vue'

const state = reactive({
  open: false,
  ref: null, // { doctype, name, title }
})

export function useCreateTask() {
  // ref = { doctype, name, title } of the selected object (all optional).
  function openTask(ref = null) {
    state.ref = ref || null
    state.open = true
  }
  function closeTask() {
    state.open = false
    state.ref = null
  }
  return { state, openTask, closeTask }
}
