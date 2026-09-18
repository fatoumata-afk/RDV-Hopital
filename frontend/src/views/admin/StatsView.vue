<script setup>
import { computed, onMounted, ref } from 'vue'

import AppSpinner from '@/components/ui/AppSpinner.vue'
import StatCard from '@/components/ui/StatCard.vue'
import { appointmentsApi } from '@/services/api'
import { errorMessage } from '@/services/http'
import { useToastStore } from '@/stores/toast'
import { STATUS_STYLES } from '@/utils/format'

const toasts = useToastStore()
const stats = ref(null)
const loading = ref(true)

const statusRows = computed(() =>
  Object.entries(stats.value?.by_status ?? {}).map(([status, count]) => ({
    status,
    label: STATUS_STYLES[status]?.label ?? status,
    class: STATUS_STYLES[status]?.class ?? 'bg-slate-100 text-slate-700',
    count,
  })),
)

const maxDepartment = computed(() =>
  Math.max(1, ...(stats.value?.by_department ?? []).map((row) => row.count)),
)

onMounted(async () => {
  try {
    stats.value = await appointmentsApi.stats()
  } catch (err) {
    toasts.error(errorMessage(err, 'Statistiques indisponibles.'))
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="space-y-6">
    <header>
      <h1 class="text-2xl font-bold text-slate-900">Statistiques générales</h1>
      <p class="text-sm text-slate-500">Vue d'ensemble de l'activité hospitalière.</p>
    </header>

    <AppSpinner v-if="loading" />

    <template v-else-if="stats">
      <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Patients inscrits" :value="stats.patients" icon="🧑" />
        <StatCard label="Médecins actifs" :value="stats.doctors" icon="👩‍⚕️" tone="sky" />
        <StatCard label="Rendez-vous aujourd'hui" :value="stats.appointments_today" icon="📅" tone="amber" />
        <StatCard label="Arrivées du jour" :value="stats.arrived_today" icon="✅" />
      </div>

      <div class="grid gap-6 lg:grid-cols-2">
        <section class="card p-6">
          <h2 class="text-lg font-semibold text-slate-900">Rendez-vous par statut</h2>
          <p class="text-sm text-slate-500">{{ stats.appointments_total }} au total</p>
          <ul class="mt-4 space-y-2">
            <li v-for="row in statusRows" :key="row.status" class="flex items-center gap-3">
              <span class="badge" :class="row.class">{{ row.label }}</span>
              <span class="ml-auto font-semibold text-slate-800">{{ row.count }}</span>
            </li>
            <li v-if="!statusRows.length" class="text-sm text-slate-500">Aucun rendez-vous.</li>
          </ul>
        </section>

        <section class="card p-6">
          <h2 class="text-lg font-semibold text-slate-900">Activité par service</h2>
          <ul class="mt-4 space-y-3">
            <li v-for="row in stats.by_department" :key="row.department__name">
              <div class="flex justify-between text-sm">
                <span class="text-slate-700">{{ row.department__name }}</span>
                <span class="font-semibold text-slate-800">{{ row.count }}</span>
              </div>
              <div class="mt-1 h-2 rounded-full bg-slate-100">
                <div
                  class="h-2 rounded-full bg-brand-600"
                  :style="{ width: `${(row.count / maxDepartment) * 100}%` }"
                />
              </div>
            </li>
            <li v-if="!stats.by_department?.length" class="text-sm text-slate-500">
              Aucune donnée pour le moment.
            </li>
          </ul>
        </section>
      </div>
    </template>
  </div>
</template>
