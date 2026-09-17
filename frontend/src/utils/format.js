const dateFormatter = new Intl.DateTimeFormat('fr-FR', {
  weekday: 'long',
  day: 'numeric',
  month: 'long',
  year: 'numeric',
})
const shortDateFormatter = new Intl.DateTimeFormat('fr-FR', {
  day: '2-digit',
  month: '2-digit',
  year: 'numeric',
})
const timeFormatter = new Intl.DateTimeFormat('fr-FR', { hour: '2-digit', minute: '2-digit' })

export function formatDate(value) {
  return value ? dateFormatter.format(new Date(value)) : '—'
}

export function formatShortDate(value) {
  return value ? shortDateFormatter.format(new Date(value)) : '—'
}

export function formatTime(value) {
  return value ? timeFormatter.format(new Date(value)) : '—'
}

export function formatDateTime(value) {
  return value ? `${dateFormatter.format(new Date(value))} à ${formatTime(value)}` : '—'
}

/** Date au format AAAA-MM-JJ en heure locale (les entrées <input type="date">). */
export function toIsoDate(date) {
  const local = new Date(date)
  local.setMinutes(local.getMinutes() - local.getTimezoneOffset())
  return local.toISOString().slice(0, 10)
}

export function addDays(date, days) {
  const next = new Date(date)
  next.setDate(next.getDate() + days)
  return next
}

/** Délai relatif lisible : « dans 3 jours », « il y a 2 heures ». */
export function relativeTime(value) {
  if (!value) return ''
  const diff = new Date(value).getTime() - Date.now()
  const formatter = new Intl.RelativeTimeFormat('fr-FR', { numeric: 'auto' })
  const units = [
    ['day', 86400000],
    ['hour', 3600000],
    ['minute', 60000],
  ]
  for (const [unit, ms] of units) {
    if (Math.abs(diff) >= ms) return formatter.format(Math.round(diff / ms), unit)
  }
  return formatter.format(Math.round(diff / 1000), 'second')
}

export const STATUS_STYLES = {
  BOOKED: { label: 'Réservé', class: 'bg-sky-100 text-sky-800' },
  CONFIRMED: { label: 'Confirmé', class: 'bg-brand-100 text-brand-800' },
  ARRIVED: { label: 'Arrivé', class: 'bg-emerald-100 text-emerald-800' },
  IN_CONSULTATION: { label: 'En consultation', class: 'bg-indigo-100 text-indigo-800' },
  COMPLETED: { label: 'Terminé', class: 'bg-slate-200 text-slate-700' },
  CANCELLED: { label: 'Annulé', class: 'bg-rose-100 text-rose-800' },
  NO_SHOW: { label: 'Absent', class: 'bg-amber-100 text-amber-900' },
}

export const WEEKDAYS = [
  'Lundi',
  'Mardi',
  'Mercredi',
  'Jeudi',
  'Vendredi',
  'Samedi',
  'Dimanche',
]
