<script setup>
defineProps({
  label: { type: String, required: true },
  error: { type: String, default: '' },
  hint: { type: String, default: '' },
  id: { type: String, default: undefined },
})
</script>

<template>
  <div>
    <label :for="id" class="field-label">{{ label }}</label>
    <slot />
    <p v-if="hint && !error" class="mt-1 text-xs text-slate-500">{{ hint }}</p>
    <p v-if="error" class="mt-1 text-xs font-medium text-rose-600">{{ error }}</p>
  </div>
</template>
