<script setup>
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'

import AppointmentCard from '@/components/appointments/AppointmentCard.vue'
import AppSpinner from '@/components/ui/AppSpinner.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import { appointmentsApi } from '@/services/api'
import { errorMessage } from '@/services/http'
import { useToastStore } from '@/stores/toast'

const toasts = useToastStore()
const tab = ref('upcoming')
const upcoming = ref([])
const history = ref([])
const loading = ref(true)

onMounted(async () => {
  try {
    ;[upcoming.value, history.value] = await Promise.all([
      appointmentsApi.upcoming(),
      appointmentsApi.history(),
    ])
  } catch (err) {
    toasts.error(errorMessage(err, 'Impossible de charger vos rendez-vous.'))
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="space-y-6">
    <header class="flex flex-wrap items-center justify-between gap-4">
      <h1 class="text-2xl font-bold text-slate-900">Mes rendez-vous</h1>
      <RouterLink to="/patient/reserver" class="btn-primary">Nouveau rendez-vous</RouterLink>
    </header>

    <div class="inline-flex rounded-xl bg-slate-100 p-1">
      <button
        type="button"
        class="rounded-lg px-4 py-2 text-sm font-semibold transition"
        :class="tab === 'upcoming' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-600'"
        @click="tab = 'upcoming'"
      >
        À venir ({{ upcoming.length }})
      </button>
      <button
        type="button"
        class="rounded-lg px-4 py-2 text-sm font-semibold transition"
        :class="tab === 'history' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-600'"
        @click="tab = 'history'"
      >
        Historique ({{ history.length }})
      </button>
    </div>

    <AppSpinner v-if="loading" />

    <template v-else>
      <div v-if="tab === 'upcoming'" class="grid gap-4 lg:grid-cols-2">
        <AppointmentCard
          v-for="appointment in upcoming"
          :key="appointment.id"
          :appointment="appointment"
          :to="`/patient/rendez-vous/${appointment.id}`"
        />
        <EmptyState
          v-if="!upcoming.length"
          class="lg:col-span-2"
          title="Aucun rendez-vous à venir"
          description="Réservez un créneau auprès du médecin de votre choix."
        />
      </div>

      <div v-else class="grid gap-4 lg:grid-cols-2">
        <AppointmentCard
          v-for="appointment in history"
          :key="appointment.id"
          :appointment="appointment"
          :to="`/patient/rendez-vous/${appointment.id}`"
        />
        <EmptyState
          v-if="!history.length"
          class="lg:col-span-2"
          title="Historique vide"
          description="Vos rendez-vous passés apparaîtront ici."
          icon="🗂️"
        />
      </div>
    </template>
  </div>
</template>
