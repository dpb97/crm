<!--
  GlobalSearchDialog — Ctrl/Cmd+K search across leads, deals, contacts,
  organizations and LCS projects.

  Thin wrapper around the pilanda_theme SSOT block PpCommandPalette@2
  (components/pp/, byte-identical copy): the palette renders overlay,
  input, grouping and keyboard handling; this wrapper feeds it
  server-side results (filter=false — the backend already filters,
  permission-checked per doctype) and routes the selection.
-->

<template>
  <PpCommandPalette
    :open="show"
    :items="items"
    :filter="false"
    :hotkey="false"
    :placeholder="__('Search leads, deals, contacts, projects...')"
    @update:open="(v) => (show = v)"
    @update:query="onQuery"
    @select="onSelect"
  />
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { call } from 'frappe-ui'
import { useDebounceFn } from '@vueuse/core'
import PpCommandPalette from '@/components/pp/PpCommandPalette.vue'

const show = defineModel({ type: Boolean, default: false })
const router = useRouter()

const GROUP_LABELS = {
  'CRM Lead': 'Leads',
  'CRM Deal': 'Deals',
  Contact: 'Contacts',
  'CRM Organization': 'Organizations',
  'LCS Project': 'Projects',
}
const ROUTES = {
  'CRM Lead': (n) => ({ name: 'Lead', params: { leadId: n } }),
  'CRM Deal': (n) => ({ name: 'Deal', params: { dealId: n } }),
  Contact: (n) => ({ name: 'Contact', params: { contactId: n } }),
  'CRM Organization': (n) => ({ name: 'Organization', params: { organizationId: n } }),
  'LCS Project': (n) => ({ name: 'LCS Project', params: { id: n } }),
}

const groups = ref([])

const items = computed(() =>
  groups.value.flatMap((g) =>
    g.results.map((r) => ({
      id: `${g.doctype}::${r.name}`,
      label: r.sub ? `${r.label} — ${r.sub}` : r.label,
      group: __(GROUP_LABELS[g.doctype] || g.doctype),
      doctype: g.doctype,
      name: r.name,
    })),
  ),
)

const onQuery = useDebounceFn(async (q) => {
  if ((q || '').trim().length < 2) {
    groups.value = []
    return
  }
  try {
    groups.value = (await call('lcs_integrations.global_search.api.global_search', { txt: q })) || []
  } catch (e) {
    groups.value = []
  }
}, 250)

function onSelect(item) {
  const to = ROUTES[item.doctype]?.(item.name)
  if (to) router.push(to)
}
</script>
