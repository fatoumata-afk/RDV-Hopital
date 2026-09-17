import axios from 'axios'

const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? '/api/v1',
  headers: { 'Content-Type': 'application/json' },
})

let accessToken = null
let onUnauthorized = null
let refreshHandler = null
let refreshing = null

export function setAccessToken(token) {
  accessToken = token
}

export function configureHttp({ refresh, unauthorized }) {
  refreshHandler = refresh
  onUnauthorized = unauthorized
}

http.interceptors.request.use((config) => {
  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`
  }
  return config
})

http.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config
    const status = error.response?.status

    // Une seule tentative de rafraîchissement, partagée entre les requêtes concurrentes.
    if (status === 401 && original && !original._retried && refreshHandler) {
      original._retried = true
      refreshing = refreshing ?? refreshHandler()
      const token = await refreshing.finally(() => {
        refreshing = null
      })
      if (token) {
        original.headers.Authorization = `Bearer ${token}`
        return http(original)
      }
      onUnauthorized?.()
    }
    return Promise.reject(error)
  },
)

/** Message lisible extrait d'une erreur DRF, quel que soit son format. */
export function errorMessage(error, fallback = 'Une erreur est survenue.') {
  const data = error?.response?.data
  if (!data) return error?.message ?? fallback
  if (typeof data === 'string') return data
  if (data.detail) return data.detail
  const first = Object.values(data).flat()[0]
  return typeof first === 'string' ? first : fallback
}

/** Erreurs de validation par champ, pour un affichage sous les inputs. */
export function fieldErrors(error) {
  const data = error?.response?.data
  if (!data || typeof data !== 'object') return {}
  return Object.fromEntries(
    Object.entries(data)
      .filter(([key]) => key !== 'detail' && key !== 'code')
      .map(([key, value]) => [key, Array.isArray(value) ? value.join(' ') : String(value)]),
  )
}

export default http
