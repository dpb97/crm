<!--
  SyncStatusBadge
  ===============
  Uniform visual indicator for the outbound sync state of a CRM record
  towards an external system (abas, Outlook, Proxess). Intended to be placed
  next to record titles so operators immediately see whether a Lead / Deal
  is in flight, out of sync, or fully reconciled.

  Props
  -----
  status   Required. One of: 'synced' | 'pending' | 'error' | 'disabled'.
  system   Display label for the target system. Kept free-form so new
           integrations can be added without changing this component.
  detail   Optional tooltip text (e.g. timestamp of last sync, error message).
-->

<script setup lang="ts">
import { computed } from 'vue'

type SyncState = 'synced' | 'pending' | 'error' | 'disabled'

const props = defineProps<{
  status: SyncState
  system: string
  detail?: string
}>()

// Kept inline — palette is derived from the LCS Tailwind theme and there is
// no real logic to unit-test.
const styles = computed<Record<SyncState, string>>(() => ({
  synced: 'bg-lcs-success/10 text-lcs-success ring-lcs-success/30',
  pending: 'bg-lcs-accent/10 text-lcs-warning ring-lcs-accent/30',
  error: 'bg-lcs-danger/10 text-lcs-danger ring-lcs-danger/30',
  disabled: 'bg-lcs-muted/10 text-lcs-muted ring-lcs-muted/30',
}))

const label = computed(() => {
  switch (props.status) {
    case 'synced':
      return `${props.system} · synchronised`
    case 'pending':
      return `${props.system} · pending`
    case 'error':
      return `${props.system} · error`
    case 'disabled':
      return `${props.system} · disabled`
  }
})
</script>

<template>
  <span
    :class="[
      'inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset',
      styles[status],
    ]"
    :title="detail || label"
  >
    <span
      class="h-1.5 w-1.5 rounded-full"
      :class="{
        'bg-lcs-success': status === 'synced',
        'bg-lcs-warning animate-pulse': status === 'pending',
        'bg-lcs-danger': status === 'error',
        'bg-lcs-muted': status === 'disabled',
      }"
      aria-hidden="true"
    />
    {{ label }}
  </span>
</template>
