<script setup>
import { onMounted, reactive, ref } from 'vue'

import AppSpinner from '@/components/ui/AppSpinner.vue'
import FormField from '@/components/ui/FormField.vue'
import { schedulingApi } from '@/services/api'
import { errorMessage, fieldErrors } from '@/services/http'
import { useToastStore } from '@/stores/toast'
import { formatDateTime, WEEKDAYS } from '@/utils/format'

const toasts = useToastStore()

const schedules = ref([])
const timeOff = ref([])
const loading = ref(true)
const errors = ref({})

const scheduleForm = reactive({
  weekday: 0,
  start_time: '08:00',
  end_time: '12:00',
  slot_duration: 30,
})
const timeOffForm = reactive({ start_datetime: '', end_datetime: '', reason: '' })

async function load() {
  loading.value = true
  try {
    ;[schedules.value, timeOff.value] = await Promise.all([
      schedulingApi.schedules(),
      schedulingApi.timeOff(),
    ])
  } catch (err) {
    toasts.error(errorMessage(err, 'Chargement impossible.'))
  } finally {
    loading.value = false
  }
}

async function addSchedule() {
  errors.value = {}
  try {
    schedules.value = [...schedules.value, await schedulingApi.createSchedule({ ...scheduleForm })]
    toasts.success('Horaire ajouté : les créneaux sont générés automatiquement.')
  } catch (err) {
    errors.value = fieldErrors(err)
    toasts.error(errorMessage(err, "L'horaire n'a pas pu être ajouté."))
  }
}

async function toggleSchedule(schedule) {
  try {
    const updated = await schedulingApi.updateSchedule(schedule.id, {
      is_active: !schedule.is_active,
    })
    schedules.value = schedules.value.map((item) => (item.id === updated.id ? updated : item))
  } catch (err) {
    toasts.error(errorMessage(err))
  }
}

async function removeSchedule(schedule) {
  try {
    await schedulingApi.deleteSchedule(schedule.id)
    schedules.value = schedules.value.filter((item) => item.id !== schedule.id)
    toasts.success('Horaire supprimé.')
  } catch (err) {
    toasts.error(errorMessage(err))
  }
}

async function addTimeOff() {
  try {
    timeOff.value = [...timeOff.value, await schedulingApi.createTimeOff({ ...timeOffForm })]
    toasts.success('Indisponibilité enregistrée : les créneaux concernés sont bloqués.')
  } catch (err) {
    toasts.error(errorMessage(err, "L'indisponibilité n'a pas pu être enregistrée."))
  }
}

async function removeTimeOff(entry) {
  try {
    await schedulingApi.deleteTimeOff(entry.id)
    timeOff.value = timeOff.value.filter((item) => item.id !== entry.id)
    toasts.success('Indisponibilité levée.')
  } catch (err) {
    toasts.error(errorMessage(err))
  }
}

onMounted(load)
</script>

<template>
  <div class="space-y-6">
    <header>
      <h1 class="text-2xl font-bold text-slate-900">Mes disponibilités</h1>
      <p class="text-sm text-slate-500">
        Les créneaux proposés aux patients sont générés à partir de ces horaires.
      </p>
    </header>

    <AppSpinner v-if="loading" />

    <template v-else>
      <section class="card p-6">
        <h2 class="text-lg font-semibold text-slate-900">Horaires récurrents</h2>
        <ul class="mt-4 divide-y divide-slate-100">
          <li
            v-for="schedule in schedules"
            :key="schedule.id"
            class="flex flex-wrap items-center gap-3 py-3"
          >
            <span class="w-28 font-medium text-slate-800">{{ WEEKDAYS[schedule.weekday] }}</span>
            <span class="text-slate-600">
              {{ schedule.start_time.slice(0, 5) }} – {{ schedule.end_time.slice(0, 5) }}
            </span>
            <span class="text-xs text-slate-400">{{ schedule.slot_duration }} min</span>
            <span
              class="badge"
              :class="schedule.is_active ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-200 text-slate-600'"
            >
              {{ schedule.is_active ? 'Actif' : 'Suspendu' }}
            </span>
            <div class="ml-auto flex gap-2">
              <button type="button" class="btn-ghost" @click="toggleSchedule(schedule)">
                {{ schedule.is_active ? 'Suspendre' : 'Réactiver' }}
              </button>
              <button type="button" class="btn-ghost text-rose-600" @click="removeSchedule(schedule)">
                Supprimer
              </button>
            </div>
          </li>
          <li v-if="!schedules.length" class="py-4 text-sm text-slate-500">
            Aucun horaire défini : ajoutez-en un pour ouvrir des créneaux.
          </li>
        </ul>

        <form class="mt-5 grid gap-4 border-t border-slate-100 pt-5 sm:grid-cols-4" @submit.prevent="addSchedule">
          <FormField id="weekday" label="Jour" :error="errors.weekday">
            <select id="weekday" v-model.number="scheduleForm.weekday" class="field-input">
              <option v-for="(label, index) in WEEKDAYS" :key="label" :value="index">
                {{ label }}
              </option>
            </select>
          </FormField>
          <FormField id="start_time" label="Début" :error="errors.start_time">
            <input id="start_time" v-model="scheduleForm.start_time" type="time" required class="field-input" />
          </FormField>
          <FormField id="end_time" label="Fin" :error="errors.end_time">
            <input id="end_time" v-model="scheduleForm.end_time" type="time" required class="field-input" />
          </FormField>
          <FormField id="slot_duration" label="Durée (min)" :error="errors.slot_duration">
            <input
              id="slot_duration"
              v-model.number="scheduleForm.slot_duration"
              type="number"
              min="5"
              max="180"
              class="field-input"
            />
          </FormField>
          <div class="sm:col-span-4">
            <button type="submit" class="btn-primary">Ajouter cet horaire</button>
          </div>
        </form>
      </section>

      <section class="card p-6">
        <h2 class="text-lg font-semibold text-slate-900">Indisponibilités</h2>
        <p class="text-sm text-slate-500">
          Les créneaux libres compris dans la période sont bloqués immédiatement.
        </p>
        <ul class="mt-4 divide-y divide-slate-100">
          <li v-for="entry in timeOff" :key="entry.id" class="flex flex-wrap items-center gap-3 py-3">
            <span class="text-sm text-slate-700">
              {{ formatDateTime(entry.start_datetime) }} → {{ formatDateTime(entry.end_datetime) }}
            </span>
            <span class="text-xs text-slate-500">{{ entry.reason }}</span>
            <button type="button" class="btn-ghost ml-auto text-rose-600" @click="removeTimeOff(entry)">
              Lever
            </button>
          </li>
          <li v-if="!timeOff.length" class="py-4 text-sm text-slate-500">
            Aucune indisponibilité enregistrée.
          </li>
        </ul>

        <form class="mt-5 grid gap-4 border-t border-slate-100 pt-5 sm:grid-cols-3" @submit.prevent="addTimeOff">
          <FormField id="start_datetime" label="Début">
            <input
              id="start_datetime"
              v-model="timeOffForm.start_datetime"
              type="datetime-local"
              required
              class="field-input"
            />
          </FormField>
          <FormField id="end_datetime" label="Fin">
            <input
              id="end_datetime"
              v-model="timeOffForm.end_datetime"
              type="datetime-local"
              required
              class="field-input"
            />
          </FormField>
          <FormField id="reason" label="Motif">
            <input id="reason" v-model="timeOffForm.reason" class="field-input" placeholder="Congé, formation…" />
          </FormField>
          <div class="sm:col-span-3">
            <button type="submit" class="btn-secondary">Bloquer cette période</button>
          </div>
        </form>
      </section>
    </template>
  </div>
</template>
