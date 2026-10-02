<template>
  <main class="dashboard-workspace" dir="rtl">
    <header class="dashboard-intro"><span>مرکز عملیات · {{ projectName }}</span><h1>کارهای امروز را از اینجا شروع کنید</h1><p>به بخش‌های در دسترس پروژه بروید و گزارش مدیریتی را هر زمان لازم داشتید ببینید.</p></header>
    <div v-if="loading && !loaded" class="report-state" role="status"><span class="spinner-border spinner-border-sm" aria-hidden="true"></span><p>در حال دریافت فضای کاری…</p></div>
    <div v-if="failed" class="dashboard-error" role="alert">دریافت فهرست بخش‌ها ممکن نشد. <button type="button" @click="getProjectList">تلاش دوباره</button></div>
    <section v-if="quickLinks.length" class="dashboard-section" aria-labelledby="quick-links-title"><div class="dashboard-section-head"><span>دسترسی سریع</span><h2 id="quick-links-title">بخش‌های کاری شما</h2></div><div class="dashboard-links"><router-link v-for="(item, index) in quickLinks" :key="item.id" :to="item.frontend_route_url" class="dashboard-link"><span class="link-number">{{ number(index + 1) }}</span><strong>{{ item.verbose_name || item.title_fa || item.title }}</strong><span class="link-arrow" aria-hidden="true">←</span></router-link></div></section>
    <section class="dashboard-report" aria-labelledby="report-title"><div class="report-heading"><div><span>نمای تحلیلی</span><h2 id="report-title">گزارش مدیریتی پروژه</h2><p>گزارش متصل به این پروژه را برای بررسی روندها و شاخص‌ها باز کنید.</p></div><button v-if="iframeLink" type="button" class="report-toggle" :aria-expanded="showReport ? 'true' : 'false'" @click="showReport = !showReport">{{ showReport ? 'بستن گزارش' : 'نمایش گزارش' }} <span aria-hidden="true">{{ showReport ? '↑' : '↓' }}</span></button></div>
      <iframe v-if="iframeLink && showReport" :src="iframeLink" title="گزارش مدیریتی پروژه" class="dashboard-frame" loading="lazy" />
      <div v-else-if="!iframeLink && !loading" class="report-state"><svg viewBox="0 0 48 48" aria-hidden="true"><rect x="8" y="8" width="32" height="32" rx="5"/><path d="M16 31V24M24 31V17M32 31V21"/></svg><h3>{{ failed ? 'گزارش در دسترس نیست' : 'گزارشی برای این پروژه تعریف نشده است' }}</h3><p>{{ failed ? 'پس از برقراری اتصال دوباره تلاش کنید.' : 'از بخش‌های کاری بالا یا منوی کناری استفاده کنید.' }}</p></div>
    </section>
  </main>
</template>
<script>
import { normalizeMenu } from '@/utils/adminNavigation';
export default {
  data() { return { iframeLink: null, links: [], projectName: 'پروژه شما', loading: true, loaded: false, failed: false, showReport: window.innerWidth >= 768, sequence: 0 }; },
  computed: {
    projectId() { return this.$STORE.state.userConfig.setProjectId; },
    quickLinks() {
      const preferred = ['/visitmanagment/lists', '/service-cases', '/elevatormanagement/groupbuildinglist', '/customermanagement/list', '/usermanagement/list', '/warehouse/warelist'];
      const rank = route => { const index = preferred.indexOf(route); return index < 0 ? preferred.length : index; };
      return [...this.links].sort((a, b) => rank(a.frontend_route_url) - rank(b.frontend_route_url)).slice(0, 6);
    },
  },
  mounted() { this.getProjectList(); },
  beforeDestroy() { this.sequence++; },
  watch: { projectId() { this.sequence++; this.links = []; this.iframeLink = null; this.projectName = 'پروژه شما'; this.loaded = false; this.getProjectList(); } },
  methods: {
    number(value) { return Number(value).toLocaleString('fa-IR'); },
    async getProjectList() {
      if (!this.projectId) return;
      const project = this.projectId;
      const sequence = ++this.sequence;
      this.loading = true; this.failed = false;
      try {
        const [res, membershipRes] = await Promise.all([
          this.$ApiServiceLayer.get(this.$PATH.RELATIVE_PATH.GET.MENU_LIST + '?p=' + project + '&is_active=true', this.$PATH.SERVICE_NAME.AUTH),
          this.$ApiServiceLayer.get(this.$PATH.RELATIVE_PATH.GET.AUTH_ROLE, this.$PATH.SERVICE_NAME.AUTH),
        ]);
        if (sequence !== this.sequence) return;
        if (membershipRes.status === 200) {
          const assignments = Array.isArray(membershipRes.data) ? membershipRes.data : (membershipRes.data.results || []);
          const active = assignments.find(item => item.project && item.project.id === Number(project));
          if (active) this.projectName = active.project.name_fa || active.project.name || 'پروژه شما';
        }
        if (res.status !== 200) { this.failed = true; return; }
        const flatten = nodes => nodes.reduce((all, node) => [...all, node, ...flatten(node.children || [])], []);
        const menus = flatten(normalizeMenu(res.data));
        const dashboard = menus.find(menu => menu.frontend_route_url === '/dashboard' && menu.iframe_link);
        this.iframeLink = dashboard ? dashboard.iframe_link : null;
        this.links = menus.filter(menu => !menu.has_submenu && !(menu.children || []).length && menu.frontend_route_url && menu.frontend_route_url !== '/dashboard' && this.$router.resolve(menu.frontend_route_url).resolved.matched.length);
        this.loaded = true;
      } catch (_) { if (sequence === this.sequence) this.failed = true; }
      finally { if (sequence === this.sequence) this.loading = false; }
    },
  },
};
</script>
<style scoped>
.dashboard-workspace{display:grid;gap:22px;color:#17394e}.dashboard-intro{position:relative;overflow:hidden;padding:30px;border-radius:20px;background:linear-gradient(140deg,#102f4d,#1f6986);color:#fff;box-shadow:0 12px 28px #163c5421}.dashboard-intro:after{content:'';position:absolute;width:180px;height:180px;left:-45px;top:-80px;border-radius:50%;border:1px solid #ffffff3b;box-shadow:0 0 0 29px #ffffff0b,0 0 0 61px #ffffff08}.dashboard-intro span{color:#bfe7ed;font-size:12px;font-weight:700}.dashboard-intro h1{color:#fff;margin:7px 0;font-size:25px;line-height:1.5}.dashboard-intro p{color:#e3f2f5;margin:0;max-width:560px;font-size:13px;line-height:1.9}.dashboard-section,.dashboard-report{padding:24px;border:1px solid #dce8ed;border-radius:18px;background:#fff;box-shadow:0 5px 17px #173f5809}.dashboard-section-head span,.report-heading span{color:#367994;font-size:11px;font-weight:700}.dashboard-section h2,.report-heading h2{color:#17394e;font-size:19px;margin:4px 0 18px}.dashboard-links{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:11px}.dashboard-link{display:flex;align-items:center;gap:11px;min-height:75px;padding:15px;border:1px solid #dbe9ef;border-radius:14px;background:#f8fbfc;color:#214b61;text-decoration:none}.dashboard-link:hover{border-color:#8cb9ca;background:#eef7f8}.dashboard-link strong{flex:1;font-size:13px;line-height:1.6}.link-number{display:grid;place-items:center;width:32px;height:32px;flex:none;border-radius:10px;background:#e1f1f3;color:#236d83;font-size:12px;font-weight:800}.link-arrow{font-size:19px;color:#2c758d}.report-heading{display:flex;align-items:flex-start;justify-content:space-between;gap:16px}.report-heading h2{margin-bottom:4px}.report-heading p{color:#647e8c;font-size:12px;line-height:1.8;margin:0 0 15px}.report-toggle{min-height:44px;flex:none;padding:9px 15px;border:1px solid #b9d9e2;border-radius:11px;background:#e9f5f6;color:#1d617d;font-size:12px;font-weight:700}.dashboard-frame{display:block;width:100%;height:calc(100vh - 240px);min-height:500px;border:0;border-radius:11px}.report-state{display:flex;flex-direction:column;align-items:center;justify-content:center;padding:32px 20px;min-height:160px;text-align:center;color:#667e8c}.report-state svg{width:44px;height:44px;stroke:#8da6b3;stroke-width:2;fill:none;margin-bottom:12px}.report-state h3{font-size:15px;color:#244b60;margin-bottom:8px}.report-state p{font-size:12px;margin:0}.dashboard-error{padding:13px 16px;border-radius:12px;background:#fff0ef;color:#9e4141;font-size:13px}.dashboard-error button{border:0;background:transparent;color:inherit;text-decoration:underline}.dashboard-workspace a:focus-visible,.dashboard-workspace button:focus-visible{outline:3px solid #3094bd;outline-offset:3px}@media(max-width:900px){.dashboard-links{grid-template-columns:repeat(2,minmax(0,1fr))}}@media(max-width:650px){.dashboard-intro{padding:23px}.dashboard-intro h1{font-size:22px}.dashboard-section,.dashboard-report{padding:18px}.dashboard-links{grid-template-columns:1fr}.report-heading{flex-direction:column}.report-toggle{width:100%}.dashboard-frame{height:520px;min-height:0}}
</style>
