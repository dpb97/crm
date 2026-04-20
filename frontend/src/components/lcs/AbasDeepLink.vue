<!--
  AbasDeepLink
  ============
  Opens the matching abas ERP record in a new tab. Accepts the abas entity
  id (e.g. "K12345" for customers, "A99001" for quotations) and resolves it
  to the configured abas web-client URL pattern.

  The URL pattern is read from the Frappe site config so that dev / staging /
  production point at different abas tenants without code changes. Until the
  config is loaded the component renders a neutral placeholder — it never
  emits a broken `href`.

  Props
  -----
  entity    Required. The abas entity id to link to.
  kind      Required. 'customer' | 'quotation' | 'order' | 'contact'.
  label     Optional visible text (defaults to the entity id).
-->

<script setup lang="ts">
import { computed, ref, onMounted } from 'vue'

type AbasKind = 'customer' | 'quotation' | 'order' | 'contact'

const props = defineProps<{
  entity: string
  kind: AbasKind
  label?: string
}>()

// Populated from `frappe.boot.lcs_abas_web_base` during mount. A trailing
// slash is optional in the config — we normalise it here.
const base = ref<string>('')

onMounted(() => {
  const anyWindow = window as unknown as {
    frappe?: { boot?: { lcs_abas_web_base?: string } }
  }
  const configured = anyWindow.frappe?.boot?.lcs_abas_web_base ?? ''
  base.value = configured.replace(/\/+$/, '')
})

const href = computed(() => {
  if (!base.value || !props.entity) return ''
  // abas web-client uses /ui/<kind>/<id>; this is the pattern LCS already
  // uses in production — change here if abas relaunches its UI.
  return `${base.value}/ui/${props.kind}/${encodeURIComponent(props.entity)}`
})

const visible = computed(() => props.label || props.entity)
</script>

<template>
  <a
    v-if="href"
    :href="href"
    target="_blank"
    rel="noopener noreferrer"
    class="inline-flex items-center gap-1 text-lcs-secondary underline-offset-2 hover:text-lcs-primary hover:underline"
    :title="`Open ${kind} ${entity} in abas`"
  >
    {{ visible }}
    <svg
      class="h-3 w-3"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      stroke-width="2"
      aria-hidden="true"
    >
      <path d="M14 3h7v7" />
      <path d="M10 14 21 3" />
      <path d="M21 14v7h-7" />
      <path d="M3 10V3h7" />
    </svg>
  </a>
  <span v-else class="text-lcs-muted">{{ visible }}</span>
</template>
