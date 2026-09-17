<script setup>
import { useToastStore } from '@/stores/toast'

const toasts = useToastStore()

const STYLES = {
  success: 'border-emerald-200 bg-emerald-50 text-emerald-900',
  error: 'border-rose-200 bg-rose-50 text-rose-900',
  info: 'border-slate-200 bg-white text-slate-800',
}
</script>

<template>
  <div class="no-print pointer-events-none fixed inset-x-0 top-4 z-50 flex flex-col items-center gap-2 px-4">
    <TransitionGroup name="toast">
      <div
        v-for="toast in toasts.toasts"
        :key="toast.id"
        class="pointer-events-auto w-full max-w-md rounded-xl border px-4 py-3 text-sm shadow-lg"
        :class="STYLES[toast.type]"
        role="status"
      >
        <div class="flex items-start gap-3">
          <span class="flex-1">{{ toast.message }}</span>
          <button
            type="button"
            class="text-slate-400 hover:text-slate-600"
            aria-label="Fermer"
            @click="toasts.dismiss(toast.id)"
          >
            ✕
          </button>
        </div>
      </div>
    </TransitionGroup>
  </div>
</template>

<style scoped>
.toast-enter-active,
.toast-leave-active {
  transition: all 0.25s ease;
}
.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}
</style>
