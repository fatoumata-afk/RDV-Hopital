<script setup>
import { reactive, ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'

import FormField from '@/components/ui/FormField.vue'
import { errorMessage } from '@/services/http'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'

const auth = useAuthStore()
const toasts = useToastStore()
const router = useRouter()
const route = useRoute()

const form = reactive({ email: '', password: '' })
const loading = ref(false)
const error = ref('')

async function submit() {
  loading.value = true
  error.value = ''
  try {
    const user = await auth.login({ ...form })
    toasts.success(`Bienvenue ${user.first_name} !`)
    router.push(route.query.redirect ?? auth.homeRoute)
  } catch (err) {
    error.value = errorMessage(err, 'Identifiants incorrects.')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="flex min-h-screen items-center justify-center bg-slate-50 px-4 py-12">
    <div class="w-full max-w-md">
      <RouterLink to="/" class="mb-6 flex items-center justify-center gap-2.5">
        <span class="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-700 text-white">
          <svg viewBox="0 0 24 24" class="h-5 w-5" fill="currentColor" aria-hidden="true">
            <path d="M10 3h4v7h7v4h-7v7h-4v-7H3v-4h7z" />
          </svg>
        </span>
        <span class="text-lg font-bold text-slate-900">HospiRDV</span>
      </RouterLink>

      <div class="card p-6 sm:p-8">
        <h1 class="text-xl font-semibold text-slate-900">Connexion</h1>
        <p class="mt-1 text-sm text-slate-500">Accédez à votre espace personnel.</p>

        <form class="mt-6 space-y-4" @submit.prevent="submit">
          <FormField id="email" label="Adresse e-mail">
            <input
              id="email"
              v-model="form.email"
              type="email"
              autocomplete="email"
              required
              class="field-input"
              placeholder="vous@exemple.com"
            />
          </FormField>

          <FormField id="password" label="Mot de passe">
            <input
              id="password"
              v-model="form.password"
              type="password"
              autocomplete="current-password"
              required
              class="field-input"
              placeholder="••••••••"
            />
          </FormField>

          <p v-if="error" class="rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">
            {{ error }}
          </p>

          <button type="submit" class="btn-primary w-full" :disabled="loading">
            {{ loading ? 'Connexion…' : 'Se connecter' }}
          </button>
        </form>

        <p class="mt-6 text-center text-sm text-slate-600">
          Pas encore de compte ?
          <RouterLink to="/inscription" class="font-semibold text-brand-700 hover:underline">
            Créer un compte patient
          </RouterLink>
        </p>
      </div>
    </div>
  </div>
</template>
