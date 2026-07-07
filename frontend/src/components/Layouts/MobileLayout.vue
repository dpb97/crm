<template>
  <div class="flex h-screen w-screen">
    <MobileSidebar />
    <!-- min-w-0 + overflow-x-hidden: without them any over-wide child
         (mail cards, long addresses) stretches past the viewport and the
         whole page scrolls horizontally on phones. Inner tables keep
         their own overflow-x-auto containers. -->
    <div class="flex h-full min-w-0 flex-1 flex-col overflow-y-auto overflow-x-hidden bg-surface-white">
      <MobileAppHeader />
      <slot />
    </div>
    <GlobalModals />
  </div>
</template>
<script setup>
import MobileSidebar from '@/components/Mobile/MobileSidebar.vue'
import MobileAppHeader from '@/components/Mobile/MobileAppHeader.vue'
import GlobalModals from '@/components/Modals/GlobalModals.vue'
</script>
