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

import WhatsAppPanel from '../WhatsAppPanel.vue'

const mountOpts = { global: { mocks: { __: (s: string) => s } } }

function mountWithMessages(messages: unknown[], settings = { enabled: true }) {
  callMock.mockImplementation((method: string) => {
    if (method === 'lcs_integrations.whatsapp.api.list_messages') {
      return Promise.resolve(messages)
    }
    if (method === 'lcs_integrations.whatsapp.api.settings_summary') {
      return Promise.resolve(settings)
    }
    if (method === 'lcs_integrations.whatsapp.service.send_text') {
      return Promise.resolve({ name: 'NEW', wa_message_id: 'wamid.NEW' })
    }
    return Promise.resolve({})
  })
  return mount(WhatsAppPanel, {
    props: { contact: 'Erika Mustermann', phone: '+491701234567' },
    ...mountOpts,
  })
}

describe('WhatsAppPanel', () => {
  it('shows the no-phone fallback when no phone is provided', async () => {
    const wrapper = mount(WhatsAppPanel, { props: { contact: null, phone: null }, ...mountOpts })
    await flushPromises()
    expect(wrapper.text()).toContain('No phone number on this contact')
  })

  it('renders inbound and outbound bubbles in chronological order', async () => {
    const wrapper = mountWithMessages([
      { name: 'A', direction: 'Outbound', body: 'Hi', status: 'sent', creation: '2026-05-01 10:00:00' },
      { name: 'B', direction: 'Inbound', body: 'Hallo', status: 'received', creation: '2026-05-01 09:30:00' },
    ])
    await flushPromises()

    const bubbles = wrapper.findAll('[data-testid="wa-list"] li')
    expect(bubbles).toHaveLength(2)
    // chronological reverse: oldest at index 0 — incoming "Hallo" precedes outgoing "Hi"
    expect(bubbles[0].text()).toContain('Hallo')
    expect(bubbles[1].text()).toContain('Hi')
    // Outbound bubble carries the right alignment class
    expect(bubbles[1].classes().join(' ')).toMatch(/justify-end/)
  })

  it('disables sending when settings are not enabled', async () => {
    const wrapper = mountWithMessages([], { enabled: false })
    await flushPromises()
    expect(wrapper.text()).toContain('Sending is disabled')
    expect(wrapper.find('form').exists()).toBe(false)
  })

  it('sends a message and clears the draft', async () => {
    const wrapper = mountWithMessages([])
    await flushPromises()

    const textarea = wrapper.find('textarea')
    await textarea.setValue('Hallo Erika')
    await wrapper.find('form').trigger('submit.prevent')
    await flushPromises()

    expect(callMock).toHaveBeenCalledWith(
      'lcs_integrations.whatsapp.service.send_text',
      expect.objectContaining({ to: '+491701234567', body: 'Hallo Erika' }),
    )
    // Draft cleared after success
    expect((textarea.element as HTMLTextAreaElement).value).toBe('')
  })
})
