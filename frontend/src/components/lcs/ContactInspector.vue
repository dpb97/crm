<!--
  ContactInspector — docked-inspector content for a contact (Personen).
  ================================================================
  Mounted into the Pilanda shell inspector via usePilandaInspect().inspectPanel
  when a row in the Personen list is single-clicked. Read-only summary + quick
  communication actions + "Open" (→ full contact detail). Mirrors the role that
  ProjectInspector plays for the Sales Projects list.

  Fetches the contact by name so it does not depend on the (transformed) list
  row shape.
-->
<template>
  <div class="ci">
    <div v-if="loading" class="ci-muted">{{ __('Loading...') }}</div>

    <template v-else-if="c">
      <div class="ci-head">
        <Avatar :image="c.image" :label="c.full_name || contactId" size="lg" />
        <div class="min-w-0">
          <div class="ci-name">{{ c.full_name || contactId }}</div>
          <div v-if="c.designation" class="ci-role">{{ c.designation }}</div>
        </div>
      </div>

      <dl class="ci-meta">
        <div>
          <dt>{{ __('Company') }}</dt>
          <dd>
            <span v-if="c.company_name">{{ c.company_name }}</span>
            <button
              v-else-if="c.email_id"
              type="button"
              class="ci-linkbtn"
              :disabled="linkingCompany"
              @click="linkCompany"
            >{{ linkingCompany ? __('Linking …') : __('Link via email domain') }}</button>
            <span v-else class="ci-muted">—</span>
          </dd>
        </div>
        <div>
          <dt>{{ __('Email') }}</dt>
          <dd>
            <a v-if="c.email_id" :href="`mailto:${c.email_id}`" class="ci-link">{{ c.email_id }}</a>
            <span v-else class="ci-muted">—</span>
          </dd>
        </div>
        <div>
          <dt>{{ __('Phone') }}</dt>
          <dd>
            <a v-if="phone" :href="`tel:${phone}`" class="ci-link">{{ phone }}</a>
            <span v-else class="ci-muted">—</span>
          </dd>
        </div>
      </dl>

      <QuickContactActions :email="c.email_id" :phone="phone" />

      <div class="ci-foot">
        <Button variant="solid" iconLeft="target" :label="__('Create opportunity')" :loading="creatingChance" @click="createChance" />
        <Button variant="subtle" iconLeft="external-link" :label="__('Open')" @click="$emit('open', contactId)" />
      </div>
    </template>

    <div v-else class="ci-muted">{{ __('No contact selected') }}</div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { call, toast, Avatar, Button } from 'frappe-ui'
import QuickContactActions from '@/components/lcs/QuickContactActions.vue'

const props = defineProps({
  contactId: { type: String, default: '' },
})
defineEmits(['open'])

const router = useRouter()
const c = ref(null)
const loading = ref(false)
const phone = ref('')

// Kontakt → Chance: create a fresh opportunity prefilled from this contact and
// open it so the salesperson can rate the Opportunity Matrix right away.
// Kontakt → Firma über die Mail-Domain verknüpfen (Website-Match, sonst Firma
// von Kontakten gleicher Domain). Persistiert company_name serverseitig.
const linkingCompany = ref(false)
async function linkCompany() {
  if (!props.contactId) return
  linkingCompany.value = true
  try {
    const res = await call('lcs_integrations.projects.api.link_company_by_domain', { contact: props.contactId })
    const r = res?.message || res || {}
    if (r.linked) { toast.success(__('Company linked') + ': ' + r.company); await load() }
    else toast.error(__('No company found for this email domain.'))
  } catch (e) {
    toast.error(e?.messages?.[0] || e?.message || __('Linking failed.'))
  } finally {
    linkingCompany.value = false
  }
}

const creatingChance = ref(false)
async function createChance() {
  if (!props.contactId) return
  creatingChance.value = true
  try {
    const res = await call('lcs_integrations.projects.api.create_chance_from_contact', { contact: props.contactId })
    const id = res?.name || res?.message?.name
    toast.success(__('Opportunity created') + (res?.chance_no ? ': ' + res.chance_no : ''))
    if (id) router.push({ name: 'LCS Chance', params: { id } })
  } catch (e) {
    toast.error(e?.messages?.[0] || e?.message || __('Could not create the opportunity.'))
  } finally {
    creatingChance.value = false
  }
}

async function load() {
  if (!props.contactId) {
    c.value = null
    return
  }
  loading.value = true
  try {
    const data = await call('frappe.client.get_value', {
      doctype: 'Contact',
      filters: { name: props.contactId },
      fieldname: ['full_name', 'email_id', 'mobile_no', 'phone', 'company_name', 'designation', 'image'],
    })
    c.value = data || null
    phone.value = data?.mobile_no || data?.phone || ''
  } catch (e) {
    c.value = null
  } finally {
    loading.value = false
  }
}
watch(() => props.contactId, load, { immediate: true })
</script>

<style scoped>
.ci { display: flex; flex-direction: column; gap: var(--pp-space-4); }
.ci-muted { color: var(--pp-text-tertiary); font-size: var(--pp-fs-13, 13px); }

.ci-head { display: flex; align-items: center; gap: var(--pp-space-3); }
.ci-name { font-size: var(--pp-fs-16, 16px); font-weight: var(--pp-weight-semibold);
  color: var(--pp-text-primary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.ci-role { font-size: var(--pp-fs-12); color: var(--pp-text-tertiary); }

.ci-meta { display: flex; flex-direction: column; gap: var(--pp-space-3); margin: 0; }
.ci-meta dt { font-size: 10px; text-transform: uppercase; letter-spacing: 0.06em;
  color: var(--pp-text-tertiary); font-weight: var(--pp-weight-semibold); }
.ci-meta dd { margin: 2px 0 0; font-size: var(--pp-fs-14); color: var(--pp-text-primary); }
.ci-link { color: var(--pp-brand-primary); text-decoration: none; }
.ci-link:hover { text-decoration: underline; }
.ci-linkbtn { appearance: none; cursor: pointer; font-family: inherit; font-size: var(--pp-fs-12, 12px);
  padding: 3px var(--pp-space-2); border: 1px dashed var(--pp-border-default); border-radius: var(--pp-radius-ui);
  background: transparent; color: var(--pp-brand-primary); }
.ci-linkbtn:hover:not(:disabled) { border-style: solid; border-color: var(--pp-brand-primary);
  background: color-mix(in oklab, var(--pp-brand-primary) 8%, transparent); }
.ci-linkbtn:disabled { opacity: 0.6; cursor: default; }

.ci-foot { margin-top: var(--pp-space-1); }
</style>
