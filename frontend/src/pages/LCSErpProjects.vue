<!--
  LCSErpProjects
  ==============
  "Projekte" = the running/execution projects, which live in ERPNext.
  The ERPNext default project overview is embedded here so the CRM nav
  stays visible (no jump out of the app).
-->

<template>
  <div class="flex h-full flex-col">
    <LayoutHeader>
      <template #left-header>
        <Breadcrumbs :items="[{ label: __('Projekte'), route: { name: 'LCS ERP Projects' } }]" />
      </template>
      <template #right-header>
        <Button :label="__('Open in ERPNext')" iconLeft="external-link" @click="openExternal" />
      </template>
    </LayoutHeader>
    <iframe :src="src" class="min-h-0 w-full flex-1 border-0" title="ERPNext Projekte" />
  </div>
</template>

<script setup>
import { Breadcrumbs, Button } from 'frappe-ui'
import LayoutHeader from '@/components/LayoutHeader.vue'

const src = '/app/project/view/list'
function openExternal() {
  window.open(src, '_blank')
}
</script>
