<template>
  <LayoutHeader>
    <template #left-header>
      <Breadcrumbs :items="breadcrumbs" />
    </template>
    <template v-if="doc.name" #right-header>
      <div class="flex items-center gap-3">
        <!-- Pending-sync indicator for this specific project -->
        <span
          v-if="pendingChangeCount > 0"
          class="flex items-center gap-1 rounded-full bg-amber-50 px-2 py-0.5 text-xs font-medium text-amber-700 border border-amber-200"
          :title="__('Changes queued for sync')"
        >
          <FeatherIcon name="clock" class="h-3 w-3 animate-pulse" />
          {{ pendingChangeCount }} {{ __('pending') }}
        </span>
        <span v-else-if="lastSaved" class="text-xs text-gray-400">{{ __('Saved') }} {{ lastSaved }}</span>
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

        <!-- 💰 3 Pricing stages — always visible -->
        <div class="flex items-end gap-1">
          <Tooltip :text="__('What the customer indicates they are willing to spend')">
            <div class="rounded-lg border border-gray-200 bg-white px-3 py-1.5">
              <div class="text-[9px] font-bold uppercase tracking-wider text-gray-400">{{ __('Budget') }}</div>
              <div class="mt-0.5 text-sm font-semibold tabular-nums" :class="doc.budget_customer ? 'text-gray-700' : 'text-gray-300'">
                {{ doc.budget_customer ? formatCurrency(doc.budget_customer) : '—' }}
              </div>
            </div>
          </Tooltip>
          <span class="mb-2 text-gray-300">→</span>
          <Tooltip :text="__('Internal rough estimate before formal quote')">
            <div class="rounded-lg border border-blue-200 bg-blue-50 px-3 py-1.5">
              <div class="text-[9px] font-bold uppercase tracking-wider text-blue-600">{{ __('Richtpreis') }}</div>
              <div class="mt-0.5 text-sm font-semibold tabular-nums" :class="doc.richtpreis ? 'text-blue-900' : 'text-blue-300'">
                {{ doc.richtpreis ? formatCurrency(doc.richtpreis) : '—' }}
              </div>
            </div>
          </Tooltip>
          <span class="mb-2 text-gray-300">→</span>
          <Tooltip :text="__('Formal quoted total — synced from accepted offer')">
            <div class="rounded-lg border px-3 py-1.5" :class="doc.angebot_total ? 'border-green-300 bg-green-50' : 'border-gray-200 bg-white'">
              <div class="text-[9px] font-bold uppercase tracking-wider" :class="doc.angebot_total ? 'text-green-700' : 'text-gray-400'">{{ __('Angebot') }}</div>
              <div class="mt-0.5 text-sm font-bold tabular-nums" :class="doc.angebot_total ? 'text-green-800' : 'text-gray-300'">
                {{ doc.angebot_total ? formatCurrency(doc.angebot_total) : '—' }}
              </div>
            </div>
          </Tooltip>
          <!-- Win probability badge -->
          <div v-if="doc.probability" class="ml-2 flex flex-col items-center">
            <span :class="probabilityClass(doc.probability)" class="rounded-md bg-gray-50 px-2 py-0.5 text-sm font-bold">
              {{ Math.round(doc.probability) }}%
            </span>
            <span class="mt-0.5 text-[9px] uppercase text-gray-400">{{ __('Win') }}</span>
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
                  <div class="relative">
                    <textarea
                      v-model="editNotesValue"
                      class="w-full rounded-lg border border-amber-200 bg-white px-3 py-2 pr-10 text-sm text-gray-800 focus:border-amber-400 focus:ring-1 focus:ring-amber-400"
                      rows="5"
                      :placeholder="__('Write project notes, internal reminders, or next steps...')"
                      ref="notesInput"
                    />
                    <div class="absolute right-2 top-2">
                      <VoiceInput :hotkey="true" @transcript="onVoiceNote" />
                    </div>
                  </div>
                  <div class="flex items-center justify-between gap-2">
                    <div class="flex gap-2">
                      <Button variant="solid" size="sm" @click="saveNotes" :label="__('Save')" iconLeft="check" />
                      <Button variant="ghost" size="sm" @click="cancelNotesEdit" :label="__('Cancel')" />
                    </div>
                    <span class="text-[10px] text-gray-400">{{ __('Click mic for voice input') }}</span>
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
                  <div class="relative">
                    <textarea
                      v-model="editDescriptionValue"
                      class="w-full rounded-lg border border-gray-200 px-3 py-2 pr-10 text-sm text-gray-800 focus:border-lcs-secondary focus:ring-1 focus:ring-lcs-secondary"
                      rows="4"
                      :placeholder="__('Add a project description...')"
                      ref="descriptionInput"
                    />
                    <div class="absolute right-2 top-2">
                      <VoiceInput @transcript="onDescriptionVoice" />
                    </div>
                  </div>
                  <div class="flex items-center justify-between gap-2">
                    <div class="flex gap-2">
                      <Button variant="solid" size="sm" @click="saveDescription" :label="__('Save')" />
                      <Button variant="ghost" size="sm" @click="cancelDescriptionEdit" :label="__('Cancel')" />
                    </div>
                    <span class="text-[10px] text-gray-400">{{ __('Click mic or press Ctrl+Shift+V for voice input') }}</span>
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

              <!-- Pricing stages — editable cards showing Budget → Richtpreis → Angebot progression -->
              <section v-if="canShow('show_pricing_details')">
                <h3 class="mb-3 flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-gray-400">
                  <FeatherIcon name="trending-up" class="h-3.5 w-3.5" />
                  {{ __('Pricing Stages') }}
                  <span class="ml-2 text-[10px] font-normal normal-case text-gray-400">
                    {{ __('Customer budget → internal estimate → formal quote') }}
                  </span>
                </h3>
                <div class="grid grid-cols-1 gap-3 sm:grid-cols-3">
                  <PriceStageCard
                    :label="__('Budget')"
                    :sublabel="__('Customer indication')"
                    :value="doc.budget_customer"
                    color="gray"
                    icon="user"
                    :editable="true"
                    @save="updateField('budget_customer', $event)"
                  />
                  <PriceStageCard
                    :label="__('Richtpreis')"
                    :sublabel="__('Internal estimate')"
                    :value="doc.richtpreis"
                    color="blue"
                    icon="clipboard"
                    :editable="true"
                    @save="updateField('richtpreis', $event)"
                  />
                  <PriceStageCard
                    :label="__('Angebot')"
                    :sublabel="__('Formal quote')"
                    :value="doc.angebot_total"
                    color="green"
                    icon="file-text"
                    :editable="true"
                    @save="updateField('angebot_total', $event)"
                  />
                </div>
                <!-- Forecasting row: weighted value and variance -->
                <div class="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-3">
                  <div class="rounded-lg border bg-gray-50 p-3">
                    <div class="text-xs text-gray-500">{{ __('Weighted Value') }}</div>
                    <div class="mt-1 text-base font-bold text-gray-700">
                      {{ formatCurrency((doc.estimated_value || 0) * (doc.probability || 0) / 100) }}
                    </div>
                    <div class="mt-0.5 text-[10px] text-gray-400">{{ __('value × probability') }}</div>
                  </div>
                  <div v-if="doc.probability != null" class="rounded-lg border bg-gray-50 p-3">
                    <div class="text-xs text-gray-500">{{ __('Win Probability') }}</div>
                    <div class="mt-1 text-base font-bold" :class="probabilityClass(doc.probability)">
                      {{ Math.round(doc.probability) }}%
                    </div>
                  </div>
                  <div v-if="budgetVsAngebot" class="rounded-lg border bg-gray-50 p-3">
                    <div class="text-xs text-gray-500">{{ __('Budget vs. Angebot') }}</div>
                    <div class="mt-1 text-base font-bold" :class="budgetVsAngebot >= 0 ? 'text-green-600' : 'text-amber-600'">
                      {{ budgetVsAngebot >= 0 ? '+' : '' }}{{ Math.round(budgetVsAngebot) }}%
                    </div>
                    <div class="mt-0.5 text-[10px] text-gray-400">
                      {{ budgetVsAngebot >= 0 ? __('under customer budget') : __('over customer budget') }}
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

              <!-- Offers list — skeleton prevents layout shift on slow network -->
              <div v-if="offersResource.loading && !offers.length" class="space-y-2">
                <div v-for="i in 3" :key="i" class="animate-pulse rounded-xl border bg-white p-4">
                  <div class="flex items-start justify-between gap-4">
                    <div class="flex-1 space-y-2">
                      <div class="h-4 w-48 rounded bg-gray-200" />
                      <div class="h-3 w-36 rounded bg-gray-100" />
                    </div>
                    <div class="space-y-2">
                      <div class="h-5 w-20 rounded-full bg-gray-200" />
                      <div class="h-5 w-24 rounded bg-gray-100" />
                    </div>
                  </div>
                </div>
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
                  class="rounded-xl border bg-white p-4 transition hover:shadow-sm cursor-pointer hover:border-lcs-secondary"
                  :class="{ 'ring-2 ring-green-200': offer.status === 'Accepted', 'opacity-60': offer.status === 'Expired' }"
                  @click="$router.push({ name: 'LCS Offer', params: { id: offer.name } })"
                >
                  <div class="flex items-start justify-between gap-4">
                    <div class="min-w-0 flex-1">
                      <div class="flex items-center gap-2">
                        <span class="font-medium text-gray-900">{{ offer.offer_title }}</span>
                        <span class="rounded-full bg-gray-100 px-2 py-0.5 text-[10px] font-mono font-semibold text-gray-600">
                          v{{ offer.version }}
                        </span>
                        <FeatherIcon name="external-link" class="ml-auto h-3 w-3 text-gray-300" />
                      </div>
                      <div class="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-gray-500">
                        <span v-if="offer.offer_date">📅 {{ formatDate(offer.offer_date) }}</span>
                        <span v-if="offer.valid_until" :class="{ 'text-red-500': isExpired(offer.valid_until) }">
                          ⏰ {{ __('until') }} {{ formatDate(offer.valid_until) }}
                        </span>
                        <span v-if="offer.probability">🎯 {{ Math.round(offer.probability) }}%</span>
                      </div>
                      <p v-if="offer.lost_reason" class="mt-2 rounded-md bg-red-50 px-2 py-1 text-xs italic text-red-700">
                        <FeatherIcon name="x-circle" class="mr-1 inline h-3 w-3" />
                        {{ __('Lost') }}: {{ offer.lost_reason }}
                      </p>
                      <p v-else-if="offer.won_notes" class="mt-2 rounded-md bg-green-50 px-2 py-1 text-xs italic text-green-700">
                        <FeatherIcon name="check-circle" class="mr-1 inline h-3 w-3" />
                        {{ offer.won_notes }}
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
                  <div class="mt-3 flex items-center justify-between border-t pt-3" @click.stop>
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

            <!-- PLM / BOM Tab -->
            <div v-if="activeTab === 'PLM'" class="space-y-4">
              <FusionItemPicker
                :project-name="projectId"
                :fusion-workspace="doc.fusion_workspace"
                :fusion-item-id="doc.fusion_item_id"
                :fusion-number="doc.fusion_item_number"
                :fusion-description="doc.fusion_item_description"
                :fusion-state="doc.fusion_item_state"
                @linked="onFusionLinked"
                @unlinked="onFusionUnlinked"
              />

              <!-- BOM view — only when linked -->
              <div v-if="doc.fusion_item_id">
                <div v-if="bomLoading" class="flex items-center justify-center py-8">
                  <div class="h-6 w-6 animate-spin rounded-full border-2 border-gray-200 border-t-lcs-secondary" />
                </div>
                <div v-else-if="bomError" class="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
                  <FeatherIcon name="alert-circle" class="mr-1 inline h-3.5 w-3.5" />
                  {{ bomError }}
                </div>
                <BomTree v-else :rows="bomRows" />
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
        <!-- Integrated systems: CRM · ERPNext · BSM · HRMS · LMS · Fusion Manage
           Hidden if user disabled this panel in preferences OR profile hides it. -->
        <div v-if="doc.name && canShow('show_integration_panel')" class="border-b px-5 py-4">
          <IntegrationStatusPanel :project="projectId" />
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

            <!-- Pricing quick reference in side panel — respects prefs + access profile -->
            <div v-if="canShow('show_pricing_details')" class="space-y-2 px-5 py-4">
              <h4 class="text-[10px] font-bold uppercase tracking-wider text-gray-400">{{ __('Pricing') }}</h4>
              <SideField :label="__('Budget')">
                <span class="text-sm tabular-nums" :class="doc.budget_customer ? 'text-gray-800' : 'text-gray-400'">
                  {{ doc.budget_customer ? formatCurrency(doc.budget_customer) : '—' }}
                </span>
              </SideField>
              <SideField :label="__('Richtpreis')">
                <span class="text-sm tabular-nums" :class="doc.richtpreis ? 'text-blue-700 font-medium' : 'text-gray-400'">
                  {{ doc.richtpreis ? formatCurrency(doc.richtpreis) : '—' }}
                </span>
              </SideField>
              <SideField :label="__('Angebot')">
                <span class="text-sm tabular-nums" :class="doc.angebot_total ? 'text-green-700 font-semibold' : 'text-gray-400'">
                  {{ doc.angebot_total ? formatCurrency(doc.angebot_total) : '—' }}
                </span>
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
        <!-- Template selector — quick-start from predefined template -->
        <div v-if="offerTemplates.length" class="rounded-lg border border-lcs-secondary/20 bg-lcs-secondary/5 p-3">
          <label class="text-xs font-semibold uppercase tracking-wide text-lcs-primary">{{ __('Start from Template') }}</label>
          <div class="mt-2 flex flex-wrap gap-2">
            <button
              v-for="t in offerTemplates"
              :key="t.name"
              class="rounded-lg border bg-white px-3 py-1.5 text-xs font-medium text-gray-700 transition hover:border-lcs-secondary hover:bg-lcs-secondary/10"
              @click="applyTemplate(t)"
            >
              <span class="flex items-center gap-1">
                <FeatherIcon name="file-plus" class="h-3 w-3" />
                {{ t.template_name }}
                <span v-if="t.usage_count" class="ml-1 text-[10px] text-gray-400">{{ t.usage_count }}×</span>
              </span>
            </button>
          </div>
        </div>
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
        <div class="relative">
          <label class="mb-1 block text-xs text-gray-700">{{ __('Notes') }}</label>
          <textarea
            v-model="newOffer.notes"
            class="w-full rounded-lg border border-gray-300 px-3 py-2 pr-10 text-sm focus:border-lcs-secondary focus:ring-1 focus:ring-lcs-secondary"
            rows="3"
            :placeholder="__('Offer notes, terms, reminders...')"
          />
          <div class="absolute right-2 top-7">
            <VoiceInput @transcript="onOfferNotesVoice" />
          </div>
        </div>
      </div>
    </template>
    <template #actions>
      <div class="flex justify-end gap-2">
        <Button variant="ghost" @click="showNewOfferDialog = false" :label="__('Cancel')" />
        <Button variant="solid" @click="createOffer" :loading="creatingOffer" :disabled="!newOffer.offer_title || creatingOffer" :label="__('Create')" iconLeft="plus" />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { ref, computed, watch, nextTick, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  createDocumentResource, createListResource, createResource,
  Breadcrumbs, Button, Dropdown, Dialog, Tabs, Tooltip, FeatherIcon, FormControl,
  toast, usePageMeta,
} from 'frappe-ui'
import LayoutHeader from '@/components/LayoutHeader.vue'
import Resizer from '@/components/Resizer.vue'
import SyncStatusBadge from '@/components/lcs/SyncStatusBadge.vue'
import ErpNextDeepLink from '@/components/lcs/ErpNextDeepLink.vue'
import FusionManageDeepLink from '@/components/lcs/FusionManageDeepLink.vue'
import IntegrationStatusPanel from '@/components/lcs/IntegrationStatusPanel.vue'
import FusionItemPicker from '@/components/lcs/FusionItemPicker.vue'
import BomTree from '@/components/lcs/BomTree.vue'
import OpportunityMatrix from '@/components/lcs/OpportunityMatrix.vue'
import PriceStageCard from '@/components/lcs/PriceStageCard.vue'
import VoiceInput from '@/components/lcs/VoiceInput.vue'
import { queueMutation, cachePut, listMutations, onQueueChange } from '@/utils/offlineDB'
import { drain } from '@/utils/syncEngine'
import { copyToClipboard, timeAgo } from '@/utils'
import { useUserPreferences } from '@/composables/useUserPreferences'

const { canShow } = useUserPreferences()

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

// Pending mutations for this project
const pendingChangeCount = ref(0)
async function refreshPending() {
  const all = await listMutations()
  pendingChangeCount.value = all.filter(m =>
    m.doctype === 'LCS Project' && m.name === projectId.value && (m.status === 'pending' || m.status === 'syncing' || m.status === 'failed')
  ).length
}
refreshPending()
const unsubQueue = onQueueChange(refreshPending)
onUnmounted(() => { if (unsubQueue) unsubQueue() })

// Budget vs Angebot variance (% under/over customer budget)
const budgetVsAngebot = computed(() => {
  const budget = doc.value.budget_customer
  const angebot = doc.value.angebot_total
  if (!budget || !angebot) return null
  return ((budget - angebot) / budget) * 100
})

// Tabs — Offers tab added prominently
const tabIndex = ref(0)
// Offer count stored in a dedicated ref so tabs computed doesn't touch
// `offers` (which is declared further down in this file — referring to
// it here causes a TDZ error when the minifier inlines the getter).
const tabOfferCount = ref(0)

const tabs = computed(() => {
  const all = [
    { name: 'Overview', label: __('Overview'), show: true },
    { name: 'Offers', label: __('Offers') + (tabOfferCount.value ? ` (${tabOfferCount.value})` : ''), show: true },
    { name: 'Contacts', label: __('Contacts'), show: true },
    { name: 'PLM', label: __('PLM / BOM'), show: canShow('show_fusion_section') },
    { name: 'Matrix', label: __('Opportunity Matrix'), show: canShow('show_opportunity_matrix') },
    { name: 'Activity', label: __('Activity'), show: true },
  ]
  return all.filter(t => t.show)
})
const activeTab = computed(() => tabs.value[tabIndex.value]?.name || 'Overview')

// ---- Fusion BOM loading ----
const bomRows = ref([])
const bomLoading = ref(false)
const bomError = ref('')

async function loadBom() {
  if (!doc.value.fusion_item_id) {
    bomRows.value = []
    return
  }
  bomLoading.value = true
  bomError.value = ''
  try {
    const res = await createResource({
      url: 'lcs_integrations.fusion_manage.service.get_bom_tree',
      params: { project: projectId.value },
    }).fetch()
    const payload = res || {}
    if (payload.error) bomError.value = payload.error
    bomRows.value = payload.rows || []
  } catch (err) {
    bomError.value = err.message || String(err)
  } finally {
    bomLoading.value = false
  }
}

// Reload BOM whenever the user enters the PLM tab or the link changes
watch(activeTab, (t) => { if (t === 'PLM') loadBom() })
watch(() => doc.value.fusion_item_id, () => loadBom())

function onFusionLinked(info) {
  // Optimistically update the cached doc so the BOM section renders immediately
  if (project.doc) {
    project.doc.fusion_workspace = info.workspace
    project.doc.fusion_item_id = info.item_id
    project.doc.fusion_item_number = info.item?.number || info.item?.itemNumber
    project.doc.fusion_item_description = info.item?.description || info.item?.title
    project.doc.fusion_item_state = info.item?.currentState || info.item?.state
  }
  project.reload?.()
  loadBom()
}

function onFusionUnlinked() {
  if (project.doc) {
    project.doc.fusion_workspace = null
    project.doc.fusion_item_id = null
    project.doc.fusion_item_number = null
    project.doc.fusion_item_description = null
    project.doc.fusion_item_state = null
  }
  bomRows.value = []
  project.reload?.()
}

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

// Voice input — project notes
let voiceBaseline = ''
function onVoiceNote({ final, interim }) {
  if (final && voiceBaseline === '') voiceBaseline = editNotesValue.value || ''
  const separator = voiceBaseline ? (voiceBaseline.endsWith('\n') ? '' : '\n') : ''
  editNotesValue.value = voiceBaseline + separator + (final || '') + (interim || '')
}

// Voice input — new offer dialog
let offerNotesBaseline = ''
function onOfferNotesVoice({ final, interim }) {
  if (final && offerNotesBaseline === '') offerNotesBaseline = newOffer.value.notes || ''
  const separator = offerNotesBaseline ? (offerNotesBaseline.endsWith('\n') ? '' : '\n') : ''
  newOffer.value.notes = offerNotesBaseline + separator + (final || '') + (interim || '')
}

// Voice input — project description
let descriptionBaseline = ''
function onDescriptionVoice({ final, interim }) {
  if (final && descriptionBaseline === '') descriptionBaseline = editDescriptionValue.value || ''
  const separator = descriptionBaseline ? (descriptionBaseline.endsWith('\n') ? '' : '\n') : ''
  editDescriptionValue.value = descriptionBaseline + separator + (final || '') + (interim || '')
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
  setTimeout(() => { justCopied.value = false }, 3500)
  toast({ title: __('Copied'), icon: 'check', iconClasses: 'text-green-500' })
}

// 💼 Offers — NEW
const offersResource = createResource({
  url: 'lcs_integrations.projects.api.get_project_offers',
  params: { project: projectId.value },
  auto: true,
})
const offers = computed(() => offersResource.data || [])
// Keep the tabs count in sync — lives in a separate ref above because
// `tabs` must not reference `offers` directly (TDZ in setup order).
watch(offers, (v) => { tabOfferCount.value = (v || []).length }, { immediate: true })
const latestOffer = computed(() => offers.value[0] || null)
const activeOffersCount = computed(() => offers.value.filter(o => ['Draft', 'Sent', 'In Review'].includes(o.status)).length)
const offerStatusCounts = computed(() => {
  const counts = {}
  offers.value.forEach(o => { counts[o.status] = (counts[o.status] || 0) + 1 })
  return counts
})

const showNewOfferDialog = ref(false)
const creatingOffer = ref(false)

// Offer templates
const templatesResource = createResource({
  url: 'lcs_integrations.projects.api.get_offer_templates',
  auto: true,
  onSuccess: () => {},
})
const offerTemplates = computed(() => templatesResource.data || [])

function applyTemplate(t) {
  const projectName = doc.value.project_name || ''
  const projectNumber = doc.value.project_number || ''
  newOffer.value = {
    ...newOffer.value,
    offer_title: (t.default_title || '')
      .replace('{project_number}', projectNumber)
      .replace('{project_name}', projectName) || `Offer for ${projectName}`,
    probability: t.default_probability || null,
    notes: t.default_notes || '',
    value: doc.value.richtpreis || doc.value.budget_customer || null,
    valid_until: t.default_validity_days
      ? new Date(Date.now() + t.default_validity_days * 86400000).toISOString().split('T')[0]
      : '',
  }
  toast({ title: __('Template applied'), text: t.template_name, icon: 'check', iconClasses: 'text-green-500' })
}

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
  if (creatingOffer.value) return  // guard against double-submit
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

async function updateField(fieldname, value) {
  // Capture the value we *think* is currently on the server so the sync
  // engine can detect conflicts when replaying this mutation.
  const baseValues = project.doc ? { [fieldname]: project.doc[fieldname] } : {}
  const baseModified = project.doc?.modified || null

  // Optimistic: cache the updated doc immediately so offline reads see it
  if (project.doc) {
    const updated = { ...project.doc, [fieldname]: value }
    await cachePut('LCS Project', projectId.value, updated)
  }

  if (navigator.onLine) {
    try {
      await project.setValue.submit({ [fieldname]: value })
      toast({ title: __('Updated'), icon: 'check-circle', iconClasses: 'text-green-500' })
    } catch (err) {
      await queueMutation({
        doctype: 'LCS Project',
        name: projectId.value,
        method: 'update',
        params: { [fieldname]: value },
        baseValues,
        baseModified,
        description: `Update ${fieldname}`,
      })
      toast({
        title: __('Queued for sync'),
        text: err.messages?.[0] || __('Network error — will retry automatically'),
        icon: 'clock',
        iconClasses: 'text-amber-500',
      })
    }
    return
  }

  await queueMutation({
    doctype: 'LCS Project',
    name: projectId.value,
    method: 'update',
    params: { [fieldname]: value },
    baseValues,
    baseModified,
    description: `Update ${fieldname}`,
  })
  if (project.doc) {
    project.doc[fieldname] = value
  }
  toast({
    title: __('Saved offline'),
    text: __('Will sync when reconnected'),
    icon: 'wifi-off',
    iconClasses: 'text-amber-500',
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
