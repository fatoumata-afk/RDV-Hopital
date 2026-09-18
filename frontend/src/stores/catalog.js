import { defineStore } from 'pinia'
import { ref } from 'vue'

import { catalogApi } from '@/services/api'

/** Catalogue hospitalier mis en cache : il change rarement pendant une session. */
export const useCatalogStore = defineStore('catalog', () => {
  const specialties = ref([])
  const departments = ref([])
  const loaded = ref(false)

  async function load(force = false) {
    if (loaded.value && !force) return
    const [specialtyList, departmentList] = await Promise.all([
      catalogApi.specialties(),
      catalogApi.departments(),
    ])
    specialties.value = specialtyList
    departments.value = departmentList
    loaded.value = true
  }

  return { specialties, departments, loaded, load }
})
