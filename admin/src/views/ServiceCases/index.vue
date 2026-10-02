<template>
  <main class="service-workspace" dir="rtl">
    <header class="service-hero"><div><span class="service-kicker">خدمات پس از فروش · برد آسانسور</span><h1>گارانتی و تعمیرات</h1><p>ادعاهای مشتری را بررسی کنید و هر قطعه را از دریافت تا تحویل با ردپای روشن پیش ببرید.</p></div><button type="button" class="service-refresh" :disabled="loading" @click="load"><span aria-hidden="true">↻</span> به‌روزرسانی</button></header>
    <div v-if="error" class="service-error" role="alert">{{ error }} <button type="button" @click="load">تلاش دوباره</button></div>
    <div v-if="notice" class="service-notice" role="status">{{ notice }}</div>
    <div v-if="loading && !loaded" class="service-loading" role="status">در حال دریافت پرونده‌ها…</div>
    <template v-if="loaded">
      <div class="service-metrics"><button type="button" @click="tab = 'claims'"><span>در انتظار تصمیم</span><strong>{{ number(pendingClaims.length) }}</strong><small>ادعای گارانتی</small></button><button type="button" @click="tab = 'repairs'"><span>تعمیرهای باز</span><strong>{{ number(openRepairs.length) }}</strong><small>پرونده فعال</small></button><button type="button" @click="tab = 'contracts'"><span>قراردادها</span><strong>{{ number(contracts.length) }}</strong><small>پوشش ثبت‌شده</small></button></div>
      <nav class="service-tabs" aria-label="بخش‌های مرکز خدمات"><button v-for="item in tabs" :key="item.key" type="button" :class="{ active: tab === item.key }" :aria-current="tab === item.key ? 'page' : null" @click="tab = item.key">{{ item.label }}</button></nav>
      <div v-if="decision.claim || transition.case || loaner.case || material.case" class="service-backdrop" @click="closeDialogs" />

      <section v-if="tab === 'claims'" class="service-section"><div class="service-section-head"><div><span>اولویت با درخواست‌های تازه</span><h2>ادعاهای گارانتی</h2></div></div>
        <div v-if="!claims.length" class="service-empty">هنوز ادعایی برای این پروژه ثبت نشده است.</div>
        <article v-for="claim in claims" :key="claim.id" class="service-card"><div class="service-card-top"><div><small>درخواست {{ number(claim.id) }} · {{ date(claim.opened_at) }}</small><h3>{{ productName(claim.product) }}</h3><span>{{ clientName(claim.client) }}</span></div><span class="service-badge" :class="claim.status.toLowerCase()">{{ claimLabel(claim.status) }}</span></div><p>{{ claim.issue }}</p><div v-if="claim.decision_reason" class="service-detail-note">دلیل تصمیم: {{ claim.decision_reason }}</div>
          <div v-if="claim.status === 'PENDING'" class="service-card-actions"><button type="button" class="service-primary" :disabled="busy" @click="openDecision(claim, 'COVERED')">تأیید پوشش</button><button type="button" class="service-secondary" :disabled="busy" @click="openDecision(claim, 'DENIED')">رد پوشش</button></div>
          <div v-else-if="!repairs.some(row => row.claim === claim.id)" class="service-card-actions"><button type="button" class="service-secondary" :disabled="busy" @click="createRepair(claim)">ایجاد پرونده تعمیر</button></div>
        </article>
        <form v-if="decision.claim" class="service-form service-modal" role="dialog" aria-modal="true" aria-label="ثبت تصمیم گارانتی" @submit.prevent="saveDecision"><div class="service-form-head"><h3>{{ decision.status === 'COVERED' ? 'تأیید پوشش' : 'رد پوشش' }} · درخواست {{ number(decision.claim.id) }}</h3><button type="button" @click="decision = { claim: null, status: '', reason: '' }" aria-label="بستن">×</button></div><p>دلیل تصمیم برای مشتری نمایش داده می‌شود و پس از ثبت قابل تغییر نیست.</p><label>دلیل تصمیم<textarea v-model.trim="decision.reason" rows="3" maxlength="2000" required /></label><button type="submit" class="service-primary" :disabled="busy || !decision.reason">{{ busy ? 'در حال ثبت…' : 'ثبت تصمیم' }}</button></form>
      </section>

      <section v-if="tab === 'repairs'" class="service-section"><div class="service-section-head"><div><span>از دریافت تا آزمون و تحویل</span><h2>پرونده‌های تعمیر</h2></div></div>
        <div v-if="!repairs.length" class="service-empty">پرونده تعمیری برای این پروژه ثبت نشده است. از یک ادعای بررسی‌شده شروع کنید.</div>
        <article v-for="repair in repairs" :key="repair.id" class="service-card"><div class="service-card-top"><div><small>RMA {{ String(repair.rma_key || '').slice(0, 8) }} · {{ date(repair.received_at) }}</small><h3>{{ productName(repair.product) }}</h3><span>سریال {{ repair.serial_snapshot || 'نامشخص' }} · {{ clientName(repair.client) }}</span></div><span class="service-badge" :class="repair.status === 'DELIVERED' ? 'covered' : 'pending'">{{ repairLabel(repair.status) }}</span></div>
          <div class="service-case-fields"><span v-if="repair.diagnosis">تشخیص: {{ repair.diagnosis }}</span><span v-if="repair.work_performed">اقدام: {{ repair.work_performed }}</span><span v-if="repair.test_result">آزمون: {{ repair.test_result }}</span><span v-if="repair.loaner_product && !repair.loaner_returned_at">برد امانی: {{ productName(repair.loaner_product) }} تا {{ date(repair.loaner_due_at) }}</span><span v-for="part in repair.materials" :key="part.transaction_id">مصرف: {{ number(part.quantity) }} {{ part.ware_name }} · {{ date(part.at) }}</span></div>
          <div class="service-card-actions"><button v-if="nextStates(repair.status).length" type="button" class="service-primary" :disabled="busy" @click="openTransition(repair)">تغییر مرحله</button><button v-if="repair.status === 'REPAIRING'" type="button" class="service-secondary" :disabled="busy" @click="openMaterial(repair)">ثبت قطعه مصرفی</button><button v-if="!['DELIVERED', 'CANCELED'].includes(repair.status)" type="button" class="service-secondary" :disabled="busy" @click="openLoaner(repair)">{{ repair.loaner_product && !repair.loaner_returned_at ? 'ثبت برگشت امانی' : 'تحویل برد امانی' }}</button><button type="button" class="service-link" @click="selectedEvents = selectedEvents === repair.id ? null : repair.id">تاریخچه {{ repair.events.length }} رویداد</button></div>
          <ol v-if="selectedEvents === repair.id" class="service-timeline"><li v-for="event in repair.events" :key="event.id"><strong>{{ repairLabel(event.to_status) }}</strong><span>{{ dateTime(event.at) }}</span><p>{{ event.note || 'تغییر مرحله ثبت شد.' }}</p></li></ol>
        </article>
        <form v-if="transition.case" class="service-form service-modal" role="dialog" aria-modal="true" aria-label="تغییر مرحله تعمیر" @submit.prevent="saveTransition"><div class="service-form-head"><h3>تغییر مرحله · {{ productName(transition.case.product) }}</h3><button type="button" @click="transition.case = null" aria-label="بستن">×</button></div><label>مرحله بعد<select v-model="transition.to_status" required><option v-for="state in nextStates(transition.case.status)" :key="state" :value="state">{{ repairLabel(state) }}</option></select></label><label v-if="transition.to_status === 'REPAIRING'">تشخیص عیب<textarea v-model.trim="transition.diagnosis" rows="2" :required="!transition.case.diagnosis" /></label><label v-if="transition.to_status === 'TESTING'">کار انجام‌شده<textarea v-model.trim="transition.work_performed" rows="2" :required="!transition.case.work_performed" /></label><label v-if="transition.to_status === 'READY'">نتیجه آزمون<textarea v-model.trim="transition.test_result" rows="2" :required="!transition.case.test_result" /></label><label>یادداشت رویداد<textarea v-model.trim="transition.note" rows="2" /></label><button type="submit" class="service-primary" :disabled="busy || !transition.to_status">ثبت مرحله</button></form>
        <form v-if="loaner.case" class="service-form service-modal" role="dialog" aria-modal="true" aria-label="ثبت برد امانی" @submit.prevent="saveLoaner"><div class="service-form-head"><h3>{{ loaner.case.loaner_product && !loaner.case.loaner_returned_at ? 'ثبت برگشت برد امانی' : 'تحویل برد امانی' }}</h3><button type="button" @click="loaner.case = null" aria-label="بستن">×</button></div><template v-if="!loaner.case.loaner_product || loaner.case.loaner_returned_at"><p v-if="loanerLoading">در حال دریافت بردهای آزاد…</p><p v-else-if="loanerError" class="service-inline-error">{{ loanerError }}</p><p v-else-if="!loanerCandidates.length">برد امانی آزادی در این پروژه ثبت نشده است.</p><label v-else>برد امانی<select v-model="loaner.product" required><option value="">انتخاب کنید</option><option v-for="product in loanerCandidates" :key="product.id" :value="product.id">{{ product.serial_number || productName(product.id) }}</option></select></label><label v-if="loanerCandidates.length">موعد برگشت<input v-model="loaner.due_at" type="date" :min="today" required /></label></template><p v-else>برگشت برد {{ productName(loaner.case.loaner_product) }} ثبت می‌شود.</p><button type="submit" class="service-primary" :disabled="busy || loanerLoading || (!!loanerError) || ((!loaner.case.loaner_product || loaner.case.loaner_returned_at) && !loanerCandidates.length)">ثبت</button></form>
        <form v-if="material.case" class="service-form service-modal" role="dialog" aria-modal="true" aria-label="ثبت قطعه مصرفی" @submit.prevent="saveMaterial"><div class="service-form-head"><h3>قطعه مصرفی · RMA {{ String(material.case.rma_key).slice(0, 8) }}</h3><button type="button" @click="material.case = null" aria-label="بستن">×</button></div><p v-if="materialLoading">در حال دریافت موجودی…</p><p v-else-if="materialError" class="service-inline-error">{{ materialError }}</p><p v-else-if="!materialOptions.length">موجودی قابل مصرفی در این پروژه پیدا نشد.</p><template v-else><label>کالا و مبدأ موجودی<select v-model="material.option" required><option value="">انتخاب کنید</option><option v-for="(option, index) in materialOptions" :key="index" :value="index">{{ option.ware_name }} · {{ option.source_name }} · موجودی {{ number(option.available) }}</option></select></label><label>تعداد<input v-model.number="material.quantity" type="number" min="1" :max="chosenMaterial ? chosenMaterial.available : undefined" required /></label></template><button type="submit" class="service-primary" :disabled="busy || materialLoading || !chosenMaterial || material.quantity < 1 || material.quantity > chosenMaterial.available">ثبت مصرف</button></form>
      </section>

      <section v-if="tab === 'contracts'" class="service-section"><div class="service-section-head"><div><span>تعریف پوشش قطعات</span><h2>قراردادهای گارانتی</h2></div><button type="button" class="service-primary" @click="showContract = !showContract">{{ showContract ? 'بستن فرم' : 'قرارداد جدید' }}</button></div>
        <form v-if="showContract" class="service-form" @submit.prevent="saveContract"><div class="service-form-grid"><label>مشتری<select v-model="contract.client" required><option value="">انتخاب کنید</option><option v-for="client in clients" :key="client.id" :value="client.id">{{ clientName(client.id) }}</option></select></label><label>قطعه نصب‌شده<select v-model="contract.product" required :disabled="!contract.client || eligibleLoading || !!eligibleError"><option value="">انتخاب کنید</option><option v-for="product in eligibleProducts" :key="product.id" :value="product.id">{{ product.serial_number || productName(product.id) }}</option></select><small v-if="eligibleLoading">در حال دریافت قطعات مشتری…</small><small v-else-if="eligibleError" class="service-inline-error">{{ eligibleError }}</small><small v-else-if="contract.client && !eligibleProducts.length">قطعه نصب‌شده‌ای برای این مشتری پیدا نشد.</small></label><label>شماره قرارداد<input v-model.trim="contract.reference" maxlength="80" required /></label><label>شروع پوشش<input v-model="contract.coverage_start" type="date" required /></label><label>پایان پوشش<input v-model="contract.coverage_end" type="date" :min="contract.coverage_start" required /></label></div><label>شرایط پوشش<textarea v-model.trim="contract.terms" rows="2" /></label><label>استثناها<textarea v-model.trim="contract.exclusions" rows="2" /></label><button type="submit" class="service-primary" :disabled="busy || !contract.product">ثبت قرارداد</button></form>
        <div v-if="!contracts.length" class="service-empty">قراردادی برای این پروژه ثبت نشده است.</div>
        <article v-for="row in contracts" :key="row.id" class="service-card"><div class="service-card-top"><div><small>قرارداد {{ row.reference }}</small><h3>{{ productName(row.product) }}</h3><span>{{ clientName(row.client) }}</span></div><span class="service-badge" :class="row.is_active ? 'covered' : 'denied'">{{ row.is_active ? 'فعال' : 'غیرفعال' }}</span></div><div class="service-case-fields"><span>از {{ date(row.coverage_start) }} تا {{ date(row.coverage_end) }}</span><span v-if="row.terms">شرایط: {{ row.terms }}</span><span v-if="row.exclusions">استثناها: {{ row.exclusions }}</span></div></article>
      </section>
    </template>
  </main>
</template>

<script>
import { persistentRequestKey, clearRequestKey } from '@/utils/idempotency';
const rows = data => Array.isArray(data) ? data : ((data && data.results) || []);
const stages = { RECEIVED: ['DIAGNOSING', 'CANCELED'], DIAGNOSING: ['REPAIRING', 'CANCELED'], REPAIRING: ['TESTING', 'CANCELED'], TESTING: ['REPAIRING', 'READY', 'CANCELED'], READY: ['DELIVERED', 'CANCELED'] };
export default {
  name: 'ServiceCases',
  data: () => ({ tab: 'claims', tabs: [{ key: 'claims', label: 'ادعاها' }, { key: 'repairs', label: 'تعمیرات' }, { key: 'contracts', label: 'قراردادها' }], claims: [], repairs: [], contracts: [], clients: [], products: [], loading: false, loaded: false, busy: false, error: '', notice: '', selectedEvents: null, showContract: false, contract: { client: '', product: '', reference: '', coverage_start: '', coverage_end: '', terms: '', exclusions: '' }, eligibleProducts: [], eligibleLoading: false, eligibleError: '', eligibleSequence: 0, decision: { claim: null, status: '', reason: '' }, transition: { case: null, to_status: '', note: '', diagnosis: '', work_performed: '', test_result: '' }, loaner: { case: null, product: '', due_at: '' }, loanerCandidates: [], loanerLoading: false, loanerError: '', material: { case: null, option: '', quantity: 1 }, materialOptions: [], materialLoading: false, materialError: '' }),
  computed: { project() { return this.$STORE.state.userConfig.setProjectId; }, pendingClaims() { return this.claims.filter(row => row.status === 'PENDING'); }, openRepairs() { return this.repairs.filter(row => !['DELIVERED', 'CANCELED'].includes(row.status)); }, today() { return new Date().toISOString().slice(0, 10); }, chosenMaterial() { return this.material.option === '' ? null : this.materialOptions[this.material.option]; } },
  mounted() { this.load(); },
  watch: { project() { this.loaded = false; this.load(); }, 'contract.client'() { this.contract.product = ''; this.loadEligibleProducts(); } },
  methods: {
    number(value) { return Number(value || 0).toLocaleString('fa-IR'); },
    date(value) { if (!value) return 'نامشخص'; const parsed = new Date(value); return Number.isNaN(parsed.getTime()) ? value : parsed.toLocaleDateString('fa-IR'); },
    dateTime(value) { if (!value) return 'نامشخص'; return new Date(value).toLocaleString('fa-IR'); },
    clientName(id) { const row = this.clients.find(item => item.id === id); return row ? row.name_fa || row.name || 'مشتری ' + id : 'مشتری ' + id; },
    productName(id) { const row = this.products.find(item => item.id === id); return row ? row.serial_number || 'قطعه ' + id : 'قطعه ' + id; },
    claimLabel(value) { return { PENDING: 'در انتظار بررسی', COVERED: 'تحت پوشش', DENIED: 'خارج از پوشش' }[value] || value; },
    repairLabel(value) { return { RECEIVED: 'دریافت', DIAGNOSING: 'عیب‌یابی', REPAIRING: 'تعمیر', TESTING: 'آزمون', READY: 'آماده تحویل', DELIVERED: 'تحویل‌شده', CANCELED: 'متوقف‌شده' }[value] || value; },
    nextStates(value) { return stages[value] || []; },
    closeDialogs() { if (this.busy) return; this.decision.claim = null; this.transition.case = null; this.loaner.case = null; this.material.case = null; },
    path(value) { return value + (value.includes('?') ? '&' : '?') + 'p=' + this.project; },
    async loadEligibleProducts() {
      const client = this.contract.client; const sequence = ++this.eligibleSequence;
      this.eligibleProducts = []; this.eligibleError = '';
      if (!client) return;
      this.eligibleLoading = true;
      try {
        const response = await this.$ApiServiceLayer.get(this.path('/api/warranty/eligible_products/?client=' + client), '/core');
        if (sequence !== this.eligibleSequence) return;
        if (response.status !== 200) throw new Error(this.$ApiServiceLayer.getErrorMessage(response));
        this.eligibleProducts = rows(response.data);
      } catch (error) { if (sequence === this.eligibleSequence) this.eligibleError = error.message || 'دریافت قطعات ممکن نشد.'; }
      finally { if (sequence === this.eligibleSequence) this.eligibleLoading = false; }
    },
    async load() {
      if (!this.project || this.loading) return;
      this.loading = true; this.error = '';
      const paths = [
        ['/api/warranty/claims/', '/core'], ['/api/repair/cases/', '/core'],
        ['/api/warranty/contracts/', '/core'], ['/api/visit/ClientListCreate/', ''],
        ['/api/visit/ProductListCreate/', ''],
      ];
      try {
        const responses = await Promise.all(paths.map(([path, service]) => this.$ApiServiceLayer.get(this.path(path), service)));
        const failure = responses.find(response => response.status !== 200);
        if (failure) throw new Error(this.$ApiServiceLayer.getErrorMessage(failure));
        [this.claims, this.repairs, this.contracts, this.clients, this.products] = responses.map(response => rows(response.data));
        this.loaded = true;
      } catch (error) { this.error = error.message || 'دریافت پرونده‌ها انجام نشد.'; }
      finally { this.loading = false; }
    },
    async write(path, body) {
      this.busy = true; this.error = ''; this.notice = '';
      try {
        const response = await this.$ApiServiceLayer.post(this.path(path), '/core', body);
        if (response.status < 200 || response.status >= 300) throw new Error(this.$ApiServiceLayer.getErrorMessage(response));
        return response.data;
      } catch (error) { this.error = error.message || 'ثبت تغییر انجام نشد.'; return null; }
      finally { this.busy = false; }
    },
    openDecision(claim, status) { this.decision = { claim, status, reason: '' }; },
    async saveDecision() { const claim = this.decision.claim; if (!claim || !this.decision.reason) return; const result = await this.write('/api/warranty/claims/' + claim.id + '/decision/', { status: this.decision.status, reason: this.decision.reason }); if (result) { this.claims = this.claims.map(row => row.id === claim.id ? result : row); this.decision.claim = null; this.notice = 'تصمیم گارانتی ثبت شد.'; } },
    async createRepair(claim) { const result = await this.write('/api/repair/cases/', { client: claim.client, product: claim.product, claim: claim.id }); if (result) { this.repairs.unshift(result); this.tab = 'repairs'; this.notice = 'پرونده تعمیر ایجاد شد.'; } },
    openTransition(repair) { this.transition = { case: repair, to_status: '', note: '', diagnosis: '', work_performed: '', test_result: '' }; },
    async saveTransition() { const item = this.transition; if (!item.case || !item.to_status) return; const body = { to_status: item.to_status, note: item.note }; if (item.diagnosis) body.diagnosis = item.diagnosis; if (item.work_performed) body.work_performed = item.work_performed; if (item.test_result) body.test_result = item.test_result; const result = await this.write('/api/repair/cases/' + item.case.id + '/transition/', body); if (result) { this.repairs = this.repairs.map(row => row.id === result.id ? result : row); this.transition.case = null; this.notice = 'مرحله تعمیر ثبت شد.'; } },
    async openLoaner(repair) {
      this.loaner = { case: repair, product: '', due_at: '' }; this.loanerCandidates = []; this.loanerError = '';
      if (repair.loaner_product && !repair.loaner_returned_at) return;
      this.loanerLoading = true;
      try {
        const response = await this.$ApiServiceLayer.get(this.path('/api/repair/cases/' + repair.id + '/loaner/'), '/core');
        if (response.status !== 200) throw new Error(this.$ApiServiceLayer.getErrorMessage(response));
        if (this.loaner.case && this.loaner.case.id === repair.id) this.loanerCandidates = rows(response.data);
      } catch (error) { this.loanerError = error.message || 'دریافت بردهای آزاد انجام نشد.'; }
      finally { this.loanerLoading = false; }
    },
    async saveLoaner() { const item = this.loaner; if (!item.case) return; const isReturn = item.case.loaner_product && !item.case.loaner_returned_at; const body = isReturn ? { action: 'return' } : { action: 'assign', product: item.product, due_at: item.due_at }; const result = await this.write('/api/repair/cases/' + item.case.id + '/loaner/', body); if (result) { this.repairs = this.repairs.map(row => row.id === result.id ? result : row); this.loaner.case = null; this.notice = isReturn ? 'برگشت برد امانی ثبت شد.' : 'تحویل برد امانی ثبت شد.'; } },
    async openMaterial(repair) {
      this.material = { case: repair, option: '', quantity: 1 }; this.materialOptions = []; this.materialError = ''; this.materialLoading = true;
      try {
        const response = await this.$ApiServiceLayer.get(this.path('/api/repair/cases/' + repair.id + '/materials/'), '/core');
        if (response.status !== 200) throw new Error(this.$ApiServiceLayer.getErrorMessage(response));
        if (this.material.case && this.material.case.id === repair.id) this.materialOptions = rows(response.data);
      } catch (error) { this.materialError = error.message || 'دریافت موجودی ممکن نشد.'; }
      finally { this.materialLoading = false; }
    },
    async saveMaterial() {
      const item = this.material; const option = this.chosenMaterial;
      if (!item.case || !option || !Number.isSafeInteger(Number(item.quantity)) || item.quantity < 1 || item.quantity > option.available) return;
      const body = { ware: option.ware, quantity: Number(item.quantity), source_type: option.source_type, source_id: option.source_id };
      const scope = 'repair-material.' + this.project + '.' + item.case.id;
      body.request_key = persistentRequestKey(scope, body);
      const result = await this.write('/api/repair/cases/' + item.case.id + '/materials/', body);
      if (result) { clearRequestKey(scope, body.request_key); this.repairs = this.repairs.map(row => row.id === result.id ? result : row); this.material.case = null; this.notice = 'قطعه مصرفی از موجودی کسر و در پرونده ثبت شد.'; }
    },
    async saveContract() { const result = await this.write('/api/warranty/contracts/', this.contract); if (result) { this.contracts.unshift(result); this.showContract = false; this.contract = { client: '', product: '', reference: '', coverage_start: '', coverage_end: '', terms: '', exclusions: '' }; this.notice = 'قرارداد گارانتی ثبت شد.'; } },
  },
};
</script>

<style scoped>
.service-workspace { color: #1b3445; max-width: 1320px; margin: auto; padding-bottom: 40px; }
.service-hero { display: flex; justify-content: space-between; align-items: center; gap: 20px; background: linear-gradient(110deg,#143953,#1e6481); color: white; padding: 26px 30px; border-radius: 19px; box-shadow: 0 12px 25px #1b476129; }
.service-kicker { color: #b8e1eb; font-size: 12px; font-weight: 600; }.service-hero h1 { font-size: 27px; margin: 5px 0 4px; }.service-hero p { margin: 0; color: #e3eff4; font-size: 13px; line-height: 1.8; }
.service-refresh { color: #103c55; background: #ddf4e8; border: 0; border-radius: 10px; padding: 10px 15px; white-space: nowrap; font-weight: 700; }.service-refresh span { font-size: 21px; vertical-align: middle; }
.service-metrics { display: grid; grid-template-columns: repeat(3,minmax(0,1fr)); gap: 13px; margin: 20px 0; }.service-metrics button { text-align: right; border: 1px solid #dbe9ee; border-radius: 15px; background: white; padding: 16px 18px; display: grid; gap: 2px; box-shadow: 0 5px 14px #1945580a; }.service-metrics span { color: #577285; font-size: 12px; }.service-metrics strong { color: #174a68; font-size: 27px; }.service-metrics small { color: #78919e; }
.service-tabs { display: flex; gap: 8px; border-bottom: 1px solid #d9e5e9; margin-bottom: 20px; }.service-tabs button { border: 0; border-bottom: 3px solid transparent; background: transparent; color: #617a89; padding: 13px 17px; font-weight: 700; }.service-tabs button.active { color: #166086; border-bottom-color: #166086; }
.service-section-head { display: flex; justify-content: space-between; align-items: center; gap: 12px; margin-bottom: 15px; }.service-section-head span { color: #5d899e; font-size: 11px; }.service-section-head h2 { margin: 3px 0 0; font-size: 19px; }.service-card { background: white; border: 1px solid #dfe9ed; border-radius: 15px; padding: 19px; margin-bottom: 12px; box-shadow: 0 5px 16px #1c4c5e09; }.service-card-top { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; }.service-card small { color: #7a929e; }.service-card h3 { font-size: 17px; margin: 5px 0 3px; }.service-card-top span:not(.service-badge) { color: #5d7685; font-size: 12px; }.service-card > p { margin: 16px 0; line-height: 1.9; white-space: pre-wrap; }.service-badge { border-radius: 99px; padding: 7px 10px; white-space: nowrap; font-size: 11px; font-weight: 700; color: #956411; background: #fff1d3; }.service-badge.covered { color: #14734c; background: #dff4e9; }.service-badge.denied { color: #ab4b48; background: #fce8e6; }.service-card-actions { display: flex; flex-wrap: wrap; gap: 8px; border-top: 1px solid #edf2f4; padding-top: 14px; margin-top: 15px; }.service-primary,.service-secondary,.service-link { border: 0; border-radius: 9px; padding: 9px 13px; font-size: 12px; font-weight: 700; }.service-primary { background: #166389; color: white; }.service-secondary { background: #eaf3f7; color: #256386; }.service-link { color: #357496; background: transparent; }.service-primary:disabled,.service-secondary:disabled { opacity: .55; }.service-case-fields { display: flex; flex-wrap: wrap; gap: 8px 15px; margin-top: 15px; color: #547182; font-size: 12px; line-height: 1.8; }.service-detail-note { color: #38647a; background: #edf6f9; padding: 10px; border-radius: 9px; font-size: 12px; }
.service-form { background: white; border: 1px solid #d2e2e9; border-radius: 16px; padding: 20px; margin: 16px 0; display: grid; gap: 14px; box-shadow: 0 8px 25px #173f5514; }.service-backdrop { position: fixed; inset: 0; z-index: 49; background: #102e40a6; }.service-modal { position: fixed; z-index: 50; top: 50%; left: 50%; transform: translate(-50%,-50%); width: min(560px,calc(100vw - 28px)); max-height: calc(100vh - 36px); overflow: auto; }.service-form-head { display: flex; justify-content: space-between; align-items: center; }.service-form h3 { font-size: 17px; margin: 0; }.service-form-head button { border: 0; background: #eff4f6; border-radius: 8px; width: 31px; height: 31px; font-size: 22px; }.service-form p { margin: 0; color: #667e8c; font-size: 12px; }.service-form label { display: grid; gap: 6px; color: #385c6f; font-size: 12px; font-weight: 700; }.service-form input,.service-form select,.service-form textarea { width: 100%; min-height: 39px; padding: 8px 10px; border: 1px solid #cbdde5; border-radius: 9px; color: #213f50; background: white; resize: vertical; }.service-form-grid { display: grid; grid-template-columns: repeat(2,minmax(0,1fr)); gap: 12px; }.service-form .service-primary { justify-self: start; }.service-error,.service-notice,.service-loading,.service-empty { border-radius: 12px; padding: 17px; margin: 15px 0; }.service-error { color: #a33a3a; background: #fff0ef; }.service-error button { border: 0; background: transparent; text-decoration: underline; color: inherit; }.service-notice { color: #126746; background: #e4f6ec; }.service-loading,.service-empty { text-align: center; color: #647e8c; background: white; border: 1px dashed #cbdce4; }.service-timeline { margin: 16px 0 0; padding: 0 24px 0 0; border-right: 2px solid #d7e9ef; }.service-timeline li { padding: 0 12px 15px 0; }.service-timeline strong { font-size: 12px; }.service-timeline span { color: #718b99; font-size: 11px; margin-right: 8px; }.service-timeline p { color: #547182; font-size: 12px; margin: 4px 0; }
.service-workspace button:focus-visible,.service-workspace input:focus-visible,.service-workspace select:focus-visible,.service-workspace textarea:focus-visible { outline: 3px solid #4da1c8; outline-offset: 2px; }
.service-form .service-inline-error { color: #a33a3a; }
@media (max-width: 700px) { .service-hero { align-items: flex-start; flex-direction: column; padding: 22px; }.service-metrics { gap: 7px; }.service-metrics button { padding: 11px; }.service-metrics strong { font-size: 23px; }.service-metrics span { font-size: 10px; }.service-form-grid { grid-template-columns: 1fr; } }
@media (max-width: 430px) { .service-metrics { grid-template-columns: 1fr 1fr; }.service-metrics button:last-child { grid-column: 1/-1; }.service-card-top { flex-wrap: wrap; }.service-tabs button { flex: 1; padding: 11px 5px; } }
</style>
