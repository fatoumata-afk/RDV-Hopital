<script setup>
defineProps({
  title: { type: String, required: true },
  description: { type: String, default: '' },
  icon: { type: String, default: '🗓️' },
})
</script>

<template>
  <div class="flex flex-col items-center justify-center rounded-2xl border border-dashed border-slate-300 bg-white/60 px-6 py-12 text-center">
    <span class="text-3xl" aria-hidden="true">{{ icon }}</span>
    <p class="mt-3 text-base font-semibold text-slate-700">{{ title }}</p>
    <p v-if="description" class="mt-1 max-w-sm text-sm text-slate-500">{{ description }}</p>
    <div class="mt-4"><slot /></div>
  </div>
</template>
