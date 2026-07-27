<!--
  LCSComingSoon — Platzhalter für Funktionen, die im modulweisen Rollout noch
  nicht live sind. Statt eines kaputten Desk-Handoffs (z. B. Produktportfolio →
  /app/product-portfolio, App pilanda_productportfolio noch nicht installiert)
  fängt PilandaSidebar das Ziel ab und leitet auf diese Seite. Titel/Beschreibung
  kommen aus der Route-Query, damit EINE Seite alle „bald verfügbar"-Fälle deckt.
-->
<template>
  <div class="flex h-full flex-col">
    <LayoutHeader>
      <template #left-header>
        <Breadcrumbs :items="[{ label: 'Vertrieb' }, { label: featureTitle }]" />
      </template>
    </LayoutHeader>

    <div class="cs">
      <div class="cs-card">
        <div class="cs-badge"><IconSparkles class="cs-badge-ico" /> {{ __('Coming soon') }}</div>
        <div class="cs-icon"><IconRocket /></div>
        <h1 class="cs-title">{{ featureTitle }}</h1>
        <p v-if="featureDesc" class="cs-desc">{{ featureDesc }}</p>
        <p class="cs-note">
          {{ __('This module is not live yet — we roll out module by module. It will appear here as soon as it is available.') }}
        </p>
        <div class="cs-actions">
          <Button variant="solid" :label="__('Back')" iconLeft="arrow-left" @click="goBack" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Breadcrumbs, Button } from 'frappe-ui'
import LayoutHeader from '@/components/LayoutHeader.vue'
import IconRocket from '~icons/lucide/rocket'
import IconSparkles from '~icons/lucide/sparkles'

const route = useRoute()
const router = useRouter()

const featureTitle = computed(() => route.query.feature || __('Coming soon'))
const featureDesc = computed(() => route.query.desc || '')

function goBack() {
  if (window.history.length > 1) router.back()
  else router.push({ name: 'LCS Sales Meeting' })
}
</script>

<style scoped>
.cs { flex: 1; min-height: 0; display: flex; align-items: center; justify-content: center;
  padding: var(--pp-space-6); background: var(--pp-bg-base); }
.cs-card { width: 100%; max-width: 480px; display: flex; flex-direction: column; align-items: center;
  text-align: center; gap: var(--pp-space-3); padding: var(--pp-space-8) var(--pp-space-6);
  background: var(--pp-bg-surface); border: 1px solid var(--pp-border-subtle);
  border-radius: var(--pp-radius-ui); box-shadow: var(--pp-shadow-sm); }

.cs-badge { display: inline-flex; align-items: center; gap: 6px; font-size: 11px; font-weight: var(--pp-weight-bold);
  letter-spacing: var(--pp-tracking-wide, 0.04em); text-transform: uppercase; color: var(--pp-brand-primary);
  padding: 3px var(--pp-space-3); border-radius: var(--pp-radius-full);
  background: color-mix(in oklab, var(--pp-brand-primary) 12%, transparent); }
.cs-badge-ico { width: 13px; height: 13px; }

.cs-icon { display: inline-flex; align-items: center; justify-content: center; width: 64px; height: 64px;
  margin-top: var(--pp-space-2); border-radius: var(--pp-radius-full);
  background: color-mix(in oklab, var(--pp-brand-primary) 10%, transparent); color: var(--pp-brand-primary); }
.cs-icon :deep(svg) { width: 30px; height: 30px; }

.cs-title { margin: 0; font-size: var(--pp-fs-22, 22px); font-weight: var(--pp-weight-bold);
  color: var(--pp-text-primary); font-family: var(--pp-font-heading); }
.cs-desc { margin: 0; font-size: var(--pp-fs-14, 14px); color: var(--pp-text-secondary); }
.cs-note { margin: 0; font-size: var(--pp-fs-13, 13px); color: var(--pp-text-tertiary); line-height: 1.5; }
.cs-actions { margin-top: var(--pp-space-3); }
</style>
