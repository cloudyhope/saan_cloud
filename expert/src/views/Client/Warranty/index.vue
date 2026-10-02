<template>
  <main class="field-page warranty-page" dir="rtl">
    <header class="warranty-hero">
      <div class="warranty-hero-mark"><v-icon color="white" size="25">mdi-shield-check-outline</v-icon></div>
      <span class="warranty-kicker">سان اپ · پشتیبانی قطعات</span>
      <h1>گارانتی و تعمیرات</h1>
      <p>وضعیت پوشش قطعات، درخواست‌های گارانتی و مسیر تعمیر را شفاف پیگیری کنید.</p>
    </header>

    <div class="warranty-tabs" role="tablist" aria-label="بخش خدمات قطعات">
      <button v-for="item in tabs" :key="item.key" type="button" role="tab" :aria-selected="tab === item.key" :class="{ active: tab === item.key }" @click="tab = item.key">{{ item.label }}</button>
    </div>
    <v-alert v-if="error" type="error" outlined role="alert">{{ error }} <v-btn text color="error" @click="load">تلاش دوباره</v-btn></v-alert>
    <v-skeleton-loader v-if="loading && !loaded" type="article, article" />

    <template v-if="loaded">
      <section v-if="tab === 'coverage'" aria-labelledby="coverage-title">
        <div class="warranty-section-title"><div><span>پوشش شما</span><h2 id="coverage-title">قراردادهای گارانتی</h2></div><span class="warranty-count">{{ number(contracts.length) }}</span></div>
        <EmptyState v-if="!contracts.length" kind="warranty" size="sm" title="قرارداد گارانتی ثبت نشده است" description="در صورت ثبت قرارداد توسط شرکت، جزئیات پوشش اینجا دیده می‌شود." />
        <article v-for="contract in contracts" :key="contract.id" class="warranty-card">
          <div class="warranty-card-head"><span class="warranty-symbol"><v-icon color="#21658b">mdi-shield-check-outline</v-icon></span><div><small>شماره قرارداد</small><h3>{{ contract.reference }}</h3></div><span class="warranty-state" :class="coverageActive(contract) ? 'covered' : 'expired'">{{ coverageActive(contract) ? 'فعال' : 'پایان‌یافته' }}</span></div>
          <div class="warranty-card-meta"><span>از {{ date(contract.coverage_start) }}</span><span>تا {{ date(contract.coverage_end) }}</span></div>
          <p v-if="contract.terms" class="warranty-card-text">{{ contract.terms }}</p>
          <p v-if="contract.exclusions" class="warranty-card-muted">استثناها: {{ contract.exclusions }}</p>
        </article>
      </section>

      <section v-else-if="tab === 'claims'" aria-labelledby="claims-title">
        <div class="warranty-section-title"><div><span>درخواست بررسی</span><h2 id="claims-title">ادعاهای گارانتی</h2></div><button type="button" class="warranty-add" @click="showForm = !showForm"><v-icon size="19">{{ showForm ? 'mdi-close' : 'mdi-plus' }}</v-icon>{{ showForm ? 'بستن' : 'ثبت مورد' }}</button></div>
        <form v-if="showForm" class="warranty-form" @submit.prevent="submitClaim">
          <h3>ثبت مشکل قطعه</h3><p>قطعه‌ای را انتخاب کنید که اکنون روی آسانسور شما نصب است.</p>
          <v-select v-model="form.client" :items="clientOptions" label="مالک / مدیریت" outlined dense required :disabled="sending" />
          <v-select v-model="form.product" :items="productOptions" label="قطعه" outlined dense required :disabled="sending" />
          <v-select v-if="matchingContracts.length > 1" v-model="form.contract" :items="matchingContracts.map(row => ({ value: row.id, text: row.reference }))" label="قرارداد گارانتی" outlined dense required :disabled="sending" />
          <v-textarea v-model.trim="form.issue" label="شرح مشکل و زمان رخداد" outlined rows="3" counter="2000" required :disabled="sending" />
          <v-alert v-if="formError" type="error" outlined role="alert">{{ formError }}</v-alert>
          <v-btn block large color="primary" type="submit" :loading="sending" :disabled="!form.client || !form.product || !form.issue || (matchingContracts.length > 1 && !form.contract) || sending">ثبت برای بررسی</v-btn>
        </form>
        <v-alert v-if="success" type="success" outlined role="status">درخواست بررسی گارانتی ثبت شد.</v-alert>
        <EmptyState v-if="!claims.length" kind="documents" size="sm" title="درخواستی ثبت نشده است" description="اگر قطعه‌ای مشکل دارد، از «ثبت مورد» آن را برای بررسی بفرستید." />
        <article v-for="claim in claims" :key="claim.id" class="warranty-card">
          <div class="warranty-card-head"><span class="warranty-symbol"><v-icon color="#21658b">mdi-clipboard-text-outline</v-icon></span><div><small>درخواست #{{ number(claim.id) }}</small><h3>{{ productName(claim.product) }}</h3></div><span class="warranty-state" :class="String(claim.status || '').toLowerCase()">{{ claimStatus(claim.status) }}</span></div>
          <p class="warranty-card-text">{{ claim.issue }}</p><div class="warranty-card-meta"><span>ثبت: {{ date(claim.opened_at) }}</span><span v-if="claim.decided_at">بررسی: {{ date(claim.decided_at) }}</span></div>
          <p v-if="claim.decision_reason" class="warranty-decision">نتیجه بررسی: {{ claim.decision_reason }}</p>
        </article>
      </section>

      <section v-else aria-labelledby="repairs-title">
        <div class="warranty-section-title"><div><span>از دریافت تا تحویل</span><h2 id="repairs-title">پرونده‌های تعمیر</h2></div><span class="warranty-count">{{ number(repairs.length) }}</span></div>
        <EmptyState v-if="!repairs.length" kind="parts" size="sm" title="تعمیر فعالی ندارید" description="پرونده‌های تعمیر قطعات شما پس از دریافت توسط شرکت اینجا نمایش داده می‌شوند." />
        <article v-for="repair in repairs" :key="repair.id" class="warranty-card">
          <div class="warranty-card-head"><span class="warranty-symbol"><v-icon color="#21658b">mdi-wrench-outline</v-icon></span><div><small>کد تعمیر {{ String(repair.rma_key || '').slice(0, 8) }}</small><h3>{{ productName(repair.product) }}</h3></div><span class="warranty-state" :class="repair.status === 'DELIVERED' ? 'covered' : 'pending'">{{ repairStatus(repair.status) }}</span></div>
          <div class="warranty-card-meta"><span>شماره سریال: {{ repair.serial_snapshot || 'ثبت نشده' }}</span><span>دریافت: {{ date(repair.received_at) }}</span></div>
          <p v-if="repair.diagnosis" class="warranty-card-text">تشخیص: {{ repair.diagnosis }}</p>
          <p v-if="repair.test_result" class="warranty-card-muted">نتیجه آزمون: {{ repair.test_result }}</p>
          <p v-if="repair.materials && repair.materials.length" class="warranty-card-muted">قطعات استفاده‌شده: {{ repair.materials.map(part => number(part.quantity) + ' ' + part.ware_name).join('، ') }}</p>
          <div v-if="repair.loaner_product && !repair.loaner_returned_at" class="warranty-loaner"><v-icon size="18">mdi-swap-horizontal</v-icon><span>برد امانی فعال تا {{ date(repair.loaner_due_at) }}</span></div>
        </article>
      </section>
    </template>
  </main>
</template>

<script>
import { pageRows, errorMessage } from '@/utils/clientRequests';

import EmptyState from '@/components/EmptyState/index.vue';
export default {
  components: { EmptyState },
  name: 'ClientWarranty',
  data: () => ({ tab: 'coverage', tabs: [
    { key: 'coverage', label: 'پوشش' }, { key: 'claims', label: 'درخواست‌ها' }, { key: 'repairs', label: 'تعمیرات' },
  ], contracts: [], claims: [], repairs: [], clients: [], products: [], loading: false, loaded: false,
  error: '', showForm: false, sending: false, formError: '', success: false, sequence: 0,
  form: { client: null, product: null, contract: null, issue: '' } }),
  computed: {
    project() { return this.$STORE.state.userConfig.selectedProject; },
    clientOptions() { return this.clients.map(item => ({ value: item.id, text: item.name_fa || item.name || 'مدیریت ' + item.id })); },
    productOptions() { return this.products.map(item => ({ value: item.id, text: (item.serial_number || 'قطعه ' + item.id) + ' · ' + ((item.model && item.model.name_fa) || 'برد آسانسور') })); },
    matchingContracts() { const today = new Date().toISOString().slice(0, 10); return this.contracts.filter(row => row.client === this.form.client && row.product === this.form.product && row.is_active && row.coverage_start <= today && row.coverage_end >= today); },
  },
  mounted() { if (['coverage', 'claims', 'repairs'].includes(this.$route.query.tab)) this.tab = this.$route.query.tab; this.load(); },
  beforeDestroy() { this.sequence += 1; },
  watch: {
    '$route.query.tab'(value) { if (['coverage', 'claims', 'repairs'].includes(value)) this.tab = value; },
    project() {
      this.sequence += 1;
      this.contracts = []; this.claims = []; this.repairs = []; this.clients = []; this.products = [];
      this.form = { client: null, product: null, contract: null, issue: '' };
      this.loaded = false; this.loading = false; this.sending = false; this.showForm = false;
      this.error = ''; this.formError = ''; this.success = false;
      this.load();
    },
    'form.product'() { this.form.contract = null; },
    'form.client'() { this.form.contract = null; },
  },
  methods: {
    number(value) { return Number(value || 0).toLocaleString('fa-IR'); },
    date(value) { if (!value) return 'نامشخص'; const d = new Date(value); return Number.isNaN(d.getTime()) ? value : d.toLocaleDateString('fa-IR'); },
    coverageActive(row) { return row.is_active && row.coverage_start <= new Date().toISOString().slice(0, 10) && row.coverage_end >= new Date().toISOString().slice(0, 10); },
    productName(id) { const item = this.products.find(row => row.id === id); return item ? item.serial_number || 'قطعه ' + id : 'قطعه ' + id; },
    claimStatus(status) { return ({ PENDING: 'در حال بررسی', COVERED: 'تحت پوشش', DENIED: 'خارج از پوشش' })[status] || 'در حال پیگیری'; },
    repairStatus(status) { return ({ RECEIVED: 'دریافت شده', DIAGNOSING: 'عیب‌یابی', REPAIRING: 'در حال تعمیر', TESTING: 'در حال آزمون', READY: 'آماده تحویل', DELIVERED: 'تحویل شده', CANCELED: 'متوقف شده' })[status] || 'در حال پیگیری'; },
    async load() {
      if (!this.project || this.loading) return;
      const project = this.project;
      const sequence = ++this.sequence;
      this.loading = true; this.error = '';
      const urls = [
        'core/api/warranty/contracts/', 'core/api/warranty/claims/', 'core/api/repair/cases/',
        'api/visit/ClientListCreate/', 'api/visit/ProductListCreate/',
      ];
      try {
        const results = await Promise.all(urls.map(path => this.$ApiServiceLayer.get(path + '?p=' + project)));
        if (sequence !== this.sequence || project !== this.project) return;
        const failed = results.find(response => response.status !== 200);
        if (failed) { this.error = errorMessage(failed); return; }
        [this.contracts, this.claims, this.repairs, this.clients, this.products] = results.map(response => pageRows(response.data));
        if (this.clients.length === 1) this.form.client = this.clients[0].id;
        this.loaded = true;
      } catch (_) { if (sequence === this.sequence && project === this.project) this.error = 'دریافت اطلاعات گارانتی ممکن نشد. دوباره تلاش کنید.'; }
      finally { if (sequence === this.sequence && project === this.project) this.loading = false; }
    },
    async submitClaim() {
      if (this.sending || !this.form.client || !this.form.product || !this.form.issue ||
          (this.matchingContracts.length > 1 && !this.form.contract)) return;
      const project = this.project;
      const sequence = this.sequence;
      const payload = { ...this.form };
      this.sending = true; this.formError = ''; this.success = false;
      try {
        const response = await this.$ApiServiceLayer.post('core/api/warranty/claims/?p=' + project, '', payload);
        if (sequence !== this.sequence || project !== this.project) return;
        if (response.status !== 201) { this.formError = errorMessage(response); return; }
        this.claims.unshift(response.data); this.form.product = null; this.form.contract = null; this.form.issue = '';
        this.showForm = false; this.success = true;
      } catch (_) { if (sequence === this.sequence && project === this.project) this.formError = 'ثبت درخواست ممکن نشد. دوباره تلاش کنید.'; }
      finally { if (sequence === this.sequence && project === this.project) this.sending = false; }
    },
  },
};
</script>

<style scoped>
.warranty-page { color: #163247; padding-bottom: 105px; }
.warranty-hero { position: relative; overflow: hidden; background: linear-gradient(145deg, #103a5a, #185d80); color: white; border-radius: 0 0 28px 28px; padding: 30px 24px 31px; margin: -16px -16px 22px; box-shadow: 0 15px 35px #143c5a29; }
.warranty-hero::after { content: ''; position: absolute; width: 180px; height: 180px; left: -35px; top: -50px; border: 1px solid #ffffff2b; border-radius: 50%; box-shadow: 0 0 0 28px #ffffff0b, 0 0 0 60px #ffffff09; }
.warranty-hero-mark { width: 45px; height: 45px; display: grid; place-items: center; border-radius: 14px; background: #ffffff26; margin-bottom: 15px; }
.warranty-kicker { display: block; font-size: 12px; color: #b8deef; margin-bottom: 5px; }
.warranty-hero h1 { font-size: clamp(24px, 7vw, 30px); margin: 0 0 7px; }
.warranty-hero p { font-size: 13px; line-height: 1.9; max-width: 370px; color: #e1f1f8; margin: 0; }
.warranty-tabs { display: flex; gap: 4px; padding: 4px; border-radius: 15px; background: #e9f1f5; margin-bottom: 25px; }
.warranty-tabs button { flex: 1; border: 0; border-radius: 11px; padding: 12px 4px; color: #577082; font-weight: 700; font-size: 13px; }
.warranty-tabs button.active { color: #174563; background: white; box-shadow: 0 3px 12px #1a4c6421; }
.warranty-tabs button:focus-visible, .warranty-add:focus-visible { outline: 3px solid #3887c3; outline-offset: 2px; }
.warranty-section-title { display: flex; align-items: end; justify-content: space-between; margin: 0 2px 16px; }
.warranty-section-title span:first-child { color: #5185a3; font-size: 11px; font-weight: 700; }
.warranty-section-title h2 { font-size: 18px; margin: 3px 0 0; }
.warranty-count { color: #5283a0; background: #eaf2f6; border-radius: 99px; min-width: 27px; height: 27px; display: grid; place-items: center; }
.warranty-add { display: flex; align-items: center; gap: 4px; border: 0; border-radius: 10px; color: white; background: #1a658a; padding: 10px 12px; font-weight: 700; font-size: 12px; }
.warranty-card, .warranty-form, .warranty-empty { background: white; border: 1px solid #e0ebf0; border-radius: 18px; padding: 18px; margin-bottom: 12px; box-shadow: 0 5px 17px #17395109; }
.warranty-card-head { display: flex; align-items: center; gap: 11px; }
.warranty-card-head > div { flex: 1; min-width: 0; }
.warranty-card-head small { color: #7793a3; font-size: 11px; }
.warranty-card-head h3 { font-size: 15px; margin: 2px 0 0; overflow-wrap: anywhere; }
.warranty-symbol { width: 42px; height: 42px; flex: none; display: grid; place-items: center; background: #eaf4f7; border-radius: 12px; }
.warranty-state { flex: none; border-radius: 99px; padding: 6px 8px; font-size: 11px; font-weight: 700; background: #eef3f5; color: #536e7b; }
.warranty-state.covered { background: #e0f4ea; color: #14734b; }
.warranty-state.pending { background: #fff2d9; color: #8f5e0c; }
.warranty-state.denied, .warranty-state.expired { background: #fce9e9; color: #9e4145; }
.warranty-card-meta { display: flex; justify-content: space-between; flex-wrap: wrap; gap: 4px 12px; color: #658093; font-size: 11px; margin-top: 16px; }
.warranty-card-text { color: #344f62; font-size: 13px; line-height: 1.8; margin: 15px 0 0; white-space: pre-wrap; }
.warranty-card-muted { color: #688394; font-size: 12px; margin: 10px 0 0; line-height: 1.7; }
.warranty-decision, .warranty-loaner { border-radius: 11px; background: #f0f7fa; padding: 10px 12px; color: #2c6584; margin: 12px 0 0; font-size: 12px; line-height: 1.8; }
.warranty-loaner { display: flex; align-items: center; gap: 7px; background: #fff5dd; color: #855d18; }
.warranty-empty { min-height: 160px; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; gap: 7px; color: #6b899a; }
.warranty-empty strong { color: #28495e; font-size: 14px; }.warranty-empty p { font-size: 12px; line-height: 1.8; margin: 0; }
.warranty-form { padding: 20px; }.warranty-form h3 { font-size: 16px; margin: 0 0 4px; }.warranty-form p { font-size: 12px; color: #728a98; margin-bottom: 20px; }
@media (max-width: 360px) { .warranty-card { padding: 14px; }.warranty-state { max-width: 85px; text-align: center; }.warranty-card-head { gap: 8px; } }
</style>
