<template>
  <section class="panel" aria-labelledby="proposals-title">
    <div class="panel-head">
      <div><h2 id="proposals-title">مأموریت‌های بدون کارشناس</h2>
        <p>به ترتیب اولویت؛ هر پیشنهاد ظرفیت کارشناس را برای پیشنهادهای بعدی رزرو می‌کند. انتخاب را می‌توانید عوض کنید.</p></div>
      <div class="actions">
        <button type="button" class="ghost" :disabled="loading" @click="load">بازمحاسبه</button>
        <button type="button" class="primary" :disabled="applying || !selectedRows.length" @click="apply">
          {{ applying ? 'در حال تخصیص…' : `تخصیص انتخاب‌شده‌ها (${fa(selectedRows.length)})` }}</button>
      </div>
    </div>
    <p v-if="error" class="error" role="alert">{{ error }}</p>
    <p v-if="outcome" class="outcome" role="status">{{ outcome }}</p>
    <div v-if="loading && !rows.length" class="muted" role="status"><b-spinner small /> در حال محاسبه پیشنهادها…</div>
    <EmptyState v-else-if="!rows.length" kind="done" title="همه مأموریت‌های فعال کارشناس دارند" description="مأموریت بدون کارشناس تازه‌ای که ثبت شود، همین‌جا پیشنهاد می‌گیرد." />
    <div v-else class="table-wrap">
      <table>
        <thead><tr><th scope="col"><input type="checkbox" :checked="allSelected" aria-label="انتخاب همه پیشنهادهای قابل تخصیص" @change="toggleAll($event.target.checked)"></th>
          <th scope="col">اولویت</th><th scope="col">مأموریت</th><th scope="col">کارشناس پیشنهادی</th><th scope="col">امتیاز و دلیل</th></tr></thead>
        <tbody>
          <template v-for="row in rows">
            <tr :key="row.visit" :class="{ done: row.done }">
              <td><input v-model="row.selected" type="checkbox" :disabled="!canApply(row)" :aria-label="'انتخاب مأموریت ' + faId(row.visit)"></td>
              <td><PriorityBadge :score="row.priority" /></td>
              <td>
                <router-link :to="'/visitmanagment/answerlist/' + row.visit">{{ row.type }} · {{ faId(row.visit) }}</router-link>
                <small>{{ row.building }}</small>
                <small>موعد: {{ row.due_date ? jDate(row.due_date) : 'بدون موعد' }}<template v-if="row.complexity > 1"> · پیچیدگی {{ fa(row.complexity) }}</template></small>
                <span v-if="row.pending_request" class="chip off">درخواست مشتری</span>
              </td>
              <td>
                <select v-model.number="row.chosen" class="form-select" :aria-label="'کارشناس مأموریت ' + faId(row.visit)" @change="touched(row)">
                  <option :value="null" disabled>انتخاب کنید</option>
                  <option v-for="item in options(row)" :key="item.user" :value="item.user">{{ item.name }} · {{ fa(item.score) }}{{ item.eligible ? '' : ' (محدودیت)' }}</option>
                </select>
                <button type="button" class="link" @click="toggleAllCandidates(row)">{{ row.expanded ? 'بستن فهرست' : 'همه کارشناسان' }}</button>
                <label v-if="row.pending_request" class="check"><input v-model="row.activate" type="checkbox">هم‌زمان فعال شود</label>
              </td>
              <td>
                <template v-if="current(row)">
                  <span class="score"><i :style="{ background: tone(current(row).score).color }" />{{ fa(current(row).score, 1) }}<small class="inline">{{ tone(current(row).score).label }}</small></span>
                  <div class="bars" aria-hidden="true">
                    <div v-for="factor in factors" :key="factor.key" class="bar-row"><span>{{ factor.label }}</span>
                      <span class="bar-track"><span :style="{ width: current(row).factors[factor.key].value + '%' }" /></span><span>{{ fa(current(row).factors[factor.key].value) }}</span></div>
                  </div>
                  <span v-for="text in current(row).blockers" :key="'b' + text" class="flag block">⛔ {{ text }}</span>
                  <span v-for="text in current(row).warnings" :key="'w' + text" class="flag warn">⚠ {{ text }}</span>
                  <label v-if="current(row).blockers.length" class="check force"><input v-model="row.force" type="checkbox" @change="row.selected = row.force">با وجود محدودیت تخصیص بده</label>
                </template>
                <span v-else class="flag block">{{ row.why_none.length ? row.why_none.join('؛ ') : 'کارشناس واجد شرایطی نیست.' }}</span>
                <span v-if="row.error" class="flag block" role="alert">{{ row.error }}</span>
              </td>
            </tr>
            <tr v-if="row.expanded" :key="'x' + row.visit" class="expand">
              <td colspan="5">
                <p v-if="row.loadingAll" class="muted"><b-spinner small /> در حال دریافت…</p>
                <table v-else-if="row.all" class="inner">
                  <thead><tr><th scope="col">کارشناس</th><th scope="col">امتیاز</th><th scope="col">مهارت</th><th scope="col">کیفیت</th><th scope="col">ظرفیت</th><th scope="col">آشنایی</th><th scope="col">وضعیت</th><th scope="col"><span class="sr-only">انتخاب</span></th></tr></thead>
                  <tbody><tr v-for="item in row.all" :key="item.user">
                    <td>{{ item.name }}<small>گرید {{ fa(item.grade) }} · {{ fa(item.open) }}/{{ fa(item.max_open) }} باز</small></td>
                    <td class="num">{{ fa(item.score, 1) }}</td>
                    <td v-for="factor in factors" :key="factor.key" class="num">{{ fa(item.factors[factor.key].value) }}</td>
                    <td><span v-if="item.eligible" class="chip ok">واجد شرایط</span><span v-for="text in item.blockers" :key="text" class="flag block">{{ text }}</span></td>
                    <td><button type="button" class="link" @click="choose(row, item.user)">انتخاب</button></td></tr></tbody>
                </table>
              </td>
            </tr>
          </template>
        </tbody>
      </table>
    </div>
  </section>
</template>

<script>
import PriorityBadge from '@/components/PriorityBadge.vue';
import { FACTORS, fa, faId, jDate, scoreTone } from '@/utils/assignment';

import EmptyState from '@/components/EmptyState/index.vue';
export default {
  name: 'ProposalsTab',
  components: { EmptyState, PriorityBadge },
  props: { data: { type: Object, required: true } },
  data: () => ({ rows: [], loading: false, applying: false, error: '', outcome: '', factors: FACTORS }),
  computed: {
    project() { return this.$STORE.state.userConfig.setProjectId; },
    selectedRows() { return this.rows.filter((row) => row.selected && this.canApply(row)); },
    allSelected() { const open = this.rows.filter(this.canApply); return open.length > 0 && open.every((row) => row.selected); },
  },
  created() { this.load(); },
  methods: {
    fa, faId, jDate, tone: scoreTone,
    options(row) {
      const base = row.all || [row.suggested, ...row.alternatives].filter(Boolean);
      return base;
    },
    current(row) { return this.options(row).find((item) => item.user === row.chosen) || null; },
    canApply(row) {
      const chosen = this.current(row);
      return !row.done && !!chosen && (chosen.eligible || row.force);
    },
    touched(row) { row.force = false; row.error = ''; row.selected = !!this.current(row) && this.current(row).eligible; },
    choose(row, user) { row.chosen = user; this.touched(row); },
    toggleAll(on) { this.rows.forEach((row) => { if (this.canApply(row)) row.selected = on; }); },
    async load() {
      this.loading = true; this.error = '';
      const response = await this.$ApiServiceLayer.get(`/api/admin/assignment/plan/?p=${this.project}&limit=50`, this.$PATH.SERVICE_NAME.AUTH);
      this.loading = false;
      if (response.status !== 200) { this.error = this.$ApiServiceLayer.getErrorMessage(response); return; }
      this.rows = response.data.proposals.map((proposal) => ({
        ...proposal, chosen: proposal.suggested ? proposal.suggested.user : null, selected: !!proposal.suggested,
        activate: proposal.pending_request, force: false, expanded: false, loadingAll: false, all: null, error: '', done: false,
      }));
    },
    async toggleAllCandidates(row) {
      row.expanded = !row.expanded;
      if (!row.expanded || row.all) return;
      row.loadingAll = true;
      const response = await this.$ApiServiceLayer.get(`/api/admin/assignment/plan/?p=${this.project}&visit=${row.visit}`, this.$PATH.SERVICE_NAME.AUTH);
      row.loadingAll = false;
      if (response.status === 200) row.all = response.data.candidates;
      else row.error = this.$ApiServiceLayer.getErrorMessage(response);
    },
    async apply() {
      const chosen = this.selectedRows;
      this.applying = true; this.error = ''; this.outcome = '';
      const response = await this.$ApiServiceLayer.post(`/api/admin/assignment/apply/?p=${this.project}`, this.$PATH.SERVICE_NAME.AUTH, {
        assignments: chosen.map((row) => ({ visit: row.visit, expert: row.chosen, force: row.force, activate: row.activate && row.pending_request })),
      });
      this.applying = false;
      if (response.status !== 200) { this.error = this.$ApiServiceLayer.getErrorMessage(response); return; }
      const byVisit = {};
      response.data.results.forEach((item) => { byVisit[item.visit] = item; });
      chosen.forEach((row) => {
        const result = byVisit[row.visit];
        if (result && result.ok) { row.done = true; row.selected = false; } else if (result) row.error = result.error;
      });
      this.outcome = `${fa(response.data.assigned)} مأموریت تخصیص یافت و به کارشناس اعلام شد.` +
        (response.data.assigned < chosen.length ? ` ${fa(chosen.length - response.data.assigned)} مورد انجام نشد؛ دلیل در همان ردیف است.` : '');
      this.$emit('changed');
      if (response.data.assigned) setTimeout(() => this.load(), 1200);
    },
  },
};
</script>

<style scoped>
.actions { display: flex; gap: 8px; flex-wrap: wrap; }
.outcome { margin: 0 0 12px; padding: 9px 12px; border-radius: 10px; background: #e8f6ec; color: #13703f; font-size: 12.5px; }
.empty { text-align: center; padding: 28px; color: #7a8496; font-size: 13px; }
tr.done { opacity: .45; }
.expand td { background: #f8fafd; }
.inner { font-size: 12px; }
.inner td, .inner th { padding: 6px 8px; }
.num { font-variant-numeric: tabular-nums; text-align: center; }
.inline { display: inline; margin: 0; }
.chip.ok { background: #e3f4ea; color: #13703f; }
.force { margin-top: 4px; }
.sr-only { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); }
select.form-select { min-width: 190px; min-height: 36px; font-size: 12.5px; }
</style>
