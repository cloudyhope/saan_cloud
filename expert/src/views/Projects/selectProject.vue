<template>
  <main class="field-page">
    <header class="field-heading"><h1>انتخاب پروژه</h1><p>پروژه‌ای که می‌خواهید در آن فعالیت کنید را انتخاب کنید.</p></header>
    <v-alert v-if="error" type="error" outlined role="alert">{{ error }}<v-btn text @click="load">تلاش دوباره</v-btn></v-alert>
    <v-progress-linear v-if="loading" indeterminate />
    <v-btn v-for="project in projects" :key="project.id" block outlined large class="mb-4" :disabled="loading" @click="choose(project.id)">{{ project.name_fa || project.name || 'پروژه ' + project.id }}</v-btn>
    <section v-if="!loading && !projects.length" class="field-empty"><h2>پروژه فعالی ندارید</h2><p>برای بررسی عضویت با مدیر سیستم تماس بگیرید.</p></section>
    <v-btn text @click="logout">خروج از حساب</v-btn>
  </main>
</template>
<script>
import { assignments, selectProject } from '@/utils/fieldSession';
import { logoutSession } from '@/api/apiServiceLayer';
export default {
  data: () => ({ rows: [], loading: false, error: '' }),
  computed: { projects() { return Array.from(new Map(this.rows.map(row => [row.project.id, row.project])).values()); } },
  mounted() { this.load(); },
  methods: {
    async load() { this.loading = true; this.error = ''; try { this.rows = await assignments(this.$ApiServiceLayer); } catch (error) { this.error = error.message; } finally { this.loading = false; } },
    async choose(id) { this.loading = true; this.error = ''; try { const route = await selectProject(this.$ApiServiceLayer, id, this.rows); await this.$router.push({ name: route }); } catch (error) { this.error = error.message; } finally { this.loading = false; } },
    async logout() { await logoutSession(); this.$router.replace({ name: 'login' }); }
  }
};
</script>
