import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it } from 'vitest'

import router from './index'
import { useAuthStore } from '@/stores/auth'

/** Les gardes de navigation sont un confort UX : l'API reste la source d'autorité. */
describe('gardes de navigation', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    useAuthStore().clearSession()
  })

  it('redirige un visiteur vers la connexion', async () => {
    await router.push('/patient')
    expect(router.currentRoute.value.name).toBe('connexion')
    expect(router.currentRoute.value.query.redirect).toBe('/patient')
  })

  it("renvoie un patient vers son espace lorsqu'il vise une zone médecin", async () => {
    useAuthStore().user = { id: 1, role: 'PATIENT', first_name: 'Awa' }
    await router.push('/medecin')
    expect(router.currentRoute.value.path).toBe('/patient')
  })

  it('laisse un agent accéder à son interface de scan', async () => {
    useAuthStore().user = { id: 2, role: 'AGENT', first_name: 'Moussa' }
    await router.push('/accueil')
    expect(router.currentRoute.value.name).toBe('agent-scan')
  })

  it("empêche un utilisateur connecté de revenir sur l'écran de connexion", async () => {
    useAuthStore().user = { id: 3, role: 'ADMIN', first_name: 'Admin' }
    await router.push('/connexion')
    expect(router.currentRoute.value.path).toBe('/admin')
  })
})
