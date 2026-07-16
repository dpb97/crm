<!--
  MoneyDual
  =========
  Shows a monetary amount in its own (target) currency AND its EUR
  equivalent, everywhere offer amounts appear. The EUR figure uses the
  offer's frozen rate once sent, or the live rate while it's a draft. A
  tooltip exposes the rate itself + whether it is frozen or live, and the
  current live rate for reference.

  Props:
    amount     Number  — value in `currency`
    currency   String  — e.g. "USD" (defaults to EUR)
    valueEur   Number  — precomputed EUR value (frozen or live); optional
    rate       Number  — <currency>→EUR rate used for valueEur; optional
    frozenAt   String  — datetime the rate was frozen; null/"" = live draft
    size       String  — 'sm' | 'md' (default) | 'lg'
-->

<template>
  <span v-if="amount == null || amount === ''" class="text-gray-300">—</span>
  <Tooltip v-else :text="tooltip">
    <span class="inline-flex flex-col leading-tight">
      <span class="font-semibold tabular-nums text-gray-900" :class="amountCls">
        {{ fmt(amount, currency) }}
      </span>
      <span v-if="showEur" class="tabular-nums text-gray-400" :class="eurCls">
        ≈ {{ fmt(eurAmount, 'EUR') }}
        <span v-if="!frozenAt" class="ml-0.5 rounded bg-amber-50 px-1 text-[9px] font-medium text-amber-600">{{ __('live') }}</span>
      </span>
    </span>
  </Tooltip>
</template>

<script setup>
import { computed } from 'vue'
import { Tooltip } from 'frappe-ui'

const props = defineProps({
  amount: { type: [Number, String], default: null },
  currency: { type: String, default: 'EUR' },
  valueEur: { type: [Number, String], default: null },
  rate: { type: [Number, String], default: null },
  frozenAt: { type: String, default: '' },
  size: { type: String, default: 'md' },
})

const cur = computed(() => (props.currency || 'EUR').toUpperCase())
const showEur = computed(() => cur.value !== 'EUR' && eurAmount.value != null)

const eurAmount = computed(() => {
  if (props.valueEur != null && props.valueEur !== '') return Number(props.valueEur)
  if (props.rate) return Number(props.amount) * Number(props.rate)
  return null
})

function fmt(n, ccy) {
  if (n == null || n === '') return '—'
  try {
    return new Intl.NumberFormat('de-DE', { style: 'currency', currency: ccy, maximumFractionDigits: 0 }).format(Number(n))
  } catch (e) {
    return `${ccy} ${Number(n).toLocaleString('de-DE')}`
  }
}

const tooltip = computed(() => {
  if (cur.value === 'EUR') return __('Amount in EUR')
  const r = props.rate ? Number(props.rate).toFixed(4) : null
  if (!r) return __('EUR equivalent')
  const kind = props.frozenAt ? __('frozen') : __('live')
  const when = props.frozenAt ? ` (${__('captured')} ${String(props.frozenAt).replace('T', ' ').slice(0, 16)})` : ''
  return `1 ${cur.value} = ${r} EUR · ${kind}${when}`
})

const amountCls = computed(() => ({ sm: 'text-xs', md: 'text-sm', lg: 'text-lg' }[props.size] || 'text-sm'))
const eurCls = computed(() => ({ sm: 'text-[10px]', md: 'text-xs', lg: 'text-sm' }[props.size] || 'text-xs'))
</script>
