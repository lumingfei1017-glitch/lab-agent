<template>
  <div>欢迎：{{ userInfo?.name }}</div>
</template>

<script setup>
import { useUser } from '@/utils/user'

const { userInfo } = useUser()
</script>
