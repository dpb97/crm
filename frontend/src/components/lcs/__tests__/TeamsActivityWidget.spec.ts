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

import TeamsActivityWidget from '../TeamsActivityWidget.vue'

// Frappe injects __ via app.config.globalProperties at runtime — emulate it
// per mount so the SFC compilation finds it on `_ctx`.
const mountOpts = { global: { mocks: { __: (s: string) => s } } }

describe('TeamsActivityWidget', () => {
  it('shows a not-provisioned CTA when no team_id is set', async () => {
    callMock.mockResolvedValueOnce({
      project: 'PRJ-1',
      project_name: 'ACME',
      team_link: null,
      team_id: null,
      notifications_channel_id: null,
      notifications_channel_name: '01-Sales',
      teams_notifications_enabled: false,
      channels: [],
      error: null,
    })

    const wrapper = mount(TeamsActivityWidget, { props: { project: 'PRJ-1' }, ...mountOpts })
    await flushPromises()

    expect(wrapper.text()).toContain('No Teams workspace yet')
    expect(callMock).toHaveBeenCalledWith(
      'lcs_integrations.teams.api.get_project_teams_info',
      { project: 'PRJ-1' },
    )
  })

  it('renders channels and tags the notifications channel', async () => {
    callMock.mockResolvedValueOnce({
      project: 'PRJ-1',
      project_name: 'ACME',
      team_link: 'https://teams.microsoft.com/l/team/abc',
      team_id: 'abc',
      notifications_channel_id: 'ch-sales',
      notifications_channel_name: '01-Sales',
      teams_notifications_enabled: true,
      channels: [
        { id: 'ch-sales', name: '01-Sales', description: 'Sales', web_url: 'https://teams.example/1' },
        { id: 'ch-pm', name: '03-Project-Management', description: 'PM', web_url: 'https://teams.example/2' },
      ],
      error: null,
    })

    const wrapper = mount(TeamsActivityWidget, { props: { project: 'PRJ-1' }, ...mountOpts })
    await flushPromises()

    expect(wrapper.text()).toContain('01-Sales')
    expect(wrapper.text()).toContain('03-Project-Management')
    // The "notify" badge should appear exactly once, on the notifications channel.
    const badges = wrapper.findAll('span').filter((el) => el.text() === 'notify')
    expect(badges).toHaveLength(1)
  })

  it('surfaces a Graph error inline without crashing', async () => {
    callMock.mockResolvedValueOnce({
      project: 'PRJ-1',
      project_name: 'ACME',
      team_link: 'https://teams.microsoft.com/l/team/abc',
      team_id: 'abc',
      notifications_channel_id: null,
      notifications_channel_name: '01-Sales',
      teams_notifications_enabled: true,
      channels: [],
      error: 'Graph HTTP 401',
    })

    const wrapper = mount(TeamsActivityWidget, { props: { project: 'PRJ-1' }, ...mountOpts })
    await flushPromises()

    expect(wrapper.text()).toContain('Graph HTTP 401')
  })
})
