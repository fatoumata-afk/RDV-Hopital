import { describe, expect, it } from 'vitest'

import { errorMessage, fieldErrors } from './http'

describe('errorMessage', () => {
  it('privilégie le détail renvoyé par l\'API', () => {
    const error = { response: { data: { detail: 'Créneau indisponible.' } } }
    expect(errorMessage(error)).toBe('Créneau indisponible.')
  })

  it('retombe sur la première erreur de champ', () => {
    const error = { response: { data: { email: ['Adresse déjà utilisée.'] } } }
    expect(errorMessage(error)).toBe('Adresse déjà utilisée.')
  })

  it('utilise le message par défaut sans réponse', () => {
    expect(errorMessage({}, 'Échec.')).toBe('Échec.')
  })
})

describe('fieldErrors', () => {
  it('aplatit les erreurs par champ en ignorant detail et code', () => {
    const error = {
      response: {
        data: { detail: 'Invalide', code: 'invalid', password: ['Trop court.', 'Trop commun.'] },
      },
    }
    expect(fieldErrors(error)).toEqual({ password: 'Trop court. Trop commun.' })
  })
})
