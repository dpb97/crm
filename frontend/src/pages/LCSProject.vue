<!--
  LCSProject — Projekt-Workspace (V2, Showcase #5 „Projekt-Workspace").
  ============================================================================
  Detailfläche eines Vertriebsprojekts (Deal = Projekt). Präsentation nach
  pilanda_theme-Showcase #5: PpPageHead + PpPhaseStepper (Phasen) + KPI-Zeile
  (PpStatTile) + PpTabs (Übersicht/Aktivitäten/Angebote/Dokumente sowie die
  fachlichen Zusatzreiter) + PpTimeline + PpComments. Meta-/Inspector-Spalte
  rechts (bestehendes Seitenpanel, Funktionserhalt).

  Alle Daten sind ECHT (DocType „LCS Project", LCS Offer, Frappe-Comments über
  crm.api.comment.add_comment). Bestehende Datenlogik, Offline-Sync, Voice-Input
  und Bearbeitungsfunktionen bleiben unverändert erhalten.
-->
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
        <span v-else-if="lastSaved" class="hidden text-xs text-gray-400 sm:inline">{{ __('Saved') }} {{ lastSaved }}</span>
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
  <div v-else class="flex h-full min-h-0 flex-col overflow-y-auto lg:flex-row lg:overflow-hidden crmw">
    <!-- Hauptspalte -->
    <div class="flex min-h-0 flex-1 flex-col overflow-y-auto">
      <div class="crmw-main">
        <!-- Kopf -->
        <PpPageHead
          eyebrow="Vertrieb / CRM · Projekt"
          :title="doc.project_name || projectId"
          :subtitle="headSubtitle"
        >
          <template #actions>
            <Tooltip :text="typeFullName(doc.project_type)">
              <span :class="typeClass(doc.project_type)" class="shrink-0 rounded-full px-2 py-0.5 text-xs font-bold">{{ doc.project_type }}</span>
            </Tooltip>
            <span :class="statusClass(doc.status)" class="inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-semibold">
              <span class="h-1.5 w-1.5 rounded-full" :class="statusDotClass(doc.status)" />
              {{ __(doc.status || 'Open') }}
            </span>
            <button class="crmw-btn" @click="activeTab = T.ACT">Aktivität</button>
            <button class="crmw-btn crmw-btn--primary" @click="showNewOfferDialog = true">Angebot erstellen</button>
          </template>
        </PpPageHead>

        <!-- Phasen-Stepper -->
        <section class="crmw-stepper">
          <PpPhaseStepper :steps="phaseSteps" :current="currentStep" />
          <p v-if="doc.phase === 'Lost'" class="crmw-lost">
            <FeatherIcon name="x-circle" class="inline h-3.5 w-3.5" /> Projekt als verloren markiert
          </p>
        </section>

        <!-- KPI-Zeile -->
        <section class="crmw-kpis">
          <PpStatTile v-for="k in kpis" :key="k.label" v-bind="k" />
        </section>

        <!-- Tabs -->
        <section class="crmw-tabs-wrap">
          <PpTabs v-model="activeTab" :tabs="tabs" />

          <!-- Übersicht -->
          <div v-if="activeTab === T.OV" class="crmw-tabpane space-y-5">
            <!-- Notizen — angepinnt, immer sichtbar -->
            <section class="rounded-xl border border-amber-200 bg-amber-50/50 p-4">
              <div class="mb-2 flex items-center justify-between">
                <h3 class="flex items-center gap-2 text-sm font-semibold text-amber-900">
                  <FeatherIcon name="edit-3" class="h-4 w-4" />
                  {{ __('Notes') }}
                  <span v-if="doc.notes" class="rounded-full bg-amber-200 px-1.5 py-0.5 text-[10px] text-amber-800">{{ __('active') }}</span>
                </h3>
                <Button v-if="!editingNotes" variant="ghost" size="sm" iconLeft="edit-2" @click="startNotesEdit" :label="doc.notes ? __('Edit') : __('Add')" class="text-amber-700 hover:bg-amber-100" />
              </div>
              <div v-if="editingNotes" class="space-y-2">
                <div class="relative">
                  <textarea v-model="editNotesValue" class="w-full rounded-lg border border-amber-200 bg-white px-3 py-2 pr-10 text-sm text-gray-800 focus:border-amber-400 focus:ring-1 focus:ring-amber-400" rows="5" :placeholder="__('Write project notes, internal reminders, or next steps...')" ref="notesInput" />
                  <div class="absolute right-2 top-2"><VoiceInput :hotkey="true" @transcript="onVoiceNote" /></div>
                </div>
                <div class="flex items-center justify-between gap-2">
                  <div class="flex gap-2">
                    <Button variant="solid" size="sm" @click="saveNotes" :label="__('Save')" iconLeft="check" />
                    <Button variant="ghost" size="sm" @click="cancelNotesEdit" :label="__('Cancel')" />
                  </div>
                  <span class="text-[10px] text-gray-400">{{ __('Click mic for voice input') }}</span>
                </div>
              </div>
              <div v-else-if="doc.notes" class="whitespace-pre-wrap text-sm text-gray-800">{{ doc.notes }}</div>
              <div v-else class="text-sm italic text-amber-700/70">{{ __('No notes yet. Click Add to write project notes.') }}</div>
            </section>

            <!-- Beschreibung -->
            <section>
              <h4 class="crmw-sec-title">Projektbeschreibung</h4>
              <div v-if="editingDescription" class="mt-2 space-y-2">
                <div class="relative">
                  <textarea v-model="editDescriptionValue" class="w-full rounded-lg border border-gray-200 px-3 py-2 pr-10 text-sm text-gray-800 focus:border-lcs-secondary focus:ring-1 focus:ring-lcs-secondary" rows="4" :placeholder="__('Add a project description...')" ref="descriptionInput" />
                  <div class="absolute right-2 top-2"><VoiceInput @transcript="onDescriptionVoice" /></div>
                </div>
                <div class="flex items-center justify-between gap-2">
                  <div class="flex gap-2">
                    <Button variant="solid" size="sm" @click="saveDescription" :label="__('Save')" />
                    <Button variant="ghost" size="sm" @click="cancelDescriptionEdit" :label="__('Cancel')" />
                  </div>
                  <span class="text-[10px] text-gray-400">{{ __('Click mic or press Ctrl+Shift+V for voice input') }}</span>
                </div>
              </div>
              <div v-else @click="startDescriptionEdit" class="group mt-2 cursor-pointer">
                <p v-if="doc.project_description" class="crmw-desc rounded-lg p-2 -m-2 transition group-hover:bg-gray-50">{{ doc.project_description }}</p>
                <p v-else class="rounded-lg border border-dashed border-gray-200 p-4 text-center text-sm text-gray-400 transition hover:border-gray-300 hover:text-gray-500">{{ __('Click to add a description') }}</p>
              </div>
            </section>

            <!-- Wert-Progression (editierbar: Budget → Richtpreis → Angebot) -->
            <section v-if="canShow('show_pricing_details')">
              <h4 class="crmw-sec-title">
                Wert-Progression
                <span class="ml-2 text-[10px] font-normal normal-case text-gray-400">Kundenbudget → interne Schätzung → festes Angebot</span>
              </h4>
              <div class="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-3">
                <PriceStageCard :label="__('Budget')" :sublabel="__('Customer indication')" :value="doc.budget_customer" color="gray" icon="user" :editable="true" :currency="doc.currency" @save="updateField('budget_customer', $event)" />
                <PriceStageCard :label="__('Richtpreis')" :sublabel="__('Internal estimate')" :value="doc.richtpreis" color="blue" icon="clipboard" :editable="true" :currency="doc.currency" @save="updateField('richtpreis', $event)" />
                <PriceStageCard :label="__('Angebot')" :sublabel="__('Formal quote')" :value="doc.angebot_total" color="green" icon="file-text" :editable="true" :currency="doc.currency" @save="updateField('angebot_total', $event)" />
              </div>
              <div class="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-3">
                <div class="rounded-lg border bg-gray-50 p-3">
                  <div class="text-xs text-gray-500">{{ __('Weighted Value') }}</div>
                  <div class="mt-1 text-base font-bold text-gray-700">{{ formatCurrency((doc.estimated_value || 0) * (doc.probability || 0) / 100) }}</div>
                  <div class="mt-0.5 text-[10px] text-gray-400">{{ __('value × probability') }}</div>
                </div>
                <div v-if="doc.probability != null" class="rounded-lg border bg-gray-50 p-3">
                  <div class="text-xs text-gray-500">{{ __('Win Probability') }}</div>
                  <div class="mt-1 text-base font-bold" :class="probabilityClass(doc.probability)">{{ Math.round(doc.probability) }}%</div>
                </div>
                <div v-if="budgetVsAngebot" class="rounded-lg border bg-gray-50 p-3">
                  <div class="text-xs text-gray-500">{{ __('Budget vs. Angebot') }}</div>
                  <div class="mt-1 text-base font-bold" :class="budgetVsAngebot >= 0 ? 'text-green-600' : 'text-amber-600'">{{ budgetVsAngebot >= 0 ? '+' : '' }}{{ Math.round(budgetVsAngebot) }}%</div>
                  <div class="mt-0.5 text-[10px] text-gray-400">{{ budgetVsAngebot >= 0 ? __('under customer budget') : __('over customer budget') }}</div>
                </div>
              </div>
            </section>
          </div>

          <!-- Aktivitäten -->
          <div v-else-if="activeTab === T.ACT" class="crmw-tabpane space-y-4">
            <MailActivityWidget :project="projectId" />

            <h4 class="crmw-sec-title">Angebots-Versionen</h4>
            <PpTimeline v-if="offerTimeline.length" :items="offerTimeline" />
            <PpEmptyState v-else title="Keine Angebote" hint="Sobald ein Angebot angelegt ist, erscheint hier der Versionsverlauf." />

            <h4 class="crmw-sec-title">Notizen &amp; Kommentare</h4>
            <div v-if="activities.loading && !projectComments.length" class="flex items-center justify-center py-8">
              <div class="h-6 w-6 animate-spin rounded-full border-2 border-gray-200 border-t-lcs-secondary" />
            </div>
            <PpComments v-else :comments="projectComments" :users="commentUsers" @submit="addProjectComment" />
          </div>

          <!-- Angebote -->
          <div v-else-if="activeTab === T.OFF" class="crmw-tabpane space-y-4">
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

            <div v-if="offersResource.loading && !offers.length" class="flex items-center justify-center py-8">
              <div class="h-6 w-6 animate-spin rounded-full border-2 border-gray-200 border-t-lcs-secondary" />
            </div>
            <PpEmptyState
              v-else-if="!offers.length"
              title="Noch keine Angebote"
              hint="Lege ein Angebot an, um Versionen und Ausgänge zu verfolgen."
            >
              <template #action>
                <Button variant="outline" size="sm" iconLeft="plus" @click="showNewOfferDialog = true" :label="__('Create first offer')" />
              </template>
            </PpEmptyState>
            <PpDataGrid v-else :columns="offerCols" :rows="offerRows" @row-click="openOffer">
              <template #cell-wert="{ row }">
                <MoneyDual v-if="row._offer.value" class="items-end text-right" :amount="row._offer.value" :currency="row._offer.currency" :value-eur="row._offer.value_eur" :rate="row._offer.exchange_rate_to_eur" :frozen-at="row._offer.rate_frozen_at" size="sm" />
                <span v-else class="text-gray-300">—</span>
              </template>
              <template #cell-status="{ value }">
                <span class="crmw-pill" :data-tone="offerTone(value)"><i class="crmw-dot" />{{ __(value) }}</span>
              </template>
            </PpDataGrid>
            <p class="text-[11px] text-gray-400">{{ __('Open an offer to change its status, versions and outcome.') }}</p>
          </div>

          <!-- Dokumente -->
          <div v-else-if="activeTab === T.DOC" class="crmw-tabpane">
            <PpDocList v-if="docItems.length" :docs="docItems" />
            <PpEmptyState v-else title="Keine Dokumente verknüpft" hint="Verknüpfe einen SharePoint-Ordner, Teams-Kanal oder Dokument-Link im Projekt, um ihn hier zu öffnen." />
          </div>

          <!-- Aufgaben & Zeit -->
          <div v-else-if="activeTab === T.EXE" class="crmw-tabpane">
            <ExecutionPanel :project="projectId" />
          </div>

          <!-- Kontakte -->
          <div v-else-if="activeTab === T.CON" class="crmw-tabpane space-y-3">
            <div v-if="project.loading && !doc.contacts" class="flex items-center justify-center py-12">
              <div class="h-6 w-6 animate-spin rounded-full border-2 border-gray-200 border-t-lcs-secondary" />
            </div>
            <div v-else-if="contactsData.length" class="rounded-lg border px-3">
              <ContactRow v-for="c in contactsData" :key="c.name" :contact="c.name" />
            </div>
            <PpEmptyState v-else title="Keine Kontakte verknüpft" hint="Diesem Projekt sind noch keine Kontakte zugeordnet." />
          </div>

          <!-- PLM / BOM -->
          <div v-else-if="activeTab === T.PLM" class="crmw-tabpane space-y-4">
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
            <div v-if="doc.fusion_item_id">
              <div v-if="bomLoading" class="flex items-center justify-center py-8">
                <div class="h-6 w-6 animate-spin rounded-full border-2 border-gray-200 border-t-lcs-secondary" />
              </div>
              <div v-else-if="bomError" class="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
                <FeatherIcon name="alert-circle" class="mr-1 inline h-3.5 w-3.5" />{{ bomError }}
              </div>
              <BomTree v-else :rows="bomRows" />
            </div>
          </div>

          <!-- Chancen-Matrix -->
          <div v-else-if="activeTab === T.MTX" class="crmw-tabpane">
            <OpportunityMatrix
              :technical-fit="matrixValues.technical_fit"
              :commercial-fit="matrixValues.commercial_fit"
              :relationship="matrixValues.relationship_strength"
              :competition="matrixValues.competition_level"
              :strategic-importance="matrixValues.strategic_importance"
              @update="onMatrixUpdate"
            />
          </div>
        </section>
      </div>
    </div>

    <!-- Meta-/Inspector-Spalte (bestehendes Seitenpanel, Funktionserhalt) -->
    <Resizer side="right" class="flex !w-full shrink-0 flex-col justify-between border-t bg-white lg:!w-auto lg:border-l lg:border-t-0">
      <div v-if="doc.name && canShow('show_integration_panel')" class="border-b px-5 py-4">
        <IntegrationStatusPanel :project="projectId" />
      </div>

      <div class="flex-1 overflow-y-auto">
        <div class="divide-y">
          <div class="space-y-3 px-5 py-4">
            <h4 class="text-[10px] font-bold uppercase tracking-wider text-gray-400">{{ __('Classification') }}</h4>
            <SideField :label="__('Country')"><span class="text-sm text-gray-800">{{ doc.country || '—' }}</span></SideField>
            <SideField :label="__('GU')">
              <span v-if="doc.is_gu" class="flex items-center gap-1 text-sm text-green-600"><FeatherIcon name="check-circle" class="h-3.5 w-3.5" /> {{ __('Yes') }}</span>
              <span v-else class="text-sm text-gray-400">{{ __('No') }}</span>
            </SideField>
          </div>

          <div class="space-y-3 px-5 py-4">
            <h4 class="text-[10px] font-bold uppercase tracking-wider text-gray-400">{{ __('People') }}</h4>
            <SideField :label="__('Salesperson')"><UserPicker :value="doc.salesperson" :placeholder="__('Assign…')" @save="v => updateField('salesperson', v)" /></SideField>
            <SideField :label="__('Sales Manager')"><UserPicker :value="doc.sales_manager" :placeholder="__('Assign…')" @save="v => updateField('sales_manager', v)" /></SideField>
            <SideField :label="__('Organization')"><span class="text-sm text-gray-800">{{ doc.organization || '—' }}</span></SideField>
          </div>

          <div v-if="canShow('show_pricing_details')" class="space-y-2 px-5 py-4">
            <h4 class="text-[10px] font-bold uppercase tracking-wider text-gray-400">{{ __('Pricing') }}</h4>
            <SideField :label="__('Budget')"><span class="text-sm tabular-nums" :class="doc.budget_customer ? 'text-gray-800' : 'text-gray-400'">{{ doc.budget_customer ? formatCurrency(doc.budget_customer) : '—' }}</span></SideField>
            <SideField :label="__('Richtpreis')"><span class="text-sm tabular-nums" :class="doc.richtpreis ? 'text-blue-700 font-medium' : 'text-gray-400'">{{ doc.richtpreis ? formatCurrency(doc.richtpreis) : '—' }}</span></SideField>
            <SideField :label="__('Angebot')"><span class="text-sm tabular-nums" :class="doc.angebot_total ? 'text-green-700 font-semibold' : 'text-gray-400'">{{ doc.angebot_total ? formatCurrency(doc.angebot_total) : '—' }}</span></SideField>
          </div>

          <div v-if="doc.notes" class="space-y-2 bg-amber-50/30 px-5 py-4">
            <h4 class="flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-wider text-amber-700"><FeatherIcon name="edit-3" class="h-3 w-3" />{{ __('Notes Preview') }}</h4>
            <p class="line-clamp-4 whitespace-pre-wrap text-xs text-gray-700">{{ doc.notes }}</p>
            <button class="text-xs font-medium text-amber-700 hover:underline" @click="activeTab = T.OV">{{ __('View full notes →') }}</button>
          </div>

          <div v-if="doc.team_link || doc.sharepoint_link" class="space-y-3 px-5 py-4">
            <h4 class="text-[10px] font-bold uppercase tracking-wider text-gray-400">{{ __('External Links') }}</h4>
            <div class="flex flex-col gap-2">
              <a v-if="doc.team_link" :href="doc.team_link" target="_blank" rel="noopener noreferrer" class="inline-flex items-center gap-1.5 text-sm text-lcs-secondary hover:text-lcs-primary hover:underline"><FeatherIcon name="message-square" class="h-3.5 w-3.5" />{{ __('Teams Channel') }}</a>
              <a v-if="doc.sharepoint_link" :href="doc.sharepoint_link" target="_blank" rel="noopener noreferrer" class="inline-flex items-center gap-1.5 text-sm text-lcs-secondary hover:text-lcs-primary hover:underline"><FeatherIcon name="folder" class="h-3.5 w-3.5" />{{ __('SharePoint Folder') }}</a>
            </div>
          </div>
        </div>
      </div>
    </Resizer>
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
        <div v-if="offerTemplates.length" class="rounded-lg border border-lcs-secondary/20 bg-lcs-secondary/5 p-3">
          <label class="text-xs font-semibold uppercase tracking-wide text-lcs-primary">{{ __('Start from Template') }}</label>
          <div class="mt-2 flex flex-wrap gap-2">
            <button v-for="t in offerTemplates" :key="t.name" class="rounded-lg border bg-white px-3 py-1.5 text-xs font-medium text-gray-700 transition hover:border-lcs-secondary hover:bg-lcs-secondary/10" @click="applyTemplate(t)">
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
          <textarea v-model="newOffer.notes" class="w-full rounded-lg border border-gray-300 px-3 py-2 pr-10 text-sm focus:border-lcs-secondary focus:ring-1 focus:ring-lcs-secondary" rows="3" :placeholder="__('Offer notes, terms, reminders...')" />
          <div class="absolute right-2 top-7"><VoiceInput @transcript="onOfferNotesVoice" /></div>
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
  Breadcrumbs, Button, Dropdown, Dialog, Tooltip, FeatherIcon, FormControl,
  toast, usePageMeta, call,
} from 'frappe-ui'
import LayoutHeader from '@/components/LayoutHeader.vue'
import MoneyDual from '@/components/lcs/MoneyDual.vue'
import Resizer from '@/components/Resizer.vue'
import IntegrationStatusPanel from '@/components/lcs/IntegrationStatusPanel.vue'
import FusionItemPicker from '@/components/lcs/FusionItemPicker.vue'
import BomTree from '@/components/lcs/BomTree.vue'
import ExecutionPanel from '@/components/lcs/ExecutionPanel.vue'
import UserPicker from '@/components/lcs/UserPicker.vue'
import OpportunityMatrix from '@/components/lcs/OpportunityMatrix.vue'
import MailActivityWidget from '@/components/lcs/MailActivityWidget.vue'
import ContactRow from '@/components/lcs/ContactRow.vue'
import PriceStageCard from '@/components/lcs/PriceStageCard.vue'
import VoiceInput from '@/components/lcs/VoiceInput.vue'
// pilanda_theme-Bausteine (Copy-Modell, PP_REV in Datei-Kopf)
import PpPageHead from '@/components/pp/PpPageHead.vue'
import PpPhaseStepper from '@/components/pp/PpPhaseStepper.vue'
import PpStatTile from '@/components/pp/PpStatTile.vue'
import PpTabs from '@/components/pp/PpTabs.vue'
import PpTimeline from '@/components/pp/PpTimeline.vue'
import PpComments from '@/components/pp/PpComments.vue'
import PpDataGrid from '@/components/pp/PpDataGrid.vue'
import PpDocList from '@/components/pp/PpDocList.vue'
import PpEmptyState from '@/components/pp/PpEmptyState.vue'
import { queueMutation, cachePut, listMutations, onQueueChange } from '@/utils/offlineDB'
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

const headSubtitle = computed(() => {
  const parts = []
  if (doc.value.project_number) parts.push(doc.value.project_number)
  if (doc.value.organization) parts.push(doc.value.organization + (doc.value.country ? ` (${doc.value.country})` : ''))
  else if (doc.value.country) parts.push(doc.value.country)
  return parts.join(' · ')
})

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

// ---- Tabs (String-basiert für PpTabs) ----
const T = {
  OV: 'Übersicht', ACT: 'Aktivitäten', OFF: 'Angebote', DOC: 'Dokumente',
  EXE: 'Aufgaben & Zeit', CON: 'Kontakte', PLM: 'PLM / BOM', MTX: 'Chancen-Matrix',
}
const activeTab = ref(T.OV)
const tabs = computed(() => {
  const list = [T.OV, T.ACT, T.OFF, T.DOC, T.EXE, T.CON]
  if (canShow('show_fusion_section')) list.push(T.PLM)
  if (canShow('show_opportunity_matrix')) list.push(T.MTX)
  return list
})

// ---- Phasen-Stepper (echte LCS-Phasen → Oberstufen) ----
const PHASES = ['Qualified', 'Budget', 'Richtpreis', 'Offer', 'Negotiation', 'Won', 'Execution', 'Completed', 'Lost']
const PHASE_STEPS = [
  { key: 'Qualified',   idx: 1, group: 'Interessent', label: 'Qualifiziert' },
  { key: 'Budget',      idx: 2, group: 'Angebot',     label: 'Budget' },
  { key: 'Richtpreis',  idx: 3, group: 'Angebot',     label: 'Richtpreis' },
  { key: 'Offer',       idx: 4, group: 'Angebot',     label: 'Angebot' },
  { key: 'Negotiation', idx: 5, group: 'Angebot',     label: 'Verhandlung' },
  { key: 'Won',         idx: 6, group: 'Projekt',     label: 'Auftrag' },
  { key: 'Execution',   idx: 7, group: 'Projekt',     label: 'Ausführung' },
  { key: 'Completed',   idx: 8, group: 'Projekt',     label: 'Abgeschlossen' },
]
const phaseSteps = PHASE_STEPS.map(({ idx, group, label }) => ({ idx, group, label }))
const currentStep = computed(() => {
  const s = PHASE_STEPS.find((p) => p.key === doc.value.phase)
  return s ? s.idx : 0 // 0 = keine aktive Stufe (z. B. „Lost")
})

// ---- KPI-Zeile (echte Felder) ----
const kpis = computed(() => {
  const val = doc.value.estimated_value || doc.value.angebot_total || doc.value.richtpreis || doc.value.budget_customer || 0
  return [
    { label: 'Auftragswert', value: formatCurrency(val), hint: 'Geschätzter Auftragswert' },
    { label: 'Abschlusswahrsch.', value: `${Math.round(doc.value.probability || 0)} %`, hint: __(doc.value.phase || 'Open') },
    { label: 'Erw. Abschluss', value: doc.value.expected_close_date ? formatDate(doc.value.expected_close_date) : '—', hint: 'laut Planung' },
    { label: 'Angebote', value: String(offers.value.length), hint: activeOffersCount.value ? `${activeOffersCount.value} aktiv` : 'keine aktiven' },
  ]
})

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
watch(activeTab, (t) => { if (t === T.PLM) loadBom() })
watch(() => doc.value.fusion_item_id, () => loadBom())

function onFusionLinked(info) {
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
const showPhaseConfirm = ref(false)
const pendingPhase = ref('')
const isBackwardPhaseMove = computed(() => {
  const currentIdx = PHASES.indexOf(doc.value.phase)
  const newIdx = PHASES.indexOf(pendingPhase.value)
  return newIdx < currentIdx && pendingPhase.value !== 'Lost'
})
const phaseDropdownOptions = computed(() =>
  PHASES.map((phase) => ({
    label: __(phase),
    icon: doc.value.phase === phase ? 'check' : undefined,
    onClick: () => initiatePhaseChange(phase),
  })),
)
// Advancing INTO these phases requires a filled Opportunity Matrix.
const MATRIX_REQUIRED_PHASES = ['Offer', 'Negotiation', 'Won']
function initiatePhaseChange(phase) {
  if (phase === doc.value.phase) return
  pendingPhase.value = phase
  if (!isBackwardPhaseMove.value && MATRIX_REQUIRED_PHASES.includes(phase)
      && !matrixFilled.value && canShow('show_opportunity_matrix')) {
    pendingPhase.value = null
    toast({
      title: __('Opportunity Matrix required'),
      text: __('Fill the Opportunity Matrix before moving to this phase.'),
      icon: 'alert-circle',
      iconClasses: 'text-amber-500',
    })
    goToMatrixTab()
    return
  }
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

// 💼 Offers
const offersResource = createResource({
  url: 'lcs_integrations.projects.api.get_project_offers',
  params: { project: projectId.value },
  auto: true,
})
const offers = computed(() => offersResource.data || [])
const activeOffersCount = computed(() => offers.value.filter(o => ['Draft', 'Sent', 'In Review'].includes(o.status)).length)

// Angebote → PpDataGrid
const offerCols = [
  { key: 'nr',      label: 'Angebot', pin: true, width: 220 },
  { key: 'datum',   label: 'Datum', width: 120 },
  { key: 'version', label: 'Version', align: 'center', width: 90 },
  { key: 'wert',    label: 'Wert', align: 'right', width: 170 },
  { key: 'status',  label: 'Status', width: 150 },
]
const offerRows = computed(() =>
  offers.value.map((o) => ({
    id: o.name,
    nr: o.offer_title || o.name,
    datum: o.offer_date ? formatDate(o.offer_date) : '—',
    version: `v${o.version}`,
    wert: o.value,
    status: o.status,
    _offer: o,
  })),
)
function openOffer(id) {
  router.push({ name: 'LCS Offer', params: { id } })
}
const OFFER_TONE = {
  Draft: 'neutral', Sent: 'info', 'In Review': 'warning', Accepted: 'success',
  Rejected: 'danger', Expired: 'neutral', Revised: 'brand',
}
function offerTone(status) { return OFFER_TONE[status] || 'neutral' }

// Angebots-Versionen → PpTimeline
const offerTimeline = computed(() =>
  offers.value.map((o) => ({
    kind: 'task',
    dir: null,
    subject: `${o.offer_title || 'Angebot'} · v${o.version} — ${__(o.status)}`,
    who: doc.value.salesperson || 'Vertrieb',
    ago: o.offer_date ? formatDate(o.offer_date) : '',
  })),
)

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
  if (creatingOffer.value) return
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

// Contacts, Matrix, Activities
const contactsData = computed(() =>
  (doc.value.contacts || []).map((r) => ({ name: r.contact, role: r.role })),
)

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
let matrixSaveTimer = null
function onMatrixUpdate({ field, value }) {
  matrixValues.value[field] = value
  clearTimeout(matrixSaveTimer)
  matrixSaveTimer = setTimeout(saveMatrix, 500)
}
async function saveMatrix() {
  try {
    await call('lcs_integrations.projects.api.save_opportunity_matrix', {
      project: projectId.value,
      ...matrixValues.value,
    })
    toast({ title: __('Matrix saved'), icon: 'check-circle', iconClasses: 'text-green-500' })
  } catch (err) {
    toast({ title: __('Could not save matrix'), text: err.messages?.[0], icon: 'alert-circle', iconClasses: 'text-red-500' })
  }
}
const matrixFilled = computed(() =>
  Object.values(matrixValues.value).some((v) => (Number(v) || 0) > 0),
)
function goToMatrixTab() {
  if (canShow('show_opportunity_matrix')) activeTab.value = T.MTX
}

// Aktivitäten / Kommentare (echtes Frappe-Comment-System)
const activities = createListResource({
  doctype: 'Comment',
  fields: ['name', 'subject', 'content', 'creation', 'owner'],
  filters: { reference_doctype: 'LCS Project', reference_name: projectId.value, comment_type: ['in', ['Comment', 'Info']] },
  orderBy: 'creation desc',
  pageLength: 50,
  auto: true,
})
const stripHtml = (h) => String(h || '').replace(/<[^>]*>/g, '').replace(/\s+/g, ' ').trim()
const projectComments = computed(() =>
  (activities.data || []).map((c) => ({
    id: c.name,
    author: c.owner || 'System',
    time: formatRelativeTime(c.creation),
    text: stripHtml(c.content) || c.subject || '',
  })),
)
const commentUsers = computed(() =>
  [...new Set([doc.value.salesperson, doc.value.sales_manager, doc.value.project_manager].filter(Boolean))],
)
async function addProjectComment(text) {
  if (!text || !text.trim()) return
  try {
    await call('crm.api.comment.add_comment', {
      reference_doctype: 'LCS Project',
      reference_name: projectId.value,
      content: text,
      attachments: [],
    })
    activities.reload()
    toast({ title: __('Comment added'), icon: 'check-circle', iconClasses: 'text-green-500' })
  } catch (err) {
    toast({ title: __('Could not add comment'), text: err.messages?.[0], icon: 'alert-circle', iconClasses: 'text-red-500' })
  }
}

// Dokumente → PpDocList (echte Link-Felder des Projekts)
const docItems = computed(() => {
  const out = []
  if (doc.value.document_link) out.push({ id: 'doc', title: 'Projektdokument', kind: 'doc', href: doc.value.document_link, meta: ['Dokument-Link'] })
  if (doc.value.sharepoint_link) out.push({ id: 'sp', title: 'SharePoint-Ordner', kind: 'doc', href: doc.value.sharepoint_link, meta: ['SharePoint'] })
  if (doc.value.team_link) out.push({ id: 'teams', title: 'Teams-Kanal', kind: 'doc', href: doc.value.team_link, meta: ['Microsoft Teams'] })
  return out
})

async function updateField(fieldname, value) {
  const baseValues = project.doc ? { [fieldname]: project.doc[fieldname] } : {}
  const baseModified = project.doc?.modified || null

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
function phaseDotClass(phase) {
  const map = { Qualified: 'bg-sky-500', Budget: 'bg-teal-500', Richtpreis: 'bg-violet-500', Offer: 'bg-amber-500', Negotiation: 'bg-orange-500', Won: 'bg-green-500', Execution: 'bg-lcs-primary', Completed: 'bg-gray-400', Lost: 'bg-red-500' }
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
function probabilityClass(val) {
  if (val >= 70) return 'text-green-600'
  if (val >= 40) return 'text-amber-600'
  return 'text-red-500'
}
function formatCurrency(val) {
  return new Intl.NumberFormat('de-DE', { style: 'currency', currency: doc.value?.currency || 'EUR', maximumFractionDigits: 0 }).format(val)
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
</script>

<style scoped>
.crmw { background: var(--pp-bg-base); }
.crmw-main { max-width: 1180px; margin: 0 auto; width: 100%; padding: var(--pp-space-6) var(--pp-space-6) var(--pp-space-12);
  display: flex; flex-direction: column; gap: var(--pp-space-5); }

.crmw-btn { appearance: none; cursor: pointer; font-family: inherit; font-size: var(--pp-fs-13, 13px);
  padding: 6px var(--pp-space-3); border-radius: var(--pp-radius-ui);
  border: 1px solid var(--pp-border-default); background: var(--pp-bg-surface); color: var(--pp-text-primary); }
.crmw-btn:hover { background: var(--pp-bg-hover); border-color: var(--pp-brand-primary); color: var(--pp-brand-primary); }
.crmw-btn--primary { background: var(--pp-brand-primary); border-color: var(--pp-brand-primary); color: var(--pp-text-on-accent); }
.crmw-btn--primary:hover { filter: brightness(1.05); color: var(--pp-text-on-accent); }

.crmw-stepper { background: var(--pp-bg-surface); border: 1px solid var(--pp-border-subtle);
  border-radius: var(--pp-radius-ui); box-shadow: var(--pp-shadow-xs); padding: var(--pp-space-4); }
.crmw-lost { margin: var(--pp-space-3) 0 0; font-size: var(--pp-fs-13, 13px); color: var(--pp-state-danger);
  display: flex; align-items: center; gap: 6px; }

.crmw-kpis { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: var(--pp-space-3); }

.crmw-tabs-wrap { background: var(--pp-bg-surface); border: 1px solid var(--pp-border-subtle);
  border-radius: var(--pp-radius-ui); box-shadow: var(--pp-shadow-xs); padding: var(--pp-space-4); }
.crmw-tabpane { padding-top: var(--pp-space-4); }
.crmw-sec-title { margin: var(--pp-space-2) 0 0; font-size: var(--pp-fs-12); font-weight: var(--pp-weight-bold);
  letter-spacing: var(--pp-tracking-wide, 0.04em); text-transform: uppercase; color: var(--pp-text-tertiary); }
.crmw-sec-title:first-child { margin-top: 0; }
.crmw-desc { margin: 0; font-size: var(--pp-fs-14); color: var(--pp-text-secondary); line-height: var(--pp-lh-relaxed, 1.6); white-space: pre-wrap; }

.crmw-pill { display: inline-flex; align-items: center; gap: 5px; font-size: 11px; font-weight: var(--pp-weight-semibold);
  padding: 2px var(--pp-space-2); border-radius: var(--pp-radius-full); white-space: nowrap; }
.crmw-dot { width: 6px; height: 6px; border-radius: var(--pp-radius-full); flex-shrink: 0; background: currentColor; }
.crmw-pill[data-tone="brand"]   { background: color-mix(in oklab, var(--pp-brand-primary) 14%, transparent); color: var(--pp-brand-primary); }
.crmw-pill[data-tone="info"]    { background: color-mix(in oklab, var(--pp-state-info) 14%, transparent); color: var(--pp-state-info); }
.crmw-pill[data-tone="success"] { background: color-mix(in oklab, var(--pp-state-success) 14%, transparent); color: var(--pp-state-success); }
.crmw-pill[data-tone="warning"] { background: color-mix(in oklab, var(--pp-state-warning) 16%, transparent); color: var(--pp-state-warning); }
.crmw-pill[data-tone="danger"]  { background: color-mix(in oklab, var(--pp-state-danger) 14%, transparent); color: var(--pp-state-danger); }
.crmw-pill[data-tone="neutral"] { background: var(--pp-bg-sunken); color: var(--pp-text-secondary); }

@media (max-width: 1080px) {
  .crmw-kpis { grid-template-columns: repeat(2, 1fr); }
}
</style>
