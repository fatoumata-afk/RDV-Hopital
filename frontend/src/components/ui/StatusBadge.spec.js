import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import StatusBadge from './StatusBadge.vue'

describe('StatusBadge', () => {
  it('affiche le libellé français du statut', () => {
    const wrapper = mount(StatusBadge, { props: { status: 'ARRIVED' } })
    expect(wrapper.text()).toBe('Arrivé')
  })

  it('reste lisible pour un statut inconnu', () => {
    const wrapper = mount(StatusBadge, { props: { status: 'UNKNOWN' } })
    expect(wrapper.text()).toBe('UNKNOWN')
  })
})
