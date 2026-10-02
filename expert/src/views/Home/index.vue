<template>
  <main class="field-page expert-home" dir="rtl">
    <header class="expert-hero">
      <div class="expert-hero-top"><span class="expert-brand"><span class="expert-brand-icon"><v-icon color="white" size="19">mdi-elevator</v-icon></span>سان اپ <small>پنل کارشناس</small></span><span class="expert-top-actions"><router-link :to="{ name: 'notif' }" class="expert-account" aria-label="اعلان‌ها"><v-icon color="white" size="20">mdi-bell-outline</v-icon></router-link><router-link :to="{ name: 'setting' }" class="expert-account" aria-label="حساب کاربری"><v-icon color="white" size="20">mdi-account-outline</v-icon></router-link></span></div>
      <span class="expert-project">{{ projectName }}</span>
      <h1>مأموریت‌های شما</h1>
      <p>کارهای امروز، عقب‌افتاده و برنامه‌های آینده را همین‌جا دنبال کنید.</p>
      <div class="expert-hero-count"><v-icon color="#d9efff" size="20">mdi-clipboard-check-outline</v-icon><strong>{{ number(count) }}</strong><span>مأموریت باز</span></div>
    </header>

    <section class="expert-main" aria-labelledby="visits-heading">
      <div class="expert-section-heading"><div><span>برنامه کاری</span><h2 id="visits-heading">لیست مأموریت‌ها</h2></div><button type="button" :disabled="loading" aria-label="به‌روزرسانی مأموریت‌ها" class="expert-refresh" @click="load(true)"><v-icon size="20">mdi-refresh</v-icon></button></div>
      <v-text-field v-model="search" label="جستجوی نام یا آدرس ساختمان" prepend-inner-icon="mdi-magnify" clearable outlined dense hide-details class="expert-search" />
      <div class="expert-filters" role="group" aria-label="فیلتر زمان مأموریت">
        <button v-for="item in filters" :key="item.value" type="button" class="expert-filter" :class="{ selected: schedule === item.value }" :aria-pressed="schedule === item.value ? 'true' : 'false'" @click="schedule = item.value">{{ item.title }}</button>
      </div>
      <v-alert v-if="error" type="error" outlined role="alert">{{ error }}<v-btn text color="error" @click="load(true)">تلاش دوباره</v-btn></v-alert>
      <v-skeleton-loader v-if="loading && !loaded" type="article, article" />
      <div v-else-if="loaded && !visits.length && !error" class="expert-empty"><v-icon color="#5281a0" size="36">mdi-clipboard-text-clock-outline</v-icon><h3>{{ search ? 'مأموریتی پیدا نشد' : 'در این بازه مأموریتی ندارید' }}</h3><p>{{ search ? 'عبارت جستجو را تغییر دهید.' : 'مأموریت‌های جدید پس از برنامه‌ریزی شرکت اینجا نمایش داده می‌شوند.' }}</p></div>
      <div class="expert-visit-list">
        <router-link v-for="visit in visits" :key="visit.id" :to="{ name: 'storeDetail', params: { id: visit.id } }" class="expert-visit-card">
          <div class="expert-card-head"><span class="expert-card-icon"><v-icon color="#225e86" size="23">mdi-office-building-outline</v-icon></span><div class="expert-card-title"><h3>{{ visit.building && (visit.building.verbose_name || visit.building.name) || 'ساختمان' }}</h3><span>{{ visit.building && visit.building.code || 'کد ' + visit.id }}</span></div><span class="expert-status" :class="statusClass(visit)">{{ statusLabel(visit) }}</span></div>
          <p class="expert-address"><v-icon size="17">mdi-map-marker-outline</v-icon>{{ visit.building && visit.building.address || 'آدرس ثبت نشده' }}</p>
          <div class="expert-card-meta"><span><v-icon size="17">mdi-calendar-outline</v-icon>{{ dueLabel(visit) }}</span><span><v-icon size="17">mdi-tools</v-icon>{{ visit.type && (visit.type.verbose_name || visit.type.title) || 'ویزیت' }}</span></div>
          <div class="expert-card-action"><span>{{ visit.status === '1' ? 'ادامه ویزیت' : 'مشاهده و شروع' }}</span><v-icon size="20">mdi-arrow-left</v-icon></div>
        </router-link>
      </div>
      <button v-if="hasMore && visits.length" type="button" class="expert-more" :disabled="loading" @click="load(false)">{{ loading ? 'در حال دریافت...' : 'نمایش مأموریت‌های بیشتر' }}<v-icon size="19">mdi-chevron-down</v-icon></button>
    </section>
  </main>
</template>

<script>
import { pageRows, errorMessage } from '@/utils/clientRequests';

export default {
  name: 'ExpertHome',
  data: () => ({
    visits: [], count: 0, loading: false, loaded: false, error: '', offset: 0, hasMore: false, activeKey: '',
    search: '', schedule: 'all', sequence: 0, timer: null,
    filters: [
      { value: 'all', title: 'همه' }, { value: 'today', title: 'امروز' },
      { value: 'overdue', title: 'عقب‌افتاده' }, { value: 'upcoming', title: 'آینده' },
      { value: 'unscheduled', title: 'بدون موعد' },
    ],
  }),
  computed: {
    project() { return this.$STORE.state.userConfig.selectedProject; },
    projectName() { const membership = this.$STORE.state.userConfig.userInfo || {}; const project = membership.project || {}; return project.name_fa || project.name || 'خدمات آسانسور'; },
  },
  mounted() { this.load(true); },
  beforeDestroy() { clearTimeout(this.timer); this.sequence++; },
  watch: {
    project() { this.sequence++; this.visits = []; this.loaded = false; this.count = 0; this.activeKey = ''; this.load(true); },
    schedule() { this.load(true); },
    search() { clearTimeout(this.timer); this.sequence++; this.visits = []; this.loaded = false; this.timer = setTimeout(() => this.load(true), 320); },
  },
  methods: {
    number(value) { return Number(value || 0).toLocaleString('fa-IR'); },
    date(value) { if (!value) return 'بدون موعد'; const parsed = new Date(value); return Number.isNaN(parsed.getTime()) ? 'بدون موعد' : parsed.toLocaleDateString('fa-IR', { year: 'numeric', month: 'long', day: 'numeric' }); },
    dueLabel(visit) { return visit.has_due_date && visit.due_date ? this.date(visit.due_date) : 'بدون موعد مشخص'; },
    statusLabel(visit) { return ({ '0': 'آماده شروع', '1': 'در حال انجام', '5': 'مراجعه مجدد', '6': 'متوقف شده' }[visit.status] || 'در انتظار'); },
    statusClass(visit) { return ({ '1': 'expert-in-progress', '5': 'expert-retry', '6': 'expert-suspended' }[visit.status] || 'expert-ready'); },
    async load(reset) {
      if (this.loading && !reset) return;
      const sequence = ++this.sequence;
      const key = [this.project, this.schedule, String(this.search || '').trim()].join('|');
      if (reset && key !== this.activeKey) { this.activeKey = key; this.offset = 0; this.visits = []; this.loaded = false; this.hasMore = false; this.count = 0; }
      const offset = reset ? 0 : this.offset;
      this.loading = true; this.error = '';
      try {
        const query = new URLSearchParams({ p: this.project, offset, limit: 10, search: this.search || '' });
        if (this.schedule !== 'all') query.set('schedule', this.schedule);
        const response = await this.$ApiServiceLayer.get(this.$PATH.RELATIVE_PATH.GET.VISIT_LIST + '?' + query, this.$PATH.SERVICE_NAME.AUTH);
        if (sequence !== this.sequence) return;
        if (response.status !== 200) { this.error = errorMessage(response); return; }
        const rows = pageRows(response.data);
        this.visits = reset ? rows : [...this.visits, ...rows];
        this.offset = offset + rows.length;
        this.count = Array.isArray(response.data) ? rows.length : response.data.count;
        this.hasMore = !!response.data.next;
        this.loaded = true;
      } catch (error) { if (sequence === this.sequence) this.error = 'دریافت مأموریت‌ها ممکن نشد. دوباره تلاش کنید.'; }
      finally { if (sequence === this.sequence) this.loading = false; }
    },
  },
};
</script>

<style scoped>
.expert-home { padding: 0 0 calc(110px + env(safe-area-inset-bottom)); background: #f4f8fb; color: #15364f; }
.expert-hero { padding: calc(24px + env(safe-area-inset-top)) 20px 25px; color: #fff; background: linear-gradient(140deg,#102f4d,#1d608b); border-radius: 0 0 28px 28px; box-shadow: 0 12px 27px #10395726; }
.expert-hero-top,.expert-top-actions,.expert-brand,.expert-account,.expert-hero-count,.expert-section-heading,.expert-card-head,.expert-card-meta,.expert-card-meta span,.expert-card-action,.expert-address,.expert-more { display: flex; align-items: center; }
.expert-hero-top { justify-content: space-between; }.expert-top-actions { gap: 8px; }.expert-brand { gap: 8px; font-size: 16px; font-weight: 800; }.expert-brand small { color: #cae8f7; font-size: 11px; font-weight: 500; }.expert-brand-icon { width: 34px; height: 34px; display: grid; place-items: center; border: 1px solid #ffffff75; border-radius: 11px; background: #ffffff1b; }.expert-account { justify-content: center; width: 44px; height: 44px; border-radius: 14px; border: 1px solid #ffffff75; }.expert-project { display: block; margin-top: 23px; color: #bde1f1; font-size: 13px; }.expert-hero h1 { color: #fff; font-size: 28px; margin: 4px 0 5px; }.expert-hero p { font-size: 13px; line-height: 1.7; color: #e1f1f7; margin: 0; }.expert-hero-count { width: fit-content; gap: 7px; margin-top: 20px; padding: 9px 13px; background: #ffffff20; border: 1px solid #ffffff3a; border-radius: 12px; font-size: 12px; }.expert-hero-count strong { font-size: 17px; }
.expert-main { padding: 27px 20px 0; }.expert-section-heading { justify-content: space-between; margin-bottom: 14px; }.expert-section-heading span { font-size: 12px; font-weight: 700; color: #337793; }.expert-section-heading h2 { color: #15364f; font-size: 19px; margin: 3px 0 0; }.expert-refresh { width: 44px; height: 44px; color: #285c78; background: #fff; border: 1px solid #dce9f0; border-radius: 13px; }.expert-search { background: #fff; border-radius: 13px; }.expert-filters { display: flex; gap: 8px; overflow-x: auto; padding: 11px 0 16px; scrollbar-width: none; }.expert-filters::-webkit-scrollbar { display: none; }.expert-filter { min-height: 44px; white-space: nowrap; padding: 7px 15px; border: 1px solid #cddfe8; border-radius: 11px; color: #345d74; background: #fff; font-size: 12px; font-weight: 700; }.expert-filter.selected { background: #1d5e86; border-color: #1d5e86; color: #fff; }
.expert-visit-list { display: grid; gap: 12px; }.expert-visit-card { display: block; padding: 16px; background: #fff; border: 1px solid #e0eaf0; border-radius: 18px; color: #15364f; text-decoration: none; box-shadow: 0 4px 15px #1c42620a; }.expert-visit-card:hover { border-color: #86b4cf; box-shadow: 0 8px 23px #1c426218; }.expert-card-head { gap: 10px; }.expert-card-icon { display: grid; place-items: center; flex: none; width: 44px; height: 44px; border-radius: 13px; background: #e8f3f8; }.expert-card-title { flex: 1; min-width: 0; }.expert-card-title h3 { color: #15364f; font-size: 15px; line-height: 1.45; margin: 0; }.expert-card-title span { display: block; color: #657f90; font-size: 11px; direction: ltr; unicode-bidi: isolate; text-align: right; }.expert-status { white-space: nowrap; padding: 5px 8px; border-radius: 8px; font-size: 10px; font-weight: 700; }.expert-ready { color: #195b86; background: #e6f3fd; }.expert-in-progress { color: #8a5814; background: #fff1d9; }.expert-retry { color: #7b4f1d; background: #fff2df; }.expert-suspended { color: #8d3c39; background: #fbeae8; }.expert-address { gap: 5px; color: #526f81; font-size: 12px; margin: 14px 0; }.expert-card-meta { flex-wrap: wrap; gap: 8px 15px; color: #45677d; font-size: 12px; }.expert-card-meta span { gap: 4px; }.expert-card-action { justify-content: space-between; margin-top: 14px; padding-top: 12px; border-top: 1px solid #edf2f5; color: #22698b; font-size: 13px; font-weight: 700; }
.expert-empty { padding: 37px 17px; text-align: center; border: 1px dashed #d1e2ec; border-radius: 17px; background: #fff; }.expert-empty h3 { font-size: 17px; margin: 9px 0 3px; }.expert-empty p { color: #5d788a; font-size: 13px; margin: 0; }.expert-more { width: 100%; min-height: 46px; justify-content: center; gap: 5px; margin-top: 17px; border: 1px solid #b7d3e0; background: #fff; border-radius: 12px; color: #285e7b; font-size: 13px; font-weight: 700; }
.expert-home a:focus-visible,.expert-home button:focus-visible { outline: 3px solid #328fbc; outline-offset: 3px; }.expert-home a,.expert-home button { transition: background-color .18s ease,border-color .18s ease,box-shadow .18s ease; }@media(max-width:350px){.expert-main{padding-left:14px;padding-right:14px}.expert-hero{padding-left:16px;padding-right:16px}.expert-visit-card{padding:13px}.expert-card-head{flex-wrap:wrap}.expert-status{margin-right:54px}}@media(prefers-reduced-motion:reduce){.expert-home a,.expert-home button{transition:none}}
</style>
