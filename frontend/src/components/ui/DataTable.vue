<script setup>
defineProps({
  columns: { type: Array, required: true },
  rows: { type: Array, required: true },
  rowKey: { type: String, default: 'id' },
})
</script>

<template>
  <div class="card overflow-hidden">
    <div class="overflow-x-auto">
      <table class="min-w-full divide-y divide-slate-200 text-sm">
        <thead class="bg-slate-50">
          <tr>
            <th
              v-for="column in columns"
              :key="column.key"
              scope="col"
              class="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500"
            >
              {{ column.label }}
            </th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-100">
          <tr v-for="row in rows" :key="row[rowKey]" class="hover:bg-slate-50">
            <td v-for="column in columns" :key="column.key" class="px-4 py-3 align-middle text-slate-700">
              <slot :name="`cell-${column.key}`" :row="row">{{ row[column.key] ?? '—' }}</slot>
            </td>
          </tr>
          <tr v-if="!rows.length">
            <td :colspan="columns.length" class="px-4 py-8 text-center text-slate-500">
              Aucun élément à afficher.
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
