<template>
  <Teleport v-if="showHeader" to="#app-header">
    <slot>
      <header
        class="lcs-layout-header flex h-10.5 items-center justify-between py-[7px] sm:pl-5 pl-2"
      >
        <div class="flex items-center gap-2">
          <slot name="left-header" />
        </div>
        <div class="lcs-layout-header__actions flex items-center gap-2">
          <slot name="right-header" />
        </div>
      </header>
    </slot>
  </Teleport>
</template>
<script setup>
import { ref, nextTick } from 'vue'

const showHeader = ref(false)

nextTick(() => {
  showHeader.value = true
})
</script>

<style scoped>
/*
 * Mobile fix (390px): on a narrow viewport the fixed-height, justify-between
 * header pushed its right-hand actions off the right edge (e.g. the Dashboard
 * "Edit" button was clipped). Below 480px let the header wrap onto a second
 * line and grow in height, and let the actions cluster scroll horizontally as
 * an escape hatch. Desktop (>=481px) is untouched. Spacing via --pp tokens.
 */
@media (max-width: 480px) {
  .lcs-layout-header {
    flex-wrap: wrap;
    height: auto;
    min-height: 2.625rem; /* = h-10.5 baseline */
    row-gap: var(--pp-space-1);
  }
  .lcs-layout-header > div {
    min-width: 0; /* allow the flex children to shrink instead of overflowing */
  }
  .lcs-layout-header__actions {
    max-width: 100%;
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
    scrollbar-width: thin;
  }
}
</style>
