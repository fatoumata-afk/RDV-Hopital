<script setup>
import AppLayout from './AppLayout.vue'

const navigation = [
  { to: '/accueil', label: 'Scanner' },
  { to: '/accueil/arrivees', label: 'Arrivées du jour' },
  { to: '/accueil/profil', label: 'Mon profil' },
]
</script>

<template>
  <AppLayout :navigation="navigation" title="Accueil / contrôle" accent="bg-emerald-700" />
</template>
