<template>
  <main class="priority-page" dir="rtl">
    <header class="page-head">
      <div>
        <span class="eyebrow">اولویت‌بندی خدمات</span>
        <h1>کارهای حساس‌تر، زودتر</h1>
        <p>هر عامل یک ضریب دارد؛ امتیاز ۰ تا ۱۰۰ هر مشتری، ساختمان و آسانسور میانگین وزنی گزینه‌های انتخاب‌شده است. ساختمان عوامل مشتری مدیرش را، و آسانسور عوامل ساختمان و مشتری را هم به ارث می‌برد. فهرست مأموریت کارشناسان و ویزیت‌ها به ترتیب همین امتیاز مرتب می‌شود.</p>
      </div>
      <div class="tabs" role="tablist">
        <button v-for="item in tabs" :key="item.key" type="button" role="tab" :aria-selected="tab === item.key ? 'true' : 'false'"
                :class="{ active: tab === item.key }" @click="tab = item.key">{{ item.label }}</button>
      </div>
    </header>

    <!-- Ranking -->
    <section v-if="tab === 'ranking'" class="panel" aria-labelledby="ranking-title">
      <div class="panel-head">
        <div><h2 id="ranking-title">رتبه‌بندی بر اساس اولویت</h2><p>برای تغییر انتخاب‌ها روی هر مورد کلیک کنید و در صفحه جزئیات آن، بخش «اولویت خدمات» را ببینید.</p></div>
      </div>
      <div class="toolbar">
        <div class="segmented" role="group" aria-label="نوع">
          <button v-for="item in targets" :key="item.key" type="button" :class="{ active: target === item.key }" @click="target = item.key">{{ item.label }}</button>
        </div>
        <div class="segmented" role="group" aria-label="سطح اولویت">
          <button type="button" :class="{ active: !level }" @click="level = ''">همه سطوح</button>
          <button v-for="item in levels" :key="item.key" type="button" :class="{ active: level === item.key }" @click="level = item.key"><i :style="{ background: item.color }" />{{ item.label }}</button>
        </div>
        <input v-model.trim="search" class="form-control search" type="search" placeholder="جستجوی نام یا کد" aria-label="جستجو" />
      </div>
      <p v-if="rankingError" class="error" role="alert">{{ rankingError }}</p>
      <div class="table-wrap" :class="{ busy: rankingLoading }">
        <table>
          <thead><tr><th>رتبه</th><th>{{ targetLabel }}</th><th>{{ target === 'building' ? 'مدیر فعلی' : target === 'elevator' ? 'ساختمان' : '' }}</th><th>امتیاز</th><th>سطح</th></tr></thead>
          <tbody>
            <tr v-for="(row, index) in rows" :key="row.id" @click="$router.push(detail(row.id))">
              <td class="rank">{{ fa(index + 1) }}</td>
              <td><router-link :to="detail(row.id)">{{ row.label }}</router-link></td>
              <td class="muted">{{ row.context || '—' }}</td>
              <td class="score-cell"><span class="score-track"><span :style="{ width: (row.score || 0) + '%', background: color(row.score) }" /></span><b>{{ faScore(row.score) }}</b></td>
              <td><PriorityBadge :score="row.score" :show-score="false" /></td>
            </tr>
            <tr v-if="!rows.length && !rankingLoading"><td colspan="5"><EmptyState kind="search" size="sm" inline title="موردی پیدا نشد" description="" /></td></tr>
          </tbody>
        </table>
      </div>
      <div class="table-foot"><span class="muted">{{ fa(rows.length) }} از {{ fa(count) }} مورد</span>
        <button v-if="rows.length < count" type="button" class="ghost" :disabled="rankingLoading" @click="loadRanking(false)">نمایش بیشتر</button></div>
    </section>

    <!-- Factors and weights -->
    <section v-else class="panel" aria-labelledby="factors-title">
      <div class="panel-head">
        <div><h2 id="factors-title">عوامل و ضرایب</h2><p>عامل تازه اضافه کنید، ضریب را تغییر دهید یا گزینه‌ها و امتیازشان را تنظیم کنید. پس از ذخیره، امتیاز همه موارد پروژه دوباره محاسبه می‌شود.</p></div>
        <button type="button" class="primary" @click="addFactor">+ افزودن عامل</button>
      </div>
      <p v-if="factorsError" class="error" role="alert">{{ factorsError }}</p>
      <div v-if="weightTotal" class="share">
        <span class="share-title">سهم هر عامل در امتیاز آسانسور</span>
        <div class="share-bar"><span v-for="factor in activeFactors" :key="factor.key" :style="{ width: (factor.weight / weightTotal * 100) + '%' }" :title="factor.name"><em>{{ factor.name }} · {{ fa(Math.round(factor.weight / weightTotal * 100)) }}٪</em></span></div>
      </div>
      <div class="factor-list">
        <article v-for="factor in factors" :key="factor.key" class="factor" :class="{ inactive: !factor.is_active, dirty: factor.dirty }">
          <div class="factor-row">
            <label class="field grow">عنوان عامل<input v-model.trim="factor.name" class="form-control" maxlength="80" @input="touch(factor)" /></label>
            <label class="field">اعمال بر<select v-model="factor.target" class="form-select" @change="touch(factor)"><option v-for="item in targets" :key="item.key" :value="item.key">{{ item.label }}</option></select></label>
            <label class="field weight">ضریب <b>{{ fa(factor.weight) }}</b><input v-model.number="factor.weight" type="range" min="0" max="10" step="0.5" @input="touch(factor)" /></label>
            <label class="field narrow">مقدار پیش‌فرض<input v-model.number="factor.default_value" class="form-control" type="number" min="0" max="100" @input="touch(factor)" /></label>
            <label class="switch"><input v-model="factor.is_active" type="checkbox" @change="touch(factor)" />فعال</label>
          </div>
          <div class="options">
            <span class="options-title">گزینه‌ها و امتیاز (۰ تا ۱۰۰)</span>
            <div v-for="(option, index) in factor.options" :key="index" class="option">
              <input v-model.trim="option.label" class="form-control" placeholder="عنوان گزینه" maxlength="80" @input="touch(factor)" />
              <input v-model.number="option.value" class="form-control value" type="number" min="0" max="100" @input="touch(factor)" />
              <span class="option-bar"><span :style="{ width: (option.value || 0) + '%', background: color(option.value) }" /></span>
              <button type="button" class="icon" :aria-label="'حذف گزینه ' + option.label" :disabled="factor.options.length < 2" @click="removeOption(factor, index)">×</button>
            </div>
            <button type="button" class="link" @click="factor.options.push({ label: '', value: 50 }); touch(factor)">+ گزینه</button>
          </div>
          <div class="factor-foot">
            <span class="muted">{{ factor.id ? `${fa(factor.assigned)} انتخاب ثبت‌شده` : 'عامل تازه' }}</span>
            <span v-if="factor.error" class="error inline" role="alert">{{ factor.error }}</span>
            <button v-if="factor.dirty" type="button" class="ghost" :disabled="factor.saving" @click="reset(factor)">انصراف</button>
            <button type="button" class="primary" :disabled="!factor.dirty || factor.saving" @click="save(factor)">{{ factor.saving ? 'در حال ذخیره…' : 'ذخیره' }}</button>
          </div>
        </article>
        <EmptyState v-if="!factors.length && !factorsLoading" kind="generic" size="sm" title="هنوز عاملی تعریف نشده" description="با «افزودن عامل» اولین معیار اولویت را بسازید." />
      </div>
    </section>
  </main>
</template>

<script>
import PriorityBadge from '@/components/PriorityBadge.vue';
import { PRIORITY_LEVELS, TARGETS, TARGET_LABEL, detailRoute, faScore, levelOf } from '@/utils/priority';

import EmptyState from '@/components/EmptyState/index.vue';
const BASE = '/api/admin/priority/';
let keySeed = 0;

export default {
  name: 'PriorityPage',
  components: { EmptyState, PriorityBadge },
  data: () => ({
    tab: 'ranking', tabs: [{ key: 'ranking', label: 'رتبه‌بندی' }, { key: 'factors', label: 'عوامل و ضرایب' }],
    targets: TARGETS, levels: PRIORITY_LEVELS, target: 'building', level: '', search: '', rows: [], count: 0,
    rankingLoading: false, rankingError: '', factors: [], factorsLoading: false, factorsError: '', timer: null, sequence: 0,
  }),
  computed: {
    project() { return this.$STORE.state.userConfig.setProjectId; },
    targetLabel() { return TARGET_LABEL[this.target]; },
    activeFactors() { return this.factors.filter(f => f.is_active && f.id && f.weight > 0); },
    weightTotal() { return this.activeFactors.reduce((sum, f) => sum + f.weight, 0); },
  },
  watch: {
    target() { this.loadRanking(true); },
    level() { this.loadRanking(true); },
    search() { clearTimeout(this.timer); this.timer = setTimeout(() => this.loadRanking(true), 300); },
    tab(value) { if (value === 'factors' && !this.factors.length) this.loadFactors(); },
    project() { this.loadRanking(true); this.factors = []; if (this.tab === 'factors') this.loadFactors(); },
  },
  created() { this.loadRanking(true); },
  beforeDestroy() { clearTimeout(this.timer); },
  methods: {
    fa: value => Number(value || 0).toLocaleString('fa-IR'), faScore,
    color(score) { const level = levelOf(score); return level ? level.color : '#c9d2df'; },
    detail(id) { return detailRoute(this.target, id); },
    message(response) {
      const data = response.data || {};
      const first = Object.values(data).flat().find(value => typeof value === 'string');
      return response.status === 403 ? 'برای این تغییر دسترسی ندارید.' : first || this.$ApiServiceLayer.getErrorMessage(response);
    },
    async loadRanking(reset) {
      if (!this.project) return;
      const sequence = ++this.sequence;
      this.rankingLoading = true; this.rankingError = '';
      const query = new URLSearchParams({ p: this.project, target: this.target, limit: 25, offset: reset ? 0 : this.rows.length });
      if (this.level) query.set('level', this.level);
      if (this.search) query.set('search', this.search);
      const response = await this.$ApiServiceLayer.get(BASE + 'ranking/?' + query, this.$PATH.SERVICE_NAME.AUTH);
      if (sequence !== this.sequence) return;
      this.rankingLoading = false;
      if (response.status !== 200) { this.rankingError = this.message(response); return; }
      this.rows = reset ? response.data.results : [...this.rows, ...response.data.results];
      this.count = response.data.count;
    },
    toForm(factor) {
      return { ...factor, key: factor.id || 'new-' + (++keySeed), options: factor.options.map(o => ({ ...o })), dirty: false, saving: false, error: '', original: factor };
    },
    async loadFactors() {
      this.factorsLoading = true; this.factorsError = '';
      const response = await this.$ApiServiceLayer.get(BASE + 'factors/?p=' + this.project, this.$PATH.SERVICE_NAME.AUTH);
      this.factorsLoading = false;
      if (response.status !== 200) { this.factorsError = this.message(response); return; }
      this.factors = response.data.map(this.toForm);
    },
    touch(factor) { factor.dirty = true; factor.error = ''; },
    reset(factor) {
      if (!factor.id) { this.factors = this.factors.filter(f => f !== factor); return; }
      Object.assign(factor, this.toForm(factor.original), { key: factor.key });
    },
    addFactor() {
      this.factors.push({ ...this.toForm({ id: null, name: '', target: 'building', weight: 1, default_value: 50, is_active: true, order: this.factors.length,
        assigned: 0, options: [{ label: 'زیاد', value: 100 }, { label: 'متوسط', value: 50 }, { label: 'کم', value: 0 }] }), dirty: true });
    },
    removeOption(factor, index) { factor.options.splice(index, 1); this.touch(factor); },
    async save(factor) {
      if (!factor.name) { factor.error = 'عنوان عامل لازم است.'; return; }
      if (factor.options.some(o => !o.label || o.value === '' || o.value < 0 || o.value > 100)) { factor.error = 'برای هر گزینه عنوان و امتیاز ۰ تا ۱۰۰ لازم است.'; return; }
      factor.saving = true; factor.error = '';
      const payload = { name: factor.name, target: factor.target, weight: factor.weight, default_value: factor.default_value || 0,
        is_active: factor.is_active, order: factor.order, options: factor.options.map(o => ({ id: o.id, label: o.label, value: o.value })) };
      const response = factor.id
        ? await this.$ApiServiceLayer.put(BASE + 'factors/' + factor.id + '/?p=' + this.project, this.$PATH.SERVICE_NAME.AUTH, payload)
        : await this.$ApiServiceLayer.post(BASE + 'factors/?p=' + this.project, this.$PATH.SERVICE_NAME.AUTH, payload);
      factor.saving = false;
      if (response.status !== 200 && response.status !== 201) { factor.error = this.message(response); return; }
      const index = this.factors.indexOf(factor);
      this.$set(this.factors, index, this.toForm(response.data));
      this.$notify && this.$notify({ group: 'tc', type: 'success', text: 'ضرایب ذخیره و امتیازها دوباره محاسبه شد.' });
      this.loadRanking(true);
    },
  },
};
</script>

<style scoped>
.priority-page { display: grid; gap: 16px; color: #25324b; }
.page-head { display: flex; align-items: flex-end; justify-content: space-between; gap: 16px; padding: 22px 24px; border-radius: 18px;
  background: linear-gradient(140deg, #16264a, #2a4f9a); color: #fff; box-shadow: 0 12px 28px #16264a26; }
.eyebrow { color: #c6d6ff; font-size: 12px; font-weight: 700; }
.page-head h1 { color: #fff; font-size: 22px; margin: 4px 0; }
.page-head p { color: #dde6ff; font-size: 12.5px; line-height: 1.9; margin: 0; max-width: 720px; }
.tabs { display: inline-flex; gap: 3px; padding: 3px; border-radius: 11px; background: #ffffff1f; flex: none; }
.tabs button { min-height: 36px; padding: 5px 14px; border: 0; border-radius: 9px; background: transparent; color: #e6edff; font: inherit; font-size: 12.5px; font-weight: 700; cursor: pointer; }
.tabs button.active { background: #fff; color: #17233b; }
.panel { padding: 18px; border-radius: 16px; background: #fff; border: 1px solid #e3e9f2; box-shadow: 0 4px 14px #1b2a4a08; }
.panel-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; margin-bottom: 14px; }
.panel-head h2 { font-size: 16px; font-weight: 800; color: #17233b; margin: 0 0 3px; }
.panel-head p { font-size: 12px; color: #6b778d; margin: 0; line-height: 1.8; }
.toolbar { display: flex; flex-wrap: wrap; align-items: center; gap: 10px; margin-bottom: 12px; }
.segmented { display: inline-flex; flex-wrap: wrap; gap: 3px; padding: 3px; border-radius: 11px; background: #eef2f8; }
.segmented button { display: inline-flex; align-items: center; gap: 6px; min-height: 34px; padding: 5px 12px; border: 0; border-radius: 9px; background: transparent; color: #4a566c; font: inherit; font-size: 12.5px; font-weight: 700; cursor: pointer; }
.segmented button.active { background: #fff; color: #17233b; box-shadow: 0 2px 6px #1b2a4a1f; }
.segmented i { width: 8px; height: 8px; border-radius: 50%; }
.search { max-width: 240px; min-height: 38px; }
.table-wrap { overflow-x: auto; transition: opacity .2s; }
.table-wrap.busy { opacity: .55; }
table { width: 100%; border-collapse: collapse; font-size: 12.5px; }
th { text-align: right; color: #6b778d; font-weight: 700; padding: 9px 8px; border-bottom: 1px solid #e3e9f2; white-space: nowrap; }
td { padding: 9px 8px; border-bottom: 1px solid #f0f2f6; vertical-align: middle; }
tbody tr { cursor: pointer; }
tbody tr:hover { background: #f6f8fc; }
.rank { color: #7a8496; font-variant-numeric: tabular-nums; width: 50px; }
.score-cell { display: flex; align-items: center; gap: 10px; min-width: 180px; }
.score-track, .option-bar { flex: 1; height: 8px; border-radius: 4px; background: #eef1f6; overflow: hidden; display: flex; }
.score-track span, .option-bar span { height: 100%; border-radius: 4px; }
.score-cell b { width: 36px; text-align: left; font-variant-numeric: tabular-nums; }
.table-foot { display: flex; align-items: center; justify-content: space-between; margin-top: 10px; }
.muted { color: #7a8496; font-size: 12px; }
.empty { padding: 22px; text-align: center; color: #7a8496; font-size: 12.5px; }
.error { color: #a12b2b; background: #fdeceb; padding: 9px 12px; border-radius: 10px; font-size: 12.5px; }
.error.inline { padding: 4px 10px; margin: 0; }
button.primary, button.ghost, button.link { min-height: 36px; padding: 6px 14px; border-radius: 10px; font: inherit; font-size: 12.5px; font-weight: 700; cursor: pointer; }
button.primary { border: 0; background: #345de0; color: #fff; }
button.primary:disabled { background: #b8c6ee; cursor: default; }
button.ghost { border: 1px solid #d4dceb; background: #fff; color: #345de0; }
button.link { border: 0; background: transparent; color: #345de0; padding: 4px 0; min-height: 0; }
.share { margin-bottom: 14px; }
.share-title { display: block; font-size: 12px; font-weight: 700; color: #4a566c; margin-bottom: 6px; }
.share-bar { display: flex; gap: 2px; height: 26px; border-radius: 8px; overflow: hidden; }
.share-bar span { position: relative; min-width: 4px; background: #2a78d6; display: flex; align-items: center; overflow: hidden; }
.share-bar span:nth-child(2n) { background: #4a3aa7; }
.share-bar span:nth-child(3n) { background: #1baf7a; }
.share-bar em { padding: 0 8px; color: #fff; font-style: normal; font-size: 11px; font-weight: 700; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.factor-list { display: grid; gap: 12px; }
.factor { padding: 14px; border: 1px solid #e3e9f2; border-radius: 14px; background: #fbfcfe; }
.factor.dirty { border-color: #9fb4e6; background: #fff; }
.factor.inactive { opacity: .7; }
.factor-row { display: flex; flex-wrap: wrap; align-items: flex-end; gap: 10px 14px; }
/* The admin theme styles every label at ID specificity; match it to stack caption over control. */
#app .layout-container .field { display: grid; gap: 4px; margin: 0; font-size: 11.5px; font-weight: 700; color: #6b778d; }
.field.grow { flex: 1 1 220px; }
.field.narrow { width: 110px; }
.field.weight { width: 200px; }
.field.weight b { color: #17233b; }
.field.weight input { accent-color: #345de0; }
#app .layout-container .switch { display: inline-flex; align-items: center; gap: 6px; margin: 0 0 8px; font-size: 12.5px; color: #33405a; }
.options { margin-top: 12px; display: grid; gap: 6px; }
.options-title { font-size: 11.5px; font-weight: 700; color: #6b778d; }
.option { display: grid; grid-template-columns: minmax(140px, 1fr) 90px minmax(80px, 1fr) 32px; align-items: center; gap: 8px; }
.option .value { text-align: center; }
button.icon { width: 32px; height: 32px; border: 1px solid #ebccd1; border-radius: 8px; background: #fff; color: #b42335; font-size: 16px; cursor: pointer; }
button.icon:disabled { opacity: .4; cursor: default; }
.factor-foot { display: flex; flex-wrap: wrap; align-items: center; justify-content: flex-end; gap: 8px; margin-top: 12px; }
.factor-foot .muted { margin-left: auto; }
.priority-page button:focus-visible, .priority-page a:focus-visible, .priority-page input:focus-visible, .priority-page select:focus-visible { outline: 3px solid #345de0; outline-offset: 2px; }
@media (max-width: 760px) { .page-head { flex-direction: column; align-items: stretch; } .search { max-width: none; width: 100%; } .option { grid-template-columns: 1fr 80px 32px; } .option-bar { display: none; } .field.weight, .field.narrow { width: 100%; } }
</style>
