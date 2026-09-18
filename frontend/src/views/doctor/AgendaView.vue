<script setup>
import { computed, onMounted, ref } from 'vue'

import AppSpinner from '@/components/ui/AppSpinner.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import StatusBadge from '@/components/ui/StatusBadge.vue'
import { appointmentsApi } from '@/services/api'
import { errorMessage } from '@/services/http'
import { useToastStore } from '@/stores/toast'
import { formatDate, formatTime } from '@/utils/format'

const toasts = useToastStore()
const appointments = ref([])
const loading = ref(true)
const search = ref('')

/** Regroupement par jour pour un affichage type agenda. */
const grouped = computed(() => {
  const term = search.value.trim().toLowerCase()
  const filtered = appointments.value.filter(
    (item) => !term || item.patient_name.toLowerCase().includes(term),
  )
  const map = new Map()
  for (const appointment of filtered) {
    const day = appointment.scheduled_at.slice(0, 10)
    if (!map.has(day)) map.set(day, [])
    map.get(day).push(appointment)
  }
  return [...map.entries()].sort(([a], [b]) => a.localeCompare(b))
})

onMounted(async () => {
  try {
    appointments.value = await appointmentsApi.upcoming()
  } catch (err) {
    toasts.error(errorMessage(err, "Impossible de charger l'agenda."))
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="space-y-6">
    <header class="flex flex-wrap items-center justify-between gap-4">
      <h1 class="text-2xl font-bold text-slate-900">Mon agenda</h1>
      <input
        v-model="search"
        type="search"
        class="field-input max-w-xs"
        placeholder="Rechercher un patient…"
        aria-label="Rechercher un patient"
      />
    </header>

    <AppSpinner v-if="loading" />

    <EmptyState
      v-else-if="!grouped.length"
      title="Aucun rendez-vous à venir"
      description="Vérifiez vos disponibilités pour ouvrir de nouveaux créneaux."
    />

    <section v-for="[day, items] in grouped" :key="day" class="space-y-3">
      <h2 class="text-sm font-semibold uppercase tracking-wide capitalize text-slate-500">
        {{ formatDate(day) }}
      </h2>
      <div class="card divide-y divide-slate-100">
        <div v-for="item in items" :key="item.id" class="flex flex-wrap items-center gap-4 p-4">
          <span class="w-16 font-semibold text-slate-900">
            {{ formatTime(item.scheduled_at) }}
          </span>
          <div class="min-w-40 flex-1">
            <p class="font-medium text-slate-800">{{ item.patient_name }}</p>
            <p class="text-xs text-slate-500">{{ item.reason || 'Motif non précisé' }}</p>
          </div>
          <span class="text-sm text-slate-500">Salle {{ item.room_code ?? '—' }}</span>
          <StatusBadge :status="item.status" />
        </div>
      </div>
    </section>
  </div>
</template>
