<script setup>
import { reactive, ref, watchEffect } from 'vue'

import FormField from '@/components/ui/FormField.vue'
import { errorMessage, fieldErrors } from '@/services/http'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'

const auth = useAuthStore()
const toasts = useToastStore()

const profileForm = reactive({ first_name: '', last_name: '', phone: '' })
const patientForm = reactive({ birth_date: '', gender: '', address: '', emergency_contact: '' })
const passwordForm = reactive({ current_password: '', new_password: '' })
const errors = ref({})
const savingProfile = ref(false)
const savingPassword = ref(false)

watchEffect(() => {
  const user = auth.user
  if (!user) return
  profileForm.first_name = user.first_name
  profileForm.last_name = user.last_name
  profileForm.phone = user.phone ?? ''
  if (user.role === 'PATIENT' && user.profile) {
    patientForm.birth_date = user.profile.birth_date ?? ''
    patientForm.gender = user.profile.gender ?? ''
    patientForm.address = user.profile.address ?? ''
    patientForm.emergency_contact = user.profile.emergency_contact ?? ''
  }
})

async function saveProfile() {
  savingProfile.value = true
  errors.value = {}
  try {
    const payload = { ...profileForm }
    if (auth.role === 'PATIENT') payload.profile = { ...patientForm }
    await auth.updateProfile(payload)
    toasts.success('Profil mis à jour.')
  } catch (err) {
    errors.value = fieldErrors(err)
    toasts.error(errorMessage(err, 'La mise à jour a échoué.'))
  } finally {
    savingProfile.value = false
  }
}

async function savePassword() {
  savingPassword.value = true
  try {
    await auth.changePassword({ ...passwordForm })
    passwordForm.current_password = ''
    passwordForm.new_password = ''
    toasts.success('Mot de passe modifié.')
  } catch (err) {
    toasts.error(errorMessage(err, 'Le changement de mot de passe a échoué.'))
  } finally {
    savingPassword.value = false
  }
}
</script>

<template>
  <div class="space-y-6">
    <header>
      <h1 class="text-2xl font-bold text-slate-900">Mon profil</h1>
      <p class="text-sm text-slate-500">{{ auth.user?.email }}</p>
    </header>

    <div
      v-if="auth.user?.must_change_password"
      class="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900"
    >
      Votre mot de passe a été défini par l'administration : modifiez-le dès maintenant.
    </div>

    <section class="card p-6">
      <h2 class="text-lg font-semibold text-slate-900">Informations personnelles</h2>
      <form class="mt-4 grid gap-4 sm:grid-cols-2" @submit.prevent="saveProfile">
        <FormField id="first_name" label="Prénom" :error="errors.first_name">
          <input id="first_name" v-model="profileForm.first_name" required class="field-input" />
        </FormField>
        <FormField id="last_name" label="Nom" :error="errors.last_name">
          <input id="last_name" v-model="profileForm.last_name" required class="field-input" />
        </FormField>
        <FormField id="phone" label="Téléphone" :error="errors.phone">
          <input id="phone" v-model="profileForm.phone" class="field-input" />
        </FormField>

        <template v-if="auth.role === 'PATIENT'">
          <FormField id="birth_date" label="Date de naissance">
            <input id="birth_date" v-model="patientForm.birth_date" type="date" class="field-input" />
          </FormField>
          <FormField id="gender" label="Sexe">
            <select id="gender" v-model="patientForm.gender" class="field-input">
              <option value="">Non précisé</option>
              <option value="F">Féminin</option>
              <option value="M">Masculin</option>
            </select>
          </FormField>
          <FormField id="address" label="Adresse">
            <input id="address" v-model="patientForm.address" class="field-input" />
          </FormField>
          <FormField id="emergency_contact" label="Contact d'urgence" class="sm:col-span-2">
            <input id="emergency_contact" v-model="patientForm.emergency_contact" class="field-input" />
          </FormField>
        </template>

        <div class="sm:col-span-2">
          <button type="submit" class="btn-primary" :disabled="savingProfile">
            {{ savingProfile ? 'Enregistrement…' : 'Enregistrer' }}
          </button>
        </div>
      </form>
    </section>

    <section class="card p-6">
      <h2 class="text-lg font-semibold text-slate-900">Mot de passe</h2>
      <form class="mt-4 grid gap-4 sm:grid-cols-2" @submit.prevent="savePassword">
        <FormField id="current_password" label="Mot de passe actuel">
          <input
            id="current_password"
            v-model="passwordForm.current_password"
            type="password"
            autocomplete="current-password"
            required
            class="field-input"
          />
        </FormField>
        <FormField id="new_password" label="Nouveau mot de passe">
          <input
            id="new_password"
            v-model="passwordForm.new_password"
            type="password"
            autocomplete="new-password"
            required
            class="field-input"
          />
        </FormField>
        <div class="sm:col-span-2">
          <button type="submit" class="btn-secondary" :disabled="savingPassword">
            {{ savingPassword ? 'Modification…' : 'Modifier le mot de passe' }}
          </button>
        </div>
      </form>
    </section>
  </div>
</template>
