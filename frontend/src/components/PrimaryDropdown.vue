<template>
  <Popover>
    <template #target="{ isOpen, togglePopover }">
      <Button
        :label="value"
        class="dropdown-button flex items-center justify-between bg-surface-white !px-2.5 py-1.5 text-base text-ink-gray-8 placeholder-ink-gray-4 transition-colors hover:bg-surface-white focus:bg-surface-white focus:shadow-sm focus:outline-none focus:ring-0"
        @click="togglePopover"
      >
        <div v-if="value" class="flex items-center gap-1.5 truncate">
          <span v-if="flag" :class="flag" class="pd-flag" />
          <span class="truncate">{{ value }}</span>
        </div>
        <div v-else class="text-base leading-5 text-ink-gray-4 truncate">
          {{ placeholder }}
        </div>
        <template #suffix>
          <FeatherIcon
            :name="isOpen ? 'chevron-up' : 'chevron-down'"
            class="h-4 text-ink-gray-5"
          />
        </template>
      </Button>
    </template>
    <template #body>
      <div
        class="my-2 p-1.5 min-w-40 space-y-1.5 divide-y divide-outline-gray-1 rounded-lg bg-surface-modal shadow-2xl ring-1 ring-black ring-opacity-5 focus:outline-none"
      >
        <div>
          <PrimaryDropdownItem
            v-for="option in options"
            :key="option.name || option.value"
            :option="option"
          />
          <div v-if="!options?.length">
            <div class="p-1.5 pl-3 pr-4 text-base text-ink-gray-4">
              {{ __('No {0} available', [label]) }}
            </div>
          </div>
        </div>
        <div class="pt-1.5">
          <Button
            variant="ghost"
            class="w-full !justify-start"
            :label="__('Create New')"
            iconLeft="plus"
            @click="create && create()"
          />
        </div>
      </div>
    </template>
  </Popover>
</template>

<script setup>
import PrimaryDropdownItem from '@/components/PrimaryDropdownItem.vue'
import { Popover } from 'frappe-ui'
import { computed } from 'vue'
import { detectCountry, flagClass } from '@/utils/phoneCountry'
import 'flag-icons/css/flag-icons.min.css'

const props = defineProps({
  value: { type: [String, Number], default: '' },
  placeholder: { type: String, default: '' },
  options: { type: Array, default: () => [] },
  create: { type: Function, default: null },
  label: { type: String, default: '' },
})

// Only phone-looking values ("+<dial>…") resolve a country → a flag; e-mails
// and other Dropdown values stay flag-less.
const flag = computed(() => {
  const c = detectCountry(props.value)
  return c ? flagClass(c.iso2) : null
})
</script>

<style scoped>
.dropdown-button {
  border-color: transparent;
  background: transparent;
}
.pd-flag {
  width: 18px;
  height: 13px;
  border-radius: 2px;
  box-shadow: 0 0 0 1px rgb(0 0 0 / 0.06);
  background-size: cover;
  flex-shrink: 0;
}
</style>
