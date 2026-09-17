<script setup>
import { ref, watch } from 'vue'
import { RouterLink, RouterView, useRoute, useRouter } from 'vue-router'

import NotificationBell from '@/components/layout/NotificationBell.vue'
import { useAuthStore } from '@/stores/auth'

defineProps({
  navigation: { type: Array, required: true },
  title: { type: String, required: true },
  accent: { type: String, default: 'bg-brand-700' },
})

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()
const menuOpen = ref(false)

watch(() => route.fullPath, () => (menuOpen.value = false))

async function logout() {
  await auth.logout()
  router.push('/connexion')
}
</script>

<template>
  <div class="min-h-screen bg-slate-50">
    <header class="no-print sticky top-0 z-30 border-b border-slate-200 bg-white/95 backdrop-blur">
      <div class="mx-auto flex h-16 max-w-7xl items-center gap-4 px-4 sm:px-6 lg:px-8">
        <RouterLink :to="auth.homeRoute" class="flex items-center gap-2.5">
          <span class="flex h-9 w-9 items-center justify-center rounded-xl text-white" :class="accent">
            <svg viewBox="0 0 24 24" class="h-5 w-5" fill="currentColor" aria-hidden="true">
              <path d="M10 3h4v7h7v4h-7v7h-4v-7H3v-4h7z" />
            </svg>
          </span>
          <span class="leading-tight">
            <span class="block text-sm font-bold text-slate-900">HospiRDV</span>
            <span class="block text-xs text-slate-500">{{ title }}</span>
          </span>
        </RouterLink>

        <nav class="ml-6 hidden items-center gap-1 lg:flex" aria-label="Navigation principale">
          <RouterLink
            v-for="item in navigation"
            :key="item.to"
            :to="item.to"
            class="rounded-lg px-3 py-2 text-sm font-medium text-slate-600 transition hover:bg-slate-100 hover:text-slate-900"
            active-class="bg-brand-50 text-brand-800"
          >
            {{ item.label }}
          </RouterLink>
        </nav>

        <div class="ml-auto flex items-center gap-2">
          <NotificationBell />
          <div class="hidden text-right sm:block">
            <p class="text-sm font-semibold text-slate-800">{{ auth.user?.full_name }}</p>
            <p class="text-xs text-slate-500">{{ auth.user?.email }}</p>
          </div>
          <button type="button" class="btn-ghost hidden sm:inline-flex" @click="logout">
            Déconnexion
          </button>
          <button
            type="button"
            class="btn-ghost lg:hidden"
            :aria-expanded="menuOpen"
            aria-label="Ouvrir le menu"
            @click="menuOpen = !menuOpen"
          >
            ☰
          </button>
        </div>
      </div>

      <nav v-if="menuOpen" class="border-t border-slate-200 bg-white px-4 py-3 lg:hidden">
        <RouterLink
          v-for="item in navigation"
          :key="item.to"
          :to="item.to"
          class="block rounded-lg px-3 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100"
          active-class="bg-brand-50 text-brand-800"
        >
          {{ item.label }}
        </RouterLink>
        <button type="button" class="mt-2 w-full btn-secondary" @click="logout">Déconnexion</button>
      </nav>
    </header>

    <main class="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8 lg:py-8">
      <RouterView />
    </main>
  </div>
</template>
