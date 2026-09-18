import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import { notificationsApi } from '@/services/api'

export const useNotificationStore = defineStore('notifications', () => {
  const items = ref([])
  const loading = ref(false)

  const unreadCount = computed(() => items.value.filter((item) => !item.read_at).length)

  async function fetch() {
    loading.value = true
    try {
      items.value = await notificationsApi.list()
    } finally {
      loading.value = false
    }
  }

  async function markRead(id) {
    const updated = await notificationsApi.markRead(id)
    items.value = items.value.map((item) => (item.id === id ? updated : item))
  }

  async function markAllRead() {
    await notificationsApi.markAllRead()
    const readAt = new Date().toISOString()
    items.value = items.value.map((item) => item.read_at ? item : { ...item, read_at: readAt })
  }

  return { items, loading, unreadCount, fetch, markRead, markAllRead }
})
