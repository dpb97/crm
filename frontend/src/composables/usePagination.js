// Client-side pagination for lists that load all rows at once (the bespoke
// Pilanda list pages). Slices a rows ref into pages so long lists never grow
// unboundedly tall. Pair with LcsPagination.vue for the footer controls.
import { ref, computed, watch } from 'vue'

export function usePagination(rowsRef, opts = {}) {
  const pageSize = ref(opts.pageSize || 25)
  const page = ref(1)

  const total = computed(() => (rowsRef.value || []).length)
  const pageCount = computed(() => Math.max(1, Math.ceil(total.value / pageSize.value)))

  // Keep the current page valid when the data set or page size changes.
  watch([total, pageSize], () => {
    if (page.value > pageCount.value) page.value = pageCount.value
    if (page.value < 1) page.value = 1
  })

  const paged = computed(() => {
    const start = (page.value - 1) * pageSize.value
    return (rowsRef.value || []).slice(start, start + pageSize.value)
  })
  const from = computed(() => (total.value === 0 ? 0 : (page.value - 1) * pageSize.value + 1))
  const to = computed(() => Math.min(page.value * pageSize.value, total.value))

  function setPage(p) {
    page.value = Math.min(Math.max(1, p), pageCount.value)
  }
  function next() { setPage(page.value + 1) }
  function prev() { setPage(page.value - 1) }
  function setPageSize(n) {
    pageSize.value = n
    page.value = 1
  }

  return { paged, page, pageCount, total, from, to, pageSize, setPage, next, prev, setPageSize }
}
