<template>
  <main class="vf-page question-page" dir="rtl">
    <VisitTopBar
      :title="stepTitle"
      :eyebrow="eyebrow"
      :fallback="{ name: 'storeDetail', params: { id: visitId } }"
      back-label="بازگشت به مأموریت"
    >
      <div v-if="rows.length" class="question-progress" aria-live="polite">
        <div class="question-progress-label"><span>{{ faNumber(answeredCount) }} از {{ faNumber(rows.length) }} پرسش پاسخ داده شده</span>
          <strong v-if="requiredLeft && editable">{{ faNumber(requiredLeft) }} الزامی مانده</strong>
          <strong v-else-if="!requiredTotal">بدون پرسش الزامی</strong>
          <strong v-else>الزامی‌ها کامل است</strong></div>
        <div class="vf-progress hero-progress"><span :style="{ width: percent + '%' }" /></div>
      </div>
    </VisitTopBar>

    <div v-if="loading && !rows.length" class="vf-body" role="status" aria-label="در حال دریافت پرسش‌ها">
      <v-skeleton-loader v-for="n in 3" :key="n" class="vf-skeleton" type="article" />
    </div>

    <div v-else class="vf-body">
      <div v-if="loadError" class="vf-banner vf-banner-danger" role="alert">
        <v-icon color="#8a2f2a">mdi-alert-circle-outline</v-icon>
        <div><strong>پرسش‌ها دریافت نشد</strong><p>{{ loadError }}</p>
          <button type="button" class="vf-banner-action" @click="load"><v-icon size="16">mdi-refresh</v-icon>تلاش دوباره</button></div>
      </div>
      <div v-else-if="!editable && settingsLoaded" class="vf-banner vf-banner-info" role="note">
        <v-icon color="#1d4f6d">mdi-lock-outline</v-icon>
        <div><strong>فقط مشاهده</strong><p>{{ readonlyReason }}</p></div>
      </div>
      <div v-else-if="editable" class="vf-banner vf-banner-info compact-banner" role="note">
        <v-icon color="#1d4f6d">mdi-content-save-check-outline</v-icon>
        <p>هر پاسخ همان لحظه ذخیره می‌شود؛ برای متن، مبلغ و چندگزینه‌ای دکمه «ثبت» را بزنید.</p>
      </div>

      <EmptyState v-if="!loadError && !rows.length && !loading" kind="documents" size="sm" title="در این بخش پرسشی تعریف نشده" description="" />

      <article v-for="(row, index) in rows" :key="row.question.id" class="vf-card question-card"
               :class="{ 'is-answered': row.answered, 'is-required-missing': row.required && !row.answered && editable }"
               :aria-labelledby="'q-title-' + row.question.id">
        <header class="question-head">
          <span class="question-index" aria-hidden="true">{{ faNumber(index + 1) }}</span>
          <div class="question-copy">
            <h2 :id="'q-title-' + row.question.id">{{ row.question.text }}</h2>
            <p v-if="row.question.description" class="question-desc">{{ row.question.description }}</p>
          </div>
        </header>
        <div class="question-tags">
          <span v-if="row.required" class="vf-chip" :class="row.answered ? 'vf-tone-done' : 'vf-required'">الزامی</span>
          <span v-else class="vf-chip vf-tone-muted">اختیاری</span>
          <span class="vf-chip vf-tone-muted">{{ typeLabel(row) }}</span>
          <span class="save-state" :class="'is-' + row.state" role="status">
            <template v-if="row.state === 'saving'"><v-progress-circular indeterminate size="13" width="2" color="#1d608b" /> در حال ذخیره…</template>
            <template v-else-if="row.state === 'saved'"><v-icon size="15" color="#1a7154">mdi-check-circle</v-icon> ذخیره شد</template>
            <template v-else-if="row.state === 'error'"><v-icon size="15" color="#a33a35">mdi-alert-circle</v-icon> ذخیره نشد</template>
            <template v-else-if="row.answered"><v-icon size="15" color="#1a7154">mdi-check</v-icon> پاسخ داده شده</template>
          </span>
        </div>
        <AnswerInput
          v-for="param in row.params"
          :key="row.question.id + '-' + param.id"
          :question="row.question"
          :answer="row.answer"
          :param="param"
          :saving="row.state === 'saving'"
          :readonly="!editable"
          @save="save(row, $event)"
        />
        <p v-if="!row.params.length" class="vf-muted no-type">نوع پاسخ این پرسش تعریف نشده است.</p>
        <div v-if="row.state === 'error'" class="row-error" role="alert">
          <span>{{ row.error }}</span>
          <button type="button" class="vf-btn vf-btn-danger vf-btn-small" @click="retry(row)"><v-icon size="16">mdi-refresh</v-icon>تلاش دوباره</button>
        </div>
      </article>
    </div>

    <footer v-if="settingsLoaded" class="vf-actionbar">
      <p v-if="editable && requiredLeft" class="vf-actionbar-note is-danger">{{ faNumber(requiredLeft) }} پرسش الزامی این بخش هنوز پاسخ ندارد.</p>
      <div class="vf-actionbar-row">
        <button type="button" class="vf-btn vf-btn-ghost" @click="backToVisit"><v-icon size="19">mdi-format-list-checks</v-icon>مراحل مأموریت</button>
        <button v-if="nextStep" type="button" class="vf-btn vf-btn-primary" @click="goNext">{{ nextStep.kind === 'photo' ? 'عکس‌ها' : 'بخش بعد' }}<v-icon color="white" size="19">mdi-arrow-left</v-icon></button>
      </div>
    </footer>
  </main>
</template>

<script>
import VisitTopBar from '@/components/Visit/VisitTopBar.vue';
import AnswerInput from '@/components/Visit/AnswerInput.vue';
import { errorMessage } from '@/utils/clientRequests';
import { answerParams, faNumber, startVisit, withProject } from '@/utils/visitFlow';

import EmptyState from '@/components/EmptyState/index.vue';
const TYPE_LABELS = { YesNo: 'بله / خیر', Triple: 'بله / خیر / ندارد', Score: 'امتیاز ۱ تا ۵', Number: 'عدد', Price: 'مبلغ',
  Input: 'پاسخ کوتاه', Description: 'توضیحات', RadioChoice: 'یک گزینه', DropDownList: 'انتخاب از فهرست', Multichoice: 'چند گزینه' };

function hasValue(answer, fields) {
  if (!answer || answer.id == null) return false;
  return fields.some(field => {
    const value = answer[field];
    if (field === 'multichoice') return Array.isArray(value) && value.length > 0;
    if (typeof value === 'string') return value.trim() !== '';
    return value !== null && value !== undefined;
  });
}

export default {
  name: 'QuestionStep',
  components: { EmptyState, VisitTopBar, AnswerInput },
  data: () => ({ rows: [], settings: null, loading: true, settingsLoaded: false, loadError: '', sequence: 0 }),
  computed: {
    visitId() { return this.$route.params.id; },
    typeId() { return Number(this.$route.params.type); },
    visit() { return this.settings && this.settings.visit; },
    editable() { return !!(this.settings && this.settings.editable); },
    steps() {
      if (!this.settings) return [];
      return [...(this.settings.questions || []).map(item => ({ kind: 'question', item })),
        ...(this.settings.photos || []).map(item => ({ kind: 'photo', item }))];
    },
    stepIndex() { return this.steps.findIndex(step => step.kind === 'question' && step.item.id === this.typeId); },
    current() { return this.stepIndex >= 0 ? this.steps[this.stepIndex].item : null; },
    nextStep() { return this.stepIndex >= 0 ? this.steps[this.stepIndex + 1] || null : null; },
    stepTitle() { return (this.current && (this.current.verbose_name || this.current.name)) || 'پرسش‌ها'; },
    eyebrow() {
      const building = this.visit && this.visit.building;
      const name = building ? (building.verbose_name || building.name) : '';
      return this.stepIndex >= 0 ? `بخش ${faNumber(this.stepIndex + 1)} از ${faNumber(this.steps.length)}${name ? ' · ' + name : ''}` : name;
    },
    answeredCount() { return this.rows.filter(row => row.answered).length; },
    requiredLeft() { return this.rows.filter(row => row.required && !row.answered).length; },
    requiredTotal() { return this.rows.filter(row => row.required).length; },
    percent() { return this.rows.length ? Math.round((this.answeredCount / this.rows.length) * 100) : 0; },
    readonlyReason() {
      if (this.settings && !this.settings.is_assignee) return 'شما مجری این مأموریت نیستید.';
      const status = this.visit && this.visit.status;
      return status === '2' ? 'گزارش ثبت شده و در انتظار بررسی است؛ تغییر پاسخ ممکن نیست.'
        : status === '3' ? 'گزارش تأیید شده و بسته است.' : status === '4' ? 'گزارش رد شده و بسته است.'
          : 'این مأموریت برای ثبت پاسخ باز نیست.';
    },
  },
  watch: { '$route.params': { handler: 'load' } },
  created() { this.load(); },
  beforeDestroy() { this.sequence++; },
  methods: {
    faNumber,
    typeLabel(row) {
      return row.params.map(param => TYPE_LABELS[param.answer_type.name] || param.answer_type.name).join('، ') || '—';
    },
    toRow(item) {
      const mandatoryGroup = !!(item.question.question_type && item.question.question_type.is_mandatory);
      const row = { question: item.question, params: answerParams(item.question), answer: item.submitted_answer || {}, state: '', error: '', pending: null,
        required: mandatoryGroup || !!item.question.is_mandatory, answered: false };
      row.answered = hasValue(row.answer, this.fields(row));
      return row;
    },
    fields(row) { return row.params.map(param => param.answer_type.field); },
    async load() {
      const sequence = ++this.sequence;
      this.loading = true; this.loadError = '';
      try {
        const [settings, questions] = await Promise.all([
          this.$ApiServiceLayer.get(withProject(this.$PATH.RELATIVE_PATH.GET.VISIT_PAGE_SETTING + this.visitId + '/'), this.$PATH.SERVICE_NAME.AUTH),
          this.$ApiServiceLayer.get(withProject(this.$PATH.RELATIVE_PATH.GET.GET_QUESTIONS + this.visitId + '/', { question_type: this.typeId }), this.$PATH.SERVICE_NAME.AUTH),
        ]);
        if (sequence !== this.sequence) return;
        if (settings.status === 200) { this.settings = settings.data; this.settingsLoaded = true; }
        if (questions.status !== 200 || !Array.isArray(questions.data)) {
          this.loadError = questions.status === 404 ? 'این بخش پیدا نشد یا به شما تخصیص داده نشده است.' : errorMessage(questions);
          return;
        }
        this.rows = questions.data.map(this.toRow);
      } catch (_) {
        if (sequence === this.sequence) this.loadError = 'اتصال برقرار نشد. اینترنت را بررسی و دوباره تلاش کنید.';
      } finally {
        if (sequence === this.sequence) this.loading = false;
      }
    },
    async save(row, payload) {
      if (row.state === 'saving' || !this.editable) return;
      row.state = 'saving'; row.error = ''; row.pending = payload;
      try {
        // An open visit that is not yet «in progress» is started before its first answer.
        if (this.visit && ['0', '5', '6'].includes(this.visit.status)) {
          const started = await startVisit(this.$ApiServiceLayer, this.$PATH, this.visitId);
          if (!started.ok) { row.state = 'error'; row.error = started.message; return; }
          this.settings.visit = { ...this.visit, status: '1' };
        }
        const response = await this.$ApiServiceLayer.post(withProject(this.$PATH.RELATIVE_PATH.POST.POST_QUESTIONS),
          this.$PATH.SERVICE_NAME.AUTH, { visit: Number(this.visitId), question: row.question.id, ...payload });
        if (response.status !== 200) {
          row.state = 'error';
          row.error = response.status === 404 ? 'این مأموریت برای ثبت پاسخ باز نیست.' : errorMessage(response);
          return;
        }
        row.answer = response.data;
        row.answered = hasValue(row.answer, this.fields(row));
        row.state = 'saved'; row.pending = null;
        setTimeout(() => { if (row.state === 'saved') row.state = ''; }, 2200);
      } catch (_) {
        row.state = 'error'; row.error = 'اتصال برقرار نشد؛ پاسخ ذخیره نشد.';
      }
    },
    retry(row) { if (row.pending) { const payload = row.pending; row.state = ''; this.save(row, payload); } },
    backToVisit() { this.$router.push({ name: 'storeDetail', params: { id: this.visitId } }); },
    goNext() {
      const step = this.nextStep;
      if (!step) return this.backToVisit();
      if (step.kind === 'question') return this.$router.push({ name: 'shelfQuestion', params: { type: step.item.id, id: this.visitId } });
      const min = Math.max(step.item.min || 0, step.item.is_mandatory ? 1 : 0);
      return this.$router.push({ name: 'pickImage', params: { type: step.item.id, id: this.visitId, minImg: min } });
    },
  },
};
</script>

<style scoped>
.question-progress { margin-top: 14px; }
.question-progress-label { display: flex; justify-content: space-between; gap: 10px; font-size: 12px; color: #d4eaf5; margin-bottom: 6px; }
.question-progress-label strong { color: #fff; white-space: nowrap; }
.hero-progress { background: #ffffff2e; }
.compact-banner { align-items: center; padding: 11px 13px; }
.compact-banner p { margin: 0; font-size: 12.5px; }
.question-card { transition: border-color .2s ease; }
.question-card.is-answered { border-color: #cfe7d9; }
.question-card.is-required-missing { border-color: #f0cdc8; }
.question-head { display: flex; gap: 11px; align-items: flex-start; }
.question-index { flex: none; width: 30px; height: 30px; border-radius: 10px; display: grid; place-items: center; background: var(--vf-brand-soft);
  color: var(--vf-brand); font-weight: 800; font-size: 13px; }
.is-answered .question-index { background: var(--vf-ok-soft); color: var(--vf-ok); }
.question-copy { flex: 1; min-width: 0; }
.question-copy h2 { font-size: 14.5px; font-weight: 800; line-height: 1.75; margin: 2px 0 0; color: var(--vf-ink); }
.question-desc { margin: 4px 0 0; color: var(--vf-muted); font-size: 12.5px; line-height: 1.8; white-space: pre-line; }
.question-tags { display: flex; flex-wrap: wrap; align-items: center; gap: 6px; margin-top: 10px; }
.save-state { display: inline-flex; align-items: center; gap: 4px; margin-inline-start: auto; font-size: 11.5px; font-weight: 700; color: var(--vf-muted); }
.save-state.is-saved { color: var(--vf-ok); }
.save-state.is-error { color: var(--vf-danger); }
.row-error { display: flex; align-items: center; justify-content: space-between; gap: 10px; flex-wrap: wrap; margin-top: 12px; padding: 10px 12px;
  border-radius: 12px; background: var(--vf-danger-soft); color: var(--vf-danger); font-size: 12.5px; font-weight: 700; }
.no-type { margin: 10px 0 0; }
</style>
