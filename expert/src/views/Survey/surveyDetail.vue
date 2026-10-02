<template>
  <main class="vf-page survey-detail" dir="rtl">
    <VisitTopBar
      :title="surveyName"
      :eyebrow="visitId ? `پرسشنامه مأموریت ${faId(visitId)}` : 'پرسشنامه'"
      :fallback="visitId ? { name: 'storeDetail', params: { id: visitId } } : { name: 'tasks' }"
    >
      <div v-if="fillOut" class="survey-hero-meta">
        <span class="vf-chip" :class="closed ? 'vf-tone-done' : 'vf-tone-progress'">
          <v-icon size="15">{{ closed ? 'mdi-send-check-outline' : 'mdi-pencil-outline' }}</v-icon>{{ closed ? 'ارسال شده' : 'در حال تکمیل' }}
        </span>
        <span v-if="survey.has_phone_verification" class="vf-chip hero-chip">
          <v-icon size="15" color="#e8f5fb">{{ fillOut.phone_verified ? 'mdi-shield-check-outline' : 'mdi-shield-alert-outline' }}</v-icon>
          {{ fillOut.phone_verified ? 'شماره تأیید شده' : 'نیازمند تأیید شماره' }}
        </span>
      </div>
      <div v-if="steps.length" class="survey-hero-progress">
        <div class="survey-hero-label"><span>بخش‌های تکمیل‌شده</span><strong>{{ faNumber(doneCount) }} از {{ faNumber(steps.length) }}</strong></div>
        <div class="vf-progress hero-progress"><span :style="{ width: percent + '%' }" /></div>
      </div>
    </VisitTopBar>

    <div v-if="loading && !fillOut" class="vf-body" role="status" aria-label="در حال دریافت پرسشنامه">
      <v-skeleton-loader class="vf-skeleton" type="article" /><v-skeleton-loader class="vf-skeleton" type="list-item-two-line, list-item-two-line" />
    </div>
    <div v-else-if="error && !fillOut" class="vf-body">
      <div class="vf-banner vf-banner-danger" role="alert">
        <v-icon color="#8a2f2a">mdi-alert-circle-outline</v-icon>
        <div><strong>پرسشنامه دریافت نشد</strong><p>{{ error }}</p>
          <button type="button" class="vf-banner-action" @click="load"><v-icon size="16">mdi-refresh</v-icon>تلاش دوباره</button></div>
      </div>
    </div>

    <div v-else-if="fillOut" class="vf-body">
      <div v-if="closed" class="vf-banner vf-banner-ok" role="note">
        <v-icon color="#1b6247">mdi-send-check-outline</v-icon>
        <div><strong>پرسشنامه ارسال شده است</strong><p>پاسخ‌ها فقط قابل مشاهده‌اند.</p></div>
      </div>
      <div v-else-if="needsVerification" class="vf-banner vf-banner-warn" role="note">
        <v-icon color="#7a4d0f">mdi-shield-alert-outline</v-icon>
        <div><strong>شماره پرسش‌شونده هنوز تأیید نشده است</strong>
          <p>پیش از ارسال، کد تأیید را به شماره مدیر ساختمان بفرستید و وارد کنید.</p>
          <button type="button" class="vf-banner-action" @click="verifyOpen = true"><v-icon size="16">mdi-cellphone-message</v-icon>تأیید شماره</button></div>
      </div>
      <section v-if="survey.sms_text" class="vf-card" aria-labelledby="intro-heading">
        <div class="vf-card-title"><h2 id="intro-heading">درباره این پرسشنامه</h2></div>
        <p class="survey-intro">{{ survey.sms_text }}</p>
      </section>

      <section v-if="survey.is_mandatory_city || survey.has_phone_verification === null" class="vf-card" aria-labelledby="who-heading">
        <div class="vf-card-title"><h2 id="who-heading">مشخصات پرسش‌شونده</h2><small v-if="savingProfile">در حال ذخیره…</small></div>
        <div v-if="survey.is_mandatory_city" class="form-grid">
          <label class="field-label">استان
            <span class="select-wrap"><select v-model="provinceId" :disabled="closed || savingProfile" @change="pickProvince">
              <option value="" disabled>انتخاب استان</option>
              <option v-for="province in provinces" :key="province.id" :value="province.id">{{ province.name }}</option>
            </select><v-icon class="select-icon" size="20">mdi-chevron-down</v-icon></span>
          </label>
          <label class="field-label">شهر
            <span class="select-wrap"><select v-model="cityId" :disabled="closed || !provinceId || savingProfile" @change="saveProfile">
              <option value="" disabled>انتخاب شهر</option>
              <option v-for="city in cities" :key="city.id" :value="city.id">{{ city.name }}</option>
            </select><v-icon class="select-icon" size="20">mdi-chevron-down</v-icon></span>
          </label>
        </div>
        <label v-if="survey.has_phone_verification === null" class="field-label">شماره همراه پرسش‌شونده
          <span class="inline-field"><input v-model="phone" inputmode="tel" maxlength="11" dir="ltr" placeholder="09xxxxxxxxx" :disabled="closed || savingProfile" />
            <button type="button" class="vf-btn vf-btn-primary vf-btn-small" :disabled="closed || savingProfile || !validPhone(phone)" @click="saveProfile">ذخیره</button></span>
        </label>
        <p v-if="profileError" class="field-error" role="alert">{{ profileError }}</p>
      </section>

      <div class="vf-section-label"><h2>بخش‌ها</h2><span v-if="steps.length">{{ faNumber(doneCount) }} از {{ faNumber(steps.length) }} تکمیل</span></div>
      <div v-if="!steps.length" class="vf-empty"><v-icon color="#7c9aa9" size="28">mdi-clipboard-text-off-outline</v-icon>برای این پرسشنامه بخشی تعریف نشده است.</div>
      <div v-else>
        <button v-for="step in steps" :key="step.kind + step.id" type="button" class="vf-step" :class="{ 'is-done': step.done }" @click="open(step)">
          <span class="vf-step-icon"><v-icon :color="step.done ? '#1a7154' : '#1d608b'" size="22">{{ step.done ? 'mdi-check-circle-outline' : step.kind === 'photo' ? 'mdi-camera-outline' : 'mdi-clipboard-text-outline' }}</v-icon></span>
          <span class="vf-step-copy">
            <strong>{{ step.title }}</strong>
            <span class="vf-step-meta"><span>{{ step.kind === 'photo' ? 'عکس' : 'پرسش‌ها' }}</span><span class="vf-chip" :class="step.done ? 'vf-tone-done' : 'vf-tone-muted'">{{ step.done ? 'تکمیل' : step.progress || 'شروع نشده' }}</span></span>
          </span>
          <v-icon size="20" color="#7c9aa9">mdi-chevron-left</v-icon>
        </button>
        <button v-for="add in addIns" :key="'add' + add.id" type="button" class="vf-step" @click="verifyProfile">
          <span class="vf-step-icon"><v-icon color="#1d608b" size="22">mdi-card-account-details-outline</v-icon></span>
          <span class="vf-step-copy"><strong>{{ add.verbose_name || add.name }}</strong><span class="vf-step-meta">احراز هویت</span></span>
          <v-icon size="20" color="#7c9aa9">mdi-chevron-left</v-icon>
        </button>
      </div>
      <p v-if="actionError" class="vf-banner vf-banner-danger action-error" role="alert"><v-icon color="#8a2f2a">mdi-alert-circle-outline</v-icon><span>{{ actionError }}</span></p>
    </div>

    <footer v-if="fillOut && !closed" class="vf-actionbar">
      <p class="vf-actionbar-note" :class="{ 'is-danger': !ready }">{{ readyNote }}</p>
      <div class="vf-actionbar-row">
        <button v-if="needsVerification" type="button" class="vf-btn vf-btn-ghost" @click="verifyOpen = true"><v-icon size="19">mdi-cellphone-message</v-icon>تأیید شماره</button>
        <button type="button" class="vf-btn vf-btn-success" :disabled="!ready || sending" @click="send">
          <v-progress-circular v-if="sending" indeterminate size="20" width="2" color="white" /><template v-else><v-icon color="white" size="19">mdi-send-outline</v-icon>ارسال پرسشنامه</template>
        </button>
      </div>
    </footer>

    <v-bottom-sheet v-model="verifyOpen" max-width="576px">
      <v-sheet class="vf-sheet" role="dialog" aria-labelledby="verify-title">
        <div class="vf-sheet-handle" aria-hidden="true" />
        <div class="vf-sheet-head"><h2 id="verify-title">تأیید شماره پرسش‌شونده</h2>
          <button type="button" class="vf-icon-btn" aria-label="بستن" @click="verifyOpen = false"><v-icon size="22">mdi-close</v-icon></button></div>
        <label class="field-label">شماره همراه
          <span class="inline-field"><input v-model="verifyPhone" inputmode="tel" maxlength="11" dir="ltr" placeholder="09xxxxxxxxx" :disabled="codeSending" />
            <button type="button" class="vf-btn vf-btn-primary vf-btn-small" :disabled="codeSending || countdown > 0 || !validPhone(verifyPhone)" @click="sendCode">
              {{ countdown > 0 ? faNumber(countdown) + ' ثانیه' : verification ? 'ارسال دوباره' : 'ارسال کد' }}</button></span>
        </label>
        <label v-if="verification" class="field-label">کد تأیید
          <input v-model="code" class="code-input" inputmode="numeric" maxlength="5" dir="ltr" placeholder="•••••" :disabled="verifying" @input="code.length === 5 && verifyCode()" />
        </label>
        <p class="vf-muted sms-note">ارسال کد به سرویس پیامک نیاز دارد؛ اگر کد نرسید، چند لحظه بعد دوباره تلاش کنید.</p>
        <p v-if="verifyError" class="field-error" role="alert">{{ verifyError }}</p>
        <button v-if="verification" type="button" class="vf-btn vf-btn-primary vf-btn-block" :disabled="code.length !== 5 || verifying" @click="verifyCode">تأیید کد</button>
      </v-sheet>
    </v-bottom-sheet>
    <v-snackbar v-model="toast" :timeout="2400" top color="#15364f">{{ toastText }}</v-snackbar>
  </main>
</template>

<script>
import VisitTopBar from '@/components/Visit/VisitTopBar.vue';
import { errorMessage } from '@/utils/clientRequests';
import { faId, faNumber, withProject } from '@/utils/visitFlow';

const latin = value => String(value || '').replace(/[۰-۹]/g, d => '۰۱۲۳۴۵۶۷۸۹'.indexOf(d)).replace(/[٠-٩]/g, d => '٠١٢٣٤٥٦٧٨٩'.indexOf(d));

export default {
  name: 'SurveyOverview',
  components: { VisitTopBar },
  data: () => ({
    page: null, loading: true, error: '', actionError: '', provinces: [], cities: [], provinceId: '', cityId: '', phone: '',
    savingProfile: false, profileError: '', sending: false, verifyOpen: false, verifyPhone: '', verification: null,
    code: '', codeSending: false, verifying: false, verifyError: '', countdown: 0, timer: null, toast: false, toastText: '',
  }),
  computed: {
    fillId() { return this.$route.params.fill_id || this.$route.params.id; },
    visitId() { return this.$route.params.visit_id || (this.fillOut && this.fillOut.visit) || null; },
    fillOut() { return this.page && this.page.survey_fill_out; },
    survey() { return (this.fillOut && this.fillOut.survey) || {}; },
    surveyName() { return this.survey.verbose_name || this.survey.name || 'پرسشنامه'; },
    closed() { return !!(this.fillOut && this.fillOut.is_closed); },
    needsVerification() { return !!(this.survey.has_phone_verification && this.fillOut && !this.fillOut.phone_verified); },
    steps() {
      if (!this.page) return [];
      return [...(this.page.questions || []).map(item => ({ kind: 'question', id: item.id, title: item.verbose_name || item.name, done: !!item.status, progress: this.progressLabel(item.progress) })),
        ...(this.page.photos || []).map(item => ({ kind: 'photo', id: item.id, title: item.verbose_name || item.name, done: !!item.status, progress: this.progressLabel(item.progress) }))];
    },
    addIns() { return (this.page && this.page.add_ins) || []; },
    doneCount() { return this.steps.filter(step => step.done).length; },
    percent() { return this.steps.length ? Math.round((this.doneCount / this.steps.length) * 100) : 0; },
    locationMissing() { return !!(this.survey.is_mandatory_city && !(this.fillOut && this.fillOut.city)); },
    ready() { return this.steps.every(step => step.done) && !this.needsVerification && !this.locationMissing; },
    readyNote() {
      if (this.needsVerification) return 'برای ارسال، ابتدا شماره پرسش‌شونده را تأیید کنید.';
      if (this.locationMissing) return 'استان و شهر پرسش‌شونده را انتخاب کنید.';
      const left = this.steps.length - this.doneCount;
      return left ? `${faNumber(left)} بخش هنوز کامل نشده است.` : 'همه بخش‌ها کامل است؛ پرسشنامه را ارسال کنید.';
    },
  },
  watch: { countdown(value) { clearTimeout(this.timer); if (value > 0) this.timer = setTimeout(() => { this.countdown -= 1; }, 1000); } },
  created() { this.load(); },
  beforeDestroy() { clearTimeout(this.timer); },
  methods: {
    faId, faNumber,
    notify(text) { this.toastText = text; this.toast = true; },
    progressLabel(value) {
      const number = parseFloat(value);
      return Number.isFinite(number) && number > 0 ? `${faNumber(Math.round(number))}٪` : '';
    },
    validPhone(value) { return /^09\d{9}$/.test(latin(value)); },
    async load() {
      this.loading = true; this.error = '';
      try {
        const response = await this.$ApiServiceLayer.get(
          withProject(this.$PATH.RELATIVE_PATH.MULTI.SURVEY_QUESTION_TYPE + this.fillId + '/'), this.$PATH.SERVICE_NAME.AUTH);
        if (response.status !== 200 || !response.data || !response.data.survey_fill_out) {
          this.error = response.status === 404 ? 'این پرسشنامه پیدا نشد یا در دسترس شما نیست.' : errorMessage(response);
          return;
        }
        this.page = response.data;
        const fillOut = response.data.survey_fill_out;
        this.phone = fillOut.phone_number || '';
        this.verifyPhone = this.verifyPhone || fillOut.phone_number || '';
        if (fillOut.survey && fillOut.survey.is_mandatory_city) {
          this.provinceId = fillOut.province ? (fillOut.province.id || fillOut.province) : '';
          this.cityId = fillOut.city ? (fillOut.city.id || fillOut.city) : '';
          if (!this.provinces.length) this.loadProvinces();
          if (this.provinceId) this.loadCities();
        }
      } catch (_) {
        this.error = 'اتصال برقرار نشد. دوباره تلاش کنید.';
      } finally { this.loading = false; }
    },
    async loadProvinces() {
      const response = await this.$ApiServiceLayer.get(withProject(this.$PATH.RELATIVE_PATH.GET.PROVINCE_LIST), this.$PATH.SERVICE_NAME.AUTH);
      if (response.status === 200) this.provinces = Array.isArray(response.data) ? response.data : response.data.results || [];
    },
    async loadCities() {
      const response = await this.$ApiServiceLayer.get(withProject(this.$PATH.RELATIVE_PATH.GET.CITY_LIST, { province: this.provinceId }), this.$PATH.SERVICE_NAME.AUTH);
      if (response.status === 200) this.cities = Array.isArray(response.data) ? response.data : response.data.results || [];
    },
    pickProvince() { this.cityId = ''; this.cities = []; this.loadCities(); },
    async saveProfile() {
      if (this.closed) return;
      this.savingProfile = true; this.profileError = '';
      const payload = {};
      if (this.survey.is_mandatory_city && this.cityId) { payload.city = this.cityId; payload.province = this.provinceId; }
      if (this.survey.has_phone_verification === null && this.phone) payload.phone_number = latin(this.phone);
      try {
        const response = await this.$ApiServiceLayer.patch(
          withProject(this.$PATH.RELATIVE_PATH.MULTI.SURVEY_FILL_OUT_EDIT + this.fillId + '/'), this.$PATH.SERVICE_NAME.AUTH, payload);
        if (response.status !== 200) { this.profileError = response.status === 400 ? 'این شماره قبلاً برای همین پرسشنامه ثبت شده است.' : errorMessage(response); return; }
        this.notify('مشخصات ذخیره شد.');
        await this.load();
      } catch (_) { this.profileError = 'ذخیره انجام نشد. دوباره تلاش کنید.'; }
      finally { this.savingProfile = false; }
    },
    open(step) {
      if (step.kind === 'photo') this.$router.push({ name: 'surveyImage', params: { surveyId: this.fillId, id: step.id }, query: this.visitId ? { visit: this.visitId } : {} });
      else this.$router.push({ name: 'surveyQuestions', params: { surveyId: this.fillId, id: step.id }, query: this.visitId ? { visit: this.visitId } : {} });
    },
    verifyProfile() { this.$router.push({ name: 'verifyProfile', params: { id: this.fillId } }); },
    async sendCode() {
      this.codeSending = true; this.verifyError = '';
      try {
        const response = await this.$ApiServiceLayer.post(withProject(this.$PATH.RELATIVE_PATH.POST.SURVEY_VERIFICATION_SEND_CODE),
          this.$PATH.SERVICE_NAME.AUTH, { phone_number: latin(this.verifyPhone), survey_fill_out: Number(this.fillId) });
        if (response.status !== 201) { this.verifyError = response.status === 400 ? 'این شماره قبلاً برای همین پرسشنامه ثبت شده است.' : errorMessage(response); return; }
        this.verification = response.data;
        this.countdown = 60;
        this.code = '';
      } catch (_) { this.verifyError = 'ارسال کد ممکن نشد. دوباره تلاش کنید.'; }
      finally { this.codeSending = false; }
    },
    async verifyCode() {
      if (this.verifying || !this.verification) return;
      this.verifying = true; this.verifyError = '';
      try {
        const response = await this.$ApiServiceLayer.post(withProject(this.$PATH.RELATIVE_PATH.POST.SURVEY_OTP_VALIDATE_VERIFICATION),
          this.$PATH.SERVICE_NAME.AUTH, { code: latin(this.code), verification_token: this.verification.verification_token,
            id: this.verification.id, phone_number: this.verification.phone_number });
        if (response.status !== 200) {
          this.verifyError = response.status === 419 ? 'کد منقضی شده است؛ کد تازه بگیرید.' : (response.data && response.data.detail) || 'کد واردشده درست نیست.';
          this.code = '';
          return;
        }
        this.verifyOpen = false;
        this.notify('شماره تأیید شد.');
        await this.load();
      } catch (_) { this.verifyError = 'تأیید ممکن نشد. دوباره تلاش کنید.'; }
      finally { this.verifying = false; }
    },
    async send() {
      if (!this.ready || this.sending) return;
      this.sending = true; this.actionError = '';
      try {
        const response = await this.$ApiServiceLayer.patch(
          withProject(this.$PATH.RELATIVE_PATH.MULTI.SURVEY_FILL_OUT_EDIT + this.fillId + '/'), this.$PATH.SERVICE_NAME.AUTH, { is_closed: true });
        if (response.status !== 200) { this.actionError = errorMessage(response); return; }
        this.notify('پرسشنامه ارسال شد.');
        if (this.visitId) await this.$router.push({ name: 'storeDetail', params: { id: this.visitId } });
        else await this.load();
      } catch (_) { this.actionError = 'ارسال انجام نشد. دوباره تلاش کنید.'; }
      finally { this.sending = false; }
    },
  },
};
</script>

<style scoped>
.survey-hero-meta { display: flex; flex-wrap: wrap; gap: 7px; margin-top: 14px; }
.hero-chip { background: #ffffff1f; color: #e8f5fb; border: 1px solid #ffffff3a; }
.survey-hero-progress { margin-top: 14px; }
.survey-hero-label { display: flex; justify-content: space-between; font-size: 12px; color: #d4eaf5; margin-bottom: 6px; }
.survey-hero-label strong { color: #fff; }
.hero-progress { background: #ffffff2e; }
.survey-intro { margin: 0; white-space: pre-line; color: #2a4b60; font-size: 13.5px; line-height: 1.9; }
.form-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 10px; margin-bottom: 10px; }
.field-label { display: grid; gap: 6px; font-size: 12.5px; font-weight: 700; color: var(--vf-muted); margin-bottom: 10px; }
.select-wrap { position: relative; display: block; }
.select-wrap select, .inline-field input, .code-input { width: 100%; height: 48px; padding: 0 13px; border-radius: 13px; border: 1.5px solid #d6e3eb;
  background: #fff; font-size: 14px; color: var(--vf-ink); }
.select-wrap select { padding-left: 38px; appearance: none; -webkit-appearance: none; }
.select-icon { position: absolute; left: 11px; top: 50%; transform: translateY(-50%); pointer-events: none; }
.inline-field { display: flex; gap: 8px; }
.inline-field input { flex: 1; min-width: 0; text-align: left; }
.code-input { text-align: center; font-size: 22px; font-weight: 800; letter-spacing: 10px; }
.field-error { color: var(--vf-danger); font-size: 12px; font-weight: 700; margin: 4px 0 0; }
.sms-note { margin: 0 0 12px; line-height: 1.7; }
.action-error { margin: 0; align-items: center; }
</style>
