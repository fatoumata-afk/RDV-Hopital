<script setup>
import { computed } from 'vue'

import { STATUS_STYLES } from '@/utils/format'

const props = defineProps({ status: { type: String, required: true } })

const style = computed(
  () => STATUS_STYLES[props.status] ?? { label: props.status, class: 'bg-slate-100 text-slate-700' },
)
</script>

<template>
  <span class="badge" :class="style.class">{{ style.label }}</span>
</template>
