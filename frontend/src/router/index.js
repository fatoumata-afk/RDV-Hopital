import { createRouter, createWebHistory } from 'vue-router'

import { HOME_BY_ROLE, useAuthStore } from '@/stores/auth'

const routes = [
  { path: '/', name: 'accueil', component: () => import('@/views/public/HomeView.vue') },
  {
    path: '/connexion',
    name: 'connexion',
    component: () => import('@/views/auth/LoginView.vue'),
    meta: { guestOnly: true },
  },
  {
    path: '/inscription',
    name: 'inscription',
    component: () => import('@/views/auth/RegisterView.vue'),
    meta: { guestOnly: true },
  },

  {
    path: '/patient',
    component: () => import('@/layouts/PatientLayout.vue'),
    meta: { roles: ['PATIENT'] },
    children: [
      { path: '', name: 'patient-dashboard', component: () => import('@/views/patient/PatientDashboard.vue') },
      { path: 'reserver', name: 'patient-booking', component: () => import('@/views/patient/BookingView.vue') },
      { path: 'rendez-vous', name: 'patient-appointments', component: () => import('@/views/patient/AppointmentsView.vue') },
      { path: 'rendez-vous/:id', name: 'patient-appointment', component: () => import('@/views/patient/AppointmentDetailView.vue'), props: true },
      { path: 'profil', name: 'patient-profile', component: () => import('@/views/shared/ProfileView.vue') },
    ],
  },

  {
    path: '/medecin',
    component: () => import('@/layouts/DoctorLayout.vue'),
    meta: { roles: ['DOCTOR'] },
    children: [
      { path: '', name: 'doctor-dashboard', component: () => import('@/views/doctor/DoctorDashboard.vue') },
      { path: 'agenda', name: 'doctor-agenda', component: () => import('@/views/doctor/AgendaView.vue') },
      { path: 'disponibilites', name: 'doctor-availability', component: () => import('@/views/doctor/AvailabilityView.vue') },
      { path: 'profil', name: 'doctor-profile', component: () => import('@/views/shared/ProfileView.vue') },
    ],
  },

  {
    path: '/accueil',
    component: () => import('@/layouts/AgentLayout.vue'),
    meta: { roles: ['AGENT'] },
    children: [
      { path: '', name: 'agent-scan', component: () => import('@/views/agent/ScanView.vue') },
      { path: 'arrivees', name: 'agent-recent', component: () => import('@/views/agent/RecentCheckInsView.vue') },
      { path: 'profil', name: 'agent-profile', component: () => import('@/views/shared/ProfileView.vue') },
    ],
  },

  {
    path: '/admin',
    component: () => import('@/layouts/AdminLayout.vue'),
    meta: { roles: ['ADMIN'] },
    children: [
      { path: '', name: 'admin-stats', component: () => import('@/views/admin/StatsView.vue') },
      { path: 'utilisateurs', name: 'admin-users', component: () => import('@/views/admin/UsersView.vue') },
      { path: 'organisation', name: 'admin-organization', component: () => import('@/views/admin/OrganizationView.vue') },
      { path: 'rendez-vous', name: 'admin-appointments', component: () => import('@/views/admin/AdminAppointmentsView.vue') },
      { path: 'profil', name: 'admin-profile', component: () => import('@/views/shared/ProfileView.vue') },
    ],
  },

  { path: '/:pathMatch(.*)*', name: 'introuvable', component: () => import('@/views/public/NotFoundView.vue') },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior: () => ({ top: 0 }),
})

/**
 * Garde de navigation : confort d'interface uniquement.
 * L'autorisation réelle est appliquée par l'API sur chaque requête.
 */
router.beforeEach((to) => {
  const auth = useAuthStore()
  const roles = to.matched.flatMap((record) => record.meta.roles ?? [])

  if (roles.length && !auth.isAuthenticated) {
    return { name: 'connexion', query: { redirect: to.fullPath } }
  }
  if (roles.length && !roles.includes(auth.role)) {
    return HOME_BY_ROLE[auth.role] ?? { name: 'connexion' }
  }
  if (to.meta.guestOnly && auth.isAuthenticated) {
    return auth.homeRoute
  }
  return true
})

export default router
