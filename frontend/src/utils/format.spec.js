import { describe, expect, it } from 'vitest'

import { formatShortDate, STATUS_STYLES, toIsoDate } from './format'

describe('toIsoDate', () => {
  it('renvoie la date locale au format AAAA-MM-JJ', () => {
    expect(toIsoDate(new Date(2026, 8, 25, 23, 30))).toBe('2026-09-25')
  })
})

describe('formatShortDate', () => {
  it('affiche un tiret quand la valeur est absente', () => {
    expect(formatShortDate(null)).toBe('—')
  })

  it('formate une date ISO en jj/mm/aaaa', () => {
    expect(formatShortDate('2026-09-25T10:30:00Z')).toMatch(/^\d{2}\/\d{2}\/2026$/)
  })
})

describe('STATUS_STYLES', () => {
  it('couvre tous les statuts exposés par le backend', () => {
    expect(Object.keys(STATUS_STYLES).sort()).toEqual(
      [
        'ARRIVED',
        'BOOKED',
        'CANCELLED',
        'COMPLETED',
        'CONFIRMED',
        'IN_CONSULTATION',
        'NO_SHOW',
      ],
    )
  })
})
