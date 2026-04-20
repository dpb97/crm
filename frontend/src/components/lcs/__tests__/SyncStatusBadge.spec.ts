import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import SyncStatusBadge from '../SyncStatusBadge.vue'

describe('SyncStatusBadge', () => {
  it('renders the synchronised state with the success palette', () => {
    const wrapper = mount(SyncStatusBadge, {
      props: { status: 'synced', system: 'abas' },
    })
    expect(wrapper.text()).toContain('abas')
    expect(wrapper.text()).toContain('synchronised')
    expect(wrapper.classes().join(' ')).toMatch(/lcs-success/)
  })

  it('animates the pending dot', () => {
    const wrapper = mount(SyncStatusBadge, {
      props: { status: 'pending', system: 'Outlook' },
    })
    const dot = wrapper.find('span span')
    expect(dot.classes()).toContain('animate-pulse')
  })

  it('uses detail as tooltip when provided', () => {
    const wrapper = mount(SyncStatusBadge, {
      props: { status: 'error', system: 'Proxess', detail: '401 Unauthorised' },
    })
    expect(wrapper.attributes('title')).toBe('401 Unauthorised')
  })

  it('falls back to the label in the tooltip', () => {
    const wrapper = mount(SyncStatusBadge, {
      props: { status: 'disabled', system: 'Entra' },
    })
    expect(wrapper.attributes('title')).toBe('Entra · disabled')
  })
})
