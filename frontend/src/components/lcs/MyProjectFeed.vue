<!--
  MyProjectFeed
  =============
  Dashboard top strip: newest mails from the current user's LCS Projects
  (click to read / reply) plus the user's notifications (click to open).
  Data from lcs_integrations.projects.api.get_my_project_feed.
-->

<template>
  <div class="grid gap-3 md:grid-cols-2">
    <!-- Latest mails from my projects -->
    <div class="rounded-xl border bg-white p-3">
      <div class="mb-2 flex items-center justify-between">
        <span class="text-xs font-semibold uppercase tracking-wide text-gray-500">
          <FeatherIcon name="activity" class="mr-1 inline h-3 w-3" />
          {{ __('Latest from my projects') }}
        </span>
        <button class="text-gray-400 hover:text-gray-600" :title="__('Refresh')" @click="feed.reload()">
          <FeatherIcon name="refresh-cw" class="h-3.5 w-3.5" :class="feed.loading ? 'animate-spin' : ''" />
        </button>
      </div>
      <div v-if="!activity.length" class="py-6 text-center text-xs text-gray-400">
        {{ feed.loading ? __('Loading...') : __('No recent activity on your projects.') }}
      </div>
      <ul v-else class="divide-y">
        <li
          v-for="(a, i) in activity"
          :key="i"
          class="-mx-1 flex cursor-pointer items-start gap-2 rounded px-1 py-2 hover:bg-gray-50"
          @click="openMail(a)"
        >
          <FeatherIcon :name="mediumIcon(a.medium)" class="mt-0.5 h-4 w-4 shrink-0 text-lcs-secondary" />
          <div class="min-w-0 flex-1">
            <p class="truncate text-sm text-gray-900">
              <span
                v-if="a.direction"
                class="mr-1 rounded px-1 py-0.5 text-[9px] font-bold uppercase"
                :class="a.direction === 'Sent' ? 'bg-blue-50 text-blue-600' : 'bg-green-50 text-green-600'"
              >{{ a.direction === 'Sent' ? __('out') : __('in') }}</span>
              {{ a.title }}
            </p>
            <p class="truncate text-xs text-gray-400">
              <router-link
                :to="{ name: 'LCS Project', params: { id: a.project } }"
                class="hover:text-lcs-secondary"
                @click.stop
              >{{ a.project_label || a.project }}</router-link>
              <span v-if="a.meta"> · {{ a.meta }}</span>
            </p>
          </div>
          <span class="shrink-0 whitespace-nowrap text-[10px] text-gray-400">{{ rel(a.time) }}</span>
        </li>
      </ul>
    </div>

    <!-- Notifications -->
    <div class="rounded-xl border bg-white p-3">
      <div class="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-500">
        <FeatherIcon name="bell" class="mr-1 inline h-3 w-3" />
        {{ __('Notifications') }}
      </div>
      <div v-if="!notifications.length" class="py-6 text-center text-xs text-gray-400">
        {{ feed.loading ? __('Loading...') : __('No notifications.') }}
      </div>
      <ul v-else class="divide-y">
        <li
          v-for="(n, i) in notifications"
          :key="i"
          class="-mx-1 flex items-start gap-2 rounded px-1 py-2"
          :class="n.document_name ? 'cursor-pointer hover:bg-gray-50' : ''"
          @click="openNotification(n)"
        >
          <span class="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full" :class="n.read ? 'bg-gray-200' : 'bg-lcs-primary'" />
          <div class="min-w-0 flex-1">
            <p class="text-sm text-gray-900" :class="n.read ? 'font-normal' : 'font-medium'">{{ n.subject }}</p>
            <p v-if="n.document_name" class="truncate text-xs text-gray-400">{{ n.document_type }} · {{ n.document_name }}</p>
          </div>
          <span class="shrink-0 whitespace-nowrap text-[10px] text-gray-400">{{ rel(n.creation) }}</span>
        </li>
      </ul>
    </div>
  </div>

  <!-- Mail reader / reply -->
  <Dialog v-model="mailOpen" :options="{ size: 'xl' }">
    <template #body>
      <div v-if="selectedMail" class="-m-1">
        <!-- Header -->
        <div class="flex items-center gap-3 border-b pb-3">
          <div
            class="flex h-11 w-11 shrink-0 items-center justify-center rounded-full"
            :class="selectedMail.direction === 'Sent' ? 'bg-blue-50 text-blue-600' : 'bg-green-50 text-green-700'"
          >
            <FeatherIcon :name="mediumIcon(selectedMail.medium)" class="h-5 w-5" />
          </div>
          <div class="min-w-0 flex-1">
            <h3 class="truncate text-[15px] font-semibold text-gray-900">{{ selectedMail.title }}</h3>
            <div class="mt-1 flex flex-wrap items-center gap-2 text-xs">
              <span
                class="rounded px-1.5 py-0.5 text-[10px] font-bold uppercase"
                :class="selectedMail.direction === 'Sent' ? 'bg-blue-50 text-blue-600' : 'bg-green-50 text-green-600'"
              >{{ selectedMail.direction === 'Sent' ? __('outgoing') : __('incoming') }}</span>
              <span v-if="selectedMail.medium && selectedMail.medium !== 'Email'" class="rounded bg-gray-100 px-1.5 py-0.5 text-[10px] font-medium uppercase text-gray-500">{{ __(selectedMail.medium) }}</span>
              <span class="text-gray-400">{{ rel(selectedMail.time) }}</span>
            </div>
          </div>
        </div>

        <!-- Meta -->
        <div class="grid grid-cols-[3.5rem_1fr] gap-x-3 gap-y-1.5 py-3 text-xs">
          <span class="text-gray-400">{{ __('From') }}</span>
          <span class="truncate text-gray-700">{{ selectedMail.meta }}</span>
          <template v-if="selectedMail.recipients">
            <span class="text-gray-400">{{ __('To') }}</span>
            <span class="truncate text-gray-700">{{ selectedMail.recipients }}</span>
          </template>
          <span class="text-gray-400">{{ __('Project') }}</span>
          <router-link :to="{ name: 'LCS Project', params: { id: selectedMail.project } }" class="truncate font-medium text-lcs-secondary hover:underline" @click="mailOpen = false">
            {{ selectedMail.project_label || selectedMail.project }}
          </router-link>
        </div>

        <!-- Body -->
        <div
          class="prose prose-sm min-h-[110px] max-h-[42vh] max-w-none overflow-auto border-y bg-gray-50/60 px-4 py-4 text-sm leading-relaxed text-gray-800"
          v-html="selectedMail.content || '<em class=\'not-prose text-gray-400\'>—</em>'"
        />

        <!-- Footer -->
        <div class="flex items-center justify-end gap-2 pt-3">
          <Button :label="__('Open in project')" iconLeft="external-link" @click="goToProject(selectedMail)" />
          <Button variant="solid" iconLeft="corner-up-left" :label="__('Reply')" @click="replyMail(selectedMail)" />
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { createResource, FeatherIcon, Dialog, Button } from 'frappe-ui'

const router = useRouter()

const feed = createResource({
  url: 'lcs_integrations.projects.api.get_my_project_feed',
  auto: true,
})
const activity = computed(() => feed.data?.activity || [])
const notifications = computed(() => feed.data?.notifications || [])

const mailOpen = ref(false)
const selectedMail = ref(null)
function openMail(a) {
  selectedMail.value = a
  mailOpen.value = true
}
function goToProject(m) {
  mailOpen.value = false
  router.push({ name: 'LCS Project', params: { id: m.project } })
}
function replyMail(m) {
  // Open the user's mail client. In-app send requires the mailbox to be
  // connected via Microsoft Graph (Settings → Mail → Outlook).
  const to = m.direction === 'Sent' ? m.recipients || '' : m.meta || ''
  const subject = 'AW: ' + (m.title || '').replace(/^(AW|RE):\s*/i, '')
  window.location.href = `mailto:${encodeURIComponent(to)}?subject=${encodeURIComponent(subject)}`
}

const SPA_ROUTES = {
  'LCS Project': 'LCS Project',
  'CRM Deal': 'Deal',
  'CRM Lead': 'Lead',
  Contact: 'Contact',
  'CRM Organization': 'Organization',
}
function openNotification(n) {
  if (!n.document_type || !n.document_name) return
  const routeName = SPA_ROUTES[n.document_type]
  if (routeName) {
    const paramKey = n.document_type === 'LCS Project' ? 'id' : `${routeName.toLowerCase()}Id`
    router.push({ name: routeName, params: { [paramKey]: n.document_name } }).catch(() => {
      window.open(`/app/${n.document_type.toLowerCase().replace(/ /g, '-')}/${encodeURIComponent(n.document_name)}`, '_blank')
    })
  } else {
    window.open(`/app/${n.document_type.toLowerCase().replace(/ /g, '-')}/${encodeURIComponent(n.document_name)}`, '_blank')
  }
}

const MEDIUM_ICONS = {
  Email: 'mail', Phone: 'phone', Meeting: 'users', Event: 'calendar',
  Visit: 'map-pin', SMS: 'message-square', Chat: 'message-circle',
}
function mediumIcon(m) {
  return MEDIUM_ICONS[m] || 'mail'
}

function rel(ts) {
  if (!ts) return ''
  const d = new Date(String(ts).replace(' ', 'T'))
  const s = Math.floor((Date.now() - d.getTime()) / 1000)
  if (s < 60) return __('just now')
  if (s < 3600) return Math.floor(s / 60) + ' min'
  if (s < 86400) return Math.floor(s / 3600) + ' h'
  return Math.floor(s / 86400) + ' d'
}
</script>
