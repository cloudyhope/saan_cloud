<template>
  <main class="vf-page history-page" dir="rtl">
    <VisitTopBar title="سوابق مأموریت‌ها" eyebrow="گزارش‌های ثبت‌شده" :fallback="{ name: 'setting' }"
                 subtitle="گزارش‌های پایان‌یافته، تأییدشده، ردشده و برگشتی را اینجا ببینید." />
    <div class="vf-body">
      <section class="vf-card earnings-card" aria-labelledby="earnings-heading">
        <div class="vf-card-title"><h2 id="earnings-heading">دستمزد مأموریت‌ها</h2>
          <select v-model="period" class="earnings-period" aria-label="بازه دستمزد">
            <option v-for="item in periods" :key="item.value" :value="item.value">{{ item.title }}</option>
          </select></div>
        <p v-if="earningsError" class="vf-muted">{{ earningsError }}</p>
        <div v-else class="earnings-grid" :class="{ loading: !earnings }">
          <div class="earning is-earned"><span>تأییدشده</span><strong>{{ earnings ? money(earnings.earned.wage) : '…' }}</strong>
            <small>{{ earnings ? faNumber(earnings.earned.count) + ' مأموریت' : '' }}</small></div>
          <div class="earning is-pending"><span>در انتظار بررسی</span><strong>{{ earnings ? money(earnings.pending.wage) : '…' }}</strong>
            <small>{{ earnings ? faNumber(earnings.pending.count) + ' مأموریت' : '' }}</small></div>
        </div>
        <p class="vf-muted earnings-note">فقط مأموریت‌های تأییدشده قطعی هستند؛ مأموریت ردشده دستمزد ندارد. مبالغ به ریال است.</p>
      </section>
      <div class="history-filters" role="group" aria-label="فیلتر وضعیت">
        <button v-for="item in filters" :key="item.value" type="button" class="history-filter" :class="{ selected: filter === item.value }"
                :aria-pressed="filter === item.value ? 'true' : 'false'" @click="filter = item.value">{{ item.title }}</button>
      </div>
      <div v-if="error" class="vf-banner vf-banner-danger" role="alert">
        <v-icon color="#8a2f2a">mdi-alert-circle-outline</v-icon>
        <div><strong>سوابق دریافت نشد</strong><p>{{ error }}</p>
          <button type="button" class="vf-banner-action" @click="load(true)"><v-icon size="16">mdi-refresh</v-icon>تلاش دوباره</button></div>
      </div>
      <template v-if="loading && !loaded"><v-skeleton-loader v-for="n in 3" :key="n" class="vf-skeleton" type="article" /></template>
      <EmptyState v-else-if="loaded && !shown.length && !error" kind="history"
                   :title="filter === 'all' ? 'هنوز گزارشی ثبت نکرده‌اید' : 'در این وضعیت گزارشی ندارید'"
                   :description="filter === 'all' ? 'پس از پایان اولین مأموریت، سوابق اینجا جمع می‌شوند.' : 'وضعیت دیگری را انتخاب کنید.'" />
      <router-link v-for="visit in shown" :key="visit.id" :to="{ name: 'storeDetail', params: { id: visit.id } }" class="vf-card history-card">
        <div class="history-head">
          <span class="history-icon"><v-icon color="#1d608b" size="22">mdi-office-building-outline</v-icon></span>
          <div class="history-title">
            <h2>{{ visit.building && (visit.building.verbose_name || visit.building.name) || 'ساختمان' }}</h2>
            <span>{{ typeName(visit) }} · مأموریت {{ faId(visit.id) }}</span>
          </div>
          <span class="vf-chip" :class="'vf-tone-' + status(visit).tone">{{ status(visit).label }}</span>
        </div>
        <p v-if="visit.rejection_reason && ['4', '5'].includes(visit.status)" class="history-reason">
          <v-icon size="16" :color="visit.status === '5' ? '#7a4d0f' : '#8a2f2a'">mdi-message-alert-outline</v-icon>{{ visit.rejection_reason }}
        </p>
        <div class="history-meta">
          <span><v-icon size="16">mdi-calendar-check-outline</v-icon>{{ faDate(visit.datetime_last_change) || '—' }}</span>
          <span v-if="visit.total_wage" class="history-wage" :class="{ muted: visit.status === '4' }"><v-icon size="16">mdi-cash</v-icon>{{ money(visit.total_wage) }}</span>
          <span v-if="visit.rate != null" class="history-rate"><v-icon size="16" color="#c58a12">mdi-star</v-icon>{{ faNumber(visit.rate) }}</span>
          <span class="history-open">{{ visit.status === '5' ? 'شروع اصلاح' : 'مشاهده گزارش' }}<v-icon size="17">mdi-arrow-left</v-icon></span>
        </div>
      </router-link>
      <button v-if="hasMore" type="button" class="vf-btn vf-btn-ghost vf-btn-block" :disabled="loading" @click="load(false)">
        {{ loading ? 'در حال دریافت…' : 'نمایش موارد بیشتر' }}
      </button>
    </div>
  </main>
</template>

<script>
import VisitTopBar from '@/components/Visit/VisitTopBar.vue';
import { errorMessage, pageRows } from '@/utils/clientRequests';
import { faDate, faId, faNumber, visitStatus, withProject } from '@/utils/visitFlow';

import EmptyState from '@/components/EmptyState/index.vue';
export default {
  name: 'VisitHistory',
  components: { EmptyState, VisitTopBar },
  data: () => ({
    visits: [], loading: false, loaded: false, error: '', offset: 0, hasMore: false, filter: 'all', sequence: 0,
    filters: [{ value: 'all', title: 'همه' }, { value: '5', title: 'برگشتی' }, { value: '2', title: 'در انتظار بررسی' },
      { value: '3', title: 'تأییدشده' }, { value: '4', title: 'ردشده' }],
    period: 'month', earnings: null, earningsError: '',
    periods: [{ value: 'month', title: 'این ماه' }, { value: 'last30', title: '۳۰ روز اخیر' }, { value: 'last90', title: '۹۰ روز اخیر' }],
  }),
  watch: { period() { this.loadEarnings(); } },
  computed: {
    shown() { return this.filter === 'all' ? this.visits : this.visits.filter(visit => visit.status === this.filter); },
  },
  created() { this.load(true); this.loadEarnings(); },
  beforeDestroy() { this.sequence++; },
  methods: {
    faNumber, faDate, faId,
    status(visit) { return visitStatus(visit.status); },
    money(value) { return `${faNumber(value || 0)} ریال`; },
    range() {
      const iso = date => `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
      const today = new Date();
      if (this.period === 'month') return { from: iso(new Date(today.getFullYear(), today.getMonth(), 1)), to: iso(today) };
      const days = this.period === 'last90' ? 89 : 29;
      return { from: iso(new Date(today.getTime() - days * 86400000)), to: iso(today) };
    },
    async loadEarnings() {
      this.earnings = null; this.earningsError = '';
      try {
        const response = await this.$ApiServiceLayer.get(withProject('/api/promoter/visit/earnings/', this.range()), this.$PATH.SERVICE_NAME.AUTH);
        if (response.status === 200) this.earnings = response.data;
        else this.earningsError = errorMessage(response);
      } catch (_) { this.earningsError = 'دستمزد دریافت نشد.'; }
    },
    typeName(visit) { return (visit.type && (visit.type.verbose_name || visit.type.title)) || 'خدمت'; },
    async load(reset) {
      if (this.loading && !reset) return;
      const sequence = ++this.sequence;
      const offset = reset ? 0 : this.offset;
      this.loading = true; this.error = '';
      try {
        const response = await this.$ApiServiceLayer.get(
          withProject(this.$PATH.RELATIVE_PATH.GET.GET_VISIT_HISTORY, { offset, limit: 20 }), this.$PATH.SERVICE_NAME.AUTH);
        if (sequence !== this.sequence) return;
        if (response.status !== 200) { this.error = errorMessage(response); return; }
        const rows = pageRows(response.data);
        this.visits = reset ? rows : [...this.visits, ...rows];
        this.offset = offset + rows.length;
        this.hasMore = !!(response.data && response.data.next);
        this.loaded = true;
      } catch (_) {
        if (sequence === this.sequence) this.error = 'اتصال برقرار نشد. دوباره تلاش کنید.';
      } finally {
        if (sequence === this.sequence) this.loading = false;
      }
    },
  },
};
</script>

<style scoped>
.history-filters { display: flex; gap: 8px; overflow-x: auto; scrollbar-width: none; padding-bottom: 2px; }
.history-filters::-webkit-scrollbar { display: none; }
.history-filter { min-height: 42px; white-space: nowrap; padding: 6px 14px; border: 1px solid #cddfe8; border-radius: 11px; background: #fff;
  color: #345d74; font-size: 12px; font-weight: 700; }
.history-filter.selected { background: #1d5e86; border-color: #1d5e86; color: #fff; }
.history-card { display: block; color: var(--vf-ink); text-decoration: none; }
.history-card:hover { border-color: #9cc3d8; }
.history-head { display: flex; gap: 10px; align-items: flex-start; }
.history-icon { flex: none; width: 44px; height: 44px; border-radius: 13px; display: grid; place-items: center; background: var(--vf-brand-soft); }
.history-title { flex: 1; min-width: 0; }
.history-title h2 { font-size: 14.5px; font-weight: 800; margin: 0; line-height: 1.5; }
.history-title span { color: var(--vf-muted); font-size: 11.5px; }
.history-reason { display: flex; gap: 6px; align-items: flex-start; margin: 12px 0 0; padding: 9px 11px; border-radius: 12px; background: #fff7e8;
  color: #6c4513; font-size: 12.5px; line-height: 1.8; }
.history-reason .v-icon { margin-top: 3px; flex: none; }
.history-meta { display: flex; align-items: center; flex-wrap: wrap; gap: 8px 14px; margin-top: 12px; padding-top: 11px; border-top: 1px solid #edf2f5;
  color: var(--vf-muted); font-size: 12px; }
.history-meta span { display: inline-flex; align-items: center; gap: 4px; }
.history-rate { color: #8a5f0a; font-weight: 800; }
.history-wage { color: var(--vf-ok); font-weight: 800; }
.history-wage.muted { color: var(--vf-soft); text-decoration: line-through; }
.earnings-period { min-height: 36px; padding: 4px 10px; border: 1px solid #cddfe8; border-radius: 10px; background: #fff; color: #345d74; font: inherit; font-size: 12px; }
.earnings-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.earnings-grid.loading { opacity: .6; }
.earning { display: grid; gap: 2px; padding: 12px; border-radius: 14px; }
.earning span { font-size: 11.5px; font-weight: 700; }
.earning strong { font-size: 16px; font-weight: 800; }
.earning small { font-size: 11px; opacity: .85; }
.earning.is-earned { background: var(--vf-ok-soft); color: var(--vf-ok); }
.earning.is-pending { background: #ece9fb; color: #4b3f99; }
.earnings-note { margin: 10px 2px 0; line-height: 1.8; }
.history-open { margin-inline-start: auto; color: var(--vf-brand); font-weight: 800; }
</style>
