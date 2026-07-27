import { createRouter, createWebHistory } from 'vue-router'
import { call } from 'frappe-ui'
import { usersStore } from '@/stores/users'
import { sessionStore } from '@/stores/session'
import { viewsStore } from '@/stores/views'

const routes = [
  {
    path: '/',
    name: 'Home',
  },
  {
    path: '/notifications',
    name: 'Notifications',
    component: () => import('@/pages/MobileNotification.vue'),
  },
  {
    // CRM-Integration Teil 3/3: das CRM-Dashboard bekommt die Pilanda-UX
    // (LCSCRMDashboard, PpDashboard-Komposition). Route-Shape unverändert
    // (path/name 'Dashboard'), Datenlogik bleibt Dominiks get_dashboard.
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('@/pages/LCSCRMDashboard.vue'),
  },
  {
    // Dominiks Original-Dashboard (editierbares Chart-Grid) bleibt als
    // Fallback erreichbar — nicht in der Sidebar verlinkt.
    path: '/dashboard-upstream',
    name: 'Dashboard Upstream',
    component: () => import('@/pages/Dashboard.vue'),
  },
  {
    // CRM-Integration Teil 1/3: die Interessenten-Kernfläche bekommt die
    // Pilanda-UX (LCSLeads, Pp*-Bausteine). Route-Shape unverändert
    // (alias/path/name), damit der beforeEach-viewType-Guard weiter greift —
    // LCSLeads ignoriert den viewType-Param.
    alias: '/leads',
    path: '/leads/view/:viewType?',
    name: 'Leads',
    component: () => import('@/pages/LCSLeads.vue'),
  },
  {
    // Dominiks Original-Leads-Liste bleibt als Fallback erreichbar
    // (nicht in der Sidebar) — Übergang, bis der Detail-Umbau folgt.
    alias: '/leads-upstream',
    path: '/leads-upstream/view/:viewType?',
    name: 'Leads Upstream',
    component: () => import('@/pages/Leads.vue'),
  },
  {
    // CRM-Integration (Detail-Welle): die Interessenten-DETAILSEITE bekommt die
    // Pilanda-UX (LCSLead, Pp*-Bausteine). Route-Shape unverändert
    // (path/name 'Lead'), damit der „Im CRM öffnen"-Link der Liste und der
    // beforeEach-Hash-Guard weiter greifen.
    path: '/leads/:leadId',
    name: 'Lead',
    component: () => import('@/pages/LCSLead.vue'),
    props: true,
  },
  {
    // Dominiks Original-Detailseite bleibt als Fallback erreichbar (nicht in der
    // Sidebar) — Ziel von „Vollansicht öffnen" (E-Mail-Composer, Telefonie,
    // WhatsApp, Tabs), die die Pilanda-Seite bewusst nicht nachbaut.
    path: '/leads-upstream/:leadId',
    name: 'Lead Upstream',
    component: () => import(`@/pages/${handleMobileView('Lead')}.vue`),
    props: true,
  },
  {
    // CRM-Integration Teil 2/3: die Verkaufschancen-Kernfläche bekommt die
    // Pilanda-UX (LCSDeals, PpKanban-Pipeline). Route-Shape unverändert
    // (alias/path/name), damit der beforeEach-viewType-Guard weiter greift —
    // LCSDeals ist selbst das Board und ignoriert den viewType-Param.
    alias: '/deals',
    path: '/deals/view/:viewType?',
    name: 'Deals',
    component: () => import('@/pages/LCSDeals.vue'),
    // Normalise the bare /deals landing to the Kanban board URL.
    beforeEnter: (to) => {
      if (!to.params.viewType && !to.query.view) {
        return { name: 'Deals', params: { viewType: 'kanban' }, query: to.query }
      }
    },
  },
  {
    // Dominiks Original-Deals-Liste bleibt als Fallback erreichbar
    // (nicht in der Sidebar) — Übergang, bis der Detail-Umbau folgt.
    alias: '/deals-upstream',
    path: '/deals-upstream/view/:viewType?',
    name: 'Deals Upstream',
    component: () => import('@/pages/Deals.vue'),
  },
  {
    // CRM-Integration (Detail-Welle): die Verkaufschancen-DETAILSEITE bekommt die
    // Pilanda-UX (LCSDeal, Pp*-Bausteine). Route-Shape unverändert
    // (path/name 'Deal'), damit der „Im CRM öffnen"-Link der Liste und der
    // beforeEach-Hash-Guard weiter greifen.
    path: '/deals/:dealId',
    name: 'Deal',
    component: () => import('@/pages/LCSDeal.vue'),
    props: true,
    // Unified Deal/Project: open the LCS Project workspace instead of the bare
    // deal page. Falls through to the deal page if no project exists yet, or
    // when ?noredirect=1 is set (escape hatch for debugging the raw deal).
    // Guard UNVERÄNDERT (Deal=Projekt-Logik von Dominik/lcs_integrations).
    beforeEnter: async (to) => {
      if (to.query.noredirect) return true
      try {
        const project = await call(
          'lcs_integrations.projects.api.find_project_for',
          { doctype: 'CRM Deal', name: to.params.dealId },
        )
        if (project?.name) {
          return { name: 'LCS Project', params: { id: project.name }, query: to.query }
        }
      } catch (e) {
        /* fall through to the deal page */
      }
      return true
    },
  },
  {
    // Dominiks Original-Detailseite bleibt als Fallback erreichbar (nicht in der
    // Sidebar) — Ziel von „Vollansicht öffnen" (E-Mail-Composer, Telefonie,
    // WhatsApp, Tabs), die die Pilanda-Seite bewusst nicht nachbaut.
    path: '/deals-upstream/:dealId',
    name: 'Deal Upstream',
    component: () => import(`@/pages/${handleMobileView('Deal')}.vue`),
    props: true,
  },
  {
    path: '/projects',
    name: 'LCS Projects',
    component: () => import('@/pages/LCSProjects.vue'),
  },
  {
    path: '/projects-map',
    name: 'LCS Projects Map',
    component: () => import('@/pages/LCSProjectsMap.vue'),
  },
  {
    // Phased rollout placeholder for features that are not live yet
    // (e.g. Produktportfolio → /app/product-portfolio). Fed a title/desc via query.
    path: '/coming-soon',
    name: 'Coming Soon',
    component: () => import('@/pages/LCSComingSoon.vue'),
  },
  {
    path: '/projects/:id',
    name: 'LCS Project',
    component: () => import('@/pages/LCSProject.vue'),
    props: true,
  },
  {
    path: '/network',
    name: 'LCS Network',
    component: () => import('@/pages/LCSNetwork.vue'),
  },
  {
    path: '/market-assignment',
    name: 'LCS Market Assignment',
    component: () => import('@/pages/LCSMarketAssignment.vue'),
  },
  {
    path: '/sales-meeting',
    name: 'LCS Sales Meeting',
    component: () => import('@/pages/LCSSalesMeeting.vue'),
  },
  {
    path: '/forecasting',
    name: 'LCS Forecasting',
    component: () => import('@/pages/LCSForecasting.vue'),
  },
  {
    path: '/quick-note',
    name: 'LCS Quick Note',
    component: () => import('@/pages/LCSQuickNote.vue'),
  },
  {
    path: '/offers/:id',
    name: 'LCS Offer',
    component: () => import('@/pages/LCSOfferDetail.vue'),
    props: true,
  },
  {
    alias: '/notes',
    path: '/notes/view/:viewType?',
    name: 'Notes',
    component: () => import('@/pages/Notes.vue'),
  },
  {
    alias: '/tasks',
    path: '/tasks/view/:viewType?',
    name: 'Tasks',
    component: () => import('@/pages/Tasks.vue'),
  },
  {
    // Personen bekommen die Pilanda-UX (LCSContacts). Route-Shape unverändert
    // (alias/path/name 'Contacts'), damit Nav + getRowRoute-Links weiter greifen.
    // LCSContacts ignoriert den viewType-Param.
    alias: '/contacts',
    path: '/contacts/view/:viewType?',
    name: 'Contacts',
    component: () => import('@/pages/LCSContacts.vue'),
  },
  {
    // Generische Upstream-Kontaktliste bleibt als Fallback erreichbar
    // (nicht in der Sidebar) — volle Filter/Views/Spaltenkonfig.
    alias: '/contacts-upstream',
    path: '/contacts-upstream/view/:viewType?',
    name: 'Contacts Upstream',
    component: () => import('@/pages/Contacts.vue'),
  },
  {
    path: '/contacts/:contactId',
    name: 'Contact',
    component: () => import(`@/pages/${handleMobileView('Contact')}.vue`),
    props: true,
  },
  {
    // Firmen bekommen die Pilanda-UX (LCSOrganizations). Route-Shape unverändert
    // (alias/path/name 'Organizations'). LCSOrganizations ignoriert viewType.
    alias: '/organizations',
    path: '/organizations/view/:viewType?',
    name: 'Organizations',
    component: () => import('@/pages/LCSOrganizations.vue'),
  },
  {
    // Generische Upstream-Firmenliste bleibt als Fallback erreichbar.
    alias: '/organizations-upstream',
    path: '/organizations-upstream/view/:viewType?',
    name: 'Organizations Upstream',
    component: () => import('@/pages/Organizations.vue'),
  },
  {
    path: '/organizations/:organizationId',
    name: 'Organization',
    component: () => import(`@/pages/${handleMobileView('Organization')}.vue`),
    props: true,
  },
  {
    alias: '/call-logs',
    path: '/call-logs/view/:viewType?',
    name: 'Call Logs',
    component: () => import('@/pages/LCSCallLogs.vue'),
  },
  {
    alias: '/call-logs-upstream',
    path: '/call-logs-upstream/view/:viewType?',
    name: 'Call Logs Upstream',
    component: () => import('@/pages/CallLogs.vue'),
  },
  {
    path: '/data-import',
    name: 'DataImportList',
    component: () => import('@/pages/DataImport.vue'),
  },
  {
    path: '/data-import/doctype/:doctype',
    name: 'NewDataImport',
    component: () => import('@/pages/DataImport.vue'),
    props: true,
  },
  {
    path: '/data-import/:importName',
    name: 'DataImport',
    component: () => import('@/pages/DataImport.vue'),
    props: true,
  },
  {
    path: '/welcome',
    name: 'Welcome',
    component: () => import('@/pages/Welcome.vue'),
  },
  {
    path: '/:invalidpath',
    name: 'Invalid Page',
    component: () => import('@/pages/InvalidPage.vue'),
  },
  {
    path: '/not-permitted',
    name: 'Not Permitted',
    component: () => import('@/pages/NotPermitted.vue'),
  },
]

const handleMobileView = (componentName) => {
  return window.innerWidth < 768 ? `Mobile${componentName}` : componentName
}

let router = createRouter({
  history: createWebHistory('/crm'),
  routes,
})

router.beforeEach(async (to, from, next) => {
  router.previousRoute = from

  const { isLoggedIn } = sessionStore()
  const { users, isCrmUser } = usersStore()

  if (isLoggedIn && !users.fetched) {
    try {
      await users.promise
    } catch (error) {
      console.error('Error loading users', error)
    }
  }

  if (isLoggedIn && to.name !== 'Not Permitted' && !isCrmUser()) {
    next({ name: 'Not Permitted' })
  } else if (to.name === 'Home' && isLoggedIn) {
    const { views, getDefaultView } = viewsStore()
    await views.promise

    let defaultView = getDefaultView()
    if (!defaultView) {
      next({ name: 'Leads' })
      return
    }

    let { route_name, type, name, is_standard } = defaultView
    route_name = route_name || 'Leads'

    if (name && !is_standard) {
      next({
        name: route_name,
        params: { viewType: type },
        query: { view: name },
      })
    } else {
      next({ name: route_name, params: { viewType: type } })
    }
  } else if (!isLoggedIn) {
    window.location.href = '/login?redirect-to=/crm'
  } else if (to.matched.length === 0) {
    next({ name: 'Invalid Page' })
  } else if (['Deal', 'Lead'].includes(to.name) && !to.hash) {
    let storageKey = to.name === 'Deal' ? 'lastDealTab' : 'lastLeadTab'
    const activeTab = localStorage.getItem(storageKey) || 'activity'
    const hash = '#' + activeTab
    next({ ...to, hash })
  } else if (
    [
      'Leads',
      'Deals',
      'Contacts',
      'Organizations',
      'Notes',
      'Tasks',
      'Call Logs',
    ].includes(to.name) &&
    !to.query?.view
  ) {
    const { views, standardViews, getDefaultView } = viewsStore()
    await views.promise

    const viewType = to.params?.viewType ?? ''
    const standardViewTypes = ['list', 'kanban', 'group_by']

    if (!viewType) {
      const doctypeMap = {
        Leads: 'CRM Lead',
        Deals: 'CRM Deal',
        Contacts: 'Contact',
        Organizations: 'CRM Organization',
        Notes: 'FCRM Note',
        Tasks: 'CRM Task',
        'Call Logs': 'CRM Call Log',
      }

      const doctype = doctypeMap[to.name]
      let defaultViewType = 'list'

      let globalDefault = getDefaultView()
      if (globalDefault && globalDefault.route_name === to.name) {
        defaultViewType = globalDefault.type || 'list'
        if (globalDefault.name && !globalDefault.is_standard) {
          next({
            name: to.name,
            params: { viewType: defaultViewType },
            query: { ...to.query, view: globalDefault.name },
          })
          return
        }
      }

      for (const viewType of standardViewTypes) {
        const standardView = standardViews.value?.[doctype + ' ' + viewType]
        if (standardView?.is_default) {
          defaultViewType = viewType
          break
        }
      }

      next({
        name: to.name,
        params: { viewType: defaultViewType },
        query: to.query,
      })
    } else if (!standardViewTypes.includes(viewType)) {
      const viewNameOrLabel = viewType

      let view = views.data?.find(
        (v) => v.name == viewNameOrLabel || v.label === viewNameOrLabel,
      )

      if (view) {
        next({
          name: to.name,
          params: { viewType: view.type || 'list' },
          query: { ...to.query, view: view.name },
        })
      } else {
        next({
          name: to.name,
          params: { viewType: 'list' },
          query: to.query,
        })
      }
    } else {
      next()
    }
  } else {
    next()
  }
})

export default router
