import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import AbasDeepLink from '../AbasDeepLink.vue'

type GlobalWithFrappe = typeof globalThis & {
  frappe?: { boot?: { lcs_abas_web_base?: string } }
}

describe('AbasDeepLink', () => {
  beforeEach(() => {
    ;(globalThis as GlobalWithFrappe).frappe = {
      boot: { lcs_abas_web_base: 'https://abas.example.com/' },
    }
  })

  afterEach(() => {
    delete (globalThis as GlobalWithFrappe).frappe
  })

  it('renders a link with the normalised base + encoded id', async () => {
    const wrapper = mount(AbasDeepLink, {
      props: { entity: 'K 12345', kind: 'customer' },
    })
    await flushPromises()
    const anchor = wrapper.find('a')
    expect(anchor.exists()).toBe(true)
    expect(anchor.attributes('href')).toBe(
      'https://abas.example.com/ui/customer/K%2012345',
    )
    expect(anchor.attributes('target')).toBe('_blank')
    expect(anchor.attributes('rel')).toBe('noopener noreferrer')
  })

  it('falls back to a plain span when base url is not configured', async () => {
    ;(globalThis as GlobalWithFrappe).frappe = { boot: {} }
    const wrapper = mount(AbasDeepLink, {
      props: { entity: 'K12345', kind: 'customer' },
    })
    await flushPromises()
    expect(wrapper.find('a').exists()).toBe(false)
    expect(wrapper.find('span').text()).toBe('K12345')
  })

  it('honours a custom label', async () => {
    const wrapper = mount(AbasDeepLink, {
      props: { entity: 'K12345', kind: 'customer', label: 'Open in abas' },
    })
    await flushPromises()
    expect(wrapper.text()).toContain('Open in abas')
  })
})
