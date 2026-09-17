<script setup>
import { RouterLink } from 'vue-router'

import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()

const steps = [
  { icon: '🩺', title: 'Choisissez', text: 'Service, spécialité, médecin, date et créneau disponible.' },
  { icon: '✅', title: 'Confirmez', text: 'Votre rendez-vous est enregistré et un QR code est généré.' },
  { icon: '📱', title: 'Présentez', text: 'À l\'arrivée, montrez votre QR code à l\'accueil.' },
  { icon: '➡️', title: 'Orientez-vous', text: 'Le service et la salle vous sont indiqués immédiatement.' },
]
</script>

<template>
  <div class="min-h-screen bg-white">
    <header class="border-b border-slate-200">
      <div class="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6">
        <span class="flex items-center gap-2.5">
          <span class="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-700 text-white">
            <svg viewBox="0 0 24 24" class="h-5 w-5" fill="currentColor" aria-hidden="true">
              <path d="M10 3h4v7h7v4h-7v7h-4v-7H3v-4h7z" />
            </svg>
          </span>
          <span class="text-base font-bold text-slate-900">HospiRDV</span>
        </span>
        <nav class="flex items-center gap-2">
          <RouterLink v-if="auth.isAuthenticated" :to="auth.homeRoute" class="btn-primary">
            Mon espace
          </RouterLink>
          <template v-else>
            <RouterLink to="/connexion" class="btn-secondary">Se connecter</RouterLink>
            <RouterLink to="/inscription" class="btn-primary">Créer un compte</RouterLink>
          </template>
        </nav>
      </div>
    </header>

    <section class="mx-auto max-w-6xl px-4 py-16 sm:px-6 lg:py-24">
      <div class="grid items-center gap-12 lg:grid-cols-2">
        <div>
          <p class="inline-flex rounded-full bg-brand-50 px-3 py-1 text-xs font-semibold text-brand-800">
            Parcours patient simplifié
          </p>
          <h1 class="mt-4 text-4xl font-bold tracking-tight text-slate-900 sm:text-5xl">
            Votre rendez-vous à l'hôpital, sans file d'attente inutile.
          </h1>
          <p class="mt-5 text-lg text-slate-600">
            Réservez en ligne, recevez un QR code sécurisé et soyez orienté vers le bon service
            dès votre arrivée.
          </p>
          <div class="mt-8 flex flex-wrap gap-3">
            <RouterLink to="/inscription" class="btn-primary px-6 py-3 text-base">
              Prendre un rendez-vous
            </RouterLink>
            <RouterLink to="/connexion" class="btn-secondary px-6 py-3 text-base">
              J'ai déjà un compte
            </RouterLink>
          </div>
        </div>

        <div class="card p-6 sm:p-8">
          <p class="text-xs font-semibold uppercase tracking-wide text-slate-400">
            Exemple de rendez-vous
          </p>
          <p class="mt-2 text-xl font-semibold text-slate-900">Dr Amadou Diallo</p>
          <p class="text-slate-500">Cardiologie</p>
          <dl class="mt-5 grid grid-cols-2 gap-4 text-sm">
            <div><dt class="text-slate-400">Date</dt><dd class="font-medium">25 septembre 2026</dd></div>
            <div><dt class="text-slate-400">Heure</dt><dd class="font-medium">10:30</dd></div>
            <div><dt class="text-slate-400">Service</dt><dd class="font-medium">Cardiologie</dd></div>
            <div><dt class="text-slate-400">Salle</dt><dd class="font-medium">B-204</dd></div>
          </dl>
          <div class="mt-6 flex items-center gap-4 rounded-xl bg-slate-50 p-4">
            <span class="text-3xl" aria-hidden="true">🔳</span>
            <p class="text-sm text-slate-600">
              Un QR code unique et sécurisé est généré : il ne contient aucune donnée médicale.
            </p>
          </div>
        </div>
      </div>
    </section>

    <section class="border-t border-slate-200 bg-slate-50 py-16">
      <div class="mx-auto max-w-6xl px-4 sm:px-6">
        <h2 class="text-center text-2xl font-bold text-slate-900">Comment ça marche&nbsp;?</h2>
        <div class="mt-10 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          <div v-for="step in steps" :key="step.title" class="card p-6">
            <span class="text-2xl" aria-hidden="true">{{ step.icon }}</span>
            <h3 class="mt-3 font-semibold text-slate-900">{{ step.title }}</h3>
            <p class="mt-1 text-sm text-slate-600">{{ step.text }}</p>
          </div>
        </div>
      </div>
    </section>

    <footer class="border-t border-slate-200 py-8 text-center text-sm text-slate-500">
      HospiRDV — Gestion des rendez-vous et de l'accueil hospitalier.
    </footer>
  </div>
</template>
