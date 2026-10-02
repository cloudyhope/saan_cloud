<template>
  <main class="project-picker" dir="rtl">
    <section class="picker-card" aria-labelledby="project-title">
      <div class="picker-header">
        <img :src="$PATH.GET_IMAGE_PATH('logo.svg')" alt="سان" class="picker-logo" />
        <button type="button" class="logout-button" @click="logout">خروج</button>
      </div>
      <span class="eyebrow">پنل مدیریت سان</span>
      <h1 id="project-title">انتخاب پروژه</h1>
      <p class="intro">پروژه‌ای را که می‌خواهید مدیریت کنید انتخاب کنید. داده‌ها و دسترسی‌های هر پروژه جدا هستند.</p>

      <div v-if="loading" class="picker-message" role="status">در حال دریافت پروژه‌های شما…</div>
      <div v-else-if="error" class="picker-message picker-error" role="alert">
        {{ error }}
        <button type="button" @click="loadProjects">تلاش دوباره</button>
      </div>
      <div v-else-if="!projects.length" class="picker-message">
        هنوز دسترسی فعالی به پروژه‌ای برای این حساب ثبت نشده است.
      </div>
      <div v-else class="project-list">
        <button v-for="project in projects" :key="project.id" type="button" class="project-option" @click="selectProject(project.id)">
          <span class="project-symbol" aria-hidden="true">{{ (project.name_fa || project.name || 'س').charAt(0) }}</span>
          <span class="project-copy"><strong>{{ project.name_fa || project.name || `پروژه ${project.id}` }}</strong><small>{{ project.company_name || project.name || 'مدیریت خدمات سان' }}</small></span>
          <span class="project-arrow" aria-hidden="true">←</span>
        </button>
      </div>
    </section>
  </main>
</template>

<script>
import { logoutSession } from '@/api/apiServiceLayer';

export default {
  data() { return { loading: true, error: '', projects: [] }; },
  mounted() { this.loadProjects(); },
  methods: {
    async loadProjects() {
      this.loading = true;
      this.error = '';
      try {
        const res = await this.$ApiServiceLayer.get(
          this.$PATH.RELATIVE_PATH.GET.AUTH_ROLE,
          this.$PATH.SERVICE_NAME.AUTH
        );
        if (res.status !== 200) {
          this.error = this.$ApiServiceLayer.getErrorMessage(res);
          return;
        }
        const assignments = Array.isArray(res.data) ? res.data : (res.data.results || []);
        const unique = new Map();
        assignments.forEach(assignment => {
          if (assignment.project && assignment.project.id) unique.set(assignment.project.id, assignment.project);
        });
        this.projects = Array.from(unique.values());
        if (this.projects.length === 1) this.selectProject(this.projects[0].id);
      } catch (_) {
        this.error = 'دریافت پروژه‌ها ممکن نشد. دوباره تلاش کنید.';
      } finally {
        this.loading = false;
      }
    },
    selectProject(id) {
      this.$STORE.commit('userConfig/setProjectInfo', id);
      this.$router.push({ name: 'dashboard' });
    },
    async logout() {
      await logoutSession();
      this.$router.push({ name: 'login' });
    },
  },
};
</script>

<style scoped>
.project-picker { min-height: 100vh; min-height: 100dvh; display: grid; place-items: center; padding: 24px; background: radial-gradient(circle at 12% 10%, #dceefa 0, transparent 30%), #f4f7fa; color: #16364d; }
.picker-card { width: min(100%, 620px); padding: 32px; background: #fff; border: 1px solid #dfe9ef; border-radius: 22px; box-shadow: 0 18px 54px #1c4c6614; }
.picker-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 22px; }.picker-logo { width: 105px; height: 50px; object-fit: contain; filter: brightness(0) saturate(100%) opacity(.72); }.logout-button { min-width: 72px; min-height: 44px; border: 1px solid #d8e4eb; border-radius: 11px; background: #fff; color: #406378; }
.eyebrow { color: #39738d; font-size: 12px; font-weight: 700; }h1 { margin: 5px 0 6px; color: #153c54; font-size: 26px; }.intro { margin: 0 0 23px; color: #5b7485; font-size: 14px; line-height: 1.85; }
.project-list { display: grid; gap: 10px; }.project-option { width: 100%; min-height: 78px; display: flex; align-items: center; gap: 14px; padding: 12px; text-align: right; border: 1px solid #dfe9ef; border-radius: 15px; background: #f9fcfd; color: #173c54; }.project-option:hover { background: #eff8fb; border-color: #8ab8c9; }.project-symbol { width: 46px; height: 46px; flex: none; display: grid; place-items: center; border-radius: 13px; background: #d9eef3; color: #23657e; font-weight: 800; font-size: 21px; }.project-copy { flex: 1; min-width: 0; display: grid; gap: 4px; }.project-copy strong { font-size: 15px; }.project-copy small { color: #607b8a; font-size: 12px; }.project-arrow { font-size: 22px; color: #4a829a; }
.picker-message { padding: 20px; border: 1px dashed #c9dce6; border-radius: 13px; color: #567283; background: #f9fcfd; font-size: 13px; line-height: 1.8; }.picker-error { border-color: #e8bcbc; color: #963837; background: #fff6f5; }.picker-error button { display: block; min-height: 44px; margin-top: 8px; border: 0; background: transparent; color: #8e3131; text-decoration: underline; }
.project-option:focus-visible,.picker-card button:focus-visible { outline: 3px solid #4a9fc4; outline-offset: 2px; }
@media(max-width: 540px) { .project-picker { padding: 14px; }.picker-card { padding: 22px 18px; border-radius: 18px; }h1 { font-size: 23px; } }
</style>
