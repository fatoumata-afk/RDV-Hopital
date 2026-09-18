<script setup>
import AppLayout from './AppLayout.vue'

const navigation = [
  { to: '/patient', label: 'Tableau de bord' },
  { to: '/patient/reserver', label: 'Prendre rendez-vous' },
  { to: '/patient/rendez-vous', label: 'Mes rendez-vous' },
  { to: '/patient/profil', label: 'Mon profil' },
]
</script>

<template>
  <AppLayout :navigation="navigation" title="Espace patient" />
</template>
