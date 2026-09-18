<script setup>
defineProps({
  open: { type: Boolean, default: false },
  title: { type: String, default: '' },
})
const emit = defineEmits(['close'])
</script>

<template>
  <Teleport to="body">
    <div
      v-if="open"
      class="fixed inset-0 z-40 flex items-end justify-center bg-slate-900/50 p-4 sm:items-center"
      role="dialog"
      aria-modal="true"
      @click.self="emit('close')"
    >
      <div class="w-full max-w-lg rounded-2xl bg-white p-6 shadow-xl">
        <div class="mb-4 flex items-start justify-between gap-4">
          <h2 class="text-lg font-semibold text-slate-900">{{ title }}</h2>
          <button type="button" class="text-slate-400 hover:text-slate-600" aria-label="Fermer" @click="emit('close')">
            ✕
          </button>
        </div>
        <slot />
        <div class="mt-6 flex justify-end gap-3"><slot name="footer" /></div>
      </div>
    </div>
  </Teleport>
</template>
