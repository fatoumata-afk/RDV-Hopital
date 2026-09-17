<script setup>
import AppLayout from './AppLayout.vue'

const navigation = [
  { to: '/medecin', label: 'Tableau de bord' },
  { to: '/medecin/agenda', label: 'Agenda' },
  { to: '/medecin/disponibilites', label: 'Mes disponibilités' },
  { to: '/medecin/profil', label: 'Mon profil' },
]
</script>

<template>
  <AppLayout :navigation="navigation" title="Espace médecin" accent="bg-sky-700" />
</template>
