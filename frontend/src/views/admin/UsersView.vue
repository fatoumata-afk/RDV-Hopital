<script setup>
import { onMounted, reactive, ref, watch } from 'vue'

import AppModal from '@/components/ui/AppModal.vue'
import AppSpinner from '@/components/ui/AppSpinner.vue'
import DataTable from '@/components/ui/DataTable.vue'
import FormField from '@/components/ui/FormField.vue'
import { adminApi } from '@/services/api'
import { errorMessage, fieldErrors } from '@/services/http'
import { useCatalogStore } from '@/stores/catalog'
import { useToastStore } from '@/stores/toast'
import { formatShortDate } from '@/utils/format'

const toasts = useToastStore()
const catalog = useCatalogStore()

const ROLE_LABELS = {
  PATIENT: 'Patient',
  DOCTOR: 'Médecin',
  AGENT: "Agent d'accueil",
  ADMIN: 'Administrateur',
}

const columns = [
  { key: 'full_name', label: 'Nom' },
  { key: 'email', label: 'E-mail' },
  { key: 'role', label: 'Rôle' },
  { key: 'is_active', label: 'Statut' },
  { key: 'date_joined', label: 'Inscrit le' },
  { key: 'actions', label: '' },
]

const users = ref([])
const loading = ref(true)
const roleFilter = ref('')
const search = ref('')
const modalOpen = ref(false)
const saving = ref(false)
const errors = ref({})

const form = reactive({
  role: 'DOCTOR',
  first_name: '',
  last_name: '',
  email: '',
  phone: '',
  password: '',
  license_number: '',
  specialty: '',
  department: '',
  room: '',
  badge_number: '',
})

async function load() {
  loading.value = true
  try {
    const data = await adminApi.users({
      role: roleFilter.value || undefined,
      search: search.value || undefined,
    })
    users.value = data.results ?? data
  } catch (err) {
    toasts.error(errorMessage(err, 'Chargement des utilisateurs impossible.'))
  } finally {
    loading.value = false
  }
}

async function openModal() {
  await catalog.load()
  modalOpen.value = true
}

async function createStaff() {
  saving.value = true
  errors.value = {}
  try {
    const payload = Object.fromEntries(
      Object.entries(form).filter(([, value]) => value !== '' && value !== null),
    )
    await adminApi.createStaff(payload)
    toasts.success('Compte créé. Le mot de passe devra être changé à la première connexion.')
    modalOpen.value = false
    await load()
  } catch (err) {
    errors.value = fieldErrors(err)
    toasts.error(errorMessage(err, 'Création impossible.'))
  } finally {
    saving.value = false
  }
}

async function toggleActive(user) {
  try {
    const updated = await adminApi.updateUser(user.id, { is_active: !user.is_active })
    users.value = users.value.map((item) => (item.id === updated.id ? updated : item))
  } catch (err) {
    toasts.error(errorMessage(err))
  }
}

onMounted(async () => {
  await Promise.all([load(), catalog.load().catch(() => {})])
})
watch([roleFilter], load)
</script>

<template>
  <div class="space-y-6">
    <header class="flex flex-wrap items-center justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold text-slate-900">Utilisateurs</h1>
        <p class="text-sm text-slate-500">Patients, médecins, agents et administrateurs.</p>
      </div>
      <button type="button" class="btn-primary" @click="openModal">Créer un compte</button>
    </header>

    <div class="flex flex-wrap gap-3">
      <select v-model="roleFilter" class="field-input max-w-48" aria-label="Filtrer par rôle">
        <option value="">Tous les rôles</option>
        <option v-for="(label, value) in ROLE_LABELS" :key="value" :value="value">
          {{ label }}
        </option>
      </select>
      <form class="flex gap-2" @submit.prevent="load">
        <input
          v-model="search"
          type="search"
          class="field-input"
          placeholder="Rechercher un nom, un e-mail…"
          aria-label="Rechercher"
        />
        <button type="submit" class="btn-secondary">Rechercher</button>
      </form>
    </div>

    <AppSpinner v-if="loading" />

    <DataTable v-else :columns="columns" :rows="users">
      <template #cell-role="{ row }">{{ ROLE_LABELS[row.role] ?? row.role }}</template>
      <template #cell-is_active="{ row }">
        <span
          class="badge"
          :class="row.is_active ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-200 text-slate-600'"
        >
          {{ row.is_active ? 'Actif' : 'Désactivé' }}
        </span>
      </template>
      <template #cell-date_joined="{ row }">{{ formatShortDate(row.date_joined) }}</template>
      <template #cell-actions="{ row }">
        <button type="button" class="btn-ghost" @click="toggleActive(row)">
          {{ row.is_active ? 'Désactiver' : 'Réactiver' }}
        </button>
      </template>
    </DataTable>

    <AppModal :open="modalOpen" title="Créer un compte personnel" @close="modalOpen = false">
      <form id="staff-form" class="grid gap-4 sm:grid-cols-2" @submit.prevent="createStaff">
        <FormField id="role" label="Rôle" :error="errors.role" class="sm:col-span-2">
          <select id="role" v-model="form.role" class="field-input">
            <option value="DOCTOR">Médecin</option>
            <option value="AGENT">Agent d'accueil</option>
            <option value="ADMIN">Administrateur</option>
          </select>
        </FormField>
        <FormField id="first_name" label="Prénom" :error="errors.first_name">
          <input id="first_name" v-model="form.first_name" required class="field-input" />
        </FormField>
        <FormField id="last_name" label="Nom" :error="errors.last_name">
          <input id="last_name" v-model="form.last_name" required class="field-input" />
        </FormField>
        <FormField id="email" label="E-mail" :error="errors.email">
          <input id="email" v-model="form.email" type="email" required class="field-input" />
        </FormField>
        <FormField id="phone" label="Téléphone" :error="errors.phone">
          <input id="phone" v-model="form.phone" class="field-input" />
        </FormField>
        <FormField
          id="password"
          label="Mot de passe provisoire"
          :error="errors.password"
          class="sm:col-span-2"
        >
          <input id="password" v-model="form.password" type="password" required class="field-input" />
        </FormField>

        <template v-if="form.role === 'DOCTOR'">
          <FormField id="license_number" label="N° d'ordre" :error="errors.license_number">
            <input id="license_number" v-model="form.license_number" class="field-input" />
          </FormField>
          <FormField id="specialty" label="Spécialité" :error="errors.specialty">
            <select id="specialty" v-model="form.specialty" class="field-input">
              <option value="">—</option>
              <option v-for="item in catalog.specialties" :key="item.id" :value="item.id">
                {{ item.name }}
              </option>
            </select>
          </FormField>
          <FormField id="department" label="Service" :error="errors.department">
            <select id="department" v-model="form.department" class="field-input">
              <option value="">—</option>
              <option v-for="item in catalog.departments" :key="item.id" :value="item.id">
                {{ item.name }}
              </option>
            </select>
          </FormField>
          <FormField id="room" label="Salle" :error="errors.room">
            <select id="room" v-model="form.room" class="field-input">
              <option value="">—</option>
              <option
                v-for="item in catalog.departments.find((d) => d.id === form.department)?.rooms ?? []"
                :key="item.id"
                :value="item.id"
              >
                {{ item.code }} — {{ item.name }}
              </option>
            </select>
          </FormField>
        </template>

        <template v-if="form.role === 'AGENT'">
          <FormField id="badge_number" label="N° de badge" :error="errors.badge_number">
            <input id="badge_number" v-model="form.badge_number" class="field-input" />
          </FormField>
          <FormField id="agent_department" label="Service d'affectation">
            <select id="agent_department" v-model="form.department" class="field-input">
              <option value="">—</option>
              <option v-for="item in catalog.departments" :key="item.id" :value="item.id">
                {{ item.name }}
              </option>
            </select>
          </FormField>
        </template>
      </form>

      <template #footer>
        <button type="button" class="btn-secondary" @click="modalOpen = false">Annuler</button>
        <button type="submit" form="staff-form" class="btn-primary" :disabled="saving">
          {{ saving ? 'Création…' : 'Créer le compte' }}
        </button>
      </template>
    </AppModal>
  </div>
</template>
