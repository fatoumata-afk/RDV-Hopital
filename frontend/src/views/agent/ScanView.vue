<script setup>
import QrScanner from 'qr-scanner'
import { onBeforeUnmount, ref } from 'vue'

import StatusBadge from '@/components/ui/StatusBadge.vue'
import { checkinApi } from '@/services/api'
import { errorMessage } from '@/services/http'
import { useToastStore } from '@/stores/toast'
import { formatDate, formatTime } from '@/utils/format'

const toasts = useToastStore()

const video = ref(null)
const scanner = ref(null)
const scanning = ref(false)
const manualCode = ref('')
const token = ref('')
const source = ref('SCAN')
const appointment = ref(null)
const checkIn = ref(null)
const error = ref('')
const busy = ref(false)

async function startCamera() {
  error.value = ''
  try {
    scanner.value = new QrScanner(video.value, (result) => onScan(result.data), {
      highlightScanRegion: true,
      highlightCodeOutline: true,
    })
    await scanner.value.start()
    scanning.value = true
  } catch {
    error.value =
      "La caméra n'est pas accessible. Utilisez la saisie manuelle du code figurant sous le QR code."
  }
}

function stopCamera() {
  scanner.value?.stop()
  scanner.value?.destroy()
  scanner.value = null
  scanning.value = false
}

async function onScan(data) {
  stopCamera()
  await verify(data, 'SCAN')
}

async function verify(value, scanSource) {
  busy.value = true
  error.value = ''
  appointment.value = null
  checkIn.value = null
  try {
    token.value = value.trim()
    source.value = scanSource
    appointment.value = await checkinApi.verify(token.value)
  } catch (err) {
    error.value = errorMessage(err, 'QR code invalide.')
  } finally {
    busy.value = false
  }
}

async function confirmArrival() {
  busy.value = true
  try {
    checkIn.value = await checkinApi.confirm(token.value, source.value)
    appointment.value = checkIn.value.appointment
    toasts.success('Arrivée enregistrée.')
  } catch (err) {
    error.value = errorMessage(err, "L'arrivée n'a pas pu être enregistrée.")
  } finally {
    busy.value = false
  }
}

function reset() {
  appointment.value = null
  checkIn.value = null
  token.value = ''
  manualCode.value = ''
  error.value = ''
}

onBeforeUnmount(stopCamera)
</script>

<template>
  <div class="mx-auto max-w-2xl space-y-6">
    <header class="text-center">
      <h1 class="text-2xl font-bold text-slate-900">Scanner le QR code du patient</h1>
      <p class="text-sm text-slate-500">
        Vérification immédiate du rendez-vous et orientation vers le bon service.
      </p>
    </header>

    <!-- Étape scan -->
    <section v-if="!appointment && !checkIn" class="card p-6">
      <div class="overflow-hidden rounded-xl bg-slate-900">
        <video ref="video" class="aspect-video w-full object-cover" muted playsinline />
      </div>
      <div class="mt-4 flex gap-3">
        <button v-if="!scanning" type="button" class="btn-primary flex-1" @click="startCamera">
          Activer la caméra
        </button>
        <button v-else type="button" class="btn-secondary flex-1" @click="stopCamera">
          Arrêter la caméra
        </button>
      </div>

      <form class="mt-6 border-t border-slate-100 pt-5" @submit.prevent="verify(manualCode, 'MANUAL')">
        <label for="manual" class="field-label">Saisie manuelle du code</label>
        <div class="flex flex-col gap-3 sm:flex-row">
          <input
            id="manual"
            v-model="manualCode"
            class="field-input font-mono"
            placeholder="HMS:…"
            required
          />
          <button type="submit" class="btn-secondary sm:w-40" :disabled="busy">Vérifier</button>
        </div>
      </form>

      <p v-if="error" class="mt-4 rounded-lg bg-rose-50 px-3 py-2 text-sm font-medium text-rose-700">
        {{ error }}
      </p>
    </section>

    <!-- Résultat de la vérification -->
    <section v-else class="card overflow-hidden">
      <div
        class="px-6 py-4 text-white"
        :class="checkIn ? 'bg-emerald-600' : 'bg-brand-700'"
      >
        <p class="text-lg font-bold">
          {{ checkIn ? '✓ Patient arrivé' : '✓ Rendez-vous confirmé' }}
        </p>
        <p v-if="checkIn" class="text-sm text-emerald-50">
          Heure d'arrivée : {{ formatTime(checkIn.arrived_at) }}
        </p>
      </div>

      <dl class="grid gap-4 p-6 sm:grid-cols-2">
        <div class="sm:col-span-2">
          <dt class="text-xs uppercase tracking-wide text-slate-400">Patient</dt>
          <dd class="text-xl font-bold text-slate-900">{{ appointment.patient_name }}</dd>
        </div>
        <div>
          <dt class="text-xs uppercase tracking-wide text-slate-400">Médecin</dt>
          <dd class="font-semibold text-slate-800">{{ appointment.doctor_name }}</dd>
        </div>
        <div>
          <dt class="text-xs uppercase tracking-wide text-slate-400">Spécialité</dt>
          <dd class="font-semibold text-slate-800">{{ appointment.specialty }}</dd>
        </div>
        <div>
          <dt class="text-xs uppercase tracking-wide text-slate-400">Date</dt>
          <dd class="font-semibold capitalize text-slate-800">
            {{ formatDate(appointment.scheduled_at) }}
          </dd>
        </div>
        <div>
          <dt class="text-xs uppercase tracking-wide text-slate-400">Heure</dt>
          <dd class="font-semibold text-slate-800">{{ formatTime(appointment.scheduled_at) }}</dd>
        </div>
        <div>
          <dt class="text-xs uppercase tracking-wide text-slate-400">Service</dt>
          <dd class="font-semibold text-slate-800">{{ appointment.department }}</dd>
        </div>
        <div>
          <dt class="text-xs uppercase tracking-wide text-slate-400">Salle</dt>
          <dd class="font-semibold text-slate-800">{{ appointment.room ?? 'À préciser' }}</dd>
        </div>
        <div>
          <dt class="text-xs uppercase tracking-wide text-slate-400">Statut</dt>
          <dd><StatusBadge :status="appointment.status" /></dd>
        </div>
      </dl>

      <div class="border-t border-slate-100 bg-slate-50 px-6 py-5">
        <p class="text-xs uppercase tracking-wide text-slate-400">Orientation</p>
        <p class="text-lg font-bold text-slate-900">
          {{ checkIn?.direction_note ?? appointment.direction }}
        </p>
      </div>

      <p v-if="error" class="mx-6 mb-4 rounded-lg bg-rose-50 px-3 py-2 text-sm font-medium text-rose-700">
        {{ error }}
      </p>

      <div class="flex flex-col gap-3 p-6 pt-0 sm:flex-row">
        <button
          v-if="!checkIn"
          type="button"
          class="btn-primary flex-1 py-3 text-base"
          :disabled="busy"
          @click="confirmArrival"
        >
          {{ busy ? 'Enregistrement…' : "Valider l'arrivée" }}
        </button>
        <button type="button" class="btn-secondary flex-1" @click="reset">
          Scanner un autre patient
        </button>
      </div>
    </section>
  </div>
</template>
