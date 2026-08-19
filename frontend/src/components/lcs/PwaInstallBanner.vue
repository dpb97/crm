<!--
  PwaInstallBanner — dezente Install-Leiste unten. Erscheint, sobald die App
  installierbar ist (Chrome/Edge/Android via beforeinstallprompt) oder auf iOS
  (dort mit „Teilen → Zum Home-Bildschirm"-Anleitung). Merkt sich das Wegklicken.
-->
<template>
  <transition name="pwab-fade">
    <div v-if="show" class="pwab" role="dialog" aria-label="App installieren">
      <img class="pwab-icon" :src="iconUrl" alt="" />
      <div class="pwab-txt">
        <div class="pwab-title">{{ __('Install LCS CRM') }}</div>
        <div v-if="isIOS" class="pwab-sub">{{ __('Tap Share, then “Add to Home Screen”.') }}</div>
        <div v-else class="pwab-sub">{{ __('Add to your home screen — full-screen and offline.') }}</div>
      </div>
      <button v-if="canPrompt" type="button" class="pwab-btn" @click="doInstall">{{ __('Install') }}</button>
      <button type="button" class="pwab-x" :title="__('Dismiss')" aria-label="Schließen" @click="dismiss">✕</button>
    </div>
  </transition>
</template>

<script setup>
import { computed, ref } from 'vue'
import { usePwaInstall } from '@/composables/usePwaInstall'

// Runtime-served public asset — kept as a dynamic binding so Vite/rollup does not
// try to resolve it as a build-time import (it lives in crm/public, not src).
const iconUrl = '/assets/crm/frontend/favicon-192.png'
const { canPrompt, install, isIOS, isStandalone } = usePwaInstall()
const dismissed = ref(localStorage.getItem('lcs-pwa-dismissed') === '1')
const show = computed(() => !dismissed.value && !isStandalone && (canPrompt.value || isIOS))

function dismiss() {
  dismissed.value = true
  localStorage.setItem('lcs-pwa-dismissed', '1')
}
async function doInstall() {
  const ok = await install()
  if (ok) dismiss()
}
</script>

<style scoped>
.pwab {
  position: fixed; left: 50%; transform: translateX(-50%); bottom: max(12px, env(safe-area-inset-bottom));
  z-index: 3000; display: flex; align-items: center; gap: var(--pp-space-3);
  width: calc(100% - 24px); max-width: 440px; padding: 10px 12px;
  background: var(--pp-bg-surface); border: 1px solid var(--pp-border-default);
  border-radius: var(--pp-radius-ui); box-shadow: var(--pp-shadow-lg, 0 8px 30px rgba(0,0,0,0.18));
}
.pwab-icon { width: 40px; height: 40px; border-radius: 8px; flex-shrink: 0; }
.pwab-txt { min-width: 0; flex: 1; }
.pwab-title { font-size: var(--pp-fs-13, 13px); font-weight: var(--pp-weight-semibold); color: var(--pp-text-primary); }
.pwab-sub { font-size: 11px; color: var(--pp-text-tertiary); line-height: 1.35; }
.pwab-btn { flex-shrink: 0; appearance: none; cursor: pointer; font: inherit; font-size: 13px; font-weight: var(--pp-weight-medium);
  padding: 9px 16px; border: 0; border-radius: var(--pp-radius-ui); background: var(--pp-brand-primary); color: var(--pp-text-on-accent); }
.pwab-x { flex-shrink: 0; appearance: none; cursor: pointer; border: 0; background: none; color: var(--pp-text-tertiary); font-size: 14px; padding: 6px; }
.pwab-x:hover { color: var(--pp-text-primary); }
.pwab-fade-enter-active, .pwab-fade-leave-active { transition: opacity .2s, transform .2s; }
.pwab-fade-enter-from, .pwab-fade-leave-to { opacity: 0; transform: translate(-50%, 12px); }
</style>
