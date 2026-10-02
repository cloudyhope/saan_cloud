<template>
  <main class="field-page client-dashboard" dir="rtl">
    <div v-if="!online" class="dashboard-offline" role="status"><v-icon small>mdi-wifi-off</v-icon>{{ dashboard ? 'اتصال اینترنت قطع است؛ اطلاعات بارگذاری‌شده پیشین نمایش داده می‌شود.' : 'اتصال اینترنت قطع است؛ برای دریافت داشبورد دوباره وصل شوید.' }}</div>

    <section class="dashboard-hero" aria-labelledby="dashboard-title">
      <div class="hero-pattern" aria-hidden="true"></div>
      <div class="hero-topline">
        <span class="hero-brand"><span class="brand-mark"><v-icon color="white" size="19">mdi-elevator</v-icon></span> سان اپ</span>
        <span class="hero-top-actions"><router-link :to="{ name: 'notif' }" class="hero-account" aria-label="اعلان‌ها"><v-icon color="white" size="20">mdi-bell-outline</v-icon></router-link><router-link :to="{ name: 'setting' }" class="hero-account" aria-label="مشاهده حساب کاربری"><v-icon color="white" size="20">mdi-account-outline</v-icon></router-link></span>
      </div>
      <div class="hero-copy"><span class="hero-eyebrow">{{ projectName }}</span><h1 id="dashboard-title">سلام{{ firstName ? '، ' + firstName : '' }}<span class="hero-dot">.</span></h1><p>وضعیت ساختمان‌ها و خدمات آسانسورهای شما، یک‌جا و همیشه در دسترس.</p></div>
      <button class="hero-action" type="button" :disabled="!online || !dashboard || !dashboard.counts.buildings" @click="startRequest"><span class="hero-action-icon"><v-icon color="#123450" size="22">mdi-plus</v-icon></span><span>ثبت درخواست خدمت</span><v-icon class="hero-action-arrow" size="22">mdi-arrow-left</v-icon></button>
      <span class="hero-footnote">{{ online ? 'ساختمان را انتخاب کنید، آسانسورها و نوع خدمت را مشخص کنید.' : 'ثبت درخواست پس از وصل شدن اینترنت در دسترس است.' }}</span>
    </section>

    <div v-if="dashboardLoading && !dashboard" class="dashboard-loading" aria-label="در حال بارگذاری داشبورد"><v-skeleton-loader type="article, list-item-three-line, article" /></div>
    <v-alert v-else-if="dashboardError && !dashboard" type="error" outlined role="alert" class="dashboard-error">{{ dashboardError }}<v-btn text color="error" @click="loadDashboard">تلاش دوباره</v-btn></v-alert>
    <template v-else-if="dashboard">
      <div v-if="dashboardError" class="dashboard-notice" role="status">اطلاعات قبلی نمایش داده می‌شود. <button type="button" @click="loadDashboard">تلاش دوباره</button></div>

      <section class="dashboard-section" aria-labelledby="summary-heading">
        <div class="section-title-row"><div><span class="section-eyebrow">نمای کلی</span><h2 id="summary-heading">امروز در چه وضعیتی هستید؟</h2></div><button type="button" class="refresh-button" :disabled="dashboardLoading" aria-label="به‌روزرسانی داشبورد" @click="loadDashboard"><v-icon size="19">mdi-refresh</v-icon></button></div>
        <div class="metric-grid">
          <div class="metric-card metric-primary"><span class="metric-icon"><v-icon size="22">mdi-office-building-outline</v-icon></span><strong>{{ number(dashboard.counts.buildings) }}</strong><span>ساختمان شما</span></div>
          <div class="metric-card"><span class="metric-icon"><v-icon size="22">mdi-elevator</v-icon></span><strong>{{ number(dashboard.counts.elevators) }}</strong><span>آسانسور</span></div>
          <router-link :to="{ name: 'clientVisits' }" class="metric-card metric-link"><span class="metric-icon metric-amber"><v-icon size="22">mdi-clock-outline</v-icon></span><strong>{{ number(dashboard.counts.pending) }}</strong><span>در انتظار بررسی</span></router-link>
          <router-link :to="{ name: 'clientVisits' }" class="metric-card metric-link"><span class="metric-icon metric-blue"><v-icon size="22">mdi-progress-wrench</v-icon></span><strong>{{ number(dashboard.counts.active) }}</strong><span>خدمت در جریان</span></router-link>
        </div>
        <router-link v-if="dashboard.counts.overdue" :to="{ name: 'clientVisits' }" class="overdue-banner"><v-icon size="19">mdi-alert-circle-outline</v-icon><span>{{ number(dashboard.counts.overdue) }} مراجعه از موعد مقرر گذشته است.</span><v-icon size="18">mdi-chevron-left</v-icon></router-link>
      </section>

      <section class="dashboard-section" aria-labelledby="appointment-heading">
        <div class="section-title-row"><div><span class="section-eyebrow">برنامه خدمت</span><h2 id="appointment-heading">مراجعه بعدی</h2></div></div>
        <div v-if="dashboard.next_visit" class="appointment-card"><span class="appointment-icon"><v-icon color="#15476e" size="25">mdi-calendar-check-outline</v-icon></span><div class="appointment-copy"><strong>{{ dashboard.next_visit.type_name || 'خدمت آسانسور' }}</strong><span>{{ dashboard.next_visit.building_name || 'ساختمان' }}</span><small>تاریخ برنامه‌ریزی: {{ date(dashboard.next_visit.due_date) }}</small></div><router-link :to="{ name: 'clientVisits' }" class="appointment-link" aria-label="مشاهده جزئیات مراجعات"><v-icon size="20">mdi-arrow-left</v-icon></router-link></div>
        <div v-else class="dashboard-empty-appointment"><v-icon color="#6a8295" size="24">mdi-calendar-blank-outline</v-icon><span>فعلاً مراجعه برنامه‌ریزی‌شده‌ای ندارید.</span></div>
      </section>

      <router-link :to="{ name: 'clientWarranty' }" class="warranty-dashboard-link"><span class="warranty-dashboard-icon"><v-icon color="#1b6585" size="25">mdi-shield-check-outline</v-icon></span><span class="warranty-dashboard-copy"><strong>گارانتی و تعمیرات</strong><small>پوشش قطعات، درخواست بررسی و وضعیت تعمیر را دنبال کنید.</small></span><v-icon color="#35718c" size="20">mdi-chevron-left</v-icon></router-link>
      <router-link :to="{ name: 'clientSupport' }" class="warranty-dashboard-link support-dashboard-link"><span class="warranty-dashboard-icon"><v-icon color="#1b6585" size="25">mdi-lifebuoy</v-icon></span><span class="warranty-dashboard-copy"><strong>پشتیبانی و گفتگو</strong><small>موضوع خود را مطرح کنید و پاسخ را همین‌جا ببینید.</small></span><v-icon color="#35718c" size="20">mdi-chevron-left</v-icon></router-link>
      <router-link :to="{ name: 'qrCodeScanner' }" class="warranty-dashboard-link payment-dashboard-link"><span class="warranty-dashboard-icon"><v-icon color="#1b6585" size="25">mdi-qrcode-scan</v-icon></span><span class="warranty-dashboard-copy"><strong>پرداخت فاکتور</strong><small>کد فاکتور نیروی اجرایی را اسکن و اطلاعات آن را پیش از پرداخت بررسی کنید.</small></span><v-icon color="#35718c" size="20">mdi-chevron-left</v-icon></router-link>
      <router-link :to="{ name: 'wallet' }" class="warranty-dashboard-link wallet-dashboard-link"><span class="warranty-dashboard-icon"><v-icon color="#1b6585" size="25">mdi-wallet-outline</v-icon></span><span class="warranty-dashboard-copy"><strong>کیف پول و مانده‌ها</strong><small>مانده‌های ثبت‌شده حساب و راه اسکن فاکتور را ببینید.</small></span><v-icon color="#35718c" size="20">mdi-chevron-left</v-icon></router-link>

      <section class="dashboard-section" aria-labelledby="recent-heading">
        <div class="section-title-row"><div><span class="section-eyebrow">پیگیری آسان</span><h2 id="recent-heading">آخرین فعالیت‌ها</h2></div><router-link :to="{ name: 'clientVisits' }" class="section-link">همه سوابق <v-icon size="18">mdi-chevron-left</v-icon></router-link></div>
        <EmptyState v-if="!dashboard.recent_visits.length" kind="visits" size="sm" title="هنوز درخواستی ثبت نشده" description="از یک ساختمان شروع کنید." />
        <router-link v-for="visit in dashboard.recent_visits" :key="visit.id" :to="{ name: 'clientVisitDetail', params: { id: visit.id } }" class="recent-card"><span class="recent-icon"><v-icon size="20">mdi-file-document-outline</v-icon></span><span class="recent-copy"><strong>{{ visit.type_name || 'درخواست خدمت' }}</strong><small>{{ visit.building_name || 'ساختمان' }} · {{ date(visit.datetime_created) }}</small></span><span class="recent-status" :class="statusClass(visit)">{{ statusLabel(visit) }}</span></router-link>
      </section>

      <section ref="buildingsSection" class="dashboard-section buildings-section" aria-labelledby="buildings-heading">
        <div class="section-title-row"><div><span class="section-eyebrow">دارایی‌های شما</span><h2 id="buildings-heading">ساختمان‌ها</h2></div><span class="section-count">{{ number(dashboard.counts.buildings) }} ساختمان</span></div>
        <p class="buildings-intro">برای دیدن آسانسورها یا ثبت درخواست، ساختمان را باز کنید.</p>
        <v-text-field ref="searchField" v-model="search" label="جستجوی نام، کد یا آدرس ساختمان" prepend-inner-icon="mdi-magnify" outlined dense clearable hide-details class="field-search dashboard-search" />
        <v-alert v-if="buildingsError" type="error" outlined role="alert">{{ buildingsError }} <v-btn text color="error" @click="loadBuildings(true)">تلاش دوباره</v-btn></v-alert>
        <v-skeleton-loader v-if="buildingsLoading && !visibleBuildings.length" type="list-item-three-line, list-item-three-line" />
        <EmptyState v-else-if="!visibleBuildings.length && !buildingsError" kind="building" size="sm"
                   :title="search ? 'ساختمانی پیدا نشد' : 'ساختمانی متصل نیست'"
                   :description="search ? 'ساختمانی با این عبارت پیدا نشد.' : 'هنوز ساختمانی به حساب شما متصل نشده است.'" />
        <div class="building-grid"><router-link v-for="building in visibleBuildings" :key="building.id" :to="{ name: 'buildingDetail', params: { id: building.id } }" class="dashboard-building-card"><div class="building-card-top"><span class="building-symbol"><v-icon color="#19537b" size="23">mdi-office-building-outline</v-icon></span><span class="building-id">{{ building.code || 'کد ' + building.id }}</span></div><strong>{{ building.verbose_name || building.name || 'ساختمان' }}</strong><span class="building-address"><v-icon size="15">mdi-map-marker-outline</v-icon>{{ building.address || 'آدرس ثبت نشده' }}</span><div class="building-card-footer"><span><v-icon size="17">mdi-elevator</v-icon>{{ number(building.elevator_count != null ? building.elevator_count : (building.elevators || []).length) }} آسانسور</span><span class="building-open">مشاهده <v-icon size="18">mdi-arrow-left</v-icon></span></div></router-link></div>
        <button v-if="!showAll && dashboard.counts.buildings > dashboard.buildings.length" class="show-more-buildings" type="button" @click="showAllBuildings">نمایش همه ساختمان‌ها <v-icon size="19">mdi-chevron-down</v-icon></button>
        <button v-if="showAll && hasMore" class="show-more-buildings" type="button" :disabled="buildingsLoading" @click="loadBuildings(false)">{{ buildingsLoading ? 'در حال دریافت...' : 'ساختمان‌های بیشتر' }} <v-icon size="19">mdi-chevron-down</v-icon></button>
      </section>
    </template>
  </main>
</template>

<script>
import { pageRows, errorMessage } from '@/utils/clientRequests';

import EmptyState from '@/components/EmptyState/index.vue';
export default {
  components: { EmptyState },
  name: 'ClientDashboard',
  data: () => ({ dashboard: null, dashboardLoading: false, dashboardProject: null, dashboardSequence: 0, dashboardError: '', buildings: [], buildingsLoading: false, buildingsError: '', search: '', showAll: false, offset: 0, hasMore: false, sequence: 0, timer: null, online: true }),
  computed: {
    project() { return this.$STORE.state.userConfig.selectedProject; },
    membership() { return this.$STORE.state.userConfig.userInfo || {}; },
    firstName() { return (this.membership.user && this.membership.user.first_name) || ''; },
    projectName() { const project = this.membership.project || {}; return project.name_fa || project.name || 'خدمات آسانسور'; },
    visibleBuildings() { return this.showAll ? this.buildings : ((this.dashboard && this.dashboard.buildings) || []); }
  },
  mounted() { this.online = navigator.onLine; window.addEventListener('online', this.onOnline); window.addEventListener('offline', this.onOffline); this.loadDashboard(); },
  beforeDestroy() { clearTimeout(this.timer); this.sequence++; this.dashboardSequence++; window.removeEventListener('online', this.onOnline); window.removeEventListener('offline', this.onOffline); },
  watch: {
    project() {
      clearTimeout(this.timer);
      this.dashboardSequence++; this.sequence++;
      this.dashboard = null; this.dashboardProject = null; this.dashboardLoading = false; this.dashboardError = '';
      this.showAll = false; this.search = ''; this.buildings = []; this.buildingsLoading = false;
      this.buildingsError = ''; this.offset = 0; this.hasMore = false;
      this.loadDashboard();
    },
    search(value) {
      clearTimeout(this.timer); this.sequence++;
      if (!this.project || (!this.showAll && !value)) return;
      this.showAll = true; this.buildings = []; this.buildingsLoading = true;
      this.timer = setTimeout(() => this.loadBuildings(true), 320);
    }
  },
  methods: {
    number(value) { return Number(value || 0).toLocaleString('fa-IR'); },
    date(value) { if (!value) return 'نامشخص'; const parsed = new Date(value); return Number.isNaN(parsed.getTime()) ? 'نامشخص' : parsed.toLocaleDateString('fa-IR', { year: 'numeric', month: 'long', day: 'numeric' }); },
    statusLabel(visit) { return visit.is_pending_request ? 'در انتظار بررسی' : ({ '0': 'در انتظار مراجعه', '1': 'در حال انجام', '2': 'انجام شده', '3': 'تأیید شده', '4': 'رد شده', '5': 'در حال اصلاح گزارش', '6': 'متوقف شده' }[visit.status] || 'در حال پیگیری'); },
    statusClass(visit) { return visit.is_pending_request ? 'status-pending' : ({ '2': 'status-done', '3': 'status-done', '4': 'status-error', '6': 'status-error' }[visit.status] || 'status-active'); },
    onOnline() { this.online = true; this.loadDashboard(); },
    onOffline() { this.online = false; },
    async loadDashboard() {
      if (!this.project || (this.dashboardLoading && this.dashboardProject === this.project)) return;
      const project = this.project;
      const sequence = ++this.dashboardSequence;
      this.dashboardProject = project;
      this.dashboardLoading = true; this.dashboardError = '';
      try {
        const response = await this.$ApiServiceLayer.get('core/api/client/dashboard/?p=' + project);
        if (sequence !== this.dashboardSequence || project !== this.project) return;
        if (response.status !== 200) { this.dashboardError = errorMessage(response); return; }
        this.dashboard = response.data;
      } catch (error) { if (sequence === this.dashboardSequence && project === this.project) this.dashboardError = 'دریافت داشبورد ممکن نشد. دوباره تلاش کنید.'; }
      finally { if (sequence === this.dashboardSequence && project === this.project) this.dashboardLoading = false; }
    },
    startRequest() {
      if (!this.online || !this.dashboard || !this.dashboard.counts.buildings) return;
      if (this.dashboard.counts.buildings === 1 && this.dashboard.buildings.length) { this.$router.push({ name: 'buildingDetail', params: { id: this.dashboard.buildings[0].id } }); return; }
      this.$refs.buildingsSection.scrollIntoView({ behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth', block: 'start' });
      this.$nextTick(() => this.$refs.searchField.focus());
    },
    showAllBuildings() { this.showAll = true; this.loadBuildings(true); },
    async loadBuildings(reset) {
      if (!this.project) return;
      if (this.buildingsLoading && !reset) return;
      const project = this.project;
      const sequence = ++this.sequence;
      if (reset) { this.offset = 0; this.buildings = []; this.hasMore = false; }
      this.buildingsLoading = true; this.buildingsError = '';
      try {
        const query = new URLSearchParams({ p: project, me: 'true', limit: 12, offset: this.offset, ordering: 'building__id', search: this.search || '' });
        const response = await this.$ApiServiceLayer.get(this.$PATH.RELATIVE_PATH.MULTI.BUILDING_CLIENT_LIST_CREATE + '?' + query);
        if (sequence !== this.sequence || project !== this.project) return;
        if (response.status !== 200) { this.buildingsError = errorMessage(response); return; }
        const rows = pageRows(response.data); const byId = new Map(this.buildings.map(building => [building.id, building]));
        rows.forEach(row => { if (row.building) byId.set(row.building.id, row.building); });
        this.buildings = Array.from(byId.values()); this.offset += rows.length; this.hasMore = !!response.data.next;
      } catch (error) { if (sequence === this.sequence && project === this.project) this.buildingsError = 'دریافت ساختمان‌ها ممکن نشد.'; }
      finally { if (sequence === this.sequence && project === this.project) this.buildingsLoading = false; }
    }
  }
};
</script>

<style scoped>
.client-dashboard { padding: 0 0 calc(112px + env(safe-area-inset-bottom)); background: #f5f8fb; color: #123047; }
.dashboard-offline { padding: 9px 20px; background: #fff5df; color: #68460b; font-size: 13px; display: flex; gap: 8px; align-items: center; }
.dashboard-hero { position: relative; overflow: hidden; min-height: 302px; padding: calc(22px + env(safe-area-inset-top)) 22px 26px; background: linear-gradient(138deg, #0d2d45 4%, #17547a 68%, #1d7190); color: #fff; border-radius: 0 0 30px 30px; box-shadow: 0 14px 32px #123b5424; }
.hero-pattern { position: absolute; inset: 0; pointer-events: none; background: radial-gradient(circle at 85% 25%, #ffffff18 0 70px, transparent 72px), radial-gradient(circle at 78% 78%, #76c4d522 0 112px, transparent 114px); }
.hero-topline,.hero-top-actions,.hero-brand,.hero-account,.hero-action,.section-title-row,.appointment-card,.recent-card,.building-card-top,.building-card-footer,.building-card-footer span,.section-link,.overdue-banner,.building-address { display: flex; align-items: center; }
.hero-topline { justify-content: space-between; position: relative; }.hero-top-actions { gap: 8px; }.hero-brand { gap: 9px; font-weight: 800; font-size: 16px; }.brand-mark { width: 34px; height: 34px; display: grid; place-items: center; border: 1px solid #ffffff60; border-radius: 11px; background: #ffffff1c; }.hero-account { width: 44px; height: 44px; justify-content: center; border: 1px solid #ffffff70; border-radius: 14px; background: #ffffff12; }
.hero-copy { position: relative; margin: 25px 0 23px; }.hero-eyebrow { color: #bce6f0; font-size: 13px; font-weight: 600; }.hero-copy h1 { color: #fff; font-size: 29px; line-height: 1.45; margin: 3px 0 5px; }.hero-dot { color: #b8e89b; }.hero-copy p { color: #e4f2f5; font-size: 14px; line-height: 1.75; margin: 0; max-width: 350px; }
.hero-action { position: relative; width: 100%; min-height: 58px; gap: 12px; background: #d7f5ba; border: 0; border-radius: 16px; color: #123450; font-weight: 800; font-size: 15px; padding: 8px 10px 8px 16px; cursor: pointer; box-shadow: 0 7px 18px #001a2733; }.hero-action:hover { background: #e5ffcf; }.hero-action:active { background: #c8eaa9; }.hero-action:disabled { opacity: .55; cursor: default; }.hero-action-icon { width: 38px; height: 38px; display: grid; place-items: center; border-radius: 11px; background: #ffffff8a; }.hero-action-arrow { margin-right: auto; color: #123450 !important; }.hero-footnote { display: block; position: relative; color: #d4eaf1; font-size: 11px; margin-top: 10px; }
.dashboard-section { padding: 0 20px; margin-top: 30px; }.dashboard-loading,.dashboard-error { margin: 24px 20px; }.dashboard-notice { margin: 18px 20px 0; font-size: 12px; color: #7a4800; }.dashboard-notice button { text-decoration: underline; }.section-title-row { justify-content: space-between; gap: 12px; margin-bottom: 15px; }.section-eyebrow { color: #286b82; font-size: 12px; font-weight: 700; }.section-title-row h2 { font-size: 18px; line-height: 1.45; color: #123047; margin: 3px 0 0; }.refresh-button { width: 44px; height: 44px; color: #25536c; background: #fff; border: 1px solid #dde9ef; border-radius: 13px; }
.metric-grid { display: grid; grid-template-columns: repeat(2,minmax(0,1fr)); gap: 11px; }.metric-card { display: flex; flex-direction: column; align-items: flex-start; min-height: 138px; gap: 1px; border: 1px solid #e1eaf0; border-radius: 18px; padding: 15px; background: #fff; box-shadow: 0 4px 18px #1c42620a; color: #123047; text-decoration: none; }.metric-card strong { font-size: 29px; line-height: 1.15; margin-top: 8px; color: #123047; }.metric-card > span:last-child { font-size: 13px; color: #506879; }.metric-icon { width: 36px; height: 36px; border-radius: 11px; display: grid; place-items: center; background: #e5f3ed; color: #146b55; }.metric-icon .v-icon { color: inherit; }.metric-primary { background: #e9f5ee; border-color: #d2e8da; }.metric-amber { color: #946417; background: #fff2d9; }.metric-blue { color: #245d8c; background: #e4f1fc; }.metric-link:hover,.dashboard-building-card:hover,.recent-card:hover { border-color: #8db7ce; box-shadow: 0 8px 22px #1c426216; }.metric-link:active,.dashboard-building-card:active,.recent-card:active { background: #f0f8fb; }
.overdue-banner { gap: 8px; min-height: 45px; margin-top: 12px; padding: 8px 12px; color: #8b3d17; background: #fff0e9; border: 1px solid #f3d3c6; border-radius: 12px; font-size: 12px; text-decoration: none; }.overdue-banner span { flex: 1; }.appointment-card { gap: 13px; padding: 16px; border-radius: 18px; background: #e8f3f4; border: 1px solid #cae2e7; }.appointment-icon { width: 46px; height: 46px; flex: none; display: grid; place-items: center; background: #fff; border-radius: 14px; }.appointment-copy { flex: 1; min-width: 0; display: grid; gap: 2px; }.appointment-copy strong { font-size: 15px; }.appointment-copy span { color: #435e70; font-size: 13px; }.appointment-copy small { font-size: 12px; color: #245b73; }.appointment-link { width: 44px; height: 44px; display: grid; place-items: center; color: #245b73; }.dashboard-empty-appointment { display: flex; align-items: center; gap: 11px; min-height: 66px; padding: 15px; color: #4e697b; border: 1px dashed #c7d9e3; background: #fff; border-radius: 16px; font-size: 13px; }
.section-link { color: #216888; font-size: 12px; font-weight: 700; text-decoration: none; white-space: nowrap; }.section-count { color: #507083; font-size: 12px; }.dashboard-empty { text-align: center; padding: 25px 18px; background: #fff; border: 1px dashed #d1e0e8; border-radius: 17px; }.dashboard-empty p { font-size: 13px; color: #526d7d; margin: 7px 0 0; }.recent-card { gap: 10px; min-height: 75px; padding: 11px 13px; margin-bottom: 9px; background: #fff; border: 1px solid #e0eaf0; border-radius: 15px; color: #123047; text-decoration: none; }.recent-icon { width: 36px; height: 36px; flex: none; display: grid; place-items: center; border-radius: 11px; background: #edf5f8; color: #2f7292; }.recent-icon .v-icon { color: inherit; }.recent-copy { display: grid; gap: 2px; flex: 1; min-width: 0; }.recent-copy strong { font-size: 13px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }.recent-copy small { font-size: 11px; color: #617689; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }.recent-status { font-size: 10px; padding: 5px 7px; border-radius: 8px; white-space: nowrap; }.status-pending { color: #805514; background: #fff2d9; }.status-active { color: #1a5d8b; background: #e5f2fc; }.status-done { color: #166049; background: #e3f4ec; }.status-error { color: #8f3c38; background: #fbeae8; }
.warranty-dashboard-link { display: flex; align-items: center; gap: 12px; margin: 27px 20px 0; padding: 16px; color: #173f58; background: #e9f4f5; border: 1px solid #cce2e8; border-radius: 17px; text-decoration: none; }.warranty-dashboard-icon { width: 43px; height: 43px; flex: none; display: grid; place-items: center; background: #fff; border-radius: 12px; }.warranty-dashboard-copy { flex: 1; display: grid; gap: 3px; }.warranty-dashboard-copy strong { font-size: 14px; }.warranty-dashboard-copy small { color: #506f81; font-size: 11px; line-height: 1.5; }
.support-dashboard-link { margin-top: 11px; background: #edf3fa; border-color: #d5e1ef; }
.payment-dashboard-link { margin-top: 11px; background: #f4f6e9; border-color: #e3e9c6; }
.wallet-dashboard-link { margin-top: 11px; background: #eaf5f3; border-color: #d0e7e0; }
.buildings-intro { font-size: 13px; color: #526b7d; margin: -6px 0 15px; }.dashboard-search { margin-bottom: 15px !important; }.building-grid { display: grid; gap: 11px; }.dashboard-building-card { display: block; padding: 16px; color: #123047; background: #fff; border: 1px solid #e0eaf0; border-radius: 18px; text-decoration: none; box-shadow: 0 3px 14px #1c42620a; }.building-card-top { gap: 8px; justify-content: space-between; margin-bottom: 12px; }.building-symbol { width: 41px; height: 41px; display: grid; place-items: center; border-radius: 13px; background: #e9f4f7; }.building-id { color: #688093; font-size: 11px; direction: ltr; unicode-bidi: isolate; }.dashboard-building-card > strong { display: block; font-size: 16px; line-height: 1.5; }.building-address { gap: 3px; color: #607789; font-size: 12px; margin: 8px 0 16px; min-height: 20px; }.building-card-footer { justify-content: space-between; border-top: 1px solid #edf2f5; padding-top: 11px; font-size: 12px; color: #526c7e; }.building-card-footer span { gap: 4px; }.building-open { color: #206f8f; font-weight: 700; }.show-more-buildings { width: 100%; min-height: 46px; display: flex; align-items: center; justify-content: center; gap: 5px; margin-top: 13px; border: 1px solid #b8d3df; border-radius: 13px; color: #245e78; background: #fff; font-size: 13px; font-weight: 700; }
.client-dashboard a:focus-visible,.client-dashboard button:focus-visible { outline: 3px solid #3094bd; outline-offset: 3px; }.client-dashboard a,.client-dashboard button { transition: background-color .18s ease,border-color .18s ease,box-shadow .18s ease; }
@media (max-width: 350px) { .dashboard-section { padding: 0 14px; }.dashboard-hero { padding-left: 16px; padding-right: 16px; }.metric-card { padding: 12px; }.recent-card { flex-wrap: wrap; }.recent-status { margin-right: 46px; } }
@media (prefers-reduced-motion: reduce) { .client-dashboard a,.client-dashboard button { transition: none; } }
</style>
