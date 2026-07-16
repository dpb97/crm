<!--
  LCSBrandHeader
  ==============
  Slim top-of-page banner that carries LCS branding on every CRM screen.
  Designed to live above the upstream `Apps` bar without competing with it:
  minimalistic, single row, no shadows, high-contrast text only.

  Props
  -----
  title        Required. Plain text, rendered in the brand font.
  subtitle     Optional muted caption for context (e.g. site name).
  href         Optional URL — when set, the brand wordmark becomes a link.
  compact      Hide the subtitle even if one is passed (mobile / dense views).
-->

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    title: string
    subtitle?: string
    href?: string
    compact?: boolean
  }>(),
  { subtitle: '', href: '', compact: false },
)

const showSubtitle = computed(() => !props.compact && !!props.subtitle)
</script>

<template>
  <header
    class="flex items-center justify-between border-b border-lcs-muted/20 bg-lcs-primary px-4 py-2 font-lcs text-white"
    role="banner"
  >
    <div class="flex items-baseline gap-3">
      <component
        :is="href ? 'a' : 'span'"
        :href="href || undefined"
        class="text-base font-semibold tracking-tight hover:text-lcs-accent"
      >
        {{ title }}
      </component>
      <span
        v-if="showSubtitle"
        class="text-xs font-normal text-lcs-surface/80"
      >
        {{ subtitle }}
      </span>
    </div>
    <slot name="actions" />
  </header>
</template>
