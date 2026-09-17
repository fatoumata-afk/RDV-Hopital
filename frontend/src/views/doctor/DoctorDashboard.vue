<script setup>
import { computed, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'

import AppSpinner from '@/components/ui/AppSpinner.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import StatCard from '@/components/ui/StatCard.vue'
import StatusBadge from '@/components/ui/StatusBadge.vue'
import { appointmentsApi } from '@/services/api'
import { errorMessage } from '@/services/http'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'
import { formatDate, formatTime } from '@/utils/format'

const auth = useAuthStore()
const toasts = useToastStore()

const today = ref([])
const upcoming = ref([])
const loading = ref(true)
const updating = ref(null)

const arrivedCount = computed(() => today.value.filter((a) => a.status === 'ARRIVED').length)
const completedCount = computed(() => today.value.filter((a) => a.status === 'COMPLETED').length)

async function load() {
  loading.value = true
  try {
    ;[today.value, upcoming.value] = await Promise.all([
      appointmentsApi.today(),
      appointmentsApi.upcoming(),
    ])
  } catch (err) {
    toasts.error(errorMessage(err, 'Impossible de charger votre journée.'))
  } finally {
    loading.value = false
  }
}

async function setStatus(appointment, status) {
  updating.value = appointment.id
  try {
    const updated = await appointmentsApi.setStatus(appointment.id, status)
    today.value = today.value.map((item) => (item.id === updated.id ? updated : item))
    toasts.success('Statut mis à jour.')
  } catch (err) {
    toasts.error(errorMessage(err, 'Transition de statut refusée.'))
  } finally {
    updating.value = null
  }
}

onMounted(load)
</script>

<template>
  <div class="space-y-6">
    <header class="flex flex-wrap items-center justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold text-slate-900">Dr {{ auth.user?.last_name }}</h1>
        <p class="text-sm capitalize text-slate-500">{{ formatDate(new Date()) }}</p>
      </div>
      <RouterLink to="/medecin/agenda" class="btn-secondary">Voir l'agenda complet</RouterLink>
    </header>

    <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <StatCard label="Rendez-vous aujourd'hui" :value="today.length" icon="📋" />
      <StatCard label="Patients arrivés" :value="arrivedCount" icon="✅" tone="sky" />
      <StatCard label="Consultations terminées" :value="completedCount" icon="🏁" tone="amber" />
      <StatCard label="Prochains rendez-vous" :value="upcoming.length" icon="📅" />
    </div>

    <AppSpinner v-if="loading" />

    <section v-else class="space-y-3">
      <h2 class="text-lg font-semibold text-slate-900">Patients du jour</h2>
      <EmptyState
        v-if="!today.length"
        title="Aucun rendez-vous aujourd'hui"
        description="Vos prochains rendez-vous apparaîtront dans votre agenda."
      />
      <article
        v-for="appointment in today"
        :key="appointment.id"
        class="card flex flex-wrap items-center gap-4 p-4"
      >
        <span class="w-16 text-lg font-bold text-slate-900">
          {{ formatTime(appointment.scheduled_at) }}
        </span>
        <div class="min-w-48 flex-1">
          <p class="font-semibold text-slate-900">{{ appointment.patient_name }}</p>
          <p class="text-xs text-slate-500">
            Dossier {{ appointment.patient_record_number }} ·
            {{ appointment.patient_phone || 'téléphone non renseigné' }}
          </p>
          <p v-if="appointment.reason" class="mt-1 text-sm text-slate-600">
            {{ appointment.reason }}
          </p>
        </div>
        <StatusBadge :status="appointment.status" />
        <div class="flex flex-wrap gap-2">
          <button
            v-if="appointment.status === 'ARRIVED'"
            type="button"
            class="btn-secondary"
            :disabled="updating === appointment.id"
            @click="setStatus(appointment, 'IN_CONSULTATION')"
          >
            Démarrer la consultation
          </button>
          <button
            v-if="appointment.status === 'IN_CONSULTATION'"
            type="button"
            class="btn-primary"
            :disabled="updating === appointment.id"
            @click="setStatus(appointment, 'COMPLETED')"
          >
            Terminer
          </button>
          <button
            v-if="['BOOKED', 'CONFIRMED'].includes(appointment.status)"
            type="button"
            class="btn-ghost"
            :disabled="updating === appointment.id"
            @click="setStatus(appointment, 'NO_SHOW')"
          >
            Absent
          </button>
        </div>
      </article>
    </section>
  </div>
</template>
