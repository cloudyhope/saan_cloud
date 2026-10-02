<template><main class="field-page"><section class="field-empty"><v-icon size="44" color="primary">mdi-shield-account-outline</v-icon><h1>دسترسی در دسترس نیست</h1><p>عضویت پروژه یا مجوزهای این بخش را با مدیر سیستم بررسی کنید.</p><v-btn outlined color="primary" :to="{ name: 'projects' }">انتخاب پروژه</v-btn><v-btn text @click="logout">خروج از حساب</v-btn></section></main></template>
<script>
import { logoutSession } from '@/api/apiServiceLayer';
export default { methods: { async logout() { await logoutSession(); this.$router.replace({ name: 'login' }); } } };
</script>
