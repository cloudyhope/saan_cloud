<template>
  <section v-if="!hidden" class="detail-section field-ops" aria-labelledby="field-ops-heading">
    <div class="detail-section-heading">
      <div><h2 id="field-ops-heading">عملیات میدانی</h2><p>پذیرش کارشناس، قطعات درخواستی، گفتگو با مدیر ساختمان و کد تأیید پایان کار.</p></div>
      <button type="button" class="detail-text-link" :disabled="loading" @click="load">به‌روزرسانی</button>
    </div>
    <div v-if="loading && !data" class="detail-state" role="status"><b-spinner small /> در حال دریافت…</div>
    <p v-else-if="error" class="ops-error" role="alert">{{ error }}</p>
    <template v-else-if="data">
      <div class="ops-grid">
        <div class="ops-tile">
          <span>وضعیت ارجاع</span>
          <strong :class="'is-' + data.assignment.state">{{ assignmentLabel }}</strong>
          <small v-if="data.assignment.accepted_at">پذیرش: {{ dateTime(data.assignment.accepted_at) }}</small>
        </div>
        <div v-if="data.requires_client_code" class="ops-tile">
          <span>کد تأیید مدیر ساختمان</span>
          <strong class="ops-code" dir="ltr">{{ data.completion_code || '—' }}</strong>
          <small>فقط اگر مدیر ساختمان به اپ دسترسی ندارد، کد را مستقیم به خود او بدهید.</small>
        </div>
        <div v-if="data.maintenance_plan" class="ops-tile">
          <span>منشأ مأموریت</span><strong>برنامه سرویس ادواری</strong><small>شماره برنامه {{ faId(data.maintenance_plan) }}</small>
        </div>
      </div>
      <div v-if="data.assignment.state === 'unassigned' && suggestions.length" class="ops-suggest">
        <h3 class="ops-subtitle">کارشناسان پیشنهادی <router-link class="detail-text-link" to="/assignment">تخصیص هوشمند</router-link></h3>
        <p v-if="assignMessage" class="ops-note" role="status">{{ assignMessage }}</p>
        <ul>
          <li v-for="item in suggestions" :key="item.user" :class="{ blocked: !item.eligible }">
            <span><b>{{ item.name }}</b><small>امتیاز {{ fa(item.score) }} · مهارت {{ fa(item.factors.skill.value) }} · کیفیت {{ fa(item.factors.quality.value) }} · ظرفیت {{ fa(item.factors.workload.value) }}</small>
              <small v-for="text in item.blockers" :key="text" class="blk">⛔ {{ text }}</small></span>
            <button type="button" class="detail-text-link" :disabled="busy || !item.eligible" @click="assign(item)">تخصیص</button>
          </li>
        </ul>
      </div>
      <div v-if="data.assignment.last_decline" class="ops-decline" role="note">
        <b>بازگردانده‌شده توسط {{ data.assignment.last_decline.by }}</b> · {{ dateTime(data.assignment.last_decline.at) }}
        <p>«{{ data.assignment.last_decline.reason }}»</p>
      </div>

      <h3 class="ops-subtitle">قطعات درخواستی <small v-if="data.parts.length">({{ fa(data.parts.length) }})</small></h3>
      <p v-if="!data.parts.length" class="ops-empty">برای این مأموریت قطعه‌ای درخواست نشده است.</p>
      <table v-else class="ops-table">
        <thead><tr><th scope="col">قطعه</th><th scope="col">تعداد</th><th scope="col">درخواست‌کننده</th><th scope="col">وضعیت</th><th scope="col">انبار / توضیح</th></tr></thead>
        <tbody>
          <tr v-for="row in data.parts" :key="row.id">
            <td>{{ row.ware_name }}<small v-if="row.identifier" dir="ltr">{{ row.identifier }}</small></td>
            <td>{{ fa(row.amount) }} {{ row.unit }}</td>
            <td>{{ row.requester }}<small>{{ dateTime(row.created_at) }}</small></td>
            <td><span class="ops-status" :class="'is-' + row.status.toLowerCase()">{{ row.status_label }}</span></td>
            <td>{{ row.location || row.decision_note || row.note || '—' }}</td>
          </tr>
        </tbody>
      </table>
      <router-link v-if="data.parts.some(p => p.status === 'PENDING')" class="detail-text-link" to="/warehouse/part-requests">رسیدگی در صف درخواست‌های قطعه</router-link>

      <h3 class="ops-subtitle">گفتگوی کارشناس و مدیر ساختمان <small>{{ data.chat.open ? '(باز)' : '(بسته)' }}</small></h3>
      <p v-if="!data.chat.messages.length" class="ops-empty">پیامی رد و بدل نشده است.</p>
      <ol v-else class="ops-chat">
        <li v-for="message in data.chat.messages" :key="message.id" :class="'is-' + message.side">
          <b>{{ message.name }} · {{ message.side === 'expert' ? 'کارشناس' : 'مدیر ساختمان' }}</b>
          <p>{{ message.body }}</p><small>{{ dateTime(message.at) }}</small>
        </li>
      </ol>
    </template>
  </section>
</template>

<script>
const STATE = { accepted: 'پذیرفته شده', pending: 'منتظر پذیرش کارشناس', unassigned: 'بدون کارشناس؛ نیازمند تخصیص' };

export default {
  name: 'FieldOpsPanel',
  props: { visitId: { type: [String, Number], required: true } },
  data: () => ({ data: null, loading: false, error: '', hidden: false, suggestions: [], busy: false, assignMessage: '' }),
  computed: {
    project() { return this.$STORE.state.userConfig.setProjectId; },
    assignmentLabel() { return STATE[this.data.assignment.state] || '—'; },
  },
  watch: { visitId: { immediate: true, handler: 'load' } },
  methods: {
    fa: value => Number(value || 0).toLocaleString('fa-IR'),
    faId: value => Number(value).toLocaleString('fa-IR', { useGrouping: false }),
    dateTime(value) {
      if (!value) return '';
      const date = new Date(value);
      return Number.isNaN(date.getTime()) ? '' : date.toLocaleString('fa-IR', { month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit' });
    },
    async load() {
      this.loading = true; this.error = '';
      const response = await this.$ApiServiceLayer.get(
        `/api/admin/visit/${this.visitId}/field_ops/?p=${this.project}`, this.$PATH.SERVICE_NAME.AUTH);
      this.loading = false;
      if (response.status === 403) { this.hidden = true; return; }
      if (response.status !== 200) { this.error = this.$ApiServiceLayer.getErrorMessage(response); return; }
      this.data = response.data;
      this.suggestions = [];
      if (response.data.assignment.state === 'unassigned') this.loadSuggestions();
    },
    async loadSuggestions() {
      const response = await this.$ApiServiceLayer.get(`/api/admin/assignment/plan/?p=${this.project}&visit=${this.visitId}`, this.$PATH.SERVICE_NAME.AUTH);
      if (response.status === 200 && response.data.assignable) this.suggestions = response.data.candidates.slice(0, 3);
    },
    async assign(item) {
      this.busy = true; this.assignMessage = '';
      const response = await this.$ApiServiceLayer.post(`/api/admin/assignment/apply/?p=${this.project}`, this.$PATH.SERVICE_NAME.AUTH,
        { assignments: [{ visit: Number(this.visitId), expert: item.user }] });
      this.busy = false;
      const result = response.status === 200 ? response.data.results[0] : null;
      if (!result || !result.ok) { this.assignMessage = result ? result.error : this.$ApiServiceLayer.getErrorMessage(response); return; }
      this.assignMessage = 'کارشناس تخصیص یافت و مطلع شد.';
      this.load();
    },
  },
};
</script>

<style scoped>
.ops-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 10px; margin-bottom: 12px; }
.ops-tile { display: grid; gap: 3px; padding: 12px 14px; border: 1px solid #e3e9f2; border-radius: 12px; background: #fafbfd; }
.ops-tile span { font-size: 11.5px; color: #6b778d; font-weight: 700; }
.ops-tile strong { font-size: 14px; color: #17233b; }
.ops-tile strong.is-pending { color: #8a5a00; }
.ops-tile strong.is-unassigned { color: #b42d2d; }
.ops-tile strong.is-accepted { color: #13703f; }
.ops-tile small { font-size: 11px; color: #7a8496; line-height: 1.7; }
.ops-code { font-size: 22px !important; letter-spacing: 5px; font-variant-numeric: tabular-nums; }
.ops-decline { padding: 10px 14px; margin-bottom: 12px; border-radius: 12px; background: #fff6e8; color: #6c4513; font-size: 12.5px; }
.ops-decline p { margin: 4px 0 0; }
.ops-subtitle { margin: 16px 0 8px; font-size: 13.5px; font-weight: 800; color: #25324b; }
.ops-subtitle small { color: #7a8496; font-weight: 400; }
.ops-empty { color: #7a8496; font-size: 12.5px; margin: 0; }
.ops-table { width: 100%; border-collapse: collapse; font-size: 12.5px; }
.ops-table th { text-align: right; padding: 8px; background: #f3f6fa; color: #4a566c; font-weight: 700; }
.ops-table td { padding: 8px; border-bottom: 1px solid #eef1f6; vertical-align: top; }
.ops-table small { display: block; color: #7a8496; font-size: 11px; }
.ops-status { display: inline-block; padding: 2px 8px; border-radius: 8px; font-size: 11.5px; font-weight: 700; background: #eef2f8; color: #4a566c; }
.ops-status.is-pending { background: #fff4dc; color: #8a5a00; }
.ops-status.is-fulfilled { background: #e3f4ea; color: #13703f; }
.ops-status.is-rejected { background: #fdeceb; color: #a12b2b; }
.ops-chat { list-style: none; margin: 0; padding: 0; display: grid; gap: 8px; max-height: 340px; overflow-y: auto; }
.ops-chat li { padding: 8px 12px; border-radius: 12px; background: #f4f7fb; font-size: 12.5px; max-width: 80%; }
.ops-chat li.is-expert { background: #e9f2fd; justify-self: start; }
.ops-chat li.is-client { justify-self: end; }
.ops-chat p { margin: 2px 0; white-space: pre-line; }
.ops-chat small { color: #7a8496; font-size: 10.5px; }
.ops-suggest ul { list-style: none; margin: 0 0 12px; padding: 0; display: grid; gap: 6px; }
.ops-suggest li { display: flex; justify-content: space-between; align-items: center; gap: 10px; padding: 8px 12px; border-radius: 10px; background: #f4f8ff; font-size: 12.5px; }
.ops-suggest li.blocked { background: #f6f6f6; color: #98a1b2; }
.ops-suggest li span { display: grid; }
.ops-suggest small { color: #6b778d; font-size: 11px; }
.ops-suggest small.blk { color: #a12b2b; }
.ops-note { margin: 0 0 8px; color: #13703f; font-size: 12.5px; }
.ops-error { color: #a12b2b; background: #fdeceb; padding: 9px 12px; border-radius: 10px; font-size: 12.5px; }
.detail-text-link { border: 0; background: transparent; }
</style>
