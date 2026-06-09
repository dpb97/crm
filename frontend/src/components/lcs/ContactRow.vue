<!--
  ContactRow
  ==========
  One project contact: avatar (with photo upload), name, role, and a
  "Share" action. Self-loads the Contact's display fields by name so the
  parent only needs to pass the contact id.

  Photo upload sets Contact.image; the lcs_integrations Contact on_update
  hook then pushes the photo to the shared mailbox via Microsoft Graph.
-->

<template>
  <div class="flex items-center gap-3 border-b py-2.5 last:border-b-0">
    <!-- Avatar + photo upload -->
    <div class="relative flex-shrink-0">
      <Avatar :image="doc.image" :label="doc.full_name || contact" size="lg" />
      <FileUploader
        :validateFile="validateIsImageFile"
        @success="onPhotoUploaded"
      >
        <template #default="{ openFileSelector, uploading }">
          <button
            type="button"
            class="absolute -bottom-1 -right-1 flex h-5 w-5 items-center justify-center rounded-full border border-white bg-lcs-secondary text-white shadow transition hover:bg-lcs-primary disabled:opacity-50"
            :aria-label="__('Change photo')"
            :disabled="uploading"
            @click="openFileSelector"
          >
            <FeatherIcon :name="uploading ? 'loader' : 'camera'" class="h-3 w-3" :class="uploading ? 'animate-spin' : ''" />
          </button>
        </template>
      </FileUploader>
    </div>

    <!-- Name + role -->
    <div class="min-w-0 flex-1">
      <p class="truncate text-sm font-medium text-gray-900">{{ doc.full_name || contact }}</p>
      <p class="truncate text-xs text-gray-500">{{ doc.designation || '—' }}</p>
    </div>

    <!-- Release (visible only while the contact is still private) -->
    <button
      v-if="!doc.lcs_released"
      type="button"
      class="flex items-center gap-1 rounded-md px-2 py-1 text-xs text-amber-600 transition hover:bg-amber-50"
      :title="__('Only you can see this contact until you release it')"
      @click="release"
    >
      <FeatherIcon name="lock" class="h-3.5 w-3.5" />
      {{ __('Release') }}
    </button>

    <!-- Share -->
    <button
      type="button"
      class="flex items-center gap-1 rounded-md px-2 py-1 text-xs text-gray-500 transition hover:bg-gray-100 hover:text-gray-700"
      @click="shareOpen = true"
    >
      <FeatherIcon name="share-2" class="h-3.5 w-3.5" />
      {{ __('Share') }}
    </button>

    <ContactShareDialog v-model="shareOpen" :contact="contact" />
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { Avatar, FileUploader, FeatherIcon, call, toast } from 'frappe-ui'
import { validateIsImageFile } from '@/utils'
import ContactShareDialog from '@/components/lcs/ContactShareDialog.vue'

const props = defineProps({
  contact: { type: String, required: true },
})

const doc = ref({ full_name: '', designation: '', image: '', lcs_released: 1 })
const shareOpen = ref(false)

async function load() {
  if (!props.contact) return
  try {
    const res = await call('frappe.client.get_value', {
      doctype: 'Contact',
      filters: { name: props.contact },
      fieldname: ['full_name', 'designation', 'image', 'lcs_released'],
    })
    if (res) doc.value = res
  } catch {
    // Leave the fallback (contact id) in place on failure.
  }
}

async function release() {
  try {
    await call('lcs_integrations.visibility.contact_visibility.release_contact', {
      contact: props.contact,
    })
    doc.value.lcs_released = 1
    toast.success(__('Contact released'))
  } catch (err) {
    toast.error(err.message || __('Could not release contact'))
  }
}

async function onPhotoUploaded(file) {
  const url = file?.file_url || ''
  if (!url) return
  try {
    await call('frappe.client.set_value', {
      doctype: 'Contact',
      name: props.contact,
      fieldname: 'image',
      value: url,
    })
    doc.value.image = url
    toast.success(__('Photo updated'))
  } catch (err) {
    toast.error(err.message || __('Could not update photo'))
  }
}

watch(() => props.contact, load, { immediate: true })
</script>
