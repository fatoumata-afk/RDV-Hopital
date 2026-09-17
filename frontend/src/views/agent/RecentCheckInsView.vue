<script setup>
import { onMounted, ref } from 'vue'

import AppSpinner from '@/components/ui/AppSpinner.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import { checkinApi } from '@/services/api'
import { errorMessage } from '@/services/http'
import { useToastStore } from '@/stores/toast'
import { formatTime } from '@/utils/format'

const toasts = useToastStore()
const checkIns = ref([])
const loading = ref(true)

async function load() {
  loading.value = true
  try {
    checkIns.value = await checkinApi.recent()
  } catch (err) {
    toasts.error(errorMessage(err, 'Chargement impossible.'))
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="space-y-6">
    <header class="flex flex-wrap items-center justify-between gap-4">
      <h1 class="text-2xl font-bold text-slate-900">Arrivées enregistrées</h1>
      <button type="button" class="btn-secondary" @click="load">Actualiser</button>
    </header>

    <AppSpinner v-if="loading" />
    <EmptyState
      v-else-if="!checkIns.length"
      title="Aucune arrivée pour le moment"
      description="Les patients enregistrés apparaîtront ici."
      icon="🚪"
    />

    <div v-else class="card divide-y divide-slate-100">
      <div v-for="entry in checkIns" :key="entry.id" class="flex flex-wrap items-center gap-4 p-4">
        <span class="w-16 font-semibold text-slate-900">{{ formatTime(entry.arrived_at) }}</span>
        <div class="min-w-48 flex-1">
          <p class="font-medium text-slate-800">{{ entry.appointment.patient_name }}</p>
          <p class="text-xs text-slate-500">{{ entry.direction_note }}</p>
        </div>
        <span class="badge bg-slate-100 text-slate-600">
          {{ entry.source === 'SCAN' ? 'Scan' : 'Saisie manuelle' }}
        </span>
      </div>
    </div>
  </div>
</template>
