import { defineStore } from 'pinia'
import { ref } from 'vue'

let nextId = 1

export const useToastStore = defineStore('toast', () => {
  const toasts = ref([])

  function push(message, type = 'info', timeout = 5000) {
    const id = nextId++
    toasts.value.push({ id, message, type })
    if (timeout) setTimeout(() => dismiss(id), timeout)
    return id
  }

  const success = (message) => push(message, 'success')
  const error = (message) => push(message, 'error', 7000)
  const info = (message) => push(message, 'info')

  function dismiss(id) {
    toasts.value = toasts.value.filter((toast) => toast.id !== id)
  }

  return { toasts, push, success, error, info, dismiss }
})
