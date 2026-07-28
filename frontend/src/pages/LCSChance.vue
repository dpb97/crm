<!--
  LCSChance — Chance-Detail (Doppelklick aus der Chancen-Liste), klickdummy.
  ============================================================
  Vier Blöcke: Ausschreibung · Scoutbewertung (Score/Relevanz/Begründung,
  kommt später aus dem Pilot) · Geo (Koordinaten + Projektlandkarte) · Vertrieb
  (Status, Verantwortlich, Notiz, CRM-Lead, „Kontakt aufgenommen → Lead").
  Daten: lcs_integrations.projects.api.get_chance.
-->
<template>
  <div class="flex min-h-0 flex-1 flex-col">
    <LayoutHeader>
      <template #left-header>
        <Breadcrumbs :items="[
          { label: 'Vertrieb' },
          { label: __('Chancen'), route: { name: 'LCS Chances' } },
          { label: c?.chance_no || id },
        ]" />
      </template>
      <template #right-header>
        <Button v-if="c && !c.crm_lead" variant="solid" :label="`${__('Contact made')} → Lead`" iconLeft="user-plus" :loading="converting" @click="toLead" />
        <Button v-else-if="c?.crm_lead" :label="__('Open lead')" iconLeft="external-link" @click="$router.push({ name: 'Lead', params: { leadId: c.crm_lead } })" />
      </template>
    </LayoutHeader>

    <div class="chd">
      <div v-if="c" class="chd-inner">
        <!-- Ausschreibung -->
        <section class="chd-card">
          <header class="chd-ch">{{ __('Tender') }}<span class="chd-ch-m">{{ c.chance_no }} · {{ __('Source') }} {{ c.source }}<template v-if="c.country"> · {{ __('Country') }} {{ c.country }}</template></span></header>
          <dl class="chd-kv">
            <div><dt>{{ __('Client') }}</dt><dd>{{ c.client || '—' }}</dd></div>
            <div><dt>{{ __('Country') }}</dt><dd>{{ c.country || '—' }}</dd></div>
            <div><dt>{{ __('Source') }}</dt><dd>{{ c.source }}<template v-if="c.source_detail"> · {{ c.source_detail }}</template></dd></div>
            <div><dt>{{ __('External ID') }}</dt><dd>{{ c.external_id || '—' }}</dd></div>
            <div><dt>{{ __('CPV Codes') }}</dt><dd>{{ c.cpv_codes || '—' }}</dd></div>
            <div><dt>{{ __('Order Value') }}</dt><dd>{{ eur(c.order_value) }}</dd></div>
            <div><dt>{{ __('Published On') }}</dt><dd>{{ fmtDate(c.published_on) }}</dd></div>
            <div><dt>{{ __('Deadline') }}</dt><dd>{{ c.deadline ? fmtDate(c.deadline) + ' — ' + dueLabel(c.deadline) : '—' }}</dd></div>
          </dl>
        </section>

        <!-- Chancen-Matrix (statt Scoutbewertung — direkt an der Chance pflegbar) -->
        <section class="chd-card">
          <header class="chd-ch">{{ __('Opportunity Matrix') }}<span class="chd-ch-m">{{ __('Rate each dimension from 0 (weak) to 100 (strong). Use mouse or arrow keys.') }}</span></header>
          <OpportunityMatrix
            :technical-fit="c.technical_fit || 0"
            :commercial-fit="c.commercial_fit || 0"
            :relationship="c.relationship_strength || 0"
            :competition="c.competition_level || 0"
            :strategic-importance="c.strategic_importance || 0"
            @update="onMatrixUpdate"
          />
          <p v-if="c.summary_de || c.reasoning" class="chd-scoutnote">
            <span class="chd-scoutnote-cap">{{ __('Note from the Pilot') }}:</span> {{ c.summary_de || c.reasoning }}
          </p>
        </section>

        <div class="chd-2col">
          <!-- Geo -->
          <section class="chd-card">
            <header class="chd-ch">{{ __('Geo') }}</header>
            <dl class="chd-kv chd-kv--wide">
              <div><dt>{{ __('Coordinates') }}</dt><dd>{{ coords }}</dd></div>
              <div><dt>{{ __('Geo Confidence') }}</dt><dd><span v-if="c.geo_confidence" class="chd-rel"><i class="chd-dot" />{{ c.geo_confidence }}</span><span v-else>—</span></dd></div>
            </dl>
            <div v-if="c.latitude" class="chd-actions">
              <Button variant="solid" :label="__('Show on projects map')" @click="$router.push({ name: 'LCS Projects Map' })" />
            </div>
          </section>

          <!-- Vertrieb -->
          <section class="chd-card">
            <header class="chd-ch">{{ __('Sales') }}</header>
            <dl class="chd-kv chd-kv--wide">
              <div><dt>{{ __('Status') }}</dt><dd><PpPill :tone="statusTone(c.status)">{{ c.status }}</PpPill></dd></div>
              <div><dt>{{ __('Responsible') }}</dt><dd>{{ c.responsible || '—' }}</dd></div>
              <div><dt>{{ __('Sales Note') }}</dt><dd>{{ c.sales_note || '—' }}</dd></div>
              <div><dt>{{ __('CRM Lead') }}</dt><dd>
                <a v-if="c.crm_lead" class="chd-link" @click="$router.push({ name: 'Lead', params: { leadId: c.crm_lead } })">{{ c.crm_lead }}</a>
                <span v-else>— <span class="chd-hint">({{ __('created on “Contacted”') }})</span></span>
              </dd></div>
              <div><dt>{{ __('Last Synced') }}</dt><dd>{{ fmtDate(c.last_synced) }}</dd></div>
            </dl>
          </section>
        </div>
      </div>

      <div v-else class="chd-loading">{{ chance.loading ? __('Loading …') : __('Chance not found') }}</div>
    </div>
  </div>
</template>

<script setup>
import { computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { createResource, call, toast, Breadcrumbs, Button } from 'frappe-ui'
import LayoutHeader from '@/components/LayoutHeader.vue'
import PpPill from '@/components/pp/PpPill.vue'
import OpportunityMatrix from '@/components/lcs/OpportunityMatrix.vue'

const props = defineProps({ id: { type: String, required: true } })
const router = useRouter()

const chance = createResource({ url: 'lcs_integrations.projects.api.get_chance', makeParams: () => ({ name: props.id }), auto: true })
const c = computed(() => chance.data || null)
watch(() => props.id, () => chance.reload())

const coords = computed(() => (c.value?.latitude ? `${c.value.latitude.toFixed(5)}° N · ${c.value.longitude.toFixed(5)}° O` : '—'))

const converting = computed(() => false)
function toLead() {
  call('lcs_integrations.projects.api.chance_to_lead', { name: props.id })
    .then((res) => {
      toast({ title: __('Lead created'), icon: 'check-circle', iconClasses: 'text-green-500' })
      if (res?.lead) router.push({ name: 'Lead', params: { leadId: res.lead } })
    })
    .catch((e) => toast({ title: __('Could not create the lead.'), text: e?.messages?.[0] || e?.message || '', icon: 'alert-circle', iconClasses: 'text-red-500' }))
}

// Chancen-Matrix: Regler → optimistisch lokal + auf der LCS Chance speichern.
function onMatrixUpdate({ field, value }) {
  if (c.value) c.value[field] = value
  call('frappe.client.set_value', { doctype: 'LCS Chance', name: props.id, fieldname: field, value })
    .catch((e) => toast({ title: __('Could not save.'), text: e?.messages?.[0] || e?.message || '', icon: 'alert-circle', iconClasses: 'text-red-500' }))
}

function statusTone(s) {
  if (/relevant/i.test(s)) return 'success'
  if (/kontakt/i.test(s)) return 'brand'
  if (/keine/i.test(s)) return 'neutral'
  return 'info'
}
function scoreColor(v) { return v >= 70 ? 'var(--pp-state-success)' : v >= 40 ? 'var(--pp-state-warning)' : 'var(--pp-state-danger)' }
function eur(v) {
  const n = Number(v) || 0
  if (n >= 1_000_000) return (n / 1_000_000).toLocaleString('de-DE', { maximumFractionDigits: 1 }) + ' M€'
  if (n >= 1_000) return Math.round(n / 1_000).toLocaleString('de-DE') + ' k€'
  return '€' + Math.round(n)
}
function fmtDate(v) {
  if (!v) return '—'
  const d = new Date(String(v).replace(' ', 'T'))
  return isNaN(d) ? String(v) : new Intl.DateTimeFormat('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric' }).format(d)
}
function dueLabel(v) {
  const n = Math.round((new Date(String(v).replace(' ', 'T')).getTime() - Date.now()) / 86400000)
  if (isNaN(n)) return ''
  return n < 0 ? `${__('overdue by')} ${-n} ${__('days')}` : `${__('in')} ${n} ${__('days')}`
}
</script>

<style scoped>
.chd { flex: 1; min-height: 0; overflow: auto; background: var(--pp-bg-base); }
.chd-inner { padding: var(--pp-space-6); display: flex; flex-direction: column; gap: var(--pp-space-4); }
.chd-2col { display: grid; grid-template-columns: 1fr 1fr; gap: var(--pp-space-4); }

.chd-card { background: var(--pp-bg-surface); border: 1px solid var(--pp-border-subtle);
  border-radius: var(--pp-radius-ui); box-shadow: var(--pp-shadow-xs); padding: var(--pp-space-4); }
.chd-ch { display: flex; align-items: baseline; justify-content: space-between; gap: var(--pp-space-3);
  margin-bottom: var(--pp-space-3); font-size: var(--pp-fs-14, 14px); font-weight: var(--pp-weight-bold); color: var(--pp-text-primary); }
.chd-ch-m { font-size: 11px; font-weight: var(--pp-weight-regular); color: var(--pp-text-tertiary); text-align: right; }

.chd-kv { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: var(--pp-space-2) var(--pp-space-6); margin: 0; }
.chd-kv--wide { grid-template-columns: 1fr; }
.chd-kv > div { display: grid; grid-template-columns: 160px 1fr; gap: var(--pp-space-3); align-items: baseline; }
.chd-kv dt { font-size: var(--pp-fs-12, 12px); color: var(--pp-text-tertiary); }
.chd-kv dd { margin: 0; font-size: var(--pp-fs-13, 13px); color: var(--pp-text-primary); }

.chd-scorerow { display: flex; align-items: center; gap: var(--pp-space-3); margin-bottom: var(--pp-space-3); flex-wrap: wrap; }
.chd-scorebar { width: 200px; height: 8px; border-radius: var(--pp-radius-full); background: var(--pp-bg-sunken); overflow: hidden; }
.chd-scorebar i { display: block; height: 100%; }
.chd-scoreval { font-size: var(--pp-fs-15, 15px); font-weight: var(--pp-weight-bold); color: var(--pp-text-primary); font-variant-numeric: tabular-nums; }
.chd-rel { display: inline-flex; align-items: center; gap: 5px; font-size: var(--pp-fs-12, 12px); color: var(--pp-state-success); font-weight: var(--pp-weight-medium); }
.chd-dot { width: 6px; height: 6px; border-radius: var(--pp-radius-full); background: currentColor; }
.chd-cat { font-size: var(--pp-fs-13, 13px); color: var(--pp-text-secondary); }

.chd-scoutnote { margin: var(--pp-space-3) 0 0; font-size: var(--pp-fs-12, 12px); color: var(--pp-text-tertiary); }
.chd-scoutnote-cap { font-weight: var(--pp-weight-semibold); color: var(--pp-text-secondary); }
.chd-actions { margin-top: var(--pp-space-3); }
.chd-link { cursor: pointer; color: var(--pp-brand-primary); font-weight: var(--pp-weight-medium); }
.chd-link:hover { text-decoration: underline; }
.chd-hint { color: var(--pp-text-tertiary); }
.chd-loading { padding: var(--pp-space-8); text-align: center; color: var(--pp-text-tertiary); }

@media (max-width: 1080px) { .chd-2col { grid-template-columns: 1fr; } .chd-kv { grid-template-columns: 1fr; } }
</style>
