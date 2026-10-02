<template>
  <section v-if="!hidden" class="detail-section priority-panel" aria-labelledby="priority-heading">
    <div class="detail-section-heading">
      <div><h2 id="priority-heading">اولویت خدمات</h2><p>امتیاز ۰ تا ۱۰۰ برای ترتیب انجام و تخصیص مأموریت‌ها.</p></div>
      <router-link class="detail-text-link" to="/priority">ضرایب و رتبه‌بندی</router-link>
    </div>
    <div v-if="loading && !data" class="detail-state" role="status"><b-spinner small /> در حال محاسبه…</div>
    <p v-else-if="error" class="priority-error" role="alert">{{ error }}</p>
    <template v-else-if="data">
      <div class="priority-summary">
        <div class="priority-score" :style="{ borderColor: level ? level.color : '#d8e0ec' }">
          <strong>{{ faScore(data.score) }}</strong><span>از ۱۰۰</span>
        </div>
        <div><PriorityBadge :score="data.score" :show-score="false" />
          <p class="priority-hint">{{ data.parts.length ? 'میانگین وزنی عوامل زیر؛ عوامل به‌ارث‌رسیده از ' + inheritedFrom + ' برچسب دارند.' : 'هنوز عاملی برای این نوع تعریف نشده است.' }}</p></div>
      </div>
      <ul v-if="data.parts.length" class="priority-parts">
        <li v-for="part in data.parts" :key="part.factor">
          <span class="part-name">{{ part.name }}<small v-if="part.inherited">از {{ targetLabel(part.target) }}</small></span>
          <span class="part-value">{{ part.option_label || 'پیش‌فرض' }} · {{ faScore(part.value) }}</span>
          <span class="part-share" :title="'سهم در امتیاز: ' + faScore(part.share) + '٪'"><span :style="{ width: part.share + '%' }" /></span>
          <span class="part-weight">{{ faScore(part.share) }}٪</span>
        </li>
      </ul>
      <div v-if="data.factors.length" class="priority-form">
        <label v-for="factor in data.factors" :key="factor.id" class="priority-field">{{ factor.name }}
          <select v-model="choices[factor.id]" class="form-select">
            <option :value="null">پیش‌فرض ({{ faScore(factor.default_value) }})</option>
            <option v-for="option in factor.options" :key="option.id" :value="option.id">{{ option.label }} · {{ faScore(option.value) }}</option>
          </select>
        </label>
        <div class="detail-form-actions">
          <button class="accept" :disabled="saving || !dirty" @click="save">{{ saving ? 'در حال ذخیره…' : 'ذخیره اولویت' }}</button>
        </div>
      </div>
    </template>
  </section>
</template>

<script>
import PriorityBadge from '@/components/PriorityBadge.vue';
import { TARGET_LABEL, faScore, levelOf } from '@/utils/priority';

export default {
  name: 'PriorityPanel',
  components: { PriorityBadge },
  props: { target: { type: String, required: true }, id: { type: [String, Number], required: true } },
  data: () => ({ data: null, choices: {}, saved: {}, loading: false, saving: false, error: '', hidden: false }),
  computed: {
    project() { return this.$STORE.state.userConfig.setProjectId; },
    url() { return `/api/admin/priority/entity/${this.target}/${this.id}/?p=${this.project}`; },
    level() { return this.data ? levelOf(this.data.score) : null; },
    dirty() { return JSON.stringify(this.choices) !== JSON.stringify(this.saved); },
    inheritedFrom() { return this.target === 'elevator' ? 'ساختمان و مشتری' : 'مشتری'; },
  },
  watch: { url: { immediate: true, handler: 'load' } },
  methods: {
    faScore,
    targetLabel: key => TARGET_LABEL[key],
    apply(data) {
      this.data = data;
      const choices = {};
      data.factors.forEach(factor => {
        const part = data.parts.find(item => item.factor === factor.id && !item.inherited);
        choices[factor.id] = part ? part.option : null;
      });
      this.choices = choices;
      this.saved = { ...choices };
    },
    async load() {
      this.loading = true; this.error = '';
      const response = await this.$ApiServiceLayer.get(this.url, this.$PATH.SERVICE_NAME.AUTH);
      this.loading = false;
      if (response.status === 403) { this.hidden = true; return; } // roles without priority access do not see the panel
      if (response.status !== 200) { this.error = this.$ApiServiceLayer.getErrorMessage(response); return; }
      this.apply(response.data);
    },
    async save() {
      this.saving = true; this.error = '';
      const response = await this.$ApiServiceLayer.put(this.url, this.$PATH.SERVICE_NAME.AUTH, { choices: this.choices });
      this.saving = false;
      if (response.status !== 200) {
        this.error = response.status === 403 ? 'برای تغییر اولویت دسترسی ندارید.' : this.$ApiServiceLayer.getErrorMessage(response);
        return;
      }
      this.apply(response.data);
      this.$notify && this.$notify({ group: 'tc', type: 'success', text: 'اولویت ذخیره و امتیاز دوباره محاسبه شد.' });
    },
  },
};
</script>

<style scoped>
.priority-summary { display: flex; align-items: center; gap: 16px; margin-bottom: 14px; }
.priority-score { display: grid; place-items: center; width: 84px; height: 84px; flex: none; border: 6px solid; border-radius: 50%; }
.priority-score strong { font-size: 22px; line-height: 1; color: #17233b; }
.priority-score span { font-size: 10.5px; color: #7a8496; }
.priority-hint { margin: 6px 0 0; font-size: 12px; color: #6b778d; line-height: 1.8; }
.priority-parts { list-style: none; margin: 0 0 14px; padding: 0; display: grid; gap: 6px; }
.priority-parts li { display: grid; grid-template-columns: minmax(130px, 1.2fr) minmax(120px, 1fr) minmax(80px, 1.4fr) 44px; align-items: center; gap: 10px; font-size: 12.5px; }
.part-name { font-weight: 700; color: #25324b; }
.part-name small { margin-right: 6px; padding: 1px 6px; border-radius: 6px; background: #eef2f8; color: #6b778d; font-size: 10.5px; font-weight: 700; }
.part-value { color: #4a566c; }
.part-share { height: 8px; border-radius: 4px; background: #eef1f6; overflow: hidden; display: flex; }
.part-share span { background: #2a78d6; border-radius: 4px; }
.part-weight { text-align: left; color: #6b778d; font-variant-numeric: tabular-nums; }
.priority-form { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 10px; align-items: end; padding-top: 12px; border-top: 1px solid #edf0f6; }
/* The admin theme styles every label at ID specificity; match it to stack caption over control. */
#app .layout-container .priority-field { display: grid; gap: 5px; margin: 0; font-size: 12px; font-weight: 700; color: #4e5c74; }
.priority-form .detail-form-actions { margin: 0; }
.priority-error { color: #a12b2b; background: #fdeceb; padding: 9px 12px; border-radius: 10px; font-size: 12.5px; }
@media (max-width: 640px) { .priority-parts li { grid-template-columns: 1fr auto; } .part-share { display: none; } }
</style>
