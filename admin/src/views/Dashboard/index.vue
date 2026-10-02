<template>
  <main class="dashboard" dir="rtl">
    <header class="dash-head">
      <div class="head-copy">
        <h1>وضعیت عملیات در یک نگاه</h1>
        <p>{{ rangeLabel }}<template v-if="updatedAt"> · به‌روزرسانی {{ updatedAt }}</template></p>
      </div>
      <button type="button" class="ghost-btn" :disabled="loading" @click="load"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20 11a8 8 0 1 0-2.3 5.7M20 4v7h-7" /></svg>{{ loading ? 'در حال دریافت…' : 'به‌روزرسانی' }}</button>
    </header>

    <nav v-if="quickLinks.length" class="quick" aria-label="دسترسی سریع">
      <router-link v-for="item in quickLinks" :key="item.id" :to="item.frontend_route_url" class="quick-link">{{ item.verbose_name }}<span aria-hidden="true">←</span></router-link>
    </nav>

    <section v-if="denied" class="panel state-panel" role="note">
      <h2>داشبورد مدیریتی برای نقش شما فعال نیست</h2>
      <p>این نما برای نقش‌هایی است که کل پروژه را مدیریت می‌کنند. از «دسترسی سریع» یا منوی کناری به بخش‌های خود بروید.</p>
    </section>

    <template v-else>
      <!-- One filter row scopes everything below it. -->
      <section class="filters" aria-label="فیلترهای داشبورد">
        <div class="segmented" role="group" aria-label="بازه زمانی">
          <button v-for="item in presets" :key="item.key" type="button" :class="{ active: preset === item.key }" :aria-pressed="preset === item.key ? 'true' : 'false'" @click="setPreset(item.key)">{{ item.label }}</button>
          <button type="button" :class="{ active: preset === 'custom' }" @click="openCustom">بازه دلخواه</button>
          <input id="dashboard-range" ref="customInput" class="range-anchor" readonly tabindex="-1" aria-hidden="true" />
          <date-picker v-model="customRange" range format="YYYY-MM-DD" display-format="jYYYY/jMM/jDD" custom-input="#dashboard-range"
                       :max="today" :show="customOpen" @close="customOpen = false" @change="applyCustom" />
        </div>
        <label class="filter-field"><span>نوع خدمت</span>
          <select v-model.number="filters.type" class="form-select"><option value="">همه</option><option v-for="item in typeOptions" :key="item.key" :value="item.key">{{ item.label }}</option></select></label>
        <label class="filter-field"><span>کارشناس</span>
          <select v-model="filters.expert" class="form-select"><option value="">همه</option><option v-for="item in expertOptions" :key="item.key" :value="item.key">{{ item.label }}</option></select></label>
        <label class="filter-field"><span>اولویت</span>
          <select v-model="filters.priority" class="form-select"><option value="">همه</option><option v-for="item in priorityLevels" :key="item.key" :value="item.key">{{ item.label }}</option><option value="none">بدون امتیاز</option></select></label>
        <label class="filter-field"><span>مشتری</span>
          <select v-model.number="filters.client" class="form-select"><option value="">همه</option><option v-for="item in clientOptions" :key="item.key" :value="item.key">{{ item.label }}</option></select></label>
      </section>
      <div v-if="chips.length" class="chips" aria-live="polite">
        <span class="chips-title">فیلتر فعال:</span>
        <button v-for="chip in chips" :key="chip.key" type="button" class="chip" @click="clear(chip.key)">{{ chip.label }}<span aria-hidden="true">×</span><span class="sr-only">حذف فیلتر</span></button>
        <button type="button" class="chip-clear" @click="clearAll">پاک کردن همه</button>
      </div>

      <div v-if="error" class="error" role="alert">{{ error }} <button type="button" @click="load">تلاش دوباره</button></div>
      <p v-if="truncated" class="note">به‌دلیل حجم زیاد، فقط ۵۰۰۰ مأموریت اخیر بازه در محاسبه آمده است؛ بازه را کوتاه‌تر کنید.</p>

      <div class="dash-body" :class="{ refreshing: loading && loaded }">
        <div v-if="!loaded && loading" class="panel state-panel" role="status"><span class="spinner-border spinner-border-sm" aria-hidden="true" /> در حال دریافت داده‌ها…</div>
        <template v-if="loaded">
          <section class="kpis" aria-label="شاخص‌های کلیدی">
            <KpiTile label="ثبت‌شده در بازه" :value="fa(kpi.created)" :hint="deltaHint(kpi.created, previous.created)" :hint-tone="deltaTone(kpi.created, previous.created, true)" :icon="icons.plus" />
            <KpiTile label="پایان‌یافته در بازه" :value="fa(kpi.completed)" :hint="deltaHint(kpi.completed, previous.completed)" :hint-tone="deltaTone(kpi.completed, previous.completed, true)"
                     tone="good" :icon="icons.flag" clickable :selected="filters.status === 'completed'" @select="toggleStatus('completed')" />
            <KpiTile label="مأموریت‌های باز" :value="fa(kpi.open)" :hint="kpi.openUrgent ? fa(kpi.openUrgent) + ' کار باز با اولویت بالا یا بحرانی' : 'کار باز پراولویتی نیست'" :icon="icons.list" clickable :selected="filters.status === 'open'" @select="toggleStatus('open')" />
            <KpiTile label="دیرکرد" :value="fa(kpi.overdue)" :hint="kpi.open ? percent(kpi.overdue / kpi.open) + ' از کارهای باز' : 'کار بازی نیست'" :hint-tone="kpi.overdue ? 'bad' : 'muted'"
                     tone="critical" :icon="icons.alert" clickable :selected="filters.status === 'overdue'" @select="toggleStatus('overdue')" />
            <KpiTile label="منتظر بررسی گزارش" :value="fa(kpi.review)" :hint="kpi.returned ? fa(kpi.returned) + ' گزارش برگشتی در دست اصلاح' : 'گزارش برگشتی ندارید'" tone="warning" :icon="icons.inbox"
                     clickable :selected="filters.status === 'review'" @select="toggleStatus('review')" />
            <KpiTile label="درخواست‌های بررسی‌نشده" :value="fa(kpi.pending)" hint="درخواست کلاینت بدون برنامه" tone="serious" :icon="icons.request"
                     clickable :selected="filters.status === 'pending'" @select="toggleStatus('pending')" />
            <KpiTile label="انجام به‌موقع" :value="percent(kpi.onTime)" :hint="kpi.onTimeBase ? `از ${fa(kpi.onTimeBase)} کار پایان‌یافته دارای موعد` : 'کار موعددار پایان‌یافته‌ای نیست'"
                     :tone="kpi.onTime === null ? 'neutral' : kpi.onTime >= .8 ? 'good' : 'warning'" :icon="icons.clock" />
            <KpiTile label="رضایت مدیران ساختمان" :value="kpi.rating ? fa(kpi.rating, 1) + ' از ۵' : '—'" :hint="kpi.ratingBase ? `${fa(kpi.ratingBase)} نظر · زمان اجرا ${cycleText}` : `زمان اجرا ${cycleText}`" :icon="icons.star" />
          </section>

          <div class="grid two-one">
            <section class="panel" aria-labelledby="trend-title">
              <div class="panel-head"><div><h2 id="trend-title">روند ثبت و پایان کار</h2><p>{{ trendData.step === 1 ? 'روزانه' : 'هفتگی' }}؛ روی یک {{ trendData.step === 1 ? 'روز' : 'هفته' }} کلیک کنید تا همه نماها به آن محدود شود.</p></div></div>
              <TrendChart :points="trendData.points" :step="trendData.step" :selected="filters.day" @select="pickPoint" />
            </section>
            <section class="panel" aria-labelledby="pipeline-title">
              <div class="panel-head"><div><h2 id="pipeline-title">وضعیت مأموریت‌ها</h2><p>کارهای این بازه و کارهای باز؛ برای فیلتر کلیک کنید.</p></div></div>
              <BarList :items="pipeline" :selected="filters.status" @select="value => (filters.status = value)" />
            </section>
          </div>

          <section class="panel" aria-labelledby="gantt-title">
            <div class="panel-head"><div><h2 id="gantt-title">برنامه زمانی مأموریت‌ها</h2><p>هر ردیف یک کارشناس؛ نوار کم‌رنگ از ثبت تا موعد و نوار رنگی اجرای واقعی است. روی نوار کلیک کنید تا گزارش باز شود.</p></div>
              <button type="button" class="ghost-btn small" :aria-expanded="tableOpen ? 'true' : 'false'" @click="tableOpen = !tableOpen">{{ tableOpen ? 'بستن جدول' : 'نمایش جدول' }}</button></div>
            <GanttChart :rows="ganttRows" :range="range" :today="today" :lookups="lookups" :selected="filters.expert" @select="value => (filters.expert = value)" @open="openVisit" />
            <div v-if="tableOpen" class="table-wrap">
              <table>
                <caption class="sr-only">مأموریت‌های فیلترشده</caption>
                <thead><tr><th>شماره</th><th>اولویت</th><th>ساختمان</th><th>نوع</th><th>کارشناس</th><th>وضعیت</th><th>موعد</th><th>پایان</th></tr></thead>
                <tbody>
                  <tr v-for="visit in tableRows" :key="visit.id" @click="openVisit(visit.id)">
                    <td><router-link :to="'/visitmanagment/answerlist/' + visit.id">{{ faId(visit.id) }}</router-link></td>
                    <td><PriorityBadge :score="visit.pr" /></td>
                    <td>{{ lookups.buildings[visit.b] || '—' }}</td><td>{{ lookups.types[visit.t] || '—' }}</td>
                    <td>{{ visit.e ? lookups.experts[visit.e] : 'بدون کارشناس' }}</td>
                    <td><span class="status-dot" :style="{ background: bucket(visit).color }" />{{ bucket(visit).label }}<b v-if="late(visit)" class="late-tag">دیرکرد</b></td>
                    <td>{{ jDate(visit.du) }}</td><td>{{ jDate(visit.co) }}</td>
                  </tr>
                  <tr v-if="!tableRows.length"><td colspan="8" class="muted">مأموریتی با این فیلترها نیست.</td></tr>
                </tbody>
              </table>
              <p v-if="filtered.length > tableRows.length" class="note">{{ fa(tableRows.length) }} مورد از {{ fa(filtered.length) }} نمایش داده شد؛ <router-link to="/visitmanagment/lists">فهرست کامل ویزیت‌ها</router-link></p>
            </div>
          </section>

          <div class="grid halves">
            <section class="panel" aria-labelledby="workload-title">
              <div class="panel-head"><div><h2 id="workload-title">بار کاری کارشناسان</h2><p>مرتب بر اساس دیرکرد؛ برای فیلتر روی نام کلیک کنید.</p></div></div>
              <WorkloadBars :rows="experts" :selected="filters.expert" @select="value => (filters.expert = value)" />
            </section>
            <section class="panel" aria-labelledby="attention-title">
              <div class="panel-head"><div><h2 id="attention-title">ساختمان‌های نیازمند پیگیری</h2><p>دیرکرد، گزارش برگشتی و گزارش منتظر بررسی.</p></div></div>
              <ul class="attention">
                <li v-for="row in attentionRows" :key="row.key">
                  <button type="button" :class="{ selected: filters.building === row.key, dim: filters.building && filters.building !== row.key }"
                          :aria-pressed="filters.building === row.key ? 'true' : 'false'" @click="filters.building = filters.building === row.key ? '' : row.key">
                    <span class="attention-name"><b>{{ row.label }}</b><small>{{ row.client || 'بدون مدیر فعلی' }}</small></span>
                    <span class="attention-tags">
                      <span v-if="row.overdue" class="tag critical">{{ fa(row.overdue) }} دیرکرد</span>
                      <span v-if="row.returned" class="tag serious">{{ fa(row.returned) }} برگشتی</span>
                      <span v-if="row.review" class="tag warning">{{ fa(row.review) }} منتظر بررسی</span>
                    </span>
                  </button>
                </li>
                <li v-if="!attentionRows.length" class="empty-row"><EmptyState kind="done" size="sm" inline title="همه‌چیز مرتب است" description="ساختمانی با کار معوق یا منتظر بررسی نیست." /></li>
              </ul>
            </section>
          </div>

          <div class="grid one-two">
            <section class="panel" aria-labelledby="types-title">
              <div class="panel-head"><div><h2 id="types-title">نوع خدمت</h2><p>تعداد مأموریت‌ها در نمای فعلی.</p></div></div>
              <BarList :items="types" :selected="filters.type" @select="value => (filters.type = value)" />
            </section>
            <section class="panel" aria-labelledby="service-title">
              <div class="panel-head"><div><h2 id="service-title">پشتیبانی، گارانتی و انبار</h2><p>وضعیت فعلی پروژه؛ فقط شمار تیکت تازه به بازه وابسته است.</p></div></div>
              <div class="service-grid">
                <router-link to="/ticket/ticketlist" class="service-tile"><span>تیکت در انتظار پاسخ</span><b :class="{ alert: services.tickets.waiting }">{{ fa(services.tickets.waiting) }}</b><small>{{ fa(services.tickets.created) }} تیکت تازه در بازه</small></router-link>
                <router-link to="/service-cases" class="service-tile"><span>ادعای گارانتی در انتظار</span><b :class="{ alert: services.claims_pending }">{{ fa(services.claims_pending) }}</b><small>نیازمند تصمیم</small></router-link>
                <router-link to="/warehouse/warelist" class="service-tile"><span>کالای مصرفی ناموجود</span><b :class="{ alert: services.out_of_stock }">{{ fa(services.out_of_stock) }}</b><small>موجودی صفر یا منفی</small></router-link>
              </div>
              <h3 class="sub-title">پرونده‌های تعمیر باز</h3>
              <BarList :items="repairs" color="#4a3aa7" empty="پرونده تعمیر بازی نیست." @select="() => $router.push('/service-cases')" />
            </section>
          </div>
        </template>
      </div>

      <section v-if="iframeLink" class="panel" aria-labelledby="report-title">
        <div class="panel-head"><div><h2 id="report-title">گزارش تکمیلی پروژه</h2><p>گزارش متصل به منوی داشبورد این پروژه.</p></div>
          <button type="button" class="ghost-btn small" :aria-expanded="showReport ? 'true' : 'false'" @click="showReport = !showReport">{{ showReport ? 'بستن' : 'نمایش' }}</button></div>
        <iframe v-if="showReport" :src="iframeLink" title="گزارش تکمیلی پروژه" class="report-frame" loading="lazy" />
      </section>
    </template>
  </main>
</template>

<script>
import { normalizeMenu } from '@/utils/adminNavigation';
import { BUCKET, STATUS_FOCUS, applyFilters, attention, bucketOf, byBucket, byExpert, byType, gantt, isOverdue, kpis, presetRange, trend } from '@/utils/dashboardData';
import KpiTile from './components/KpiTile.vue';
import TrendChart from './components/TrendChart.vue';
import BarList from './components/BarList.vue';
import WorkloadBars from './components/WorkloadBars.vue';
import GanttChart from './components/GanttChart.vue';
import { fa, faId, jDate, percent } from './components/format';
import PriorityBadge from '@/components/PriorityBadge.vue';
import { PRIORITY_LEVELS, PRIORITY_LEVEL } from '@/utils/priority';

import EmptyState from '@/components/EmptyState/index.vue';
const REPAIR_LABELS = { RECEIVED: 'دریافت‌شده', DIAGNOSING: 'در حال عیب‌یابی', REPAIRING: 'در حال تعمیر', TESTING: 'در حال آزمون', READY: 'آماده تحویل' };
const ICONS = {
  plus: 'M12 5v14M5 12h14', flag: 'M5 21V4h11l-1.5 4L16 12H5', list: 'M9 6h11M9 12h11M9 18h11M4 6h.01M4 12h.01M4 18h.01',
  alert: 'M12 8v5M12 16h.01M10.3 3.9 2.6 17a2 2 0 0 0 1.7 3h15.4a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z',
  inbox: 'M4 13h4l2 3h4l2-3h4M4 13l2.5-7h11L20 13v6H4z', request: 'M8 4h8l3 3v13H5V4zM9 12h6M9 16h4M12 8v.01',
  clock: 'M12 7v5l3 2M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18z', star: 'm12 3 2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1-4.4-4.3 6.1-.9z',
};
const EMPTY_SERVICES = { tickets: { waiting: 0, answered: 0, created: 0 }, claims_pending: 0, repairs: {}, out_of_stock: 0 };
const blankFilters = () => ({ type: '', expert: '', client: '', status: '', day: '', building: '', priority: '' });
const localToday = () => new Date().toLocaleDateString('en-CA', { timeZone: 'Asia/Tehran' });

export default {
  name: 'Dashboard',
  components: { EmptyState, KpiTile, TrendChart, BarList, WorkloadBars, GanttChart, PriorityBadge },
  data: () => ({
    preset: '30', range: presetRange('30', localToday()), today: localToday(), customRange: [], customOpen: false,
    filters: blankFilters(), visits: [], lookups: { experts: {}, types: {}, buildings: {}, clients: {} }, previous: { created: 0, completed: 0 },
    services: EMPTY_SERVICES, truncated: false, loading: false, loaded: false, error: '', denied: false, updatedAt: '', sequence: 0,
    links: [], iframeLink: null, showReport: false, projectName: 'پروژه شما', tableOpen: false, icons: ICONS,
    priorityLevels: PRIORITY_LEVELS,
    presets: [{ key: '7', label: '۷ روز' }, { key: '30', label: '۳۰ روز' }, { key: '90', label: '۹۰ روز' }, { key: 'month', label: 'ماه جاری' }],
  }),
  computed: {
    project() { return this.$STORE.state.userConfig.setProjectId; },
    ctx() { return { range: this.range, today: this.today }; },
    rangeLabel() { return `${jDate(this.range.from, { year: 'numeric', month: 'long', day: 'numeric' })} تا ${jDate(this.range.to, { year: 'numeric', month: 'long', day: 'numeric' })}`; },
    filtered() { return applyFilters(this.visits, this.filters, this.ctx); },
    kpi() { return kpis(applyFilters(this.visits, this.filters, this.ctx, 'status'), this.ctx); },
    trendData() { return trend(applyFilters(this.visits, this.filters, this.ctx, 'day'), this.range); },
    pipeline() { return byBucket(applyFilters(this.visits, this.filters, this.ctx, 'status')).map(item => ({ ...item, value: item.value })); },
    experts() { return byExpert(applyFilters(this.visits, this.filters, this.ctx, 'expert'), this.ctx, this.lookups.experts); },
    ganttRows() { return gantt(applyFilters(this.visits, this.filters, this.ctx, 'expert'), this.ctx, this.lookups.experts); },
    types() { return byType(applyFilters(this.visits, this.filters, this.ctx, 'type'), this.lookups.types); },
    attentionRows() { return attention(applyFilters(this.visits, this.filters, this.ctx, 'building'), this.ctx, this.lookups.buildings, this.lookups.clients).slice(0, 7); },
    // Most sensitive work first, then the most recent.
    tableRows() { const rank = v => (v.pr === null || v.pr === undefined ? -1 : v.pr); return [...this.filtered].sort((a, b) => rank(b) - rank(a) || b.id - a.id).slice(0, 60); },
    repairs() { return Object.keys(REPAIR_LABELS).map(key => ({ key, label: REPAIR_LABELS[key], value: this.services.repairs[key] || 0 })); },
    typeOptions() { return this.options('types', 't'); },
    expertOptions() {
      const list = this.options('experts', 'e');
      return this.visits.some(v => !v.e && !v.p) ? [...list, { key: 'none', label: 'بدون کارشناس' }] : list;
    },
    clientOptions() { return this.options('clients', 'c'); },
    cycleText() { return this.kpi.cycleDays === null ? '—' : fa(this.kpi.cycleDays, 1) + ' روز'; },
    chips() {
      const f = this.filters;
      const list = [];
      if (f.status) list.push({ key: 'status', label: STATUS_FOCUS[f.status] || f.status });
      if (f.day) list.push({ key: 'day', label: 'روز ' + jDate(f.day, { month: 'long', day: 'numeric' }) });
      if (f.type) list.push({ key: 'type', label: this.lookups.types[f.type] || 'نوع خدمت' });
      if (f.expert) list.push({ key: 'expert', label: f.expert === 'none' ? 'بدون کارشناس' : this.lookups.experts[f.expert] || 'کارشناس' });
      if (f.client) list.push({ key: 'client', label: this.lookups.clients[f.client] || 'مشتری' });
      if (f.building) list.push({ key: 'building', label: this.lookups.buildings[f.building] || 'ساختمان' });
      if (f.priority) list.push({ key: 'priority', label: 'اولویت ' + (f.priority === 'none' ? 'ثبت‌نشده' : PRIORITY_LEVEL[f.priority].label) });
      return list;
    },
    quickLinks() {
      const preferred = ['/visitmanagment/lists', '/service-cases', '/ticket/ticketlist', '/elevatormanagement/buildinglist', '/customermanagement/list', '/warehouse/warelist', '/usermanagement/list'];
      const rank = route => { const index = preferred.indexOf(route); return index < 0 ? preferred.length : index; };
      return [...this.links].sort((a, b) => rank(a.frontend_route_url) - rank(b.frontend_route_url)).slice(0, 7);
    },
  },
  watch: {
    project() { this.sequence++; this.reset(); this.loadMenu(); this.load(); },
    filters: { deep: true, handler() { this.syncQuery(); } },
  },
  created() { this.readQuery(); this.loadMenu(); this.load(); },
  beforeDestroy() { this.sequence++; },
  methods: {
    fa, faId, jDate, percent,
    bucket(visit) { return BUCKET[bucketOf(visit)]; },
    late(visit) { return isOverdue(visit, this.today); },
    options(lookup, field) {
      const present = new Set(this.visits.map(v => v[field]).filter(Boolean));
      return [...present].map(key => ({ key, label: this.lookups[lookup][key] || String(key) })).sort((a, b) => a.label.localeCompare(b.label, 'fa'));
    },
    deltaHint(current, previous) {
      if (!previous) return current ? 'بازه قبل: صفر' : 'بدون تغییر نسبت به بازه قبل';
      const change = Math.round(((current - previous) / previous) * 100);
      if (!change) return 'هم‌اندازه بازه قبل';
      return `${change > 0 ? '▲' : '▼'} ${fa(Math.abs(change))}٪ نسبت به بازه قبل (${fa(previous)})`;
    },
    deltaTone(current, previous, higherIsGood) {
      if (!previous || current === previous) return 'muted';
      return (current > previous) === higherIsGood ? 'good' : 'bad';
    },
    toggleStatus(value) { this.filters.status = this.filters.status === value ? '' : value; },
    pickPoint(point) {
      if (this.trendData.step === 1) this.filters.day = this.filters.day === point.from ? '' : point.from;
      else { this.preset = 'custom'; this.range = { from: point.from, to: point.to }; this.filters.day = ''; this.load(); }
    },
    clear(key) { this.filters[key] = ''; },
    clearAll() { this.filters = blankFilters(); },
    reset() { this.visits = []; this.loaded = false; this.filters = blankFilters(); this.links = []; this.iframeLink = null; },
    setPreset(key) { this.preset = key; this.range = presetRange(key, this.today); this.filters.day = ''; this.load(); },
    openCustom() { this.customRange = [this.range.from, this.range.to]; this.customOpen = true; },
    applyCustom(value) {
      const list = Array.isArray(value) ? value : this.customRange;
      const [from, to] = (list || []).map(item => (typeof item === 'string' ? item : item && item.format ? item.format('YYYY-MM-DD') : ''));
      if (!from || !to) return;
      this.preset = 'custom'; this.range = { from, to }; this.filters.day = ''; this.customOpen = false; this.load();
    },
    openVisit(id) { this.$router.push('/visitmanagment/answerlist/' + id); },
    readQuery() {
      const q = this.$route.query;
      if (q.from && q.to && /^\d{4}-\d{2}-\d{2}$/.test(q.from) && /^\d{4}-\d{2}-\d{2}$/.test(q.to)) { this.preset = 'custom'; this.range = { from: q.from, to: q.to }; }
      else if (['7', '30', '90', 'month'].includes(q.range)) { this.preset = q.range; this.range = presetRange(q.range, this.today); }
      ['type', 'client', 'building'].forEach(key => { if (q[key]) this.filters[key] = Number(q[key]) || ''; });
      if (q.expert) this.filters.expert = q.expert === 'none' ? 'none' : Number(q.expert) || '';
      if (q.status && STATUS_FOCUS[q.status]) this.filters.status = q.status;
      if (q.day && /^\d{4}-\d{2}-\d{2}$/.test(q.day)) this.filters.day = q.day;
      if (q.priority && (PRIORITY_LEVEL[q.priority] || q.priority === 'none')) this.filters.priority = q.priority;
    },
    // Filters live in the address so a view can be shared or restored after refresh.
    syncQuery() {
      const query = this.preset === 'custom' ? { from: this.range.from, to: this.range.to } : { range: this.preset };
      Object.entries(this.filters).forEach(([key, value]) => { if (value !== '' && value !== null) query[key] = String(value); });
      if (JSON.stringify(query) !== JSON.stringify(this.$route.query)) this.$router.replace({ query }, () => {}, () => {}); // vue-router 2: callbacks, not a promise
    },
    async load() {
      if (!this.project) return;
      const sequence = ++this.sequence;
      const project = this.project;
      this.loading = true; this.error = '';
      this.syncQuery();
      try {
        const query = new URLSearchParams({ p: project, from: this.range.from, to: this.range.to });
        const response = await this.$ApiServiceLayer.get('/api/admin/dashboard/?' + query, this.$PATH.SERVICE_NAME.AUTH);
        if (sequence !== this.sequence) return;
        if (response.status === 403) { this.denied = true; return; }
        if (response.status !== 200) { this.error = this.$ApiServiceLayer.getErrorMessage ? this.$ApiServiceLayer.getErrorMessage(response) : 'دریافت داده‌ها ممکن نشد.'; return; }
        const data = response.data;
        this.denied = false;
        this.visits = data.visits || [];
        this.lookups = { experts: {}, types: {}, buildings: {}, clients: {}, ...data.lookups };
        this.previous = data.previous || { created: 0, completed: 0 };
        this.services = { ...EMPTY_SERVICES, ...data.services };
        this.truncated = !!data.truncated;
        this.today = (data.range && data.range.today) || this.today;
        this.updatedAt = new Date().toLocaleTimeString('fa-IR', { hour: '2-digit', minute: '2-digit' });
        this.loaded = true;
      } catch (_) {
        if (sequence === this.sequence) this.error = 'اتصال برقرار نشد. دوباره تلاش کنید.';
      } finally {
        if (sequence === this.sequence) this.loading = false;
      }
    },
    async loadMenu() {
      if (!this.project) return;
      const project = this.project;
      try {
        const [menu, membership] = await Promise.all([
          this.$ApiServiceLayer.get(this.$PATH.RELATIVE_PATH.GET.MENU_LIST + '?p=' + project + '&is_active=true', this.$PATH.SERVICE_NAME.AUTH),
          this.$ApiServiceLayer.get(this.$PATH.RELATIVE_PATH.GET.AUTH_ROLE, this.$PATH.SERVICE_NAME.AUTH),
        ]);
        if (project !== this.project) return;
        if (membership.status === 200) {
          const rows = Array.isArray(membership.data) ? membership.data : membership.data.results || [];
          const active = rows.find(item => item.project && item.project.id === Number(project));
          if (active) this.projectName = active.project.name_fa || active.project.name || 'پروژه شما';
        }
        if (menu.status !== 200) return;
        const flatten = nodes => nodes.reduce((all, node) => [...all, node, ...flatten(node.children || [])], []);
        const menus = flatten(normalizeMenu(menu.data));
        const dashboard = menus.find(item => item.frontend_route_url === '/dashboard' && item.iframe_link);
        this.iframeLink = dashboard ? dashboard.iframe_link : null;
        this.links = menus.filter(item => !item.has_submenu && !(item.children || []).length && item.frontend_route_url
          && item.frontend_route_url !== '/dashboard' && this.$router.resolve(item.frontend_route_url).resolved.matched.length);
      } catch (_) { /* Shortcuts are optional; the dashboard still works without them. */ }
    },
  },
};
</script>

<style scoped>
.dashboard { display: grid; gap: 16px; color: #25324b; }
/* A slim banner: the page title above already names the screen, so this only carries range and freshness. */
.dash-head { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 10px 16px 10px 12px; border-radius: 14px;
  background: linear-gradient(140deg, #16264a, #2a4f9a); color: #fff; box-shadow: 0 6px 16px #16264a1f; }
.head-copy { display: flex; flex-wrap: wrap; align-items: baseline; gap: 2px 14px; min-width: 0; }
.dash-head h1 { color: #fff; font-size: 15px; line-height: 1.6; margin: 0; font-weight: 800; }
.dash-head p { color: #dde6ff; font-size: 12px; margin: 0; }
.ghost-btn { display: inline-flex; align-items: center; gap: 7px; min-height: 36px; padding: 6px 12px; border-radius: 10px; border: 1px solid #ffffff55;
  background: #ffffff1a; color: #fff; font: inherit; font-size: 12.5px; font-weight: 700; cursor: pointer; white-space: nowrap; }
.ghost-btn svg { width: 16px; height: 16px; fill: none; stroke: currentColor; stroke-width: 2; stroke-linecap: round; stroke-linejoin: round; }
.ghost-btn.small { min-height: 34px; padding: 5px 12px; border-color: #d4dceb; background: #fff; color: #345de0; }
.ghost-btn:disabled { opacity: .6; }
.quick { display: flex; flex-wrap: wrap; gap: 8px; }
.quick-link { display: inline-flex; align-items: center; gap: 8px; min-height: 38px; padding: 7px 14px; border-radius: 10px; border: 1px solid #dbe3f0;
  background: #fff; color: #2c3b5a; font-size: 12.5px; font-weight: 700; text-decoration: none; }
.quick-link:hover { border-color: #9fb4e6; color: #345de0; text-decoration: none; }
.quick-link span { color: #345de0; }
.filters { display: flex; flex-wrap: wrap; align-items: flex-end; gap: 10px 12px; padding: 12px 14px; border-radius: 14px; background: #fff; border: 1px solid #e3e9f2; }
.segmented { position: relative; display: inline-flex; flex-wrap: wrap; gap: 3px; padding: 3px; border-radius: 11px; background: #eef2f8; }
.segmented button { min-height: 34px; padding: 5px 12px; border: 0; border-radius: 9px; background: transparent; color: #4a566c; font: inherit; font-size: 12.5px; font-weight: 700; cursor: pointer; }
.segmented button.active { background: #fff; color: #17233b; box-shadow: 0 2px 6px #1b2a4a1f; }
.range-anchor { position: absolute; width: 1px; height: 1px; opacity: 0; pointer-events: none; bottom: 0; left: 0; }
/* The admin theme styles every label at ID specificity; match it to stack caption over control. */
#app .layout-container .filter-field { display: grid; gap: 4px; margin: 0; font-size: 11px; font-weight: 700; color: #6b778d; }
#app .layout-container .filter-field select { min-width: 160px; min-height: 38px; }
.chips { display: flex; flex-wrap: wrap; align-items: center; gap: 6px; }
.chips-title { font-size: 12px; color: #6b778d; }
.chip { display: inline-flex; align-items: center; gap: 6px; min-height: 30px; padding: 3px 10px; border-radius: 99px; border: 1px solid #c9d6f5; background: #eef3fd; color: #24408f; font: inherit; font-size: 12px; font-weight: 700; cursor: pointer; }
.chip-clear { border: 0; background: transparent; color: #b42d2d; font: inherit; font-size: 12px; font-weight: 700; cursor: pointer; }
.error { padding: 11px 14px; border-radius: 11px; background: #fdeceb; color: #9e3434; font-size: 13px; }
.error button { border: 0; background: transparent; color: inherit; text-decoration: underline; }
.note { margin: 0; font-size: 12px; color: #7a6000; }
.dash-body { display: grid; gap: 16px; transition: opacity .2s; }
.dash-body.refreshing { opacity: .55; }
.kpis { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; }
.grid { display: grid; gap: 16px; }
.two-one { grid-template-columns: minmax(0, 2fr) minmax(0, 1fr); }
.one-two { grid-template-columns: minmax(0, 1fr) minmax(0, 2fr); }
.halves { grid-template-columns: repeat(2, minmax(0, 1fr)); }
.panel { min-width: 0; padding: 18px; border-radius: 16px; background: #fff; border: 1px solid #e3e9f2; box-shadow: 0 4px 14px #1b2a4a08; }
.panel-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; margin-bottom: 12px; }
.panel-head h2 { font-size: 15.5px; font-weight: 800; color: #17233b; margin: 0 0 3px; }
.panel-head p { font-size: 11.5px; color: #6b778d; margin: 0; line-height: 1.7; }
.state-panel { text-align: center; color: #5b6880; font-size: 13px; }
.state-panel h2 { font-size: 16px; color: #25324b; }
.attention { list-style: none; margin: 0; padding: 0; display: grid; gap: 6px; }
.attention button { display: flex; align-items: center; justify-content: space-between; gap: 10px; width: 100%; min-height: 50px; padding: 8px 11px;
  border: 1px solid #eef1f6; border-radius: 11px; background: #fafbfd; font: inherit; text-align: right; cursor: pointer; }
.attention button:hover { border-color: #c9d6f5; }
.attention button.selected { border-color: #345de0; background: #eef3fd; }
.attention button.dim { opacity: .45; }
.attention-name { display: grid; min-width: 0; }
.attention-name b { font-size: 12.5px; color: #17233b; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.attention-name small { font-size: 11px; color: #7a8496; }
.attention-tags { display: flex; flex-wrap: wrap; justify-content: flex-end; gap: 4px; }
.tag { padding: 2px 8px; border-radius: 7px; font-size: 11px; font-weight: 700; white-space: nowrap; }
.tag.critical { background: #fdeceb; color: #a12b2b; }
.tag.serious { background: #fdeee6; color: #974217; }
.tag.warning { background: #fff4dc; color: #7a5300; }
.empty-row { padding: 18px; text-align: center; font-size: 12px; color: #7a8496; }
.service-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; margin-bottom: 14px; }
.service-tile { display: grid; gap: 2px; padding: 12px; border-radius: 12px; border: 1px solid #eef1f6; background: #fafbfd; color: #4a566c; text-decoration: none; font-size: 12px; }
.service-tile:hover { border-color: #c9d6f5; text-decoration: none; }
.service-tile b { font-size: 22px; color: #17233b; }
.service-tile b.alert { color: #b42d2d; }
.service-tile small { font-size: 11px; color: #7a8496; }
.sub-title { font-size: 13px; font-weight: 800; color: #25324b; margin: 0 0 8px; }
.table-wrap { margin-top: 14px; overflow-x: auto; }
table { width: 100%; border-collapse: collapse; font-size: 12.5px; }
th { text-align: right; font-weight: 700; color: #6b778d; padding: 8px; border-bottom: 1px solid #e3e9f2; white-space: nowrap; }
td { padding: 8px; border-bottom: 1px solid #f0f2f6; color: #25324b; white-space: nowrap; font-variant-numeric: tabular-nums; }
tbody tr { cursor: pointer; }
tbody tr:hover { background: #f6f8fc; }
.status-dot { display: inline-block; width: 9px; height: 9px; border-radius: 3px; margin-left: 6px; vertical-align: middle; }
.late-tag { margin-right: 6px; padding: 1px 6px; border-radius: 6px; background: #fdeceb; color: #a12b2b; font-size: 10.5px; }
.muted { color: #7a8496; text-align: center; }
.report-frame { display: block; width: 100%; height: 70vh; min-height: 460px; border: 0; border-radius: 11px; }
.sr-only { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; }
.dashboard button:focus-visible, .dashboard a:focus-visible, .dashboard select:focus-visible { outline: 3px solid #345de0; outline-offset: 2px; }
@media (max-width: 1180px) { .kpis { grid-template-columns: repeat(2, minmax(0, 1fr)); } .two-one, .one-two { grid-template-columns: 1fr; } }
@media (max-width: 760px) { .halves, .service-grid { grid-template-columns: 1fr; } .dash-head { align-items: flex-start; } #app .layout-container .filter-field { flex: 1 1 140px; } #app .layout-container .filter-field select { width: 100%; } }
@media (max-width: 420px) { .kpis { grid-template-columns: 1fr; } }
</style>
