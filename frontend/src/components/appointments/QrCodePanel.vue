<script setup>
import { ref, watch } from 'vue'

import AppSpinner from '@/components/ui/AppSpinner.vue'
import { appointmentsApi } from '@/services/api'
import { errorMessage } from '@/services/http'
import { formatDateTime } from '@/utils/format'

const print = () => window.print()

const props = defineProps({ appointmentId: { type: [String, Number], required: true } })

const qr = ref(null)
const loading = ref(false)
const error = ref('')

async function load() {
  loading.value = true
  error.value = ''
  try {
    qr.value = await appointmentsApi.qrCode(props.appointmentId)
  } catch (err) {
    error.value = errorMessage(err, "Le QR code n'est pas disponible.")
  } finally {
    loading.value = false
  }
}

watch(() => props.appointmentId, load, { immediate: true })
</script>

<template>
  <div class="card p-6 text-center">
    <h2 class="text-lg font-semibold text-slate-900">Mon QR code d'arrivée</h2>
    <p class="mt-1 text-sm text-slate-500">
      Présentez ce code à l'accueil. Il ne contient aucune donnée médicale.
    </p>

    <AppSpinner v-if="loading" label="Génération du QR code…" />
    <p v-else-if="error" class="mt-4 rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">
      {{ error }}
    </p>

    <div v-else-if="qr" class="mt-5 flex flex-col items-center gap-4">
      <img
        :src="qr.image"
        alt="QR code du rendez-vous"
        class="h-56 w-56 rounded-xl border border-slate-200 bg-white p-3"
      />
      <p class="font-mono text-xs tracking-wide text-slate-500">{{ qr.reference }}</p>
      <details class="w-full text-left">
        <summary class="cursor-pointer text-xs text-slate-500 hover:text-slate-700">
          Code de secours (saisie manuelle à l'accueil)
        </summary>
        <p class="mt-2 break-all rounded-lg bg-slate-50 p-3 font-mono text-xs text-slate-600">
          {{ qr.payload }}
        </p>
      </details>
      <p class="text-xs text-slate-400">Valable jusqu'au {{ formatDateTime(qr.expires_at) }}</p>
      <button type="button" class="btn-secondary no-print" @click="print">
        Imprimer
      </button>
    </div>
  </div>
</template>
