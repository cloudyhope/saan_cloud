<template>
  <div class="setup">
    <section class="panel" aria-labelledby="skills-title">
      <div class="panel-head"><div><h2 id="skills-title">فهرست مهارت‌ها</h2><p>تخصص‌هایی که برای خدمت‌ها لازم می‌شوند و روی کارشناسان ثبت می‌شوند.</p></div></div>
      <p v-if="skillError" class="error" role="alert">{{ skillError }}</p>
      <ul class="skill-list">
        <li v-for="skill in data.skills" :key="skill.id" :class="{ off: !skill.is_active }">
          <input v-model="drafts[skill.id]" class="form-control" maxlength="60" :aria-label="'نام مهارت ' + skill.name" :disabled="!skill.is_active">
          <small>{{ fa(skill.holders) }} کارشناس</small>
          <button v-if="skill.is_active" type="button" class="ghost" :disabled="busy || drafts[skill.id] === skill.name || !drafts[skill.id]" @click="rename(skill)">تغییر نام</button>
          <button v-if="skill.is_active" type="button" class="link danger" :disabled="busy" @click="retire(skill)">غیرفعال</button>
          <button v-else type="button" class="link" :disabled="busy" @click="reactivate(skill)">فعال‌سازی</button>
        </li>
        <li v-if="!data.skills.length" class="muted">هنوز مهارتی تعریف نشده است.</li>
      </ul>
      <form class="add-row" @submit.prevent="addSkill">
        <input v-model.trim="newSkill" class="form-control" maxlength="60" placeholder="مثلاً: بردهای کنترل" aria-label="نام مهارت تازه">
        <button type="submit" class="primary" :disabled="busy || !newSkill">+ افزودن مهارت</button>
      </form>
    </section>

    <section class="panel" aria-labelledby="types-title">
      <div class="panel-head"><div><h2 id="types-title">نیاز هر نوع خدمت</h2>
        <p>پیچیدگی را با گرید کارشناس می‌سنجیم. مهارت «الزامی» زیر حداقل سطح، کارشناس را از تخصیص خودکار کنار می‌گذارد؛ «ترجیحی» فقط امتیاز را کم می‌کند.</p></div></div>
      <p v-if="typeError" class="error" role="alert">{{ typeError }}</p>
      <article v-for="type in types" :key="type.id" class="type-card" :class="{ dirty: type.dirty }">
        <header><strong>{{ type.name }}</strong>
          <label class="field inline">پیچیدگی
            <select v-model.number="type.complexity" class="form-select narrow" @change="type.dirty = true"><option v-for="n in levels" :key="n" :value="n">{{ fa(n) }}</option></select></label></header>
        <div v-for="(item, index) in type.requirements" :key="index" class="req-row">
          <select v-model.number="item.skill" class="form-select" :aria-label="'مهارت لازم ' + (index + 1)" @change="type.dirty = true">
            <option v-for="skill in activeSkills" :key="skill.id" :value="skill.id" :disabled="type.requirements.some((r, i) => i !== index && r.skill === skill.id)">{{ skill.name }}</option></select>
          <select v-model.number="item.min_level" class="form-select narrow" :aria-label="'حداقل سطح ' + (index + 1)" @change="type.dirty = true">
            <option v-for="n in levels" :key="n" :value="n">حداقل {{ fa(n) }}</option></select>
          <select v-model="item.is_required" class="form-select narrow" :aria-label="'الزامی یا ترجیحی ' + (index + 1)" @change="type.dirty = true">
            <option :value="true">الزامی</option><option :value="false">ترجیحی</option></select>
          <button type="button" class="link danger" @click="type.requirements.splice(index, 1); type.dirty = true">حذف</button>
        </div>
        <div class="card-actions">
          <button type="button" class="ghost" :disabled="!freeSkill(type)" @click="type.requirements.push({ skill: freeSkill(type).id, min_level: 3, is_required: true }); type.dirty = true">+ مهارت لازم</button>
          <button type="button" class="primary" :disabled="busy || !type.dirty" @click="saveType(type)">ذخیره</button>
        </div>
      </article>
      <p v-if="!types.length" class="muted">نوع خدمت فعالی تعریف نشده است.</p>
    </section>

    <section class="panel" aria-labelledby="weights-title">
      <div class="panel-head"><div><h2 id="weights-title">ضرایب امتیاز تخصیص</h2>
        <p>هر ضریب سهم یک عامل را در امتیاز ۰ تا ۱۰۰ تعیین می‌کند؛ ضریب صفر آن عامل را خاموش می‌کند. برای کارهای بحرانی و با اولویت بالا، مهارت و کیفیت به‌اندازه «تقویت اولویت» پررنگ‌تر می‌شوند.</p></div></div>
      <p v-if="weightError" class="error" role="alert">{{ weightError }}</p>
      <div class="form-grid">
        <label v-for="item in weightFields" :key="item.key" class="field">{{ item.label }} <b>{{ fa(weights[item.key], 1) }}</b>
          <input v-model.number="weights[item.key]" type="range" :min="item.min" :max="item.max" :step="item.step" @input="weightsDirty = true"></label>
      </div>
      <div class="card-actions"><button type="button" class="primary" :disabled="busy || !weightsDirty" @click="saveWeights">ذخیره ضرایب</button></div>
    </section>
  </div>
</template>

<script>
import { LEVELS, fa } from '@/utils/assignment';

export default {
  name: 'SetupTab',
  props: { data: { type: Object, required: true } },
  data() {
    return {
      busy: false, levels: LEVELS, newSkill: '', skillError: '', typeError: '', weightError: '', weightsDirty: false,
      drafts: {}, types: [], weights: { ...this.data.settings },
      weightFields: [
        { key: 'skill_weight', label: 'مهارت و گرید', min: 0, max: 10, step: 0.5 },
        { key: 'quality_weight', label: 'کیفیت کار', min: 0, max: 10, step: 0.5 },
        { key: 'workload_weight', label: 'ظرفیت آزاد', min: 0, max: 10, step: 0.5 },
        { key: 'familiarity_weight', label: 'آشنایی با ساختمان', min: 0, max: 10, step: 0.5 },
        { key: 'urgent_boost', label: 'تقویت اولویت (برابر)', min: 1, max: 3, step: 0.1 },
      ],
    };
  },
  computed: {
    project() { return this.$STORE.state.userConfig.setProjectId; },
    activeSkills() { return this.data.skills.filter((skill) => skill.is_active); },
  },
  watch: { data: { immediate: true, handler() { this.sync(); } } },
  methods: {
    fa,
    sync() {
      const drafts = {};
      this.data.skills.forEach((skill) => { drafts[skill.id] = skill.name; });
      this.drafts = drafts;
      this.types = this.data.visit_types.map((type) => ({ ...type, requirements: type.requirements.map((item) => ({ ...item })), dirty: false }));
      if (!this.weightsDirty) this.weights = { ...this.data.settings };
    },
    freeSkill(type) { return this.activeSkills.find((skill) => !type.requirements.some((item) => item.skill === skill.id)); },
    base() { return `?p=${this.project}`; },
    async call(method, path, body) {
      this.busy = true;
      const response = await this.$ApiServiceLayer[method](`/api/admin/assignment/${path}${this.base()}`, this.$PATH.SERVICE_NAME.AUTH, body);
      this.busy = false;
      return response;
    },
    async addSkill() {
      this.skillError = '';
      const response = await this.call('post', 'skills/', { name: this.newSkill });
      if (response.status !== 201) { this.skillError = this.$ApiServiceLayer.getErrorMessage(response); return; }
      this.newSkill = ''; this.$emit('changed');
    },
    async rename(skill) {
      this.skillError = '';
      const response = await this.call('put', `skills/${skill.id}/`, { name: this.drafts[skill.id], description: skill.description, is_active: true });
      if (response.status !== 200) { this.skillError = this.$ApiServiceLayer.getErrorMessage(response); return; }
      this.$emit('changed');
    },
    async retire(skill) {
      this.skillError = '';
      const response = await this.call('delete', `skills/${skill.id}/`);
      if (response.status !== 200) { this.skillError = this.$ApiServiceLayer.getErrorMessage(response); return; }
      this.$emit('changed');
    },
    async reactivate(skill) {
      this.skillError = '';
      const response = await this.call('put', `skills/${skill.id}/`, { name: skill.name, description: skill.description, is_active: true });
      if (response.status !== 200) { this.skillError = this.$ApiServiceLayer.getErrorMessage(response); return; }
      this.$emit('changed');
    },
    async saveType(type) {
      this.typeError = '';
      const response = await this.call('put', `requirements/${type.id}/`, { complexity: type.complexity,
        requirements: type.requirements.map((item) => ({ skill: item.skill, min_level: item.min_level, is_required: item.is_required })) });
      if (response.status !== 200) { this.typeError = this.$ApiServiceLayer.getErrorMessage(response); return; }
      type.dirty = false;
      this.$notify && this.$notify({ group: 'tc', type: 'success', text: 'نیاز خدمت ذخیره شد.' });
      this.$emit('changed');
    },
    async saveWeights() {
      this.weightError = '';
      const response = await this.call('put', 'settings/', this.weights);
      if (response.status !== 200) { this.weightError = this.$ApiServiceLayer.getErrorMessage(response); return; }
      this.weightsDirty = false;
      this.$notify && this.$notify({ group: 'tc', type: 'success', text: 'ضرایب ذخیره شد.' });
      this.$emit('changed');
    },
  },
};
</script>

<style scoped>
.setup { display: grid; gap: 16px; }
.skill-list { list-style: none; margin: 0 0 12px; padding: 0; display: grid; gap: 8px; }
.skill-list li { display: flex; align-items: center; gap: 10px; }
.skill-list li.off input { color: #98a1b2; }
.skill-list .form-control { flex: 1; max-width: 320px; min-height: 36px; }
.add-row { display: flex; gap: 8px; max-width: 520px; }
.add-row .form-control { min-height: 36px; }
.type-card { padding: 12px 14px; border: 1px solid #e3e9f2; border-radius: 12px; background: #fbfcfe; margin-bottom: 10px; }
.type-card.dirty { border-color: #9fb4e6; background: #fff; }
.type-card header { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 10px; }
.req-row { display: flex; gap: 8px; align-items: center; margin-bottom: 8px; }
.req-row .form-select { flex: 1; min-height: 36px; }
.req-row .narrow, .type-card .narrow { flex: 0 0 110px; width: 110px; min-height: 36px; }
.card-actions { display: flex; justify-content: flex-end; gap: 8px; margin-top: 8px; }
.inline { display: flex; align-items: center; gap: 8px; }
input[type=range] { width: 100%; }
</style>
