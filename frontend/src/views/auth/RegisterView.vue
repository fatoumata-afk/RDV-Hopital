<script setup>
import { reactive, ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'

import FormField from '@/components/ui/FormField.vue'
import { errorMessage, fieldErrors } from '@/services/http'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'

const auth = useAuthStore()
const toasts = useToastStore()
const router = useRouter()

const form = reactive({
  first_name: '',
  last_name: '',
  email: '',
  phone: '',
  birth_date: '',
  gender: '',
  password: '',
})
const errors = ref({})
const error = ref('')
const loading = ref(false)

async function submit() {
  loading.value = true
  errors.value = {}
  error.value = ''
  try {
    const payload = Object.fromEntries(Object.entries(form).filter(([, value]) => value !== ''))
    await auth.register(payload)
    toasts.success('Votre compte a été créé.')
    router.push(auth.homeRoute)
  } catch (err) {
    errors.value = fieldErrors(err)
    error.value = errorMessage(err, "L'inscription a échoué.")
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="flex min-h-screen items-center justify-center bg-slate-50 px-4 py-12">
    <div class="w-full max-w-xl">
      <RouterLink to="/" class="mb-6 flex items-center justify-center gap-2.5">
        <span class="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-700 text-white">
          <svg viewBox="0 0 24 24" class="h-5 w-5" fill="currentColor" aria-hidden="true">
            <path d="M10 3h4v7h7v4h-7v7h-4v-7H3v-4h7z" />
          </svg>
        </span>
        <span class="text-lg font-bold text-slate-900">HospiRDV</span>
      </RouterLink>

      <div class="card p-6 sm:p-8">
        <h1 class="text-xl font-semibold text-slate-900">Créer un compte patient</h1>
        <p class="mt-1 text-sm text-slate-500">
          Quelques informations suffisent pour réserver votre premier rendez-vous.
        </p>

        <form class="mt-6 grid gap-4 sm:grid-cols-2" @submit.prevent="submit">
          <FormField id="first_name" label="Prénom" :error="errors.first_name">
            <input id="first_name" v-model="form.first_name" required class="field-input" />
          </FormField>
          <FormField id="last_name" label="Nom" :error="errors.last_name">
            <input id="last_name" v-model="form.last_name" required class="field-input" />
          </FormField>
          <FormField id="email" label="Adresse e-mail" :error="errors.email" class="sm:col-span-2">
            <input id="email" v-model="form.email" type="email" required class="field-input" />
          </FormField>
          <FormField id="phone" label="Téléphone" :error="errors.phone">
            <input id="phone" v-model="form.phone" class="field-input" placeholder="+221 …" />
          </FormField>
          <FormField id="birth_date" label="Date de naissance" :error="errors.birth_date">
            <input id="birth_date" v-model="form.birth_date" type="date" class="field-input" />
          </FormField>
          <FormField id="gender" label="Sexe" :error="errors.gender">
            <select id="gender" v-model="form.gender" class="field-input">
              <option value="">Non précisé</option>
              <option value="F">Féminin</option>
              <option value="M">Masculin</option>
            </select>
          </FormField>
          <FormField
            id="password"
            label="Mot de passe"
            :error="errors.password"
            hint="8 caractères minimum, évitez un mot de passe courant."
          >
            <input
              id="password"
              v-model="form.password"
              type="password"
              autocomplete="new-password"
              required
              class="field-input"
            />
          </FormField>

          <p
            v-if="error && !Object.keys(errors).length"
            class="rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700 sm:col-span-2"
          >
            {{ error }}
          </p>

          <div class="sm:col-span-2">
            <button type="submit" class="btn-primary w-full" :disabled="loading">
              {{ loading ? 'Création…' : 'Créer mon compte' }}
            </button>
          </div>
        </form>

        <p class="mt-6 text-center text-sm text-slate-600">
          Déjà inscrit ?
          <RouterLink to="/connexion" class="font-semibold text-brand-700 hover:underline">
            Se connecter
          </RouterLink>
        </p>
      </div>
    </div>
  </div>
</template>
