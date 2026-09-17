<script setup>
import { RouterLink } from 'vue-router'

import StatusBadge from '@/components/ui/StatusBadge.vue'
import { formatDate, formatTime } from '@/utils/format'

defineProps({
  appointment: { type: Object, required: true },
  showPatient: { type: Boolean, default: false },
  to: { type: [String, Object], default: null },
})
</script>

<template>
  <article class="card p-5 transition hover:shadow-md">
    <div class="flex flex-wrap items-start justify-between gap-3">
      <div>
        <p class="text-xs font-medium uppercase tracking-wide text-slate-400">
          {{ appointment.reference }}
        </p>
        <h3 class="mt-1 text-base font-semibold text-slate-900">
          {{ showPatient ? appointment.patient_name : appointment.doctor_name }}
        </h3>
        <p class="text-sm text-slate-500">{{ appointment.specialty_name }}</p>
      </div>
      <StatusBadge :status="appointment.status" />
    </div>

    <dl class="mt-4 grid grid-cols-2 gap-3 text-sm sm:grid-cols-4">
      <div>
        <dt class="text-slate-400">Date</dt>
        <dd class="font-medium text-slate-700">{{ formatDate(appointment.scheduled_at) }}</dd>
      </div>
      <div>
        <dt class="text-slate-400">Heure</dt>
        <dd class="font-medium text-slate-700">{{ formatTime(appointment.scheduled_at) }}</dd>
      </div>
      <div>
        <dt class="text-slate-400">Service</dt>
        <dd class="font-medium text-slate-700">{{ appointment.department_name }}</dd>
      </div>
      <div>
        <dt class="text-slate-400">Salle</dt>
        <dd class="font-medium text-slate-700">{{ appointment.room_code ?? 'À préciser' }}</dd>
      </div>
    </dl>

    <div class="mt-4 flex flex-wrap gap-2">
      <RouterLink v-if="to" :to="to" class="btn-secondary">Voir le détail</RouterLink>
      <slot />
    </div>
  </article>
</template>
