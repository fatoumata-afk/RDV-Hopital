import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it } from 'vitest'

import { useAuthStore } from './auth'

describe('store d\'authentification', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
  })

  it('oriente chaque rôle vers son espace', () => {
    const auth = useAuthStore()
    const homes = {
      PATIENT: '/patient',
      DOCTOR: '/medecin',
      AGENT: '/accueil',
      ADMIN: '/admin',
    }
    for (const [role, home] of Object.entries(homes)) {
      auth.user = { id: 1, role }
      expect(auth.homeRoute).toBe(home)
    }
  })

  it('efface le jeton de rafraîchissement à la déconnexion', async () => {
    const auth = useAuthStore()
    localStorage.setItem('hospirdv.refresh', 'jeton')
    auth.user = { id: 1, role: 'PATIENT' }
    auth.clearSession()
    expect(auth.isAuthenticated).toBe(false)
    expect(localStorage.getItem('hospirdv.refresh')).toBeNull()
  })
})
