<script setup>
import { onMounted, reactive, ref } from 'vue'

import AppSpinner from '@/components/ui/AppSpinner.vue'
import DataTable from '@/components/ui/DataTable.vue'
import FormField from '@/components/ui/FormField.vue'
import { adminApi, catalogApi } from '@/services/api'
import { errorMessage } from '@/services/http'
import { useCatalogStore } from '@/stores/catalog'
import { useToastStore } from '@/stores/toast'

const toasts = useToastStore()
const catalog = useCatalogStore()

const tab = ref('specialties')
const loading = ref(true)
const rooms = ref([])
const doctors = ref([])

const specialtyForm = reactive({ name: '', description: '', icon: '' })
const departmentForm = reactive({ name: '', code: '', building: '', floor: '', phone: '' })
const roomForm = reactive({ code: '', name: '', department: '', floor: '' })

async function load() {
  loading.value = true
  try {
    await catalog.load(true)
    ;[rooms.value, doctors.value] = await Promise.all([catalogApi.rooms(), catalogApi.doctors()])
  } catch (err) {
    toasts.error(errorMessage(err, 'Chargement impossible.'))
  } finally {
    loading.value = false
  }
}

async function createSpecialty() {
  try {
    await adminApi.createSpecialty({ ...specialtyForm })
    Object.assign(specialtyForm, { name: '', description: '', icon: '' })
    toasts.success('Spécialité créée.')
    await load()
  } catch (err) {
    toasts.error(errorMessage(err, 'Création impossible.'))
  }
}

async function createDepartment() {
  try {
    await adminApi.createDepartment({ ...departmentForm })
    Object.assign(departmentForm, { name: '', code: '', building: '', floor: '', phone: '' })
    toasts.success('Service créé.')
    await load()
  } catch (err) {
    toasts.error(errorMessage(err, 'Création impossible.'))
  }
}

async function createRoom() {
  try {
    await adminApi.createRoom({ ...roomForm })
    Object.assign(roomForm, { code: '', name: '', department: '', floor: '' })
    toasts.success('Salle créée.')
    await load()
  } catch (err) {
    toasts.error(errorMessage(err, 'Création impossible.'))
  }
}

async function updateDoctor(doctor, payload) {
  try {
    const updated = await adminApi.updateDoctor(doctor.id, payload)
    doctors.value = doctors.value.map((item) => (item.id === updated.id ? updated : item))
    toasts.success('Affectation mise à jour.')
  } catch (err) {
    toasts.error(errorMessage(err, 'Mise à jour impossible.'))
  }
}

onMounted(load)
</script>

<template>
  <div class="space-y-6">
    <header>
      <h1 class="text-2xl font-bold text-slate-900">Organisation hospitalière</h1>
      <p class="text-sm text-slate-500">Spécialités, services, salles et affectation des médecins.</p>
    </header>

    <div class="inline-flex flex-wrap rounded-xl bg-slate-100 p-1">
      <button
        v-for="option in [
          { key: 'specialties', label: 'Spécialités' },
          { key: 'departments', label: 'Services' },
          { key: 'rooms', label: 'Salles' },
          { key: 'doctors', label: 'Affectations' },
        ]"
        :key="option.key"
        type="button"
        class="rounded-lg px-4 py-2 text-sm font-semibold transition"
        :class="tab === option.key ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-600'"
        @click="tab = option.key"
      >
        {{ option.label }}
      </button>
    </div>

    <AppSpinner v-if="loading" />

    <template v-else>
      <section v-if="tab === 'specialties'" class="space-y-4">
        <DataTable
          :columns="[
            { key: 'name', label: 'Spécialité' },
            { key: 'doctors_count', label: 'Médecins' },
            { key: 'description', label: 'Description' },
          ]"
          :rows="catalog.specialties"
        />
        <form class="card grid gap-4 p-6 sm:grid-cols-3" @submit.prevent="createSpecialty">
          <FormField id="spec-name" label="Nom">
            <input id="spec-name" v-model="specialtyForm.name" required class="field-input" />
          </FormField>
          <FormField id="spec-icon" label="Icône (emoji)">
            <input id="spec-icon" v-model="specialtyForm.icon" class="field-input" maxlength="8" />
          </FormField>
          <FormField id="spec-desc" label="Description">
            <input id="spec-desc" v-model="specialtyForm.description" class="field-input" />
          </FormField>
          <div class="sm:col-span-3">
            <button type="submit" class="btn-primary">Ajouter la spécialité</button>
          </div>
        </form>
      </section>

      <section v-else-if="tab === 'departments'" class="space-y-4">
        <DataTable
          :columns="[
            { key: 'name', label: 'Service' },
            { key: 'code', label: 'Code' },
            { key: 'location', label: 'Localisation' },
            { key: 'phone', label: 'Téléphone' },
          ]"
          :rows="catalog.departments"
        />
        <form class="card grid gap-4 p-6 sm:grid-cols-5" @submit.prevent="createDepartment">
          <FormField id="dep-name" label="Nom">
            <input id="dep-name" v-model="departmentForm.name" required class="field-input" />
          </FormField>
          <FormField id="dep-code" label="Code">
            <input id="dep-code" v-model="departmentForm.code" required class="field-input" />
          </FormField>
          <FormField id="dep-building" label="Bâtiment">
            <input id="dep-building" v-model="departmentForm.building" class="field-input" />
          </FormField>
          <FormField id="dep-floor" label="Étage">
            <input id="dep-floor" v-model="departmentForm.floor" class="field-input" />
          </FormField>
          <FormField id="dep-phone" label="Téléphone">
            <input id="dep-phone" v-model="departmentForm.phone" class="field-input" />
          </FormField>
          <div class="sm:col-span-5">
            <button type="submit" class="btn-primary">Ajouter le service</button>
          </div>
        </form>
      </section>

      <section v-else-if="tab === 'rooms'" class="space-y-4">
        <DataTable
          :columns="[
            { key: 'code', label: 'Salle' },
            { key: 'name', label: 'Libellé' },
            { key: 'department_name', label: 'Service' },
            { key: 'floor', label: 'Étage' },
          ]"
          :rows="rooms"
        />
        <form class="card grid gap-4 p-6 sm:grid-cols-4" @submit.prevent="createRoom">
          <FormField id="room-code" label="Code">
            <input id="room-code" v-model="roomForm.code" required class="field-input" placeholder="B-204" />
          </FormField>
          <FormField id="room-name" label="Libellé">
            <input id="room-name" v-model="roomForm.name" class="field-input" />
          </FormField>
          <FormField id="room-department" label="Service">
            <select id="room-department" v-model="roomForm.department" required class="field-input">
              <option value="">—</option>
              <option v-for="item in catalog.departments" :key="item.id" :value="item.id">
                {{ item.name }}
              </option>
            </select>
          </FormField>
          <FormField id="room-floor" label="Étage">
            <input id="room-floor" v-model="roomForm.floor" class="field-input" />
          </FormField>
          <div class="sm:col-span-4">
            <button type="submit" class="btn-primary">Ajouter la salle</button>
          </div>
        </form>
      </section>

      <section v-else class="space-y-4">
        <DataTable
          :columns="[
            { key: 'display_name', label: 'Médecin' },
            { key: 'specialty', label: 'Spécialité' },
            { key: 'department', label: 'Service' },
            { key: 'room', label: 'Salle' },
            { key: 'is_accepting_appointments', label: 'Réservations' },
          ]"
          :rows="doctors"
        >
          <template #cell-specialty="{ row }">
            <select
              class="field-input py-1.5"
              :value="row.specialty"
              @change="updateDoctor(row, { specialty: Number($event.target.value) })"
            >
              <option v-for="item in catalog.specialties" :key="item.id" :value="item.id">
                {{ item.name }}
              </option>
            </select>
          </template>
          <template #cell-department="{ row }">
            <select
              class="field-input py-1.5"
              :value="row.department"
              @change="updateDoctor(row, { department: Number($event.target.value) })"
            >
              <option v-for="item in catalog.departments" :key="item.id" :value="item.id">
                {{ item.name }}
              </option>
            </select>
          </template>
          <template #cell-room="{ row }">
            <select
              class="field-input py-1.5"
              :value="row.room ?? ''"
              @change="updateDoctor(row, { room: $event.target.value ? Number($event.target.value) : null })"
            >
              <option value="">—</option>
              <option
                v-for="item in rooms.filter((r) => r.department === row.department)"
                :key="item.id"
                :value="item.id"
              >
                {{ item.code }}
              </option>
            </select>
          </template>
          <template #cell-is_accepting_appointments="{ row }">
            <button
              type="button"
              class="badge"
              :class="row.is_accepting_appointments ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-200 text-slate-600'"
              @click="updateDoctor(row, { is_accepting_appointments: !row.is_accepting_appointments })"
            >
              {{ row.is_accepting_appointments ? 'Ouvertes' : 'Fermées' }}
            </button>
          </template>
        </DataTable>
      </section>
    </template>
  </div>
</template>
