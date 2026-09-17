import http from './http'

const unwrap = (response) => response.data
/** Les endpoints paginés renvoient {count, results} ; les autres une liste brute. */
const asList = (response) => response.data?.results ?? response.data

export const authApi = {
  register: (payload) => http.post('/auth/register/', payload).then(unwrap),
  login: (credentials) => http.post('/auth/login/', credentials).then(unwrap),
  refresh: (refresh) => http.post('/auth/refresh/', { refresh }).then(unwrap),
  logout: (refresh) => http.post('/auth/logout/', { refresh }).then(unwrap),
  me: () => http.get('/auth/me/').then(unwrap),
  updateMe: (payload) => http.patch('/auth/me/', payload).then(unwrap),
  changePassword: (payload) => http.post('/auth/change-password/', payload).then(unwrap),
}

export const catalogApi = {
  specialties: (params) => http.get('/specialties/', { params }).then(asList),
  departments: (params) => http.get('/departments/', { params }).then(asList),
  rooms: (params) => http.get('/rooms/', { params }).then(asList),
  doctors: (params) => http.get('/doctors/', { params }).then(asList),
  doctor: (id) => http.get(`/doctors/${id}/`).then(unwrap),
}

export const schedulingApi = {
  availability: (doctorId, params) =>
    http.get(`/doctors/${doctorId}/availability/`, { params }).then(unwrap),
  slots: (doctorId, params) => http.get(`/doctors/${doctorId}/slots/`, { params }).then(unwrap),
  schedules: (params) => http.get('/schedules/', { params }).then(asList),
  createSchedule: (payload) => http.post('/schedules/', payload).then(unwrap),
  updateSchedule: (id, payload) => http.patch(`/schedules/${id}/`, payload).then(unwrap),
  deleteSchedule: (id) => http.delete(`/schedules/${id}/`),
  timeOff: (params) => http.get('/time-off/', { params }).then(asList),
  createTimeOff: (payload) => http.post('/time-off/', payload).then(unwrap),
  deleteTimeOff: (id) => http.delete(`/time-off/${id}/`),
}

export const appointmentsApi = {
  list: (params) => http.get('/appointments/', { params }).then(unwrap),
  retrieve: (id) => http.get(`/appointments/${id}/`).then(unwrap),
  book: (payload) => http.post('/appointments/', payload).then(unwrap),
  upcoming: () => http.get('/appointments/upcoming/').then(asList),
  history: () => http.get('/appointments/history/').then(asList),
  today: () => http.get('/appointments/today/').then(asList),
  cancel: (id, reason) => http.post(`/appointments/${id}/cancel/`, { reason }).then(unwrap),
  setStatus: (id, status, note = '') =>
    http.post(`/appointments/${id}/status/`, { status, note }).then(unwrap),
  qrCode: (id) => http.get(`/appointments/${id}/qrcode/`).then(unwrap),
  stats: () => http.get('/admin/stats/').then(unwrap),
}

export const checkinApi = {
  verify: (token) => http.post('/checkin/verify/', { token }).then(unwrap),
  confirm: (token, source) => http.post('/checkin/confirm/', { token, source }).then(unwrap),
  recent: () => http.get('/checkin/recent/').then(asList),
}

export const notificationsApi = {
  list: (params) => http.get('/notifications/', { params }).then(asList),
  markRead: (id) => http.post(`/notifications/${id}/read/`).then(unwrap),
  markAllRead: () => http.post('/notifications/read-all/').then(unwrap),
}

export const adminApi = {
  users: (params) => http.get('/admin/users/', { params }).then(unwrap),
  createStaff: (payload) => http.post('/admin/users/', payload).then(unwrap),
  updateUser: (id, payload) => http.patch(`/admin/users/${id}/`, payload).then(unwrap),
  deleteUser: (id) => http.delete(`/admin/users/${id}/`),
  patients: (params) => http.get('/admin/patients/', { params }).then(unwrap),
  doctors: (params) => http.get('/admin/doctors/', { params }).then(unwrap),
  updateDoctor: (id, payload) => http.patch(`/admin/doctors/${id}/`, payload).then(unwrap),
  createSpecialty: (payload) => http.post('/specialties/', payload).then(unwrap),
  updateSpecialty: (id, payload) => http.patch(`/specialties/${id}/`, payload).then(unwrap),
  deleteSpecialty: (id) => http.delete(`/specialties/${id}/`),
  createDepartment: (payload) => http.post('/departments/', payload).then(unwrap),
  updateDepartment: (id, payload) => http.patch(`/departments/${id}/`, payload).then(unwrap),
  deleteDepartment: (id) => http.delete(`/departments/${id}/`),
  createRoom: (payload) => http.post('/rooms/', payload).then(unwrap),
  updateRoom: (id, payload) => http.patch(`/rooms/${id}/`, payload).then(unwrap),
  deleteRoom: (id) => http.delete(`/rooms/${id}/`),
}
