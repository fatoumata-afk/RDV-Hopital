<script setup>
import { onMounted, ref, watch } from 'vue'

import AppSpinner from '@/components/ui/AppSpinner.vue'
import DataTable from '@/components/ui/DataTable.vue'
import StatusBadge from '@/components/ui/StatusBadge.vue'
import { appointmentsApi } from '@/services/api'
import { errorMessage } from '@/services/http'
import { useCatalogStore } from '@/stores/catalog'
import { useToastStore } from '@/stores/toast'
import { formatShortDate, formatTime, STATUS_STYLES } from '@/utils/format'

const toasts = useToastStore()
const catalog = useCatalogStore()

const appointments = ref([])
const count = ref(0)
const page = ref(1)
const status = ref('')
const department = ref('')
const loading = ref(true)

const columns = [
  { key: 'reference', label: 'Référence' },
  { key: 'scheduled_at', label: 'Date' },
  { key: 'patient_name', label: 'Patient' },
  { key: 'doctor_name', label: 'Médecin' },
  { key: 'department_name', label: 'Service' },
  { key: 'status', label: 'Statut' },
  { key: 'actions', label: '' },
]

async function load() {
  loading.value = true
  try {
    const data = await appointmentsApi.list({
      page: page.value,
      status: status.value || undefined,
      department: department.value || undefined,
    })
    appointments.value = data.results ?? data
    count.value = data.count ?? appointments.value.length
  } catch (err) {
    toasts.error(errorMessage(err, 'Chargement impossible.'))
  } finally {
    loading.value = false
  }
}

async function cancel(appointment) {
  try {
    const updated = await appointmentsApi.cancel(appointment.id, 'Annulation administrative')
    appointments.value = appointments.value.map((item) =>
      item.id === updated.id ? updated : item,
    )
    toasts.success('Rendez-vous annulé.')
  } catch (err) {
    toasts.error(errorMessage(err, "L'annulation a échoué."))
  }
}

onMounted(async () => {
  await Promise.all([load(), catalog.load().catch(() => {})])
})
watch([status, department, page], load)
</script>

<template>
  <div class="space-y-6">
    <header class="flex flex-wrap items-center justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold text-slate-900">Rendez-vous</h1>
        <p class="text-sm text-slate-500">{{ count }} rendez-vous enregistrés.</p>
      </div>
      <div class="flex flex-wrap gap-3">
        <select v-model="status" class="field-input max-w-48" aria-label="Filtrer par statut">
          <option value="">Tous les statuts</option>
          <option v-for="(style, key) in STATUS_STYLES" :key="key" :value="key">
            {{ style.label }}
          </option>
        </select>
        <select v-model="department" class="field-input max-w-48" aria-label="Filtrer par service">
          <option value="">Tous les services</option>
          <option v-for="item in catalog.departments" :key="item.id" :value="item.id">
            {{ item.name }}
          </option>
        </select>
      </div>
    </header>

    <AppSpinner v-if="loading" />

    <template v-else>
      <DataTable :columns="columns" :rows="appointments">
        <template #cell-scheduled_at="{ row }">
          {{ formatShortDate(row.scheduled_at) }} · {{ formatTime(row.scheduled_at) }}
        </template>
        <template #cell-status="{ row }"><StatusBadge :status="row.status" /></template>
        <template #cell-actions="{ row }">
          <button
            v-if="['BOOKED', 'CONFIRMED'].includes(row.status)"
            type="button"
            class="btn-ghost text-rose-600"
            @click="cancel(row)"
          >
            Annuler
          </button>
        </template>
      </DataTable>

      <div class="flex items-center justify-between">
        <button type="button" class="btn-secondary" :disabled="page === 1" @click="page -= 1">
          Précédent
        </button>
        <span class="text-sm text-slate-500">Page {{ page }}</span>
        <button
          type="button"
          class="btn-secondary"
          :disabled="page * 20 >= count"
          @click="page += 1"
        >
          Suivant
        </button>
      </div>
    </template>
  </div>
</template>
