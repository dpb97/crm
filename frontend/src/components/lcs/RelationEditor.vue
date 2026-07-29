<!--
  RelationEditor — inline editor for a relation child table (cross-org / person
  relationships). Reads/writes via lcs_integrations.projects.api get/save_relations.
  columns: [{ key, type: 'link'|'select'|'date'|'check'|'text', label, options?, opts? }]
-->
<template>
  <div class="rel">
    <div class="rel-head">
      <span class="rel-title">{{ title }}</span>
      <button type="button" class="rel-add" @click="addRow"><FeatherIcon name="plus" class="h-3 w-3" />{{ __('Add') }}</button>
    </div>

    <p v-if="!rows.length" class="rel-empty">{{ __('None yet.') }}</p>

    <div v-for="(row, i) in rows" :key="row._k" class="rel-row">
      <template v-for="col in columns" :key="col.key">
        <Link v-if="col.type === 'link'" :doctype="col.options" v-model="row[col.key]" class="rel-link" :placeholder="col.label" @update:modelValue="dirty = true" />
        <select v-else-if="col.type === 'select'" v-model="row[col.key]" class="rel-input" @change="dirty = true">
          <option v-for="o in col.opts" :key="o" :value="o">{{ o }}</option>
        </select>
        <input v-else-if="col.type === 'date'" type="date" v-model="row[col.key]" class="rel-input rel-input--sm" @change="dirty = true" />
        <label v-else-if="col.type === 'check'" class="rel-check"><input type="checkbox" v-model="row[col.key]" @change="dirty = true" />{{ col.label }}</label>
        <input v-else type="text" v-model="row[col.key]" class="rel-input" :placeholder="col.label" @input="dirty = true" />
      </template>
      <button type="button" class="rel-del" :aria-label="__('Remove')" @click="removeRow(i)"><FeatherIcon name="x" class="h-3.5 w-3.5" /></button>
    </div>

    <div v-if="dirty" class="rel-foot">
      <button type="button" class="rel-save" :disabled="saving" @click="save">{{ saving ? __('Saving …') : __('Save') }}</button>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { call, toast, FeatherIcon } from 'frappe-ui'
import Link from '@/components/Controls/Link.vue'

const props = defineProps({
  doctype: { type: String, required: true },
  name: { type: String, default: '' },
  fieldname: { type: String, required: true },
  title: { type: String, default: '' },
  columns: { type: Array, default: () => [] },
})

const rows = ref([])
const dirty = ref(false)
const saving = ref(false)
let keySeq = 0
const nextKey = () => `r${++keySeq}` // stable per-row key so Link inputs don't go stale on delete

async function load() {
  rows.value = []
  dirty.value = false
  if (!props.name) return
  try {
    const res = await call('lcs_integrations.projects.api.get_relations', {
      doctype: props.doctype, name: props.name, fieldname: props.fieldname,
    })
    rows.value = (res?.message || res || []).map((r) => ({ ...r, _k: nextKey() }))
  } catch { rows.value = [] }
}
watch(() => [props.name, props.fieldname], load, { immediate: true })

function addRow() {
  const blank = { _k: nextKey() }
  props.columns.forEach((c) => { blank[c.key] = c.type === 'check' ? 0 : '' })
  rows.value.push(blank)
  dirty.value = true
}
function removeRow(i) { rows.value.splice(i, 1); dirty.value = true }

async function save() {
  saving.value = true
  try {
    const clean = rows.value.map((r) => {
      const out = {}
      props.columns.forEach((c) => { out[c.key] = c.type === 'check' ? (r[c.key] ? 1 : 0) : (r[c.key] || null) })
      return out
    }).filter((r) => props.columns.some((c) => r[c.key]))
    await call('lcs_integrations.projects.api.save_relations', {
      doctype: props.doctype, name: props.name, fieldname: props.fieldname, rows: JSON.stringify(clean),
    })
    toast.success(__('Saved'))
    dirty.value = false
    load()
  } catch (e) {
    toast.error(e?.messages?.[0] || e?.message || __('Save failed'))
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.rel { display: flex; flex-direction: column; gap: var(--pp-space-2); }
.rel-head { display: flex; align-items: center; justify-content: space-between; }
.rel-title { font-size: 10px; font-weight: var(--pp-weight-bold); letter-spacing: 0.06em; text-transform: uppercase; color: var(--pp-text-tertiary); }
.rel-add { appearance: none; cursor: pointer; font-family: inherit; font-size: 11px; display: inline-flex; align-items: center; gap: 3px;
  color: var(--pp-brand-primary); background: transparent; border: 0; }
.rel-add:hover { text-decoration: underline; }
.rel-empty { margin: 0; font-size: var(--pp-fs-12, 12px); color: var(--pp-text-tertiary); }
.rel-row { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
.rel-link { flex: 1; min-width: 0; }
.rel-input { flex: 1; min-width: 0; appearance: none; font-family: inherit; font-size: var(--pp-fs-12, 12px); color: var(--pp-text-primary);
  padding: 5px var(--pp-space-2); border: 1px solid var(--pp-border-default); border-radius: var(--pp-radius-ui); background: var(--pp-bg-base); }
.rel-input--sm { flex: 0 0 auto; width: 130px; }
.rel-check { display: inline-flex; align-items: center; gap: 4px; font-size: 11px; color: var(--pp-text-secondary); white-space: nowrap; }
.rel-del { appearance: none; cursor: pointer; border: 0; background: transparent; color: var(--pp-text-tertiary); padding: 2px; }
.rel-del:hover { color: var(--pp-state-danger); }
.rel-foot { display: flex; justify-content: flex-end; }
.rel-save { appearance: none; cursor: pointer; font-family: inherit; font-size: 11px; font-weight: var(--pp-weight-semibold);
  padding: 5px 12px; border-radius: var(--pp-radius-ui); border: 1px solid var(--pp-brand-primary);
  background: var(--pp-brand-primary); color: var(--pp-text-on-accent); }
.rel-save:disabled { opacity: 0.6; cursor: default; }

/* Phone / narrow inspector overlay: stack each field full-width instead of
   squeezing link + select + date + check into one ~360px row. */
@media (max-width: 640px) {
  .rel-link, .rel-input { flex: 1 1 100%; }
  .rel-input--sm { flex: 1 1 100%; width: auto; }
}
</style>
