<script setup>
defineProps({
  label: { type: String, required: true },
  value: { type: [String, Number], default: '—' },
  icon: { type: String, default: '' },
  tone: { type: String, default: 'brand' },
})

const TONES = {
  brand: 'bg-brand-50 text-brand-700',
  sky: 'bg-sky-50 text-sky-700',
  amber: 'bg-amber-50 text-amber-700',
  rose: 'bg-rose-50 text-rose-700',
}
</script>

<template>
  <div class="card flex items-center gap-4 p-5">
    <span
      v-if="icon"
      class="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl text-lg"
      :class="TONES[tone]"
      aria-hidden="true"
    >
      {{ icon }}
    </span>
    <div>
      <p class="text-sm text-slate-500">{{ label }}</p>
      <p class="text-2xl font-semibold text-slate-900">{{ value }}</p>
    </div>
  </div>
</template>
