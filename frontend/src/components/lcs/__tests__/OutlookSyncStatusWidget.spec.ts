import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'

const callMock = vi.fn()
vi.mock('frappe-ui', () => ({
  call: (...args: unknown[]) => callMock(...args),
  FeatherIcon: { name: 'FeatherIcon', props: ['name'], template: '<i />' },
}))

beforeEach(() => {
  callMock.mockReset()
})

import OutlookSyncStatusWidget from '../OutlookSyncStatusWidget.vue'

const mountOpts = { global: { mocks: { __: (s: string) => s } } }

describe('OutlookSyncStatusWidget', () => {
  it('renders an empty state when there are no bindings', async () => {
    callMock.mockResolvedValueOnce({
      settings: { contact_push: false, inbound_contacts: false, calendar: true, teams: true },
      bindings: [],
    })
    const wrapper = mount(OutlookSyncStatusWidget, mountOpts)
    await flushPromises()
    expect(wrapper.text()).toContain('No mailbox bindings')
  })

  it('renders one row per binding with last-sync columns', async () => {
    callMock.mockResolvedValueOnce({
      settings: { contact_push: true, inbound_contacts: true, calendar: true, teams: true },
      bindings: [
        {
          name: 'BIND-1',
          user: 'erika@example.com',
          graph_mailbox: 'erika@example.com',
          is_active: 1,
          last_sync: '2026-05-04 10:00:00',
          last_calendar_sync: '2026-05-04 10:01:00',
          last_contacts_sync: null,
          last_error: null,
        },
        {
          name: 'BIND-2',
          user: 'hans@example.com',
          graph_mailbox: 'hans@example.com',
          is_active: 1,
          last_sync: null,
          last_calendar_sync: null,
          last_contacts_sync: null,
          last_error: 'Graph HTTP 401',
        },
      ],
    })

    const wrapper = mount(OutlookSyncStatusWidget, mountOpts)
    await flushPromises()

    const rows = wrapper.findAll('[data-testid="binding-list"] li')
    expect(rows).toHaveLength(2)
    expect(rows[0].text()).toContain('erika@example.com')
    expect(rows[1].text()).toContain('Graph HTTP 401')
  })

  it('triggers a per-binding resync when the inline button is clicked', async () => {
    callMock.mockImplementation((method: string, args?: Record<string, unknown>) => {
      if (method === 'lcs_integrations.outlook_sync.api.get_sync_status') {
        return Promise.resolve({
          settings: { contact_push: true, inbound_contacts: false, calendar: true, teams: false },
          bindings: [
            {
              name: 'BIND-1',
              user: 'erika@example.com',
              graph_mailbox: 'erika@example.com',
              is_active: 1,
              last_sync: '2026-05-04 10:00:00',
              last_calendar_sync: null,
              last_contacts_sync: null,
              last_error: null,
            },
          ],
        })
      }
      if (method === 'lcs_integrations.outlook_sync.api.trigger_resync') {
        return Promise.resolve({ binding: args?.binding, mail: 1, calendar: 0 })
      }
      return Promise.resolve({})
    })

    const wrapper = mount(OutlookSyncStatusWidget, mountOpts)
    await flushPromises()

    const buttons = wrapper.findAll('[data-testid="binding-list"] li button')
    expect(buttons).toHaveLength(1)
    await buttons[0].trigger('click')
    await flushPromises()

    expect(callMock).toHaveBeenCalledWith(
      'lcs_integrations.outlook_sync.api.trigger_resync',
      { binding: 'BIND-1' },
    )
  })
})
