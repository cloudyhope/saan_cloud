<template>
  <main class="ops-page" dir="rtl">
    <header class="page-head">
      <div>
        <span class="eyebrow">مدیریت انبار</span>
        <h1>درخواست‌های قطعه کارشناسان</h1>
        <p>کارشناس در حین مأموریت قطعه یدکی درخواست می‌دهد. با انتخاب انبار مبدأ، قطعه به موجودی کارشناس منتقل و در دفتر انبار ثبت می‌شود؛ رد درخواست با ذکر دلیل به کارشناس اعلام می‌شود.</p>
      </div>
      <div class="head-stat"><strong>{{ fa(pending) }}</strong><span>در انتظار رسیدگی</span></div>
    </header>

    <section class="panel" aria-labelledby="queue-title">
      <div class="panel-head"><div><h2 id="queue-title">صف درخواست‌ها</h2></div></div>
      <div class="toolbar">
        <div class="segmented" role="group" aria-label="وضعیت">
          <button v-for="item in statuses" :key="item.key" type="button" :class="{ active: status === item.key }" :aria-pressed="status === item.key ? 'true' : 'false'"
                  @click="status = item.key">{{ item.label }}</button>
        </div>
        <input v-model.trim="search" class="form-control search" type="search" placeholder="قطعه، کد کالا، کارشناس یا ساختمان" aria-label="جستجو" />
      </div>
      <p v-if="error" class="error" role="alert">{{ error }}</p>
      <div class="table-wrap" :class="{ busy: loading }">
        <table>
          <thead><tr><th scope="col">قطعه</th><th scope="col">تعداد</th><th scope="col">کارشناس و مأموریت</th><th scope="col">ثبت</th><th scope="col">وضعیت</th><th scope="col">رسیدگی</th></tr></thead>
          <tbody>
            <tr v-for="row in rows" :key="row.id">
              <td><b>{{ row.ware_name }}</b><small v-if="row.identifier" dir="ltr">{{ row.identifier }}</small><small v-if="row.note" class="note">«{{ row.note }}»</small></td>
              <td class="num">{{ fa(row.amount) }} {{ row.unit }}</td>
              <td>{{ row.requester }}<small><router-link :to="'/visitmanagment/answerlist/' + row.visit">مأموریت {{ faId(row.visit) }}</router-link>{{ row.building ? ' · ' + row.building : '' }}</small></td>
              <td class="muted">{{ dateTime(row.created_at) }}</td>
              <td><span class="chip" :class="'is-' + row.status.toLowerCase()">{{ row.status_label }}</span></td>
              <td class="decide">
                <template v-if="row.status === 'PENDING'">
                  <p v-if="!row.stock.length" class="muted">هیچ انباری موجودی کافی ندارد.</p>
                  <div v-else class="decide-row">
                    <select v-model.number="choice[row.id]" class="form-select" :aria-label="'انبار مبدأ ' + row.ware_name">
                      <option :value="undefined" disabled>انبار مبدأ</option>
                      <option v-for="item in row.stock" :key="item.location" :value="item.location" :disabled="item.amount < row.amount">{{ item.name }} · موجودی {{ fa(item.amount) }}</option>
                    </select>
                    <button type="button" class="primary" :disabled="busy === row.id || !choice[row.id]" @click="decide(row, 'fulfill')">تحویل</button>
                  </div>
                  <button type="button" class="link danger" :disabled="busy === row.id" @click="rejecting = row">رد درخواست</button>
                </template>
                <span v-else class="muted">{{ row.location ? 'از ' + row.location : row.decision_note || '—' }}{{ row.decided_by ? ' · ' + row.decided_by : '' }}</span>
              </td>
            </tr>
            <tr v-if="!rows.length && !loading"><td colspan="6"><EmptyState kind="parts" size="sm" inline title="درخواستی در این وضعیت نیست" description="" /></td></tr>
          </tbody>
        </table>
      </div>
      <div class="table-foot"><span class="muted">{{ fa(rows.length) }} از {{ fa(count) }} مورد</span>
        <button v-if="rows.length < count" type="button" class="ghost" :disabled="loading" @click="load(false)">نمایش بیشتر</button></div>
    </section>

    <b-modal :visible="!!rejecting" title="رد درخواست قطعه" ok-title="رد درخواست" cancel-title="انصراف" ok-variant="danger"
             :ok-disabled="rejectNote.trim().length < 5 || !!busy" @ok.prevent="decide(rejecting, 'reject')" @hidden="rejecting = null; rejectNote = ''">
      <p v-if="rejecting" class="muted">{{ rejecting.ware_name }} · {{ fa(rejecting.amount) }} عدد برای {{ rejecting.requester }}</p>
      <label class="field" for="reject-note">دلیل رد (به کارشناس اعلام می‌شود)</label>
      <textarea id="reject-note" v-model="rejectNote" class="form-control" rows="3" maxlength="500" />
    </b-modal>
  </main>
</template>

<script>
import EmptyState from '@/components/EmptyState/index.vue';
const PAGE = 50;

export default {
  components: { EmptyState },
  name: 'PartRequests',
  data: () => ({
    rows: [], count: 0, pending: 0, loading: false, error: '', status: 'PENDING', search: '', choice: {}, busy: null,
    rejecting: null, rejectNote: '', timer: null, sequence: 0,
    statuses: [{ key: 'PENDING', label: 'در انتظار' }, { key: 'FULFILLED', label: 'تحویل‌شده' }, { key: 'REJECTED', label: 'ردشده' },
      { key: 'CANCELED', label: 'لغوشده' }, { key: '', label: 'همه' }],
  }),
  computed: { project() { return this.$STORE.state.userConfig.setProjectId; } },
  watch: {
    status() { this.load(true); },
    search() { clearTimeout(this.timer); this.timer = setTimeout(() => this.load(true), 300); },
  },
  created() { this.load(true); },
  beforeDestroy() { clearTimeout(this.timer); },
  methods: {
    fa: (value) => Number(value || 0).toLocaleString('fa-IR'),
    faId: (value) => Number(value).toLocaleString('fa-IR', { useGrouping: false }),
    dateTime(value) {
      const date = new Date(value);
      return Number.isNaN(date.getTime()) ? '' : date.toLocaleString('fa-IR', { month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit' });
    },
    async load(reset) {
      const sequence = ++this.sequence;
      const offset = reset ? 0 : this.rows.length;
      this.loading = true; this.error = '';
      const query = new URLSearchParams({ p: this.project, status: this.status, search: this.search, limit: PAGE, offset });
      const response = await this.$ApiServiceLayer.get(`/api/warehouse/v1/part_requests/?${query}`, this.$PATH.SERVICE_NAME.EMPTY);
      if (sequence !== this.sequence) return;
      this.loading = false;
      if (response.status !== 200) {
        this.error = response.status === 403 ? 'رسیدگی به درخواست‌های قطعه نیازمند نقش مدیریت انبار است.' : this.$ApiServiceLayer.getErrorMessage(response);
        return;
      }
      this.rows = reset ? response.data.results : [...this.rows, ...response.data.results];
      this.count = response.data.count; this.pending = response.data.pending;
      // Preselect the warehouse that can cover the whole request.
      this.rows.forEach((row) => {
        if (row.status === 'PENDING' && this.choice[row.id] === undefined) {
          const enough = row.stock.find((item) => item.amount >= row.amount);
          if (enough) this.$set(this.choice, row.id, enough.location);
        }
      });
    },
    async decide(row, action) {
      if (!row) return;
      this.busy = row.id; this.error = '';
      const payload = action === 'fulfill' ? { action, location: this.choice[row.id] } : { action, note: this.rejectNote.trim() };
      const response = await this.$ApiServiceLayer.post(`/api/warehouse/v1/part_requests/${row.id}/decision/?p=${this.project}`,
        this.$PATH.SERVICE_NAME.EMPTY, payload);
      this.busy = null;
      if (response.status !== 200) { this.error = this.$ApiServiceLayer.getErrorMessage(response); this.rejecting = null; return; }
      this.rejecting = null;
      this.$notify && this.$notify({ group: 'tc', type: 'success', text: action === 'fulfill' ? 'قطعه به موجودی کارشناس منتقل شد.' : 'درخواست رد و به کارشناس اعلام شد.' });
      this.load(true);
    },
  },
};
</script>

<style scoped>
.ops-page { display: grid; gap: 16px; color: #25324b; }
.page-head { display: flex; align-items: flex-end; justify-content: space-between; gap: 16px; padding: 22px 24px; border-radius: 18px;
  background: linear-gradient(140deg, #16264a, #2a4f9a); color: #fff; box-shadow: 0 12px 28px #16264a26; }
.eyebrow { color: #c6d6ff; font-size: 12px; font-weight: 700; }
.page-head h1 { color: #fff; font-size: 22px; margin: 4px 0; }
.page-head p { color: #dde6ff; font-size: 12.5px; line-height: 1.9; margin: 0; max-width: 720px; }
.head-stat { display: grid; justify-items: center; flex: none; padding: 10px 18px; border-radius: 14px; background: #ffffff1f; }
.head-stat strong { font-size: 26px; line-height: 1.2; }
.head-stat span { font-size: 11.5px; color: #dde6ff; }
.panel { padding: 18px; border-radius: 16px; background: #fff; border: 1px solid #e3e9f2; box-shadow: 0 4px 14px #1b2a4a08; }
.panel-head h2 { font-size: 16px; font-weight: 800; color: #17233b; margin: 0 0 12px; }
.toolbar { display: flex; flex-wrap: wrap; align-items: center; gap: 10px; margin-bottom: 12px; }
.segmented { display: inline-flex; flex-wrap: wrap; gap: 3px; padding: 3px; border-radius: 11px; background: #eef2f8; }
.segmented button { min-height: 34px; padding: 5px 12px; border: 0; border-radius: 9px; background: transparent; color: #4a566c; font: inherit; font-size: 12.5px; font-weight: 700; cursor: pointer; }
.segmented button.active { background: #fff; color: #17233b; box-shadow: 0 2px 6px #1b2a4a1f; }
.search { max-width: 300px; min-height: 38px; }
.table-wrap { overflow-x: auto; transition: opacity .2s; }
.table-wrap.busy { opacity: .55; }
table { width: 100%; border-collapse: collapse; font-size: 12.5px; }
th { text-align: right; color: #6b778d; font-weight: 700; padding: 9px 8px; border-bottom: 1px solid #e3e9f2; white-space: nowrap; }
td { padding: 10px 8px; border-bottom: 1px solid #f0f2f6; vertical-align: top; }
td small { display: block; color: #7a8496; font-size: 11px; margin-top: 2px; }
td small.note { color: #6c4513; }
.num { white-space: nowrap; font-variant-numeric: tabular-nums; }
.chip { display: inline-block; padding: 2px 8px; border-radius: 8px; font-size: 11.5px; font-weight: 700; background: #eef2f8; color: #4a566c; white-space: nowrap; }
.chip.is-pending { background: #fff4dc; color: #8a5a00; }
.chip.is-fulfilled { background: #e3f4ea; color: #13703f; }
.chip.is-rejected { background: #fdeceb; color: #a12b2b; }
.decide { min-width: 250px; }
.decide-row { display: flex; gap: 6px; margin-bottom: 4px; }
.decide-row .form-select { min-height: 36px; font-size: 12px; }
.table-foot { display: flex; align-items: center; justify-content: space-between; margin-top: 10px; }
.muted { color: #7a8496; font-size: 12px; margin: 0; }
.empty { padding: 22px; text-align: center; color: #7a8496; }
.error { color: #a12b2b; background: #fdeceb; padding: 9px 12px; border-radius: 10px; font-size: 12.5px; }
button.primary, button.ghost, button.link { min-height: 36px; padding: 6px 14px; border-radius: 10px; font: inherit; font-size: 12.5px; font-weight: 700; cursor: pointer; white-space: nowrap; }
button.primary { border: 0; background: #345de0; color: #fff; }
button.primary:disabled { background: #b8c6ee; cursor: default; }
button.ghost { border: 1px solid #d4dceb; background: #fff; color: #345de0; }
button.link { border: 0; background: transparent; color: #345de0; padding: 2px 0; min-height: 0; }
button.link.danger { color: #b42d2d; }
#app .layout-container .field { display: block; margin: 8px 0 4px; font-size: 12px; font-weight: 700; color: #4e5c74; }
@media (max-width: 720px) { .page-head { flex-direction: column; align-items: stretch; } }
</style>
