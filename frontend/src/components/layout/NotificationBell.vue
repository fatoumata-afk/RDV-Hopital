<script setup>
import { onMounted, ref } from 'vue'

import { useNotificationStore } from '@/stores/notifications'
import { relativeTime } from '@/utils/format'

const notifications = useNotificationStore()
const open = ref(false)

onMounted(() => notifications.fetch().catch(() => {}))

function toggle() {
  open.value = !open.value
  if (open.value) notifications.fetch().catch(() => {})
}
</script>

<template>
  <div class="relative">
    <button
      type="button"
      class="btn-ghost relative"
      :aria-expanded="open"
      aria-label="Notifications"
      @click="toggle"
    >
      🔔
      <span
        v-if="notifications.unreadCount"
        class="absolute -right-0.5 -top-0.5 flex h-5 min-w-5 items-center justify-center rounded-full bg-rose-600 px-1 text-[11px] font-bold text-white"
      >
        {{ notifications.unreadCount }}
      </span>
    </button>

    <div
      v-if="open"
      class="absolute right-0 z-40 mt-2 w-80 rounded-2xl border border-slate-200 bg-white p-2 shadow-xl"
    >
      <div class="flex items-center justify-between px-2 py-1">
        <p class="text-sm font-semibold text-slate-800">Notifications</p>
        <button
          v-if="notifications.unreadCount"
          type="button"
          class="text-xs font-medium text-brand-700 hover:underline"
          @click="notifications.markAllRead()"
        >
          Tout marquer comme lu
        </button>
      </div>
      <ul class="max-h-80 overflow-y-auto">
        <li v-for="item in notifications.items.slice(0, 12)" :key="item.id">
          <button
            type="button"
            class="w-full rounded-xl px-3 py-2.5 text-left transition hover:bg-slate-50"
            :class="item.read_at ? 'opacity-70' : ''"
            @click="notifications.markRead(item.id)"
          >
            <p class="text-sm font-medium text-slate-800">{{ item.title }}</p>
            <p class="text-xs text-slate-500">{{ item.message }}</p>
            <p class="mt-1 text-[11px] text-slate-400">{{ relativeTime(item.created_at) }}</p>
          </button>
        </li>
        <li v-if="!notifications.items.length" class="px-3 py-6 text-center text-sm text-slate-500">
          Aucune notification.
        </li>
      </ul>
    </div>
  </div>
</template>
