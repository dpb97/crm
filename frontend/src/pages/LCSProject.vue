<template>
  <LayoutHeader>
    <template #left-header>
      <Breadcrumbs :items="breadcrumbs" />
    </template>
    <template v-if="doc.name" #right-header>
      <div class="flex items-center gap-3">
        <span v-if="lastSaved" class="text-xs text-gray-400">{{ __('Saved') }} {{ lastSaved }}</span>
        <Dropdown v-if="phaseDropdownOptions.length" :options="phaseDropdownOptions" placement="right">
          <template #default="{ open }">
            <Button :iconRight="open ? 'chevron-up' : 'chevron-down'">
              <template #prefix>
                <span class="h-2 w-2 rounded-full" :class="phaseDotClass(doc.phase)" />
              </template>
              {{ __(doc.phase || 'Set Phase') }}
            </Button>
          </template>
        </Dropdown>
      </div>
    </template>
  </LayoutHeader>

  <!-- Loading state -->
  <div v-if="project.loading && !doc.name" class="flex h-full items-center justify-center">
    <div class="flex flex-col items-center gap-3">
      <div class="h-8 w-8 animate-spin rounded-full border-2 border-gray-200 border-t-lcs-secondary" />
      <span class="text-sm text-gray-400">{{ __('Loading project...') }}</span>
    </div>
  </div>

  <!-- Not found state -->
  <div v-else-if="!doc.name && !project.loading" class="flex h-full items-center justify-center">
    <div class="flex flex-col items-center text-center">
      <div class="rounded-full bg-red-50 p-4">
        <FeatherIcon name="alert-circle" class="h-8 w-8 text-red-400" />
      </div>
      <h2 class="mt-4 text-lg font-medium text-gray-900">{{ __('Project Not Found') }}</h2>
      <Button class="mt-4" variant="outline" @click="$router.push({ name: 'LCS Projects' })" :label="__('Back to Projects')" iconLeft="arrow-left" />
    </div>
  </div>

  <!-- Main content -->
  <div v-else class="flex h-full flex-col overflow-hidden">

    <!-- 🎯 STATUS HERO BAR — H1: Visibility (status always visible at top) -->
    <div class="border-b bg-gradient-to-r from-white via-white to-gray-50 px-5 py-4">
      <div class="flex flex-wrap items-center gap-6">
        <!-- Project title + number -->
        <div class="min-w-0 flex-shrink">
          <div class="flex items-center gap-2">
            <h1 class="truncate text-xl font-bold text-gray-900">{{ doc.project_name }}</h1>
            <Tooltip :text="typeFullName(doc.project_type)">
              <span :class="typeClass(doc.project_type)" class="shrink-0 rounded-full px-2 py-0.5 text-xs font-bold">
                {{ doc.project_type }}
              </span>
            </Tooltip>
          </div>
          <div class="mt-0.5 flex items-center gap-2 text-sm font-mono text-gray-500">
            <span>{{ doc.project_number }}</span>
            <span class="text-gray-300">•</span>
            <span class="cursor-copy hover:text-gray-700" @click="copyId">
              {{ projectId }}
              <FeatherIcon v-if="justCopied" name="check" class="ml-1 inline h-3 w-3 text-green-500" />
            </span>
          </div>
        </div>

        <!-- Vertical divider -->
        <div class="h-10 w-px bg-gray-200" />

        <!-- PHASE — prominent -->
        <div>
          <div class="text-[10px] font-bold uppercase tracking-wider text-gray-400">{{ __('Phase') }}</div>
          <div class="mt-1 flex items-center gap-1.5">
            <span :class="phaseClass(doc.phase)" class="inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-sm font-semibold">
              <span class="h-2 w-2 rounded-full" :class="phaseDotClass(doc.phase)" />
              {{ __(doc.phase) }}
            </span>
          </div>
        </div>

        <!-- STATUS — prominent -->
        <div>
          <div class="text-[10px] font-bold uppercase tracking-wider text-gray-400">{{ __('Status') }}</div>
          <div class="mt-1">
            <span :class="statusClass(doc.status)" class="inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-sm font-semibold">
              <span class="h-2 w-2 rounded-full" :class="statusDotClass(doc.status)" />
              {{ __(doc.status || 'Open') }}
            </span>
          </div>
        </div>

        <!-- Latest Offer Status (if exists) -->
        <div v-if="latestOffer">
          <div class="flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider text-gray-400">
            <FeatherIcon name="file-text" class="h-3 w-3" />
            {{ __('Current Offer') }}
          </div>
          <div class="mt-1 flex items-center gap-2">
            <span :class="offerStatusClass(latestOffer.status)" class="inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-sm font-semibold">
              <span class="h-2 w-2 rounded-full" :class="offerStatusDotClass(latestOffer.status)" />
              {{ __(latestOffer.status) }}
            </span>
            <span class="text-xs font-mono text-gray-500">v{{ latestOffer.version }}</span>
          </div>
        </div>

        <!-- Spacer -->
        <div class="flex-1" />

        <!-- Value + probability -->
        <div class="text-right">
          <div class="text-[10px] font-bold uppercase tracking-wider text-gray-400">{{ __('Value') }}</div>
          <div class="mt-0.5 flex items-center justify-end gap-2">
            <span class="text-lg font-bold text-gray-900">
              {{ doc.estimated_value ? formatCurrency(doc.estimated_value) : '—' }}
            </span>
            <span v-if="doc.probability" :class="probabilityClass(doc.probability)" class="rounded-md bg-gray-50 px-2 py-0.5 text-xs font-bold">
              {{ Math.round(doc.probability) }}%
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- Main layout: tabs + side panel -->
    <div class="flex flex-1 overflow-hidden">
      <Tabs
        v-model="tabIndex"
        as="div"
        :tabs="tabs"
        class="flex flex-1 overflow-hidden flex-col [&_[role='tab']]:px-0 [&_[role='tab']]:shrink-0 [&_[role='tablist']]:px-5 [&_[role='tablist']::-webkit-scrollbar]:h-0 [&_[role='tablist']]:min-h-[45px] [&_[role='tablist']]:gap-7.5 [&_[role='tabpanel']:not([hidden])]:flex [&_[role='tabpanel']:not([hidden])]:grow"
      >
        <template #tab-panel>
          <div class="flex-1 overflow-y-auto p-5">
            <!-- Overview Tab -->
            <div v-if="activeTab === 'Overview'" class="space-y-5">
              <!-- 📝 NOTES — PINNED AT TOP, ALWAYS VISIBLE -->
              <section class="rounded-xl border border-amber-200 bg-amber-50/50 p-4">
                <div class="mb-2 flex items-center justify-between">
                  <h3 class="flex items-center gap-2 text-sm font-semibold text-amber-900">
                    <FeatherIcon name="edit-3" class="h-4 w-4" />
                    {{ __('Notes') }}
                    <span v-if="doc.notes" class="rounded-full bg-amber-200 px-1.5 py-0.5 text-[10px] text-amber-800">
                      {{ __('active') }}
                    </span>
                  </h3>
                  <Button
                    v-if="!editingNotes"
                    variant="ghost"
                    size="sm"
                    iconLeft="edit-2"
                    @click="startNotesEdit"
                    :label="doc.notes ? __('Edit') : __('Add')"
                    class="text-amber-700 hover:bg-amber-100"
                  />
                </div>
                <div v-if="editingNotes" class="space-y-2">
                  <textarea
                    v-model="editNotesValue"
                    class="w-full rounded-lg border border-amber-200 bg-white px-3 py-2 text-sm text-gray-800 focus:border-amber-400 focus:ring-1 focus:ring-amber-400"
                    rows="5"
                    :placeholder="__('Write project notes, internal reminders, or next steps...')"
                    ref="notesInput"
                  />
                  <div class="flex gap-2">
                    <Button variant="solid" size="sm" @click="saveNotes" :label="__('Save')" iconLeft="check" />
                    <Button variant="ghost" size="sm" @click="cancelNotesEdit" :label="__('Cancel')" />
                  </div>
                </div>
                <div v-else-if="doc.notes" class="whitespace-pre-wrap text-sm text-gray-800">
                  {{ doc.notes }}
                </div>
                <div v-else class="text-sm italic text-amber-700/70">
                  {{ __('No notes yet. Click Add to write project notes.') }}
                </div>
              </section>

              <!-- Description -->
              <section>
                <h3 class="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-gray-400">
                  <FeatherIcon name="file-text" class="h-3.5 w-3.5" />
                  {{ __('Description') }}
                </h3>
                <div v-if="editingDescription" class="space-y-2">
                  <textarea
                    v-model="editDescriptionValue"
                    class="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm text-gray-800 focus:border-lcs-secondary focus:ring-1 focus:ring-lcs-secondary"
                    rows="4"
                    :placeholder="__('Add a project description...')"
                    ref="descriptionInput"
                  />
                  <div class="flex gap-2">
                    <Button variant="solid" size="sm" @click="saveDescription" :label="__('Save')" />
                    <Button variant="ghost" size="sm" @click="cancelDescriptionEdit" :label="__('Cancel')" />
                  </div>
                </div>
                <div v-else @click="startDescriptionEdit" class="group cursor-pointer">
                  <p v-if="doc.project_description" class="whitespace-pre-wrap text-sm text-gray-800 group-hover:bg-gray-50 rounded-lg p-2 -m-2 transition">
                    {{ doc.project_description }}
                  </p>
                  <p v-else class="rounded-lg border border-dashed border-gray-200 p-4 text-center text-sm text-gray-400 hover:border-gray-300 hover:text-gray-500 transition">
                    {{ __('Click to add a description') }}
                  </p>
                </div>
              </section>

              <!-- Key Metrics -->
              <section v-if="doc.estimated_value || doc.probability">
                <h3 class="mb-3 flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-gray-400">
                  <FeatherIcon name="bar-chart-2" class="h-3.5 w-3.5" />
                  {{ __('Key Metrics') }}
                </h3>
                <div class="grid grid-cols-2 gap-3 sm:grid-cols-3">
                  <div v-if="doc.estimated_value" class="rounded-lg border bg-white p-3">
                    <div class="text-xs text-gray-500">{{ __('Value') }}</div>
                    <div class="mt-1 text-lg font-bold text-gray-900">{{ formatCurrency(doc.estimated_value) }}</div>
                  </div>
                  <div v-if="doc.probability != null" class="rounded-lg border bg-white p-3">
                    <div class="text-xs text-gray-500">{{ __('Probability') }}</div>
                    <div class="mt-1 text-lg font-bold" :class="probabilityClass(doc.probability)">
                      {{ Math.round(doc.probability) }}%
                    </div>
                  </div>
                  <div class="rounded-lg border bg-white p-3">
                    <div class="text-xs text-gray-500">{{ __('Weighted Value') }}</div>
                    <div class="mt-1 text-lg font-bold text-gray-700">
                      {{ formatCurrency((doc.estimated_value || 0) * (doc.probability || 0) / 100) }}
                    </div>
                  </div>
                </div>
              </section>
            </div>

            <!-- 💼 OFFERS TAB — H1: Offer status prominently visible -->
            <div v-if="activeTab === 'Offers'" class="space-y-4">
              <!-- Header with add button -->
              <div class="flex items-center justify-between">
                <div>
                  <h3 class="text-sm font-semibold text-gray-900">{{ __('Offers') }}</h3>
                  <p class="mt-0.5 text-xs text-gray-500">
                    {{ offers.length }} {{ __('offer(s)') }}
                    <span v-if="activeOffersCount > 0"> • {{ activeOffersCount }} {{ __('active') }}</span>
                  </p>
                </div>
                <Button variant="solid" size="sm" iconLeft="plus" @click="showNewOfferDialog = true" :label="__('New Offer')" />
              </div>

              <!-- Status summary bar — at-a-glance view -->
              <div v-if="offers.length" class="flex flex-wrap gap-2">
                <div
                  v-for="(count, status) in offerStatusCounts"
                  :key="status"
                  class="flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-xs"
                  :class="offerStatusClass(status)"
                >
                  <span class="h-1.5 w-1.5 rounded-full" :class="offerStatusDotClass(status)" />
                  <span class="font-semibold">{{ count }}</span>
                  <span>{{ __(status) }}</span>
                </div>
              </div>

              <!-- Offers list -->
              <div v-if="offersResource.loading" class="flex items-center justify-center py-12">
                <div class="h-6 w-6 animate-spin rounded-full border-2 border-gray-200 border-t-lcs-secondary" />
              </div>
              <div v-else-if="!offers.length" class="flex flex-col items-center rounded-xl border border-dashed border-gray-200 py-12">
                <FeatherIcon name="file-text" class="h-8 w-8 text-gray-300" />
                <p class="mt-3 text-sm text-gray-500">{{ __('No offers yet.') }}</p>
                <p class="mt-1 text-xs text-gray-400">{{ __('Create an offer to track versions and outcomes.') }}</p>
                <Button class="mt-3" variant="outline" size="sm" iconLeft="plus" @click="showNewOfferDialog = true" :label="__('Create first offer')" />
              </div>
              <div v-else class="space-y-2">
                <div
                  v-for="offer in offers"
                  :key="offer.name"
                  class="rounded-xl border bg-white p-4 transition hover:shadow-sm"
                  :class="{ 'ring-2 ring-green-200': offer.status === 'Accepted', 'opacity-60': offer.status === 'Expired' }"
                >
                  <div class="flex items-start justify-between gap-4">
                    <div class="min-w-0 flex-1">
                      <div class="flex items-center gap-2">
                        <span class="font-medium text-gray-900">{{ offer.offer_title }}</span>
                        <span class="rounded-full bg-gray-100 px-2 py-0.5 text-[10px] font-mono font-semibold text-gray-600">
                          v{{ offer.version }}
                        </span>
                      </div>
                      <div class="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-gray-500">
                        <span v-if="offer.offer_date">📅 {{ formatDate(offer.offer_date) }}</span>
                        <span v-if="offer.valid_until" :class="{ 'text-red-500': isExpired(offer.valid_until) }">
                          ⏰ {{ __('until') }} {{ formatDate(offer.valid_until) }}
                        </span>
                        <span v-if="offer.probability">🎯 {{ Math.round(offer.probability) }}%</span>
                      </div>
                      <p v-if="offer.won_lost_reason" class="mt-2 rounded-md bg-gray-50 px-2 py-1 text-xs italic text-gray-600">
                        {{ offer.won_lost_reason }}
                      </p>
                    </div>
                    <div class="flex flex-col items-end gap-2">
                      <!-- Status badge — prominent -->
                      <span :class="offerStatusClass(offer.status)" class="inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-bold">
                        <span class="h-1.5 w-1.5 rounded-full" :class="offerStatusDotClass(offer.status)" />
                        {{ __(offer.status) }}
                      </span>
                      <span v-if="offer.value" class="text-lg font-bold text-gray-900">
                        {{ formatCurrency(offer.value) }}
                      </span>
                    </div>
                  </div>
                  <!-- Status change dropdown -->
                  <div class="mt-3 flex items-center justify-between border-t pt-3">
                    <Dropdown
                      :options="offerStatusOptions(offer)"
                      placement="bottom-start"
                    >
                      <template #default="{ open }">
                        <Button variant="ghost" size="sm" :iconRight="open ? 'chevron-up' : 'chevron-down'" :label="__('Change status')" />
                      </template>
                    </Dropdown>
                  </div>
                </div>
              </div>
            </div>

            <!-- Contacts Tab -->
            <div v-if="activeTab === 'Contacts'" class="space-y-3">
              <div v-if="contactsList.loading" class="flex items-center justify-center py-12">
                <div class="h-6 w-6 animate-spin rounded-full border-2 border-gray-200 border-t-lcs-secondary" />
              </div>
              <div v-else-if="contactsData.length">
                <table class="w-full text-sm">
                  <thead>
                    <tr class="border-b text-left text-xs font-medium uppercase tracking-wide text-gray-500">
                      <th class="px-3 py-2">{{ __('Name') }}</th>
                      <th class="px-3 py-2">{{ __('Role') }}</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="c in contactsData" :key="c.name" class="border-b hover:bg-gray-50">
                      <td class="px-3 py-2.5 font-medium text-gray-900">{{ c.full_name || c.name }}</td>
                      <td class="px-3 py-2.5 text-gray-600">{{ c.designation || '—' }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <div v-else class="flex flex-col items-center py-12">
                <FeatherIcon name="users" class="h-8 w-8 text-gray-300" />
                <p class="mt-3 text-sm text-gray-500">{{ __('No contacts linked to this project yet.') }}</p>
              </div>
            </div>

            <!-- Matrix Tab -->
            <div v-if="activeTab === 'Matrix'">
              <OpportunityMatrix
                :technical-fit="matrixValues.technical_fit"
                :commercial-fit="matrixValues.commercial_fit"
                :relationship="matrixValues.relationship_strength"
                :competition="matrixValues.competition_level"
                :strategic-importance="matrixValues.strategic_importance"
                @update="onMatrixUpdate"
              />
            </div>

            <!-- Activity Tab -->
            <div v-if="activeTab === 'Activity'" class="space-y-3">
              <div v-if="activities.loading" class="flex items-center justify-center py-12">
                <div class="h-6 w-6 animate-spin rounded-full border-2 border-gray-200 border-t-lcs-secondary" />
              </div>
              <div v-else-if="!activities.data?.length" class="flex flex-col items-center py-12">
                <FeatherIcon name="clock" class="h-8 w-8 text-gray-300" />
                <p class="mt-3 text-sm text-gray-500">{{ __('No activities recorded yet.') }}</p>
              </div>
              <div v-else class="relative pl-6">
                <div class="absolute bottom-0 left-2.5 top-0 w-px bg-gray-200" />
                <div v-for="a in activities.data" :key="a.name" class="relative mb-4">
                  <div class="absolute -left-3.5 top-1.5 h-2 w-2 rounded-full border-2 border-white bg-lcs-secondary" />
                  <div class="rounded-lg border bg-white p-3 shadow-sm">
                    <div class="flex items-center justify-between">
                      <span class="text-sm font-medium text-gray-900">{{ a.subject || a.content }}</span>
                      <span class="text-xs text-gray-400">{{ formatRelativeTime(a.creation) }}</span>
                    </div>
                    <p v-if="a.content && a.subject" class="mt-1 text-sm text-gray-600">{{ a.content }}</p>
                    <p class="mt-1 text-xs text-gray-400">{{ a.owner }}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </template>
      </Tabs>

      <!-- Side panel -->
      <Resizer side="right" class="flex flex-col justify-between border-l bg-white">
        <!-- Sync status -->
        <div v-if="doc.name" class="flex flex-wrap items-center gap-2 border-b px-5 py-3">
          <SyncStatusBadge
            :status="doc.abas_id ? 'synced' : 'disabled'"
            system="abas"
            :detail="doc.abas_id ? `abas ID: ${doc.abas_id}` : __('Not synced to abas')"
          />
          <AbasDeepLink v-if="doc.abas_id" :entity="doc.abas_id" kind="order" :label="__('Open in abas')" />
        </div>

        <div class="flex-1 overflow-y-auto">
          <div class="divide-y">
            <div class="space-y-3 px-5 py-4">
              <h4 class="text-[10px] font-bold uppercase tracking-wider text-gray-400">{{ __('Classification') }}</h4>
              <SideField :label="__('Country')">
                <span class="text-sm text-gray-800">{{ doc.country || '—' }}</span>
              </SideField>
              <SideField :label="__('GU')">
                <span v-if="doc.is_gu" class="flex items-center gap-1 text-sm text-green-600">
                  <FeatherIcon name="check-circle" class="h-3.5 w-3.5" /> {{ __('Yes') }}
                </span>
                <span v-else class="text-sm text-gray-400">{{ __('No') }}</span>
              </SideField>
            </div>

            <div class="space-y-3 px-5 py-4">
              <h4 class="text-[10px] font-bold uppercase tracking-wider text-gray-400">{{ __('People') }}</h4>
              <SideField :label="__('Salesperson')">
                <span class="text-sm text-gray-800">{{ doc.salesperson || '—' }}</span>
              </SideField>
              <SideField :label="__('Organization')">
                <span class="text-sm text-gray-800">{{ doc.organization || '—' }}</span>
              </SideField>
            </div>

            <!-- Quick Notes shortcut in sidepanel -->
            <div v-if="doc.notes" class="space-y-2 bg-amber-50/30 px-5 py-4">
              <h4 class="flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-wider text-amber-700">
                <FeatherIcon name="edit-3" class="h-3 w-3" />
                {{ __('Notes Preview') }}
              </h4>
              <p class="line-clamp-4 whitespace-pre-wrap text-xs text-gray-700">{{ doc.notes }}</p>
              <button class="text-xs font-medium text-amber-700 hover:underline" @click="tabIndex = 0">
                {{ __('View full notes →') }}
              </button>
            </div>

            <div v-if="doc.team_link || doc.sharepoint_link" class="space-y-3 px-5 py-4">
              <h4 class="text-[10px] font-bold uppercase tracking-wider text-gray-400">{{ __('External Links') }}</h4>
              <div class="flex flex-col gap-2">
                <a v-if="doc.team_link" :href="doc.team_link" target="_blank" rel="noopener noreferrer" class="inline-flex items-center gap-1.5 text-sm text-lcs-secondary hover:text-lcs-primary hover:underline">
                  <FeatherIcon name="message-square" class="h-3.5 w-3.5" />
                  {{ __('Teams Channel') }}
                </a>
                <a v-if="doc.sharepoint_link" :href="doc.sharepoint_link" target="_blank" rel="noopener noreferrer" class="inline-flex items-center gap-1.5 text-sm text-lcs-secondary hover:text-lcs-primary hover:underline">
                  <FeatherIcon name="folder" class="h-3.5 w-3.5" />
                  {{ __('SharePoint Folder') }}
                </a>
              </div>
            </div>
          </div>
        </div>
      </Resizer>
    </div>
  </div>

  <!-- Phase change confirmation -->
  <Dialog v-model="showPhaseConfirm" :options="{ title: __('Confirm Phase Change'), size: 'sm' }">
    <template #body-content>
      <p class="text-sm text-gray-600">
        {{ __('Move this project from') }} <strong>{{ __(doc.phase) }}</strong>
        {{ __('to') }} <strong>{{ __(pendingPhase) }}</strong>?
      </p>
      <p v-if="isBackwardPhaseMove" class="mt-2 rounded-lg bg-amber-50 p-3 text-xs text-amber-700">
        <FeatherIcon name="alert-triangle" class="mr-1 inline h-3.5 w-3.5" />
        {{ __('This moves the project backward in the pipeline.') }}
      </p>
    </template>
    <template #actions>
      <div class="flex justify-end gap-2">
        <Button variant="ghost" @click="showPhaseConfirm = false" :label="__('Cancel')" />
        <Button variant="solid" @click="confirmPhaseChange" :label="__('Confirm')" />
      </div>
    </template>
  </Dialog>

  <!-- New Offer Dialog -->
  <Dialog v-model="showNewOfferDialog" :options="{ title: __('New Offer'), size: 'md' }">
    <template #body-content>
      <div class="space-y-4">
        <FormControl :label="__('Offer Title')" v-model="newOffer.offer_title" type="text" :placeholder="__('e.g. Initial proposal, Revision 2, ...')" required />
        <div class="grid grid-cols-2 gap-4">
          <FormControl :label="__('Value (EUR)')" v-model="newOffer.value" type="number" />
          <FormControl :label="__('Win Probability (%)')" v-model="newOffer.probability" type="number" min="0" max="100" />
        </div>
        <div class="grid grid-cols-2 gap-4">
          <FormControl :label="__('Offer Date')" v-model="newOffer.offer_date" type="date" />
          <FormControl :label="__('Valid Until')" v-model="newOffer.valid_until" type="date" />
        </div>
        <FormControl :label="__('Status')" v-model="newOffer.status" type="select" :options="['Draft', 'Sent', 'In Review', 'Accepted', 'Rejected', 'Expired', 'Revised']" />
        <FormControl :label="__('Notes')" v-model="newOffer.notes" type="textarea" rows="3" />
      </div>
    </template>
    <template #actions>
      <div class="flex justify-end gap-2">
        <Button variant="ghost" @click="showNewOfferDialog = false" :label="__('Cancel')" />
        <Button variant="solid" @click="createOffer" :loading="creatingOffer" :disabled="!newOffer.offer_title" :label="__('Create')" iconLeft="plus" />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import {
  createDocumentResource, createListResource, createResource,
  Breadcrumbs, Button, Dropdown, Dialog, Tabs, Tooltip, FeatherIcon, FormControl,
  toast, usePageMeta,
} from 'frappe-ui'
import LayoutHeader from '@/components/LayoutHeader.vue'
import Resizer from '@/components/Resizer.vue'
import SyncStatusBadge from '@/components/lcs/SyncStatusBadge.vue'
import AbasDeepLink from '@/components/lcs/AbasDeepLink.vue'
import OpportunityMatrix from '@/components/lcs/OpportunityMatrix.vue'
import { copyToClipboard, timeAgo } from '@/utils'

const SideField = {
  props: ['label'],
  template: `<div class="flex items-center justify-between"><label class="text-xs text-gray-500">{{ label }}</label><slot /></div>`,
}

const router = useRouter()
const props = defineProps({ id: { type: String, required: true } })
const projectId = computed(() => props.id)

const project = createDocumentResource({
  doctype: 'LCS Project',
  name: projectId.value,
  onError: (err) => {
    if (err.exc_type === 'DoesNotExistError') {
      toast({ title: __('Project not found'), icon: 'alert-circle', iconClasses: 'text-red-500' })
    }
  },
})
if (!project.doc) project.get.fetch()
const doc = computed(() => project.doc || {})

usePageMeta(() => ({ title: doc.value.project_name || projectId.value }))

const breadcrumbs = computed(() => [
  { label: __('Projects'), route: { name: 'LCS Projects' } },
  { label: doc.value.project_name || projectId.value, route: { name: 'LCS Project', params: { id: projectId.value } } },
])

const lastSaved = computed(() => doc.value.modified ? (timeAgo ? timeAgo(doc.value.modified) : '') : '')

// Tabs — Offers tab added prominently
const tabIndex = ref(0)
const tabs = computed(() => [
  { name: 'Overview', label: __('Overview') },
  { name: 'Offers', label: __('Offers') + (offers.value.length ? ` (${offers.value.length})` : '') },
  { name: 'Contacts', label: __('Contacts') },
  { name: 'Matrix', label: __('Opportunity Matrix') },
  { name: 'Activity', label: __('Activity') },
])
const activeTab = computed(() => tabs.value[tabIndex.value]?.name || 'Overview')

// Phase change
const phases = ['Inquiry', 'Offer', 'Negotiation', 'Order', 'Execution', 'Completed', 'Lost']
const showPhaseConfirm = ref(false)
const pendingPhase = ref('')
const isBackwardPhaseMove = computed(() => {
  const currentIdx = phases.indexOf(doc.value.phase)
  const newIdx = phases.indexOf(pendingPhase.value)
  return newIdx < currentIdx && pendingPhase.value !== 'Lost'
})
const phaseDropdownOptions = computed(() =>
  phases.map((phase) => ({
    label: __(phase),
    icon: doc.value.phase === phase ? 'check' : undefined,
    onClick: () => initiatePhaseChange(phase),
  })),
)
function initiatePhaseChange(phase) {
  if (phase === doc.value.phase) return
  pendingPhase.value = phase
  if (isBackwardPhaseMove.value) showPhaseConfirm.value = true
  else confirmPhaseChange()
}
function confirmPhaseChange() {
  showPhaseConfirm.value = false
  updateField('phase', pendingPhase.value)
}

// Notes edit — always visible
const editingNotes = ref(false)
const editNotesValue = ref('')
const notesInput = ref(null)
function startNotesEdit() {
  editNotesValue.value = doc.value.notes || ''
  editingNotes.value = true
  nextTick(() => notesInput.value?.focus())
}
function cancelNotesEdit() { editingNotes.value = false }
function saveNotes() {
  updateField('notes', editNotesValue.value)
  editingNotes.value = false
}

// Description edit
const editingDescription = ref(false)
const editDescriptionValue = ref('')
const descriptionInput = ref(null)
function startDescriptionEdit() {
  editDescriptionValue.value = doc.value.project_description || ''
  editingDescription.value = true
  nextTick(() => descriptionInput.value?.focus())
}
function cancelDescriptionEdit() { editingDescription.value = false }
function saveDescription() {
  updateField('project_description', editDescriptionValue.value)
  editingDescription.value = false
}

// Copy feedback
const justCopied = ref(false)
function copyId() {
  copyToClipboard(projectId.value)
  justCopied.value = true
  setTimeout(() => { justCopied.value = false }, 2000)
  toast({ title: __('Copied'), icon: 'check', iconClasses: 'text-green-500' })
}

// 💼 Offers — NEW
const offersResource = createResource({
  url: 'lcs_integrations.projects.api.get_project_offers',
  params: { project: projectId.value },
  auto: true,
})
const offers = computed(() => offersResource.data || [])
const latestOffer = computed(() => offers.value[0] || null)
const activeOffersCount = computed(() => offers.value.filter(o => ['Draft', 'Sent', 'In Review'].includes(o.status)).length)
const offerStatusCounts = computed(() => {
  const counts = {}
  offers.value.forEach(o => { counts[o.status] = (counts[o.status] || 0) + 1 })
  return counts
})

const showNewOfferDialog = ref(false)
const creatingOffer = ref(false)
const newOffer = ref({
  offer_title: '',
  value: null,
  probability: null,
  offer_date: new Date().toISOString().split('T')[0],
  valid_until: '',
  status: 'Draft',
  notes: '',
})

async function createOffer() {
  creatingOffer.value = true
  try {
    const res = createResource({
      url: 'frappe.client.insert',
      params: {
        doc: {
          doctype: 'LCS Offer',
          project: projectId.value,
          ...newOffer.value,
        },
      },
    })
    await res.submit()
    showNewOfferDialog.value = false
    newOffer.value = {
      offer_title: '', value: null, probability: null,
      offer_date: new Date().toISOString().split('T')[0],
      valid_until: '', status: 'Draft', notes: '',
    }
    offersResource.reload()
    project.reload()
    toast({ title: __('Offer created'), icon: 'check-circle', iconClasses: 'text-green-500' })
  } catch (err) {
    toast({ title: __('Could not create offer'), text: err.messages?.[0], icon: 'alert-circle', iconClasses: 'text-red-500' })
  } finally {
    creatingOffer.value = false
  }
}

function offerStatusOptions(offer) {
  const statuses = ['Draft', 'Sent', 'In Review', 'Accepted', 'Rejected', 'Expired', 'Revised']
  return statuses.map(s => ({
    label: __(s),
    icon: offer.status === s ? 'check' : undefined,
    onClick: () => changeOfferStatus(offer, s),
  }))
}

async function changeOfferStatus(offer, newStatus) {
  if (offer.status === newStatus) return
  try {
    const res = createResource({
      url: 'frappe.client.set_value',
      params: { doctype: 'LCS Offer', name: offer.name, fieldname: 'status', value: newStatus },
    })
    await res.submit()
    offersResource.reload()
    project.reload()
    toast({ title: __('Offer status updated'), text: __(newStatus), icon: 'check-circle', iconClasses: 'text-green-500' })
  } catch (err) {
    toast({ title: __('Update failed'), text: err.messages?.[0], icon: 'alert-circle', iconClasses: 'text-red-500' })
  }
}

// Contacts, Matrix, Activities
const contactsList = createListResource({
  doctype: 'Dynamic Link',
  fields: ['parent'],
  filters: { parenttype: 'Contact', link_doctype: 'LCS Project', link_name: projectId.value },
  auto: true,
})
const contactsData = computed(() => {
  if (!contactsList.data) return []
  return contactsList.data.map((d) => ({ name: d.parent, full_name: d.parent }))
})

const matrixValues = ref({ technical_fit: 0, commercial_fit: 0, relationship_strength: 0, competition_level: 0, strategic_importance: 0 })
createResource({
  url: 'lcs_integrations.projects.api.get_opportunity_matrix',
  params: { project: projectId.value },
  auto: true,
  onSuccess: (data) => {
    if (data && data.length) {
      const m = data[0]
      matrixValues.value = {
        technical_fit: m.technical_fit || 0,
        commercial_fit: m.commercial_fit || 0,
        relationship_strength: m.relationship_strength || 0,
        competition_level: m.competition_level || 0,
        strategic_importance: m.strategic_importance || 0,
      }
    }
  },
})
function onMatrixUpdate({ field, value }) { matrixValues.value[field] = value }

const activities = createListResource({
  doctype: 'Comment',
  fields: ['name', 'subject', 'content', 'creation', 'owner'],
  filters: { reference_doctype: 'LCS Project', reference_name: projectId.value },
  orderBy: 'creation desc',
  pageLength: 20,
  auto: true,
})

function updateField(fieldname, value) {
  project.setValue.submit({ [fieldname]: value }).then(() => {
    toast({ title: __('Updated'), icon: 'check-circle', iconClasses: 'text-green-500' })
  }).catch((err) => {
    toast({ title: __('Update failed'), text: err.messages?.[0], icon: 'alert-circle', iconClasses: 'text-red-500' })
  })
}

// Style helpers
function typeClass(type) {
  const map = { SB: 'bg-blue-100 text-blue-800', WI: 'bg-purple-100 text-purple-800', LL: 'bg-emerald-100 text-emerald-800', SK: 'bg-amber-100 text-amber-800' }
  return map[type] || 'bg-gray-100 text-gray-800'
}
function typeFullName(type) {
  const map = { SB: 'Seilbahn (Cable Car)', WI: 'Winde (Winch)', LL: 'Liftanlage (Lift)', SK: 'Sonderkonstruktion (Special)' }
  return map[type] || type
}
function phaseClass(phase) {
  const map = { Inquiry: 'bg-sky-50 text-sky-700 border border-sky-200', Offer: 'bg-amber-50 text-amber-700 border border-amber-200', Negotiation: 'bg-orange-50 text-orange-700 border border-orange-200', Order: 'bg-green-50 text-green-700 border border-green-200', Execution: 'bg-lcs-primary/5 text-lcs-primary border border-lcs-primary/20', Completed: 'bg-gray-50 text-gray-600 border border-gray-200', Lost: 'bg-red-50 text-red-700 border border-red-200' }
  return map[phase] || 'bg-gray-50 text-gray-600 border border-gray-200'
}
function phaseDotClass(phase) {
  const map = { Inquiry: 'bg-sky-500', Offer: 'bg-amber-500', Negotiation: 'bg-orange-500', Order: 'bg-green-500', Execution: 'bg-lcs-primary', Completed: 'bg-gray-400', Lost: 'bg-red-500' }
  return map[phase] || 'bg-gray-400'
}
function statusClass(status) {
  const map = { Open: 'bg-blue-50 text-blue-700 border border-blue-200', Active: 'bg-green-50 text-green-700 border border-green-200', 'On Hold': 'bg-amber-50 text-amber-700 border border-amber-200', Completed: 'bg-gray-50 text-gray-600 border border-gray-200', Cancelled: 'bg-red-50 text-red-700 border border-red-200' }
  return map[status] || 'bg-gray-50 text-gray-600 border border-gray-200'
}
function statusDotClass(status) {
  const map = { Open: 'bg-blue-500', Active: 'bg-green-500', 'On Hold': 'bg-amber-500', Completed: 'bg-gray-400', Cancelled: 'bg-red-500' }
  return map[status] || 'bg-gray-400'
}
// Offer status — H6: Recognition via distinct colors
function offerStatusClass(status) {
  const map = {
    Draft: 'bg-gray-50 text-gray-700 border border-gray-200',
    Sent: 'bg-blue-50 text-blue-700 border border-blue-200',
    'In Review': 'bg-purple-50 text-purple-700 border border-purple-200',
    Accepted: 'bg-green-50 text-green-700 border border-green-200',
    Rejected: 'bg-red-50 text-red-700 border border-red-200',
    Expired: 'bg-gray-50 text-gray-500 border border-gray-200',
    Revised: 'bg-amber-50 text-amber-700 border border-amber-200',
  }
  return map[status] || 'bg-gray-50 text-gray-600 border border-gray-200'
}
function offerStatusDotClass(status) {
  const map = { Draft: 'bg-gray-400', Sent: 'bg-blue-500', 'In Review': 'bg-purple-500', Accepted: 'bg-green-500', Rejected: 'bg-red-500', Expired: 'bg-gray-300', Revised: 'bg-amber-500' }
  return map[status] || 'bg-gray-400'
}
function probabilityClass(val) {
  if (val >= 70) return 'text-green-600'
  if (val >= 40) return 'text-amber-600'
  return 'text-red-500'
}
function formatCurrency(val) {
  return new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(val)
}
function formatDate(dateStr) {
  if (!dateStr) return ''
  return new Intl.DateTimeFormat('de-DE', { day: '2-digit', month: 'short', year: 'numeric' }).format(new Date(dateStr))
}
function formatRelativeTime(dateStr) {
  if (!dateStr) return ''
  if (timeAgo) return timeAgo(dateStr)
  return dateStr
}
function isExpired(dateStr) {
  if (!dateStr) return false
  return new Date(dateStr) < new Date()
}
</script>
