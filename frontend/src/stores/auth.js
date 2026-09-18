import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import { authApi } from '@/services/api'
import { configureHttp, setAccessToken } from '@/services/http'

const REFRESH_KEY = 'hospirdv.refresh'

export const HOME_BY_ROLE = {
  PATIENT: '/patient',
  DOCTOR: '/medecin',
  AGENT: '/accueil',
  ADMIN: '/admin',
}

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const access = ref(null)
  const refreshToken = ref(localStorage.getItem(REFRESH_KEY))
  const ready = ref(false)

  const isAuthenticated = computed(() => Boolean(user.value))
  const role = computed(() => user.value?.role ?? null)
  const homeRoute = computed(() => HOME_BY_ROLE[role.value] ?? '/connexion')

  function setSession({ access: accessValue, refresh, user: userValue }) {
    access.value = accessValue
    setAccessToken(accessValue)
    if (refresh) {
      refreshToken.value = refresh
      localStorage.setItem(REFRESH_KEY, refresh)
    }
    if (userValue) user.value = userValue
  }

  function clearSession() {
    user.value = null
    access.value = null
    refreshToken.value = null
    setAccessToken(null)
    localStorage.removeItem(REFRESH_KEY)
  }

  async function login(credentials) {
    const data = await authApi.login(credentials)
    setSession(data)
    return data.user
  }

  async function register(payload) {
    await authApi.register(payload)
    return login({ email: payload.email, password: payload.password })
  }

  /** Rafraîchit le jeton d'accès ; renvoie null si la session est perdue. */
  async function refreshAccess() {
    if (!refreshToken.value) return null
    try {
      const data = await authApi.refresh(refreshToken.value)
      access.value = data.access
      setAccessToken(data.access)
      if (data.refresh) {
        refreshToken.value = data.refresh
        localStorage.setItem(REFRESH_KEY, data.refresh)
      }
      return data.access
    } catch {
      clearSession()
      return null
    }
  }

  /** Reprend une session existante au démarrage de l'application. */
  async function restore() {
    configureHttp({ refresh: refreshAccess, unauthorized: clearSession })
    if (refreshToken.value && (await refreshAccess())) {
      try {
        user.value = await authApi.me()
      } catch {
        clearSession()
      }
    }
    ready.value = true
  }

  async function logout() {
    const token = refreshToken.value
    clearSession()
    if (token) await authApi.logout(token).catch(() => {})
  }

  async function updateProfile(payload) {
    user.value = await authApi.updateMe(payload)
    return user.value
  }

  async function changePassword(payload) {
    await authApi.changePassword(payload)
    if (user.value) user.value = { ...user.value, must_change_password: false }
  }

  return {
    user,
    access,
    ready,
    isAuthenticated,
    role,
    homeRoute,
    login,
    register,
    logout,
    restore,
    refreshAccess,
    updateProfile,
    changePassword,
    clearSession,
  }
})
