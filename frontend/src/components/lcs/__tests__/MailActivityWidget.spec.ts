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

import MailActivityWidget from '../MailActivityWidget.vue'

const mountOpts = { global: { mocks: { __: (s: string) => s } } }

describe('MailActivityWidget', () => {
  it('asks for a selector when none is provided', async () => {
    const wrapper = mount(MailActivityWidget, { props: {}, ...mountOpts })
    await flushPromises()
    expect(wrapper.text()).toContain('Pass a contact, organization, project, or email')
    expect(callMock).not.toHaveBeenCalled()
  })

  it('renders sender label for received and recipient label for sent', async () => {
    callMock.mockResolvedValueOnce([
      {
        name: 'COMM-1',
        subject: 'Anfrage Seilkran',
        sender: 'erika@example.com',
        recipients: 'sales@lcs.com',
        sent_or_received: 'Received',
        communication_date: '2026-05-04 09:00:00',
        creation: '2026-05-04 09:00:00',
        content: '<p>Hello</p>',
      },
      {
        name: 'COMM-2',
        subject: 'Re: Anfrage Seilkran',
        sender: 'sales@lcs.com',
        recipients: 'erika@example.com',
        sent_or_received: 'Sent',
        communication_date: '2026-05-04 09:30:00',
        creation: '2026-05-04 09:30:00',
        content: '<p>Hi back</p>',
      },
    ])

    const wrapper = mount(MailActivityWidget, {
      props: { contact: 'Erika' },
      ...mountOpts,
    })
    await flushPromises()

    const rows = wrapper.findAll('[data-testid="mail-list"] li')
    expect(rows).toHaveLength(2)
    expect(rows[0].text()).toContain('From: erika@example.com')
    expect(rows[1].text()).toContain('To: erika@example.com')
  })

  it('expands the body on click and strips dangerous html', async () => {
    callMock.mockResolvedValueOnce([
      {
        name: 'COMM-1',
        subject: 'Test',
        sender: 'a@b',
        recipients: 'c@d',
        sent_or_received: 'Received',
        communication_date: '2026-05-04 09:00:00',
        creation: '2026-05-04 09:00:00',
        content:
          '<p>Hello</p><script>alert(1)</script><img src=x onerror="alert(2)" />',
      },
    ])

    const wrapper = mount(MailActivityWidget, {
      props: { contact: 'Erika' },
      ...mountOpts,
    })
    await flushPromises()

    await wrapper.find('[data-testid="mail-list"] li button').trigger('click')
    await flushPromises()

    const html = wrapper.find('[data-testid="mail-list"] li > div').html()
    expect(html).toContain('Hello')
    expect(html).not.toContain('<script')
    expect(html).not.toMatch(/onerror=/i)
  })

  it('forwards the selector to the API', async () => {
    callMock.mockResolvedValueOnce([])

    mount(MailActivityWidget, { props: { project: 'PRJ-1', limit: 10 }, ...mountOpts })
    await flushPromises()

    expect(callMock).toHaveBeenCalledWith(
      'lcs_integrations.outlook_sync.api.list_communications',
      expect.objectContaining({ project: 'PRJ-1', limit: 10 }),
    )
  })
})
