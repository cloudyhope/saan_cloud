<template>
  <div class="layout-container">
    <Sidebar />
    <div class="left-container">
      <Topbar />
      <main class="content" id="main-content">
        <header class="page-heading">
          <div class="page-title-block">
            <span class="page-icon"><NavigationIcon :route="$route.path" /></span>
            <div><nav class="page-breadcrumb" aria-label="مسیر صفحه"><router-link to="/dashboard">پنل مدیریت</router-link><span aria-hidden="true">/</span><span>{{ title }}</span></nav><h1>{{ title }}</h1></div>
          </div>
          <router-link v-if="$route.name !== 'dashboard'" to="/dashboard" class="dashboard-link"><NavigationIcon route="/dashboard" />داشبورد</router-link>
        </header>
        <div class="contdainer"><router-view /></div>
      </main>
    </div>
  </div>
</template>
<script>
import Sidebar from './Sidebar.vue';
import Topbar from './Topbar.vue';
import NavigationIcon from '../components/NavigationIcon/index.vue';
export default {
  name: 'AdminLayout',
  components: { Sidebar, Topbar, NavigationIcon },
  computed: { title() { return this.$route.meta.title || 'مدیریت'; } },
};
</script>
<style scoped>
.layout-container { display: flex; height: 100vh; height: 100dvh; overflow: hidden; }
.left-container { flex: 1; min-width: 0; overflow-y: auto; background: var(--admin-bg); }
.content { padding: 28px 32px; max-width: 1680px; margin: 0 auto; }
.page-heading { display: flex; align-items: center; justify-content: space-between; gap: 16px; margin-bottom: 28px; }
.page-title-block { display: flex; align-items: center; gap: 16px; }
.page-icon { display: grid; place-items: center; width: 52px; height: 52px; border: 1px solid #dce4f5; border-radius: 16px; background: #fff; color: var(--admin-primary); box-shadow: 0 4px 10px #17243d06; }
.page-breadcrumb { display: flex; align-items: center; gap: 10px; color: var(--admin-muted); font-size: 11px; }
.page-breadcrumb a { color: var(--admin-muted); }
h1 { font-size: 24px; font-weight: 700; margin: 5px 0 0; color: var(--admin-text); }
.dashboard-link { display: inline-flex; align-items: center; gap: 8px; color: #536078; font-size: 12px; padding: 9px 14px; background: #fff; border: 1px solid var(--admin-border); border-radius: 10px; }
.dashboard-link .navigation-icon { width: 16px; height: 16px; flex-basis: 16px; }
@media (max-width: 1100px) { .content { padding: 24px; } }
@media (max-width: 767px) { .content { padding: 20px 16px; } h1 { font-size: 20px; } .page-heading { align-items: flex-start; gap: 10px; } .page-icon { display: none; } .dashboard-link { padding: 8px; } }
</style>
