<!--
  LcsPagination — token-styled pagination footer for the bespoke Pilanda list
  pages (pairs with usePagination). Page-size buttons + prev/next + range info.
-->
<template>
  <div class="lcspg">
    <div class="lcspg-size">
      <button
        v-for="s in pageSizes"
        :key="s"
        type="button"
        class="lcspg-sizebtn"
        :class="{ 'is-active': s === pageSize }"
        @click="$emit('page-size', s)"
      >{{ s }}</button>
    </div>
    <div class="lcspg-nav">
      <span class="lcspg-info">{{ from }}–{{ to }} {{ __('of') }} {{ total }}</span>
      <button type="button" class="lcspg-arrow" :disabled="page <= 1" @click="$emit('prev')">
        <IconLeft />
      </button>
      <span class="lcspg-page">{{ page }} / {{ pageCount }}</span>
      <button type="button" class="lcspg-arrow" :disabled="page >= pageCount" @click="$emit('next')">
        <IconRight />
      </button>
    </div>
  </div>
</template>

<script setup>
import IconLeft from '~icons/lucide/chevron-left'
import IconRight from '~icons/lucide/chevron-right'

defineProps({
  from: { type: Number, default: 0 },
  to: { type: Number, default: 0 },
  total: { type: Number, default: 0 },
  page: { type: Number, default: 1 },
  pageCount: { type: Number, default: 1 },
  pageSize: { type: Number, default: 25 },
  pageSizes: { type: Array, default: () => [25, 50, 100] },
})
defineEmits(['prev', 'next', 'page-size'])
</script>

<style scoped>
.lcspg { display: flex; align-items: center; justify-content: space-between; gap: var(--pp-space-4);
  padding: var(--pp-space-2) var(--pp-space-3); flex-wrap: wrap; }
.lcspg-size { display: inline-flex; gap: 2px; }
.lcspg-sizebtn { appearance: none; cursor: pointer; font-family: inherit; font-size: var(--pp-fs-12);
  padding: 3px 9px; border-radius: var(--pp-radius-ui); border: 1px solid transparent;
  background: transparent; color: var(--pp-text-tertiary); }
.lcspg-sizebtn:hover { background: var(--pp-bg-hover); color: var(--pp-text-secondary); }
.lcspg-sizebtn.is-active { background: var(--pp-accent-soft); color: var(--pp-brand-primary);
  border-color: color-mix(in oklab, var(--pp-brand-primary) 30%, transparent); font-weight: var(--pp-weight-semibold); }

.lcspg-nav { display: inline-flex; align-items: center; gap: var(--pp-space-3); }
.lcspg-info { font-size: var(--pp-fs-12); color: var(--pp-text-tertiary); font-variant-numeric: tabular-nums; }
.lcspg-page { font-size: var(--pp-fs-12); color: var(--pp-text-secondary); font-variant-numeric: tabular-nums; min-width: 44px; text-align: center; }
.lcspg-arrow { appearance: none; cursor: pointer; display: inline-flex; align-items: center; justify-content: center;
  width: 26px; height: 26px; border-radius: var(--pp-radius-ui); border: 1px solid var(--pp-border-default);
  background: var(--pp-bg-surface); color: var(--pp-text-secondary); }
.lcspg-arrow:hover:not(:disabled) { border-color: var(--pp-brand-primary); color: var(--pp-brand-primary); }
.lcspg-arrow:disabled { opacity: 0.4; cursor: default; }
.lcspg-arrow :deep(svg) { width: 15px; height: 15px; }
</style>
