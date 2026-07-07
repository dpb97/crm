<!--
  FollowButton — eye toggle for Frappe's document-follow. Following a
  record puts its changes into the user's document-follow digest mails.
-->

<template>
  <Button
    :tooltip="following ? __('Unfollow') : __('Follow')"
    :icon="following ? 'eye' : 'eye-off'"
    :loading="busy"
    @click="toggle"
  />
</template>

<script setup>
import { ref, watch } from 'vue'
import { Button, call } from 'frappe-ui'
import { sessionStore } from '@/stores/session'

const props = defineProps({
  doctype: { type: String, required: true },
  docname: { type: String, required: true },
})

const session = sessionStore()
const following = ref(false)
const busy = ref(false)

async function loadState() {
  if (!props.docname) return
  try {
    const count = await call('frappe.client.get_count', {
      doctype: 'Document Follow',
      filters: {
        ref_doctype: props.doctype,
        ref_docname: props.docname,
        user: session.user,
      },
    })
    following.value = count > 0
  } catch (e) {
    /* follow state is cosmetic — ignore */
  }
}
watch(() => props.docname, loadState, { immediate: true })

async function toggle() {
  busy.value = true
  try {
    await call('frappe.desk.form.document_follow.update_follow', {
      doctype: props.doctype,
      doc_name: props.docname,
      following: !following.value,
    })
    following.value = !following.value
  } catch (e) {
    /* leave state as-is */
  } finally {
    busy.value = false
  }
}
</script>
