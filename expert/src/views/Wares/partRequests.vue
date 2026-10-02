<template>
  <main class="vf-page parts-page" dir="rtl">
    <VisitTopBar title="درخواست قطعه از انبار" :eyebrow="`مأموریت ${faId(id)}`" :fallback="{ name: 'storeDetail', params: { id } }"
                 subtitle="پس از تأیید انباردار، قطعه به موجودی شما منتقل می‌شود و نتیجه را در اعلان‌ها می‌بینید." />
    <div class="vf-body">
      <div v-if="error" class="vf-banner vf-banner-danger" role="alert">
        <v-icon color="#8a2f2a">mdi-alert-circle-outline</v-icon>
        <div><strong>اطلاعات دریافت نشد</strong><p>{{ error }}</p>
          <button type="button" class="vf-banner-action" @click="load"><v-icon size="16">mdi-refresh</v-icon>تلاش دوباره</button></div>
      </div>
      <v-skeleton-loader v-if="loading && !data" class="vf-skeleton" type="article, list-item-two-line" />
      <template v-else-if="data">
        <form v-if="data.open" class="vf-card part-form" @submit.prevent="submit">
          <div class="vf-card-title"><h2>درخواست تازه</h2></div>
          <label class="part-field">قطعه یا کالا
            <v-autocomplete v-model="ware" :items="wareItems" item-text="label" item-value="id" outlined dense hide-details
                            placeholder="نام یا کد کالا را جستجو کنید" no-data-text="کالایی پیدا نشد" :disabled="busy">
              <template #item="{ item }">
                <div class="ware-option"><strong>{{ item.name }}</strong>
                  <small>{{ item.identifier ? item.identifier + ' · ' : '' }}موجودی انبار {{ faNumber(item.in_stock) }}{{ item.mine ? ` · نزد شما ${faNumber(item.mine)}` : '' }}{{ item.suggested ? ' · پیشنهادی این خدمت' : '' }}</small></div>
              </template>
            </v-autocomplete>
          </label>
          <p v-if="selected && !selected.in_stock" class="vf-muted stock-note">این کالا در انبارها موجودی ندارد؛ درخواست ثبت می‌شود و انباردار تأمین آن را پیگیری می‌کند.</p>
          <div class="part-row">
            <label class="part-field part-amount">تعداد
              <input v-model.number="amount" type="number" inputmode="numeric" min="1" max="1000" :disabled="busy">
            </label>
            <label class="part-field part-note">توضیح (اختیاری)
              <input v-model="note" type="text" maxlength="500" placeholder="مثلاً علت تعویض" :disabled="busy">
            </label>
          </div>
          <p v-if="formError" class="form-error" role="alert">{{ formError }}</p>
          <button type="submit" class="vf-btn vf-btn-primary vf-btn-block" :disabled="busy || !ware || !(amount >= 1)">
            <v-progress-circular v-if="busy" indeterminate size="20" width="2" color="white" />
            <template v-else><v-icon color="white" size="20">mdi-package-variant-plus</v-icon>ثبت درخواست</template>
          </button>
        </form>
        <div v-else class="vf-banner vf-banner-info" role="note"><v-icon color="#1d4f6d">mdi-lock-outline</v-icon>
          <div><strong>مأموریت بسته است</strong><p>درخواست قطعه فقط در مأموریت باز ثبت می‌شود.</p></div></div>

        <div class="vf-section-label"><h2>درخواست‌های این مأموریت</h2><span v-if="data.requests.length">{{ faNumber(data.requests.length) }} مورد</span></div>
        <EmptyState v-if="!data.requests.length" kind="parts" size="sm" title="هنوز درخواستی ثبت نکرده‌اید" description="" />
        <article v-for="row in data.requests" :key="row.id" class="vf-card request-card">
          <div class="request-head">
            <div><strong>{{ row.ware_name }}</strong><small>{{ faNumber(row.amount) }} {{ row.unit || 'عدد' }} · {{ faDate(row.created_at, true) }}</small></div>
            <span class="vf-chip" :class="tone(row.status)">{{ row.status_label }}</span>
          </div>
          <p v-if="row.note" class="request-note">{{ row.note }}</p>
          <p v-if="row.status === 'FULFILLED'" class="request-result ok">از «{{ row.location }}» به موجودی شما منتقل شد.</p>
          <p v-if="row.status === 'REJECTED'" class="request-result bad">دلیل رد: {{ row.decision_note }}</p>
          <button v-if="row.status === 'PENDING'" type="button" class="vf-btn vf-btn-danger vf-btn-small" :disabled="busy" @click="cancel(row)">لغو درخواست</button>
        </article>
      </template>
    </div>
    <v-snackbar v-model="toast" :timeout="2600" top color="#15364f">{{ toastText }}</v-snackbar>
  </main>
</template>

<script>
import VisitTopBar from '@/components/Visit/VisitTopBar.vue';
import { errorMessage } from '@/utils/clientRequests';
import { faDate, faId, faNumber, withProject } from '@/utils/visitFlow';

import EmptyState from '@/components/EmptyState/index.vue';
const TONES = { PENDING: 'vf-tone-progress', FULFILLED: 'vf-tone-done', REJECTED: 'vf-tone-danger', CANCELED: 'vf-tone-muted' };

export default {
  name: 'PartRequests',
  components: { EmptyState, VisitTopBar },
  data: () => ({ data: null, loading: false, error: '', ware: null, amount: 1, note: '', busy: false, formError: '',
    toast: false, toastText: '' }),
  computed: {
    id() { return this.$route.params.id; },
    path() { return `/api/promoter/visit/${this.id}/parts/`; },
    wareItems() {
      return ((this.data && this.data.wares) || []).map(item => ({ ...item, label: `${item.name} ${item.identifier}`.trim() }));
    },
    selected() { return this.wareItems.find(item => item.id === this.ware) || null; },
  },
  created() { this.load(); },
  methods: {
    faId, faDate, faNumber,
    tone: status => TONES[status] || 'vf-tone-muted',
    async load() {
      this.loading = true; this.error = '';
      try {
        const response = await this.$ApiServiceLayer.get(withProject(this.path), this.$PATH.SERVICE_NAME.AUTH);
        if (response.status === 200) this.data = response.data;
        else this.error = response.status === 404 ? 'این مأموریت به شما تخصیص داده نشده است.' : errorMessage(response);
      } catch (_) { this.error = 'اتصال برقرار نشد. دوباره تلاش کنید.'; } finally { this.loading = false; }
    },
    async submit() {
      if (this.busy) return;
      this.busy = true; this.formError = '';
      try {
        const response = await this.$ApiServiceLayer.post(withProject(this.path), this.$PATH.SERVICE_NAME.AUTH,
          { ware: this.ware, amount: this.amount, note: this.note });
        if (response.status !== 201) { this.formError = errorMessage(response); return; }
        this.data = response.data; this.ware = null; this.amount = 1; this.note = '';
        this.toastText = 'درخواست برای انبار ارسال شد.'; this.toast = true;
      } catch (_) { this.formError = 'ثبت درخواست ممکن نشد. دوباره تلاش کنید.'; } finally { this.busy = false; }
    },
    async cancel(row) {
      this.busy = true;
      try {
        const response = await this.$ApiServiceLayer.post(withProject(`/api/promoter/part_request/${row.id}/cancel/`), this.$PATH.SERVICE_NAME.AUTH, {});
        if (response.status === 200) { this.toastText = 'درخواست لغو شد.'; this.toast = true; await this.load(); }
        else this.formError = errorMessage(response);
      } finally { this.busy = false; }
    },
  },
};
</script>

<style scoped>
.part-form { display: grid; gap: 12px; }
.part-field { display: grid; gap: 6px; font-size: 12.5px; font-weight: 700; color: #33566b; }
.part-field input { min-height: 44px; padding: 8px 12px; border: 1px solid #c9dbe5; border-radius: 12px; background: #fff; font: inherit; font-weight: 400; color: var(--vf-ink); }
.part-field input:focus { outline: 3px solid #9fd0ea; border-color: var(--vf-brand); }
.part-row { display: grid; grid-template-columns: 96px 1fr; gap: 10px; }
.ware-option { display: grid; padding: 4px 0; }
.ware-option strong { font-size: 13px; }
.ware-option small { color: var(--vf-muted); font-size: 11px; }
.stock-note { margin: -4px 2px 0; line-height: 1.8; }
.form-error { margin: 0; color: var(--vf-danger); font-size: 12.5px; }
.request-card { display: grid; gap: 8px; }
.request-head { display: flex; justify-content: space-between; align-items: flex-start; gap: 10px; }
.request-head div { display: grid; }
.request-head strong { font-size: 14px; }
.request-head small { color: var(--vf-muted); font-size: 11.5px; }
.request-note { margin: 0; color: #33566b; font-size: 12.5px; }
.request-result { margin: 0; padding: 7px 10px; border-radius: 10px; font-size: 12px; }
.request-result.ok { background: var(--vf-ok-soft); color: var(--vf-ok); }
.request-result.bad { background: var(--vf-danger-soft); color: var(--vf-danger); }
.request-card .vf-btn { justify-self: start; }
</style>
