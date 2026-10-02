<template>
  <main class="ops-page" dir="rtl">
    <header class="page-head">
      <div>
        <span class="eyebrow">مدیریت ویزیت‌ها</span>
        <h1>انواع خدمت</h1>
        <p>دستمزد پیش‌فرض هر نوع خدمت روی مأموریت‌های تازه آن ثبت می‌شود و در سوابق کارشناس نمایش داده می‌شود. با فعال‌کردن «کد تأیید مدیر ساختمان»، کارشناس فقط با کدی که در اپ مدیر ساختمان نمایش داده می‌شود می‌تواند پایان خدمت را ثبت کند. «اجرت در گزارش مشتری» همین دستمزد را در گزارش و PDF مشتری نشان می‌دهد؛ پیش‌فرض پنهان است.</p>
      </div>
    </header>
    <section class="panel" aria-labelledby="types-title">
      <div class="panel-head"><h2 id="types-title">تنظیمات هر نوع خدمت</h2></div>
      <p v-if="error" class="error" role="alert">{{ error }}</p>
      <div class="table-wrap" :class="{ busy: loading }">
        <table>
          <thead><tr><th scope="col">نوع خدمت</th><th scope="col">دستمزد پیش‌فرض (ریال)</th><th scope="col">کد تأیید مدیر ساختمان</th><th scope="col">اجرت در گزارش مشتری</th><th scope="col">وضعیت</th><th scope="col"><span class="sr-only">ذخیره</span></th></tr></thead>
          <tbody>
            <tr v-for="row in rows" :key="row.id" :class="{ inactive: !row.is_active, dirty: row.dirty }">
              <td><input v-model.trim="row.verbose_name" class="form-control" maxlength="40" :aria-label="'عنوان ' + (row.title || '')" :disabled="!canEdit" @input="row.dirty = true">
                <small v-if="row.title" dir="ltr">{{ row.title }}</small></td>
              <td><input v-model.number="row.default_wage" class="form-control num" type="number" min="0" step="10000" :aria-label="'دستمزد ' + row.verbose_name" :disabled="!canEdit" @input="row.dirty = true">
                <small>{{ fa(row.default_wage) }} ریال</small></td>
              <td><label class="switch"><input v-model="row.requires_client_code" type="checkbox" :disabled="!canEdit" @change="row.dirty = true">{{ row.requires_client_code ? 'لازم است' : 'لازم نیست' }}</label></td>
              <td><label class="switch"><input v-model="row.show_wage_in_report" type="checkbox" :disabled="!canEdit" @change="row.dirty = true">{{ row.show_wage_in_report ? 'نمایش' : 'پنهان' }}</label>
                <small>این مبلغ حق‌الزحمه کارشناس هم هست</small></td>
              <td><label class="switch"><input v-model="row.is_active" type="checkbox" :disabled="!canEdit" @change="row.dirty = true">{{ row.is_active ? 'فعال' : 'غیرفعال' }}</label></td>
              <td><button v-if="canEdit" type="button" class="primary" :disabled="!row.dirty || busy === row.id" @click="save(row)">{{ busy === row.id ? '…' : 'ذخیره' }}</button></td>
            </tr>
            <tr v-if="!rows.length && !loading"><td colspan="6"><EmptyState kind="generic" size="sm" inline title="نوع خدمتی تعریف نشده" description="" /></td></tr>
          </tbody>
        </table>
      </div>
      <p class="muted foot">تغییر دستمزد روی مأموریت‌هایی که قبلاً ساخته شده‌اند اثر ندارد.</p>
    </section>
  </main>
</template>

<script>
import EmptyState from '@/components/EmptyState/index.vue';
const FIELDS = ['verbose_name', 'default_wage', 'requires_client_code', 'show_wage_in_report', 'is_active'];

export default {
  components: { EmptyState },
  name: 'VisitTypes',
  data: () => ({ rows: [], loading: false, error: '', busy: null, canEdit: true }),
  computed: { project() { return this.$STORE.state.userConfig.setProjectId; } },
  created() { this.load(); },
  methods: {
    fa: (value) => Number(value || 0).toLocaleString('fa-IR'),
    async load() {
      this.loading = true; this.error = '';
      const response = await this.$ApiServiceLayer.get(
        `${this.$PATH.RELATIVE_PATH.GET.VISIT_TYPE}?p=${this.project}&include_inactive=1&ordering=id`, this.$PATH.SERVICE_NAME.AUTH);
      this.loading = false;
      if (response.status !== 200) { this.error = this.$ApiServiceLayer.getErrorMessage(response); return; }
      const rows = Array.isArray(response.data) ? response.data : response.data.results || [];
      this.rows = rows.map((row) => ({ id: row.id, title: row.title, ...FIELDS.reduce((acc, key) => ({ ...acc, [key]: row[key] }), {}),
        verbose_name: row.verbose_name || row.title || '', dirty: false }));
    },
    async save(row) {
      this.busy = row.id; this.error = '';
      const payload = FIELDS.reduce((acc, key) => ({ ...acc, [key]: row[key] }), {});
      const response = await this.$ApiServiceLayer.patch(`/api/admin/visit_type/edits/${row.id}/?p=${this.project}`, this.$PATH.SERVICE_NAME.AUTH, payload);
      this.busy = null;
      if (response.status !== 200) {
        if (response.status === 403) this.canEdit = false;
        this.error = response.status === 403 ? 'برای تغییر انواع خدمت دسترسی ندارید.' : this.$ApiServiceLayer.getErrorMessage(response);
        return;
      }
      row.dirty = false;
      this.$notify && this.$notify({ group: 'tc', type: 'success', text: 'تنظیمات نوع خدمت ذخیره شد.' });
    },
  },
};
</script>

<style scoped>
.ops-page { display: grid; gap: 16px; color: #25324b; }
.page-head { padding: 22px 24px; border-radius: 18px; background: linear-gradient(140deg, #16264a, #2a4f9a); color: #fff; box-shadow: 0 12px 28px #16264a26; }
.eyebrow { color: #c6d6ff; font-size: 12px; font-weight: 700; }
.page-head h1 { color: #fff; font-size: 22px; margin: 4px 0; }
.page-head p { color: #dde6ff; font-size: 12.5px; line-height: 1.9; margin: 0; max-width: 760px; }
.panel { padding: 18px; border-radius: 16px; background: #fff; border: 1px solid #e3e9f2; box-shadow: 0 4px 14px #1b2a4a08; }
.panel-head h2 { font-size: 16px; font-weight: 800; color: #17233b; margin: 0 0 12px; }
.table-wrap { overflow-x: auto; transition: opacity .2s; }
.table-wrap.busy { opacity: .55; }
table { width: 100%; border-collapse: collapse; font-size: 12.5px; }
th { text-align: right; color: #6b778d; font-weight: 700; padding: 9px 8px; border-bottom: 1px solid #e3e9f2; white-space: nowrap; }
td { padding: 10px 8px; border-bottom: 1px solid #f0f2f6; vertical-align: top; }
td small { display: block; color: #7a8496; font-size: 11px; margin-top: 3px; }
td .form-control { min-height: 36px; font-size: 12.5px; max-width: 240px; }
td .num { direction: ltr; text-align: left; }
tr.inactive td { color: #98a1b2; }
tr.dirty { background: #f6f9ff; }
#app .layout-container .switch { display: inline-flex; align-items: center; gap: 6px; margin: 6px 0 0; font-size: 12.5px; font-weight: 700; color: #4a566c; }
.empty { padding: 22px; text-align: center; color: #7a8496; }
.error { color: #a12b2b; background: #fdeceb; padding: 9px 12px; border-radius: 10px; font-size: 12.5px; }
.muted { color: #7a8496; font-size: 12px; }
.foot { margin: 10px 0 0; }
button.primary { min-height: 34px; padding: 5px 14px; border: 0; border-radius: 10px; background: #345de0; color: #fff; font: inherit; font-size: 12.5px; font-weight: 700; cursor: pointer; }
button.primary:disabled { background: #b8c6ee; cursor: default; }
.sr-only { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); }
</style>
