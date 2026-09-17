<script setup>
import { RouterLink } from 'vue-router'

import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
</script>

<template>
  <div class="flex min-h-screen flex-col items-center justify-center gap-4 px-4 text-center">
    <p class="text-5xl font-bold text-brand-700">404</p>
    <h1 class="text-xl font-semibold text-slate-800">Cette page n'existe pas.</h1>
    <RouterLink :to="auth.isAuthenticated ? auth.homeRoute : '/'" class="btn-primary">
      Retour à l'accueil
    </RouterLink>
  </div>
</template>
