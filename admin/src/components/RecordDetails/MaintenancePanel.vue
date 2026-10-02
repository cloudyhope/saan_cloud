<template>
  <section v-if="!hidden" class="detail-section maintenance-panel" aria-labelledby="maintenance-heading">
    <div class="detail-section-heading">
      <div><h2 id="maintenance-heading">سرویس ادواری</h2>
        <p>مأموریت هر دوره چند روز پیش از موعد خودکار ساخته و به کارشناس اعلام می‌شود.</p></div>
      <button v-if="canEdit && elevators.length && !form" type="button" class="detail-text-link" @click="edit(null)">افزودن برنامه</button>
    </div>
    <div v-if="loading && !loaded" class="detail-state" role="status"><b-spinner small /> در حال دریافت…</div>
    <p v-else-if="error" class="plan-error" role="alert">{{ error }}</p>
    <template v-else>
      <p v-if="!plans.length && !form" class="detail-empty">برای {{ building ? 'آسانسورهای این ساختمان' : 'این آسانسور' }} برنامه سرویس ادواری تعریف نشده است.</p>
      <table v-if="plans.length" class="plan-table">
        <thead><tr><th v-if="building" scope="col">آسانسور</th><th scope="col">خدمت</th><th scope="col">دوره</th><th scope="col">موعد بعدی</th>
          <th scope="col">کارشناس</th><th scope="col">وضعیت</th><th v-if="canEdit" scope="col"><span class="sr-only">عملیات</span></th></tr></thead>
        <tbody>
          <tr v-for="plan in plans" :key="plan.id" :class="{ inactive: !plan.is_active }">
            <td v-if="building">{{ plan.elevator_title }}</td>
            <td>{{ plan.visit_type_name }}</td>
            <td>هر {{ fa(plan.interval_days) }} روز</td>
            <td>{{ jDate(plan.next_due) }}<small>ایجاد از {{ jDate(plan.opens_on) }}</small></td>
            <td>{{ plan.expert_name || 'نیازمند تخصیص' }}</td>
            <td>
              <span v-if="!plan.is_active" class="plan-chip is-off">متوقف</span>
              <router-link v-else-if="plan.open_visit" class="plan-chip is-open" :to="'/visitmanagment/answerlist/' + plan.open_visit">مأموریت باز {{ faId(plan.open_visit) }}</router-link>
              <span v-else class="plan-chip">در انتظار دوره</span>
            </td>
            <td v-if="canEdit" class="plan-actions">
              <RowActions :items="[{ label: 'ویرایش برنامه', icon: 'edit', action: () => edit(plan) }, { label: 'توقف برنامه', icon: 'close', action: () => stop(plan), danger: true, hidden: !plan.is_active || busy }]" />
            </td>
          </tr>
        </tbody>
      </table>
      <form v-if="form" class="plan-form" @submit.prevent="save">
        <label v-if="building" class="plan-field">آسانسور
          <select v-model.number="form.elevator" class="form-select" :disabled="!!form.id" required>
            <option v-for="item in elevators" :key="item.id" :value="item.id">{{ item.title || 'آسانسور ' + item.id }}</option>
          </select></label>
        <label class="plan-field">نوع خدمت
          <select v-model.number="form.visit_type" class="form-select" required>
            <option :value="null" disabled>انتخاب کنید</option>
            <option v-for="item in visitTypes" :key="item.id" :value="item.id">{{ item.name }}</option>
          </select></label>
        <label class="plan-field">کارشناس پیش‌فرض
          <select v-model="form.expert" class="form-select">
            <option :value="null">بدون کارشناس (برنامه‌ریز تخصیص می‌دهد)</option>
            <option v-for="item in experts" :key="item.id" :value="item.id">{{ item.name }}</option>
          </select></label>
        <label class="plan-field">دوره تکرار (روز)
          <input v-model.number="form.interval_days" type="number" min="7" max="730" class="form-control" required></label>
        <label class="plan-field">ایجاد پیش از موعد (روز)
          <input v-model.number="form.lead_days" type="number" min="0" max="60" class="form-control" required></label>
        <label class="plan-field">موعد سرویس بعدی
          <date-picker v-model="form.next_due" format="YYYY-MM-DD" display-format="jYYYY/jMM/jDD" :min="today" input-class="form-control" /></label>
        <label class="plan-field wide">یادداشت برای کارشناس
          <input v-model="form.note" type="text" maxlength="500" class="form-control" placeholder="مثلاً: روغن‌کاری ریل و بازدید ترمز"></label>
        <label v-if="form.id" class="plan-check"><input v-model="form.is_active" type="checkbox"> برنامه فعال است</label>
        <p v-if="formError" class="plan-error wide" role="alert">{{ formError }}</p>
        <div class="detail-form-actions wide">
          <button type="button" class="reject" :disabled="busy" @click="form = null">انصراف</button>
          <button type="submit" class="accept" :disabled="busy">{{ busy ? 'در حال ذخیره…' : 'ذخیره برنامه' }}</button>
        </div>
      </form>
    </template>
  </section>
</template>

<script>
import RowActions from '@/components/RowActions/index.vue';
const iso = (date) => `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;

export default {
  components: { RowActions },
  name: 'MaintenancePanel',
  props: {
    // [{ id, title }] the plans may target; one item on an elevator page.
    elevators: { type: Array, required: true },
    building: { type: [String, Number], default: null },
  },
  data: () => ({ plans: [], experts: [], visitTypes: [], loading: false, loaded: false, error: '', hidden: false,
    form: null, formError: '', busy: false, canEdit: true }),
  computed: {
    project() { return this.$STORE.state.userConfig.setProjectId; },
    base() { return `/api/admin/maintenance_plans/`; },
    filter() { return this.building ? `building=${this.building}` : `elevator=${(this.elevators[0] || {}).id}`; },
    today() { return iso(new Date()); },
  },
  watch: { filter: { immediate: true, handler: 'load' } },
  methods: {
    fa: (value) => Number(value || 0).toLocaleString('fa-IR'),
    faId: (value) => Number(value).toLocaleString('fa-IR', { useGrouping: false }),
    jDate(value) {
      if (!value) return '—';
      const date = new Date(value + 'T00:00:00');
      return Number.isNaN(date.getTime()) ? '—' : date.toLocaleDateString('fa-IR', { year: 'numeric', month: 'long', day: 'numeric' });
    },
    async load() {
      if (!this.elevators.length && !this.building) return;
      this.loading = true; this.error = '';
      const response = await this.$ApiServiceLayer.get(`${this.base}?p=${this.project}&${this.filter}`, this.$PATH.SERVICE_NAME.AUTH);
      this.loading = false;
      if (response.status === 403) { this.hidden = true; return; }
      if (response.status !== 200) { this.error = this.$ApiServiceLayer.getErrorMessage(response); return; }
      this.plans = response.data.results; this.experts = response.data.experts; this.visitTypes = response.data.visit_types;
      this.loaded = true;
    },
    edit(plan) {
      this.formError = '';
      const due = new Date(); due.setDate(due.getDate() + 30);
      this.form = plan
        ? { id: plan.id, elevator: plan.elevator, visit_type: plan.visit_type, expert: plan.expert, interval_days: plan.interval_days,
          lead_days: plan.lead_days, next_due: plan.next_due, note: plan.note, is_active: plan.is_active }
        : { id: null, elevator: (this.elevators[0] || {}).id, visit_type: (this.visitTypes[0] || {}).id || null, expert: null,
          interval_days: 30, lead_days: 7, next_due: iso(due), note: '', is_active: true };
    },
    async save() {
      this.busy = true; this.formError = '';
      const payload = { ...this.form };
      delete payload.id;
      const url = this.form.id ? `${this.base}${this.form.id}/?p=${this.project}` : `${this.base}?p=${this.project}`;
      const response = this.form.id
        ? await this.$ApiServiceLayer.put(url, this.$PATH.SERVICE_NAME.AUTH, payload)
        : await this.$ApiServiceLayer.post(url, this.$PATH.SERVICE_NAME.AUTH, payload);
      this.busy = false;
      if (![200, 201].includes(response.status)) {
        if (response.status === 403) this.canEdit = false;
        this.formError = response.status === 403 ? 'برای تعریف برنامه دسترسی ندارید.' : this.$ApiServiceLayer.getErrorMessage(response);
        return;
      }
      this.form = null;
      this.$notify && this.$notify({ group: 'tc', type: 'success', text: 'برنامه سرویس ادواری ذخیره شد.' });
      this.load();
    },
    async stop(plan) {
      this.busy = true;
      const response = await this.$ApiServiceLayer.delete(`${this.base}${plan.id}/?p=${this.project}`, this.$PATH.SERVICE_NAME.AUTH);
      this.busy = false;
      if (response.status !== 200) { this.error = this.$ApiServiceLayer.getErrorMessage(response); return; }
      this.load();
    },
  },
};
</script>

<style scoped>
.plan-table { width: 100%; border-collapse: collapse; font-size: 12.5px; margin-bottom: 12px; }
.plan-table th { text-align: right; padding: 8px; background: #f3f6fa; color: #4a566c; font-weight: 700; }
.plan-table td { padding: 8px; border-bottom: 1px solid #eef1f6; vertical-align: top; }
.plan-table td small { display: block; color: #7a8496; font-size: 11px; }
.plan-table tr.inactive td { color: #98a1b2; }
.plan-chip { display: inline-block; padding: 2px 8px; border-radius: 8px; background: #eef2f8; color: #4a566c; font-size: 11.5px; font-weight: 700; }
.plan-chip.is-open { background: #e6effd; color: #24479f; text-decoration: none; }
.plan-chip.is-off { background: #f1f1f1; color: #7a7a7a; }
.plan-actions { white-space: nowrap; }
.plan-actions .detail-text-link { border: 0; background: transparent; padding: 0 4px; }
.plan-actions .danger { color: #b42d2d; }
.plan-form { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 10px; align-items: end; padding-top: 12px; border-top: 1px solid #edf0f6; }
/* The admin theme styles every label at ID specificity; match it to stack caption over control. */
#app .layout-container .plan-field { display: grid; gap: 5px; margin: 0; font-size: 12px; font-weight: 700; color: #4e5c74; }
#app .layout-container .plan-check { display: flex; align-items: center; gap: 6px; margin: 0; font-size: 12.5px; }
.plan-form .wide { grid-column: 1 / -1; }
.plan-form .detail-form-actions { margin: 0; }
.plan-error { color: #a12b2b; background: #fdeceb; padding: 9px 12px; border-radius: 10px; font-size: 12.5px; margin: 0; }
.detail-text-link { border: 0; background: transparent; }
.sr-only { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); }
</style>
