<template>
  <section class="panel" aria-labelledby="experts-title">
    <div class="panel-head"><div><h2 id="experts-title">کارشناسان و تقویم کاری</h2>
      <p>گرید، مهارت‌ها، روزهای کاری، ظرفیت و مرخصی هر کارشناس. امتیاز کیفیت خودکار از تأیید گزارش، نظر مشتری و رعایت موعد ۱۸۰ روز اخیر محاسبه می‌شود.</p></div></div>
    <p v-if="!data.experts.length" class="muted">در این پروژه کارشناس اجرایی فعالی نیست.</p>
    <div v-else class="table-wrap">
      <table>
        <thead><tr><th scope="col">کارشناس</th><th scope="col">گرید</th><th scope="col">مهارت‌ها</th><th scope="col">کیفیت</th><th scope="col">بار کاری</th><th scope="col">تقویم</th><th scope="col"><span class="sr-only">ویرایش</span></th></tr></thead>
        <tbody>
          <tr v-for="expert in data.experts" :key="expert.id" :class="{ muted: !expert.is_assignable }">
            <td><b>{{ expert.name }}</b><small v-if="!expert.is_assignable">برای تخصیص غیرفعال</small><small v-if="expert.note">{{ expert.note }}</small></td>
            <td>{{ fa(expert.grade) }} <small>{{ gradeLabel[expert.grade] }}</small></td>
            <td><span v-for="item in expert.skills" :key="item.skill" class="chip">{{ skillName(item.skill) }}<em>{{ fa(item.level) }}</em></span>
              <span v-if="!expert.skills.length" class="muted">ثبت نشده</span></td>
            <td>
              <span class="score"><i :style="{ background: tone(expert.quality.score).color }" />{{ fa(expert.quality.score, 0) }}</span>
              <small v-if="expert.quality.has_history">{{ fa(expert.quality.reviewed) }} گزارش بررسی‌شده<template v-if="expert.quality.avg_rating"> · نظر ‌{{ fa(expert.quality.avg_rating, 1) }} از ۵</template></small>
              <small v-else>بدون سابقه کافی؛ امتیاز خنثی</small>
            </td>
            <td>{{ fa(expert.open) }} از {{ fa(expert.max_open) }} باز<small>ظرفیت روزانه {{ fa(expert.daily_capacity) }}</small></td>
            <td><small>{{ dayText(expert.work_days) }}</small><span v-for="off in expert.time_off" :key="off.id" class="chip off">مرخصی {{ jDate(off.start_date) }}–{{ jDate(off.end_date) }}</span></td>
            <td><RowActions :items="[{ label: 'ویرایش کارشناس', icon: 'edit', action: () => edit(expert) }]" /></td>
          </tr>
        </tbody>
      </table>
    </div>

    <b-modal :visible="!!form" size="lg" title="ویرایش کارشناس" hide-footer @hidden="form = null">
      <form v-if="form" class="expert-form" dir="rtl" @submit.prevent="save">
        <p class="lead">{{ form.name }}</p>
        <div class="form-grid">
          <label class="field">گرید (۱ تا ۵)
            <select v-model.number="form.grade" class="form-select"><option v-for="n in levels" :key="n" :value="n">{{ fa(n) }} · {{ gradeLabel[n] }}</option></select></label>
          <label class="field">ظرفیت روزانه
            <input v-model.number="form.daily_capacity" class="form-control" type="number" min="1" max="30" required></label>
          <label class="field">حداکثر مأموریت باز
            <input v-model.number="form.max_open" class="form-control" type="number" min="1" max="100" required></label>
          <label class="check"><input v-model="form.is_assignable" type="checkbox">در تخصیص دیده شود</label>
          <div class="wide"><span class="label">روزهای کاری</span>
            <div class="days" role="group" aria-label="روزهای کاری">
              <button v-for="day in data.weekdays" :key="day.day" type="button" class="day" :class="{ on: form.work_days.includes(day.day) }"
                      :aria-pressed="form.work_days.includes(day.day) ? 'true' : 'false'" @click="toggleDay(day.day)">{{ day.label }}</button></div></div>
          <label class="field wide">یادداشت<input v-model="form.note" class="form-control" maxlength="255" placeholder="مثلاً: فقط پروژه‌های غرب"></label>
        </div>
        <h3 class="sub">مهارت‌ها</h3>
        <div v-for="(item, index) in form.skills" :key="index" class="skill-row">
          <select v-model.number="item.skill" class="form-select" :aria-label="'مهارت ' + (index + 1)">
            <option v-for="skill in activeSkills" :key="skill.id" :value="skill.id" :disabled="usedSkill(skill.id, index)">{{ skill.name }}</option></select>
          <select v-model.number="item.level" class="form-select narrow" :aria-label="'سطح مهارت ' + (index + 1)">
            <option v-for="n in levels" :key="n" :value="n">سطح {{ fa(n) }}</option></select>
          <button type="button" class="link danger" @click="form.skills.splice(index, 1)">حذف</button>
        </div>
        <button type="button" class="ghost" :disabled="!freeSkill" @click="addSkill">+ افزودن مهارت</button>
        <p v-if="!activeSkills.length" class="muted">ابتدا در تب «مهارت‌ها و ضرایب» مهارت تعریف کنید.</p>

        <h3 class="sub">مرخصی و عدم دسترسی</h3>
        <ul class="off-list">
          <li v-for="off in form.time_off" :key="off.id"><span>{{ jDate(off.start_date) }} تا {{ jDate(off.end_date) }}{{ off.reason ? ' · ' + off.reason : '' }}</span>
            <button type="button" class="link danger" :disabled="busy" @click="removeOff(off)">حذف</button></li>
          <li v-if="!form.time_off.length" class="muted">مرخصی ثبت نشده است.</li>
        </ul>
        <div class="form-grid off-form">
          <label class="field">از تاریخ<date-picker v-model="off.start" format="YYYY-MM-DD" display-format="jYYYY/jMM/jDD" :min="today" input-class="form-control" /></label>
          <label class="field">تا تاریخ<date-picker v-model="off.end" format="YYYY-MM-DD" display-format="jYYYY/jMM/jDD" :min="off.start || today" input-class="form-control" /></label>
          <label class="field">دلیل<input v-model="off.reason" class="form-control" maxlength="255"></label>
          <button type="button" class="ghost" :disabled="busy || !off.start || !off.end" @click="addOff">ثبت مرخصی</button>
        </div>

        <p v-if="error" class="error" role="alert">{{ error }}</p>
        <div class="footer"><button type="button" class="ghost" :disabled="busy" @click="form = null">انصراف</button>
          <button type="submit" class="primary" :disabled="busy || !form.work_days.length">{{ busy ? 'در حال ذخیره…' : 'ذخیره' }}</button></div>
      </form>
    </b-modal>
  </section>
</template>

<script>
import { GRADE_LABEL, LEVELS, fa, jDate, scoreTone } from '@/utils/assignment';

import RowActions from '@/components/RowActions/index.vue';
const todayIso = () => { const d = new Date(); return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`; };

export default {
  components: { RowActions },
  name: 'ExpertsTab',
  props: { data: { type: Object, required: true } },
  data: () => ({ form: null, off: { start: '', end: '', reason: '' }, busy: false, error: '', levels: LEVELS, gradeLabel: GRADE_LABEL }),
  computed: {
    project() { return this.$STORE.state.userConfig.setProjectId; },
    today() { return todayIso(); },
    activeSkills() { return this.data.skills.filter((skill) => skill.is_active); },
    freeSkill() { return this.activeSkills.find((skill) => !this.form || !this.form.skills.some((item) => item.skill === skill.id)); },
  },
  methods: {
    fa, jDate, tone: scoreTone,
    skillName(id) { const skill = this.data.skills.find((item) => item.id === id); return skill ? skill.name : 'مهارت'; },
    dayText(days) {
      const labels = this.data.weekdays.filter((day) => days.includes(day.day)).map((day) => day.label);
      return labels.length === 7 ? 'همه روزها' : labels.join('، ');
    },
    usedSkill(id, index) { return this.form.skills.some((item, i) => i !== index && item.skill === id); },
    toggleDay(day) { const days = this.form.work_days; const at = days.indexOf(day); if (at >= 0) days.splice(at, 1); else days.push(day); },
    edit(expert) {
      this.error = ''; this.off = { start: '', end: '', reason: '' };
      this.form = { id: expert.id, name: expert.name, grade: expert.grade, daily_capacity: expert.daily_capacity, max_open: expert.max_open,
        is_assignable: expert.is_assignable, note: expert.note, work_days: [...expert.work_days],
        skills: expert.skills.map((item) => ({ ...item })), time_off: expert.time_off.map((item) => ({ ...item })) };
    },
    addSkill() { if (this.freeSkill) this.form.skills.push({ skill: this.freeSkill.id, level: 3 }); },
    async save() {
      this.busy = true; this.error = '';
      const { grade, daily_capacity, max_open, is_assignable, note, work_days, skills } = this.form;
      const response = await this.$ApiServiceLayer.put(`/api/admin/assignment/experts/${this.form.id}/?p=${this.project}`, this.$PATH.SERVICE_NAME.AUTH,
        { grade, daily_capacity, max_open, is_assignable, note, work_days, skills });
      this.busy = false;
      if (response.status !== 200) { this.error = this.$ApiServiceLayer.getErrorMessage(response); return; }
      this.form = null;
      this.$notify && this.$notify({ group: 'tc', type: 'success', text: 'مشخصات کارشناس ذخیره شد.' });
      this.$emit('changed');
    },
    async addOff() {
      this.busy = true; this.error = '';
      const response = await this.$ApiServiceLayer.post(`/api/admin/assignment/experts/${this.form.id}/time_off/?p=${this.project}`, this.$PATH.SERVICE_NAME.AUTH,
        { start_date: this.off.start, end_date: this.off.end, reason: this.off.reason });
      this.busy = false;
      if (response.status !== 201) { this.error = this.$ApiServiceLayer.getErrorMessage(response); return; }
      this.form.time_off.push(response.data); this.off = { start: '', end: '', reason: '' };
      this.$emit('changed');
    },
    async removeOff(off) {
      this.busy = true;
      const response = await this.$ApiServiceLayer.delete(`/api/admin/assignment/time_off/${off.id}/?p=${this.project}`, this.$PATH.SERVICE_NAME.AUTH);
      this.busy = false;
      if (response.status !== 204) { this.error = this.$ApiServiceLayer.getErrorMessage(response); return; }
      this.form.time_off = this.form.time_off.filter((item) => item.id !== off.id);
      this.$emit('changed');
    },
  },
};
</script>

<style scoped>
/* The modal is rendered outside the page (and outside .assign-page), so its controls are styled here. */
.expert-form .field { display: grid; gap: 4px; margin: 0; font-size: 11.5px; font-weight: 700; color: #6b778d; }
.expert-form .check { display: inline-flex; align-items: center; gap: 6px; margin: 0; font-size: 12.5px; font-weight: 600; color: #3b4963; }
.expert-form .form-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(190px, 1fr)); gap: 12px; align-items: end; }
.expert-form .wide { grid-column: 1 / -1; }
.expert-form .days { display: flex; flex-wrap: wrap; gap: 6px; }
.expert-form .day { min-height: 34px; padding: 4px 12px; border: 1px solid #d4dceb; border-radius: 9px; background: #fff; color: #4a566c; font: inherit; font-size: 12px; font-weight: 700; cursor: pointer; }
.expert-form .day.on { background: #345de0; border-color: #345de0; color: #fff; }
.expert-form button.primary, .expert-form button.ghost, .expert-form button.link { min-height: 36px; padding: 6px 14px; border-radius: 10px; font: inherit; font-size: 12.5px; font-weight: 700; cursor: pointer; white-space: nowrap; }
.expert-form button.primary { border: 0; background: #345de0; color: #fff; }
.expert-form button.primary:disabled { background: #b8c6ee; cursor: default; }
.expert-form button.ghost { border: 1px solid #d4dceb; background: #fff; color: #345de0; }
.expert-form button.link { border: 0; background: transparent; color: #345de0; padding: 2px 4px; min-height: 0; }
.expert-form button.link.danger { color: #b42d2d; }
.expert-form .error { color: #a12b2b; background: #fdeceb; padding: 9px 12px; border-radius: 10px; font-size: 12.5px; margin: 12px 0 0; }
.expert-form .muted { color: #7a8496; font-size: 12px; margin: 6px 0 0; }
.lead { font-weight: 800; font-size: 14px; margin: 0 0 12px; }
.sub { font-size: 13px; font-weight: 800; margin: 18px 0 8px; color: #25324b; }
.label { display: block; font-size: 11.5px; font-weight: 700; color: #6b778d; margin-bottom: 4px; }
.skill-row { display: flex; gap: 8px; align-items: center; margin-bottom: 8px; }
.skill-row .form-select { flex: 1; }
.skill-row .narrow { flex: 0 0 110px; }
.off-list { list-style: none; margin: 0 0 10px; padding: 0; display: grid; gap: 6px; font-size: 12.5px; }
.off-list li { display: flex; justify-content: space-between; gap: 8px; padding: 6px 10px; border-radius: 8px; background: #f6f8fc; }
.off-form { margin-top: 8px; }
.footer { display: flex; justify-content: flex-end; gap: 8px; margin-top: 18px; padding-top: 12px; border-top: 1px solid #edf0f6; }
.sr-only { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); }
tr.muted td { color: #98a1b2; }
</style>
