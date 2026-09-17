<script setup>
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'

import QrCodePanel from '@/components/appointments/QrCodePanel.vue'
import AppModal from '@/components/ui/AppModal.vue'
import AppSpinner from '@/components/ui/AppSpinner.vue'
import StatusBadge from '@/components/ui/StatusBadge.vue'
import { appointmentsApi } from '@/services/api'
import { errorMessage } from '@/services/http'
import { useToastStore } from '@/stores/toast'
import { formatDate, formatDateTime, formatTime } from '@/utils/format'

const props = defineProps({ id: { type: String, required: true } })
const route = useRoute()
const toasts = useToastStore()

const appointment = ref(null)
const loading = ref(true)
const showQr = ref(route.query.qr === '1')
const cancelOpen = ref(false)
const cancelReason = ref('')
const cancelling = ref(false)

async function load() {
  loading.value = true
  try {
    appointment.value = await appointmentsApi.retrieve(props.id)
  } catch (err) {
    toasts.error(errorMessage(err, 'Rendez-vous introuvable.'))
  } finally {
    loading.value = false
  }
}

async function cancel() {
  cancelling.value = true
  try {
    appointment.value = await appointmentsApi.cancel(props.id, cancelReason.value)
    cancelOpen.value = false
    toasts.success('Rendez-vous annulé.')
  } catch (err) {
    toasts.error(errorMessage(err, "L'annulation a échoué."))
  } finally {
    cancelling.value = false
  }
}

onMounted(load)
</script>

<template>
  <AppSpinner v-if="loading" />

  <div v-else-if="appointment" class="grid gap-6 lg:grid-cols-[1.4fr_1fr]">
    <section class="space-y-6">
      <div class="card p-6">
        <div class="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p class="text-xs font-medium uppercase tracking-wide text-slate-400">
              {{ appointment.reference }}
            </p>
            <h1 class="mt-1 text-2xl font-bold text-slate-900">{{ appointment.doctor_name }}</h1>
            <p class="text-slate-500">{{ appointment.specialty_name }}</p>
          </div>
          <StatusBadge :status="appointment.status" />
        </div>

        <dl class="mt-6 grid gap-4 sm:grid-cols-2">
          <div>
            <dt class="text-sm text-slate-400">Date</dt>
            <dd class="font-medium capitalize text-slate-800">
              {{ formatDate(appointment.scheduled_at) }}
            </dd>
          </div>
          <div>
            <dt class="text-sm text-slate-400">Heure</dt>
            <dd class="font-medium text-slate-800">{{ formatTime(appointment.scheduled_at) }}</dd>
          </div>
          <div>
            <dt class="text-sm text-slate-400">Service</dt>
            <dd class="font-medium text-slate-800">{{ appointment.department_name }}</dd>
          </div>
          <div>
            <dt class="text-sm text-slate-400">Salle</dt>
            <dd class="font-medium text-slate-800">{{ appointment.room_code ?? 'À préciser' }}</dd>
          </div>
          <div class="sm:col-span-2">
            <dt class="text-sm text-slate-400">Orientation</dt>
            <dd class="font-medium text-slate-800">{{ appointment.direction }}</dd>
          </div>
          <div v-if="appointment.reason" class="sm:col-span-2">
            <dt class="text-sm text-slate-400">Motif</dt>
            <dd class="text-slate-700">{{ appointment.reason }}</dd>
          </div>
          <div v-if="appointment.arrived_at" class="sm:col-span-2">
            <dt class="text-sm text-slate-400">Arrivée enregistrée</dt>
            <dd class="text-slate-700">{{ formatDateTime(appointment.arrived_at) }}</dd>
          </div>
        </dl>

        <div class="mt-6 flex flex-wrap gap-3">
          <button type="button" class="btn-secondary lg:hidden" @click="showQr = !showQr">
            {{ showQr ? 'Masquer le QR code' : 'Afficher mon QR code' }}
          </button>
          <button
            v-if="appointment.can_cancel"
            type="button"
            class="btn-danger"
            @click="cancelOpen = true"
          >
            Annuler le rendez-vous
          </button>
        </div>
        <p
          v-if="!appointment.can_cancel && ['BOOKED', 'CONFIRMED'].includes(appointment.status)"
          class="mt-3 text-xs text-slate-500"
        >
          L'annulation en ligne n'est plus possible : contactez le service concerné.
        </p>
      </div>

      <div v-if="appointment.status_history?.length" class="card p-6">
        <h2 class="text-lg font-semibold text-slate-900">Suivi</h2>
        <ol class="mt-4 space-y-3">
          <li
            v-for="entry in appointment.status_history"
            :key="entry.id"
            class="flex items-start gap-3 text-sm"
          >
            <span class="mt-1.5 h-2 w-2 shrink-0 rounded-full bg-brand-500" aria-hidden="true" />
            <div>
              <p class="font-medium text-slate-800">
                <StatusBadge :status="entry.to_status" />
              </p>
              <p class="text-xs text-slate-500">{{ formatDateTime(entry.changed_at) }}</p>
              <p v-if="entry.note" class="text-xs text-slate-500">{{ entry.note }}</p>
            </div>
          </li>
        </ol>
      </div>
    </section>

    <aside :class="showQr ? '' : 'hidden lg:block'">
      <QrCodePanel
        v-if="['BOOKED', 'CONFIRMED', 'ARRIVED'].includes(appointment.status)"
        :appointment-id="appointment.id"
      />
      <div v-else class="card p-6 text-sm text-slate-500">
        Le QR code n'est plus actif pour ce rendez-vous.
      </div>
    </aside>

    <AppModal :open="cancelOpen" title="Annuler ce rendez-vous ?" @close="cancelOpen = false">
      <p class="text-sm text-slate-600">
        Le créneau sera immédiatement remis à disposition d'autres patients.
      </p>
      <label for="cancel-reason" class="field-label mt-4">Motif (facultatif)</label>
      <input id="cancel-reason" v-model="cancelReason" class="field-input" maxlength="255" />
      <template #footer>
        <button type="button" class="btn-secondary" @click="cancelOpen = false">Retour</button>
        <button type="button" class="btn-danger" :disabled="cancelling" @click="cancel">
          {{ cancelling ? 'Annulation…' : 'Confirmer l\'annulation' }}
        </button>
      </template>
    </AppModal>
  </div>
</template>
