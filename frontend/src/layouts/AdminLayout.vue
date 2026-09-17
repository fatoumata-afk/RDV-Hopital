<script setup>
import AppLayout from './AppLayout.vue'

const navigation = [
  { to: '/admin', label: 'Statistiques' },
  { to: '/admin/utilisateurs', label: 'Utilisateurs' },
  { to: '/admin/organisation', label: 'Organisation' },
  { to: '/admin/rendez-vous', label: 'Rendez-vous' },
  { to: '/admin/profil', label: 'Mon profil' },
]
</script>

<template>
  <AppLayout :navigation="navigation" title="Administration" accent="bg-slate-900" />
</template>
