<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

import AppSpinner from '@/components/ui/AppSpinner.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import { appointmentsApi, catalogApi, schedulingApi } from '@/services/api'
import { errorMessage } from '@/services/http'
import { useCatalogStore } from '@/stores/catalog'
import { useToastStore } from '@/stores/toast'
import { addDays, formatDate, toIsoDate } from '@/utils/format'

const catalog = useCatalogStore()
const toasts = useToastStore()
const router = useRouter()

const STEPS = ['Spécialité', 'Médecin', 'Date', 'Créneau', 'Confirmation']
const step = ref(0)

const specialty = ref(null)
const doctor = ref(null)
const day = ref(null)
const slot = ref(null)
const reason = ref('')

const doctors = ref([])
const days = ref([])
const slots = ref([])
const loading = ref(false)
const booking = ref(false)

const rangeStart = computed(() => toIsoDate(new Date()))
const rangeEnd = computed(() => toIsoDate(addDays(new Date(), 30)))

onMounted(() => catalog.load().catch((err) => toasts.error(errorMessage(err))))

async function selectSpecialty(value) {
  specialty.value = value
  doctor.value = null
  loading.value = true
  try {
    doctors.value = await catalogApi.doctors({
      specialty: value.id,
      is_accepting_appointments: true,
    })
    step.value = 1
  } catch (err) {
    toasts.error(errorMessage(err, 'Impossible de charger les médecins.'))
  } finally {
    loading.value = false
  }
}

async function selectDoctor(value) {
  doctor.value = value
  day.value = null
  loading.value = true
  try {
    days.value = await schedulingApi.availability(value.id, {
      from: rangeStart.value,
      to: rangeEnd.value,
    })
    step.value = 2
  } catch (err) {
    toasts.error(errorMessage(err, 'Impossible de charger les disponibilités.'))
  } finally {
    loading.value = false
  }
}

async function selectDay(value) {
  day.value = value
  slot.value = null
  loading.value = true
  try {
    slots.value = await schedulingApi.slots(doctor.value.id, { date: value })
    step.value = 3
  } catch (err) {
    toasts.error(errorMessage(err, 'Impossible de charger les créneaux.'))
  } finally {
    loading.value = false
  }
}

function selectSlot(value) {
  slot.value = value
  step.value = 4
}

async function confirm() {
  booking.value = true
  try {
    const appointment = await appointmentsApi.book({ slot: slot.value.id, reason: reason.value })
    toasts.success('Rendez-vous confirmé, votre QR code est disponible.')
    router.push(`/patient/rendez-vous/${appointment.id}?qr=1`)
  } catch (err) {
    toasts.error(errorMessage(err, "La réservation a échoué : ce créneau n'est plus disponible."))
    // Le créneau vient peut-être d'être pris : on recharge la liste.
    if (day.value) await selectDay(day.value)
  } finally {
    booking.value = false
  }
}

function goBack() {
  step.value = Math.max(0, step.value - 1)
}

watch(step, () => window.scrollTo({ top: 0, behavior: 'smooth' }))
</script>

<template>
  <div class="space-y-6">
    <header>
      <h1 class="text-2xl font-bold text-slate-900">Prendre un rendez-vous</h1>
      <p class="text-sm text-slate-500">Cinq étapes, moins d'une minute.</p>
    </header>

    <ol class="flex flex-wrap gap-2" aria-label="Étapes">
      <li
        v-for="(label, index) in STEPS"
        :key="label"
        class="flex items-center gap-2 rounded-full px-3 py-1.5 text-xs font-semibold"
        :class="
          index === step
            ? 'bg-brand-700 text-white'
            : index < step
              ? 'bg-brand-50 text-brand-800'
              : 'bg-slate-100 text-slate-500'
        "
      >
        <span>{{ index + 1 }}.</span>{{ label }}
      </li>
    </ol>

    <button v-if="step > 0" type="button" class="btn-ghost -ml-2" @click="goBack">
      ← Étape précédente
    </button>

    <AppSpinner v-if="loading" />

    <!-- Étape 1 : spécialité -->
    <section v-else-if="step === 0" class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      <button
        v-for="item in catalog.specialties"
        :key="item.id"
        type="button"
        class="card p-5 text-left transition hover:border-brand-400 hover:shadow-md"
        @click="selectSpecialty(item)"
      >
        <span class="text-2xl" aria-hidden="true">{{ item.icon || '🩺' }}</span>
        <h2 class="mt-2 font-semibold text-slate-900">{{ item.name }}</h2>
        <p class="mt-1 line-clamp-2 text-sm text-slate-500">{{ item.description }}</p>
        <p class="mt-3 text-xs font-medium text-brand-700">
          {{ item.doctors_count ?? 0 }} médecin(s)
        </p>
      </button>
    </section>

    <!-- Étape 2 : médecin -->
    <section v-else-if="step === 1" class="space-y-4">
      <EmptyState
        v-if="!doctors.length"
        title="Aucun médecin disponible"
        description="Aucun praticien n'accepte actuellement de rendez-vous dans cette spécialité."
        icon="👩‍⚕️"
      />
      <div v-else class="grid gap-4 sm:grid-cols-2">
        <button
          v-for="item in doctors"
          :key="item.id"
          type="button"
          class="card p-5 text-left transition hover:border-brand-400 hover:shadow-md"
          @click="selectDoctor(item)"
        >
          <h2 class="font-semibold text-slate-900">{{ item.display_name }}</h2>
          <p class="text-sm text-slate-500">{{ item.specialty_name }}</p>
          <p class="mt-2 text-sm text-slate-600">
            {{ item.department_name }} · Salle {{ item.room_code ?? 'à préciser' }}
          </p>
          <p v-if="item.bio" class="mt-2 line-clamp-2 text-xs text-slate-500">{{ item.bio }}</p>
        </button>
      </div>
    </section>

    <!-- Étape 3 : date -->
    <section v-else-if="step === 2" class="space-y-4">
      <EmptyState
        v-if="!days.length"
        title="Aucune disponibilité"
        description="Ce médecin n'a pas de créneau libre dans les 30 prochains jours."
        icon="📅"
      />
      <div v-else class="grid gap-3 sm:grid-cols-3 lg:grid-cols-4">
        <button
          v-for="item in days"
          :key="item.date"
          type="button"
          class="card px-4 py-3 text-left transition hover:border-brand-400"
          @click="selectDay(item.date)"
        >
          <p class="text-sm font-semibold capitalize text-slate-900">{{ formatDate(item.date) }}</p>
          <p class="text-xs text-brand-700">{{ item.slots_count }} créneau(x) libre(s)</p>
        </button>
      </div>
    </section>

    <!-- Étape 4 : créneau -->
    <section v-else-if="step === 3" class="space-y-4">
      <p class="text-sm text-slate-600">
        {{ doctor.display_name }} — <span class="capitalize">{{ formatDate(day) }}</span>
      </p>
      <EmptyState
        v-if="!slots.length"
        title="Plus aucun créneau libre"
        description="Choisissez une autre date."
        icon="⏰"
      />
      <div v-else class="grid grid-cols-3 gap-3 sm:grid-cols-5 lg:grid-cols-8">
        <button
          v-for="item in slots"
          :key="item.id"
          type="button"
          class="rounded-xl border border-slate-300 bg-white py-2.5 text-sm font-semibold text-slate-700 transition hover:border-brand-500 hover:bg-brand-50"
          @click="selectSlot(item)"
        >
          {{ item.start_time.slice(0, 5) }}
        </button>
      </div>
    </section>

    <!-- Étape 5 : confirmation -->
    <section v-else-if="step === 4" class="card max-w-xl p-6">
      <h2 class="text-lg font-semibold text-slate-900">Confirmer le rendez-vous</h2>
      <dl class="mt-4 space-y-3 text-sm">
        <div class="flex justify-between gap-4">
          <dt class="text-slate-500">Médecin</dt>
          <dd class="font-medium text-slate-900">{{ doctor.display_name }}</dd>
        </div>
        <div class="flex justify-between gap-4">
          <dt class="text-slate-500">Spécialité</dt>
          <dd class="font-medium text-slate-900">{{ specialty.name }}</dd>
        </div>
        <div class="flex justify-between gap-4">
          <dt class="text-slate-500">Service</dt>
          <dd class="font-medium text-slate-900">{{ doctor.department_name }}</dd>
        </div>
        <div class="flex justify-between gap-4">
          <dt class="text-slate-500">Salle</dt>
          <dd class="font-medium text-slate-900">{{ doctor.room_code ?? 'À préciser' }}</dd>
        </div>
        <div class="flex justify-between gap-4">
          <dt class="text-slate-500">Date</dt>
          <dd class="font-medium capitalize text-slate-900">{{ formatDate(day) }}</dd>
        </div>
        <div class="flex justify-between gap-4">
          <dt class="text-slate-500">Heure</dt>
          <dd class="font-medium text-slate-900">{{ slot.start_time.slice(0, 5) }}</dd>
        </div>
      </dl>

      <label for="reason" class="field-label mt-5">Motif (facultatif)</label>
      <textarea
        id="reason"
        v-model="reason"
        rows="3"
        maxlength="255"
        class="field-input"
        placeholder="Ex. : douleurs thoraciques depuis une semaine"
      />

      <button type="button" class="btn-primary mt-5 w-full" :disabled="booking" @click="confirm">
        {{ booking ? 'Confirmation…' : 'Confirmer le rendez-vous' }}
      </button>
    </section>
  </div>
</template>
