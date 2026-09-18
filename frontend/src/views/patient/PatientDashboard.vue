<script setup>
import { computed, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'

import AppointmentCard from '@/components/appointments/AppointmentCard.vue'
import AppSpinner from '@/components/ui/AppSpinner.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import StatusBadge from '@/components/ui/StatusBadge.vue'
import { appointmentsApi } from '@/services/api'
import { errorMessage } from '@/services/http'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'
import { formatDate, formatTime, relativeTime } from '@/utils/format'

const auth = useAuthStore()
const toasts = useToastStore()

const upcoming = ref([])
const loading = ref(true)

const next = computed(() => upcoming.value[0] ?? null)
const others = computed(() => upcoming.value.slice(1))

onMounted(async () => {
  try {
    upcoming.value = await appointmentsApi.upcoming()
  } catch (err) {
    toasts.error(errorMessage(err, 'Impossible de charger vos rendez-vous.'))
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="space-y-8">
    <header class="flex flex-wrap items-center justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold text-slate-900">Bonjour {{ auth.user?.first_name }}</h1>
        <p class="text-sm text-slate-500">Voici l'état de vos rendez-vous.</p>
      </div>
      <RouterLink to="/patient/reserver" class="btn-primary">Prendre un rendez-vous</RouterLink>
    </header>

    <AppSpinner v-if="loading" />

    <section v-else-if="next" class="overflow-hidden rounded-2xl bg-brand-700 text-white shadow-lg">
      <div class="grid gap-6 p-6 sm:p-8 lg:grid-cols-[1.4fr_1fr] lg:items-center">
        <div>
          <p class="text-xs font-semibold uppercase tracking-[0.2em] text-brand-100">
            Prochain rendez-vous · {{ relativeTime(next.scheduled_at) }}
          </p>
          <h2 class="mt-3 text-3xl font-bold">{{ next.doctor_name }}</h2>
          <p class="text-brand-100">{{ next.specialty_name }}</p>

          <dl class="mt-6 grid grid-cols-2 gap-4 text-sm sm:grid-cols-4">
            <div>
              <dt class="text-brand-200">Date</dt>
              <dd class="font-semibold">{{ formatDate(next.scheduled_at) }}</dd>
            </div>
            <div>
              <dt class="text-brand-200">Heure</dt>
              <dd class="font-semibold">{{ formatTime(next.scheduled_at) }}</dd>
            </div>
            <div>
              <dt class="text-brand-200">Service</dt>
              <dd class="font-semibold">{{ next.department_name }}</dd>
            </div>
            <div>
              <dt class="text-brand-200">Salle</dt>
              <dd class="font-semibold">{{ next.room_code ?? 'À préciser' }}</dd>
            </div>
          </dl>
        </div>

        <div class="flex flex-col gap-3">
          <StatusBadge :status="next.status" class="self-start bg-white/15 text-white" />
          <RouterLink
            :to="`/patient/rendez-vous/${next.id}`"
            class="btn bg-white text-brand-800 hover:bg-brand-50"
          >
            Voir mon rendez-vous
          </RouterLink>
          <RouterLink
            :to="`/patient/rendez-vous/${next.id}?qr=1`"
            class="btn border border-white/40 text-white hover:bg-white/10"
          >
            Afficher mon QR code
          </RouterLink>
        </div>
      </div>
    </section>

    <EmptyState
      v-else
      title="Aucun rendez-vous à venir"
      description="Choisissez une spécialité et réservez un créneau en quelques clics."
    >
      <RouterLink to="/patient/reserver" class="btn-primary">Prendre un rendez-vous</RouterLink>
    </EmptyState>

    <section v-if="others.length" class="space-y-4">
      <h2 class="text-lg font-semibold text-slate-900">Autres rendez-vous à venir</h2>
      <div class="grid gap-4 lg:grid-cols-2">
        <AppointmentCard
          v-for="appointment in others"
          :key="appointment.id"
          :appointment="appointment"
          :to="`/patient/rendez-vous/${appointment.id}`"
        />
      </div>
    </section>
  </div>
</template>
