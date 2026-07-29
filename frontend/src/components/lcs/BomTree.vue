<!--
  BomTree — recursive hierarchical display of a Fusion Manage BOM.

  Each row can be expanded to reveal its children. Item numbers are
  copyable; hovering a row shows the PLM state as a pill.
-->

<template>
  <div v-if="rows.length" class="rounded-lg border bg-white">
    <div class="border-b bg-gray-50 px-3 py-2 text-xs font-semibold uppercase tracking-wide text-gray-500">
      <FeatherIcon name="git-merge" class="mr-1 inline h-3 w-3" />
      {{ __('Bill of Materials') }}
      <span class="ml-2 font-normal text-gray-400">
        ({{ totalRowCount }} {{ __('items') }})
      </span>
    </div>
    <div class="divide-y overflow-x-auto">
      <BomRow
        v-for="(row, i) in rows"
        :key="row.child_id || i"
        :row="row"
        :depth="0"
      />
    </div>
  </div>
  <div v-else class="rounded-lg border border-dashed border-gray-200 p-6 text-center">
    <FeatherIcon name="git-merge" class="mx-auto h-6 w-6 text-gray-300" />
    <p class="mt-2 text-sm text-gray-500">{{ __('No BOM rows returned') }}</p>
    <p class="mt-1 text-xs text-gray-400">
      {{ __('The linked Fusion Manage item has no child components, or the BOM view has not been configured.') }}
    </p>
  </div>
</template>

<script setup>
import { computed, defineComponent, h, ref } from 'vue'
import { FeatherIcon } from 'frappe-ui'

const props = defineProps({
  rows: { type: Array, default: () => [] },
})

const totalRowCount = computed(() => countRows(props.rows))

function countRows(rows) {
  return (rows || []).reduce((sum, r) => sum + 1 + countRows(r.children || []), 0)
}

// Recursive row — defined inline so the self-reference works
const BomRow = defineComponent({
  name: 'BomRow',
  props: {
    row: { type: Object, required: true },
    depth: { type: Number, default: 0 },
  },
  setup(props) {
    const expanded = ref(props.depth < 1)  // first level expanded by default
    const hasChildren = computed(() => (props.row.children || []).length > 0)
    const indentPx = computed(() => props.depth * 20)

    const stateColor = computed(() => {
      const s = (props.row.state || '').toLowerCase()
      if (s.includes('release')) return 'bg-green-100 text-green-800'
      if (s.includes('review')) return 'bg-amber-100 text-amber-800'
      if (s.includes('draft')) return 'bg-gray-100 text-gray-700'
      if (s.includes('obsolete')) return 'bg-red-100 text-red-700'
      return 'bg-gray-100 text-gray-700'
    })

    return () => h('div', {}, [
      h('div', {
        class: 'flex items-center gap-2 px-3 py-2 text-sm hover:bg-gray-50 cursor-pointer',
        style: { paddingLeft: `${12 + indentPx.value}px` },
        onClick: () => { if (hasChildren.value) expanded.value = !expanded.value },
      }, [
        hasChildren.value
          ? h(FeatherIcon, {
              name: expanded.value ? 'chevron-down' : 'chevron-right',
              class: 'h-3.5 w-3.5 text-gray-400 shrink-0',
            })
          : h('span', { class: 'h-3.5 w-3.5 shrink-0' }),
        h('span', {
          class: 'font-mono text-xs font-semibold text-gray-800 shrink-0',
        }, props.row.child_number || props.row.child_id || '—'),
        h('span', {
          class: 'flex-1 truncate text-gray-700',
        }, props.row.child_name || ''),
        props.row.quantity ? h('span', {
          class: 'shrink-0 rounded bg-blue-50 px-1.5 py-0.5 text-[10px] font-medium text-blue-700',
        }, `${props.row.quantity} ${props.row.unit || ''}`) : null,
        props.row.state ? h('span', {
          class: `shrink-0 rounded-full px-2 py-0.5 text-[10px] font-medium ${stateColor.value}`,
        }, props.row.state) : null,
      ]),
      hasChildren.value && expanded.value
        ? h('div', {}, (props.row.children || []).map((child, idx) =>
            h(BomRow, { row: child, depth: props.depth + 1, key: child.child_id || idx })
          ))
        : null,
    ])
  },
})
</script>
