<template>
  <main class="field-page client-visit-detail" dir="rtl">
    <header class="detail-hero">
      <router-link :to="{ name: 'clientVisits' }" class="detail-back"><v-icon color="white" size="20">mdi-arrow-right</v-icon><span>درخواست‌ها و ویزیت‌ها</span></router-link>
      <span class="detail-eyebrow">سان اپ · پیگیری خدمت</span>
      <h1>{{ visit ? visit.type_name : 'جزئیات خدمت' }}</h1>
      <p v-if="visit">{{ visit.building.name }} <span class="detail-code">{{ visit.building.code }}</span></p>
      <span v-if="visit" class="detail-status"><v-icon color="white" size="17">mdi-progress-check</v-icon>{{ status(visit) }}</span>
    </header>

    <div v-if="loading" class="detail-body" aria-label="در حال دریافت جزئیات"><v-skeleton-loader type="article, article" /></div>
    <div v-else-if="error" class="detail-body"><v-alert type="error" outlined role="alert">{{ error }}<v-btn text color="error" @click="load">تلاش دوباره</v-btn></v-alert><router-link :to="{ name: 'clientVisits' }" class="detail-text-link">بازگشت به درخواست‌ها</router-link></div>
    <div v-else-if="visit" class="detail-body">
      <section class="detail-panel" aria-labelledby="tracking-heading">
        <div class="detail-section-title"><span class="detail-section-icon"><v-icon color="#236180" size="22">mdi-clipboard-text-clock-outline</v-icon></span><div><small>آخرین وضعیت</small><h2 id="tracking-heading">مسیر این خدمت</h2></div></div>
        <p class="detail-explain">{{ explanation(visit) }}</p>
        <div class="detail-facts">
          <div><span>کد پیگیری</span><strong>{{ visit.id }}</strong></div>
          <div><span>ثبت درخواست</span><strong>{{ date(visit.created_at) }}</strong></div>
          <div><span>موعد مراجعه</span><strong>{{ date(visit.due_date) }}</strong></div>
          <div><span>کارشناس</span><strong>{{ visit.expert_name || 'هنوز تعیین نشده' }}</strong></div>
        </div>
      </section>

      <section class="detail-panel" aria-labelledby="asset-heading">
        <div class="detail-section-title"><span class="detail-section-icon"><v-icon color="#236180" size="22">mdi-office-building-outline</v-icon></span><div><small>محل خدمت</small><h2 id="asset-heading">ساختمان و آسانسورها</h2></div></div>
        <router-link :to="{ name: 'buildingDetail', params: { id: visit.building.id } }" class="detail-building">{{ visit.building.name }} <v-icon size="19">mdi-arrow-left</v-icon></router-link>
        <div v-if="visit.elevators.length" class="detail-elevators"><span v-for="elevator in visit.elevators" :key="elevator.id"><v-icon size="17">mdi-elevator</v-icon>{{ elevator.title || 'آسانسور ' + elevator.id }}</span></div>
        <p v-else class="detail-muted">برای این مراجعه آسانسور مشخصی ثبت نشده است.</p>
      </section>

      <section class="detail-panel" aria-labelledby="report-heading">
        <div class="detail-section-title"><span class="detail-section-icon"><v-icon color="#236180" size="22">mdi-file-document-check-outline</v-icon></span><div><small>نتیجه انجام خدمت</small><h2 id="report-heading">گزارش کار</h2></div></div>
        <p v-if="visit.report_version" class="detail-report-version">نسخه {{ Number(visit.report_version).toLocaleString('fa-IR') }} · ثبت ثابت در {{ date(visit.report_captured_at) }}</p>
        <v-btn v-if="visit.report_version" outlined color="primary" class="mt-3" :loading="pdfLoading" :disabled="pdfLoading" @click="downloadReport"><v-icon left size="19">mdi-file-pdf-box</v-icon>دریافت گزارش PDF</v-btn>
        <v-alert v-if="pdfError" type="error" outlined role="alert" class="mt-3">{{ pdfError }}</v-alert>
        <p v-if="!visit.report_version && ['2', '3'].includes(visit.status)" class="detail-report-version">این گزارش قدیمی نسخه ثابت ندارد.</p>
        <div v-if="visit.report.length" class="detail-report"><div v-for="(answer, index) in visit.report" :key="index" class="detail-answer"><strong>{{ answer.question }}</strong><span>{{ answerText(answer) }}</span></div></div>
        <p v-else class="detail-muted">{{ ['2', '3'].includes(visit.status) ? 'برای این خدمت پاسخی در گزارش ثبت نشده است.' : 'گزارش پس از پایان خدمت اینجا نمایش داده می‌شود.' }}</p>
      </section>

      <section v-if="['2', '3'].includes(visit.status)" class="detail-panel" aria-labelledby="feedback-heading">
        <div class="detail-section-title"><span class="detail-section-icon"><v-icon color="#236180" size="22">mdi-star-check-outline</v-icon></span><div><small>نظر شما</small><h2 id="feedback-heading">دریافت و کیفیت خدمت</h2></div></div>
        <p class="detail-muted">اگر خدمت را دریافت کرده‌اید، آن را تأیید کنید و تجربه‌تان را ثبت کنید.</p>
        <v-progress-linear v-if="feedbackLoading" indeterminate color="primary" class="mt-4" />
        <v-alert v-if="feedbackError" type="error" outlined role="alert" class="mt-4">{{ feedbackError }} <v-btn text color="error" @click="loadFeedback(sequence)">تلاش دوباره</v-btn></v-alert>
        <div v-if="!feedbackLoading && !feedbackError" class="feedback-form">
          <div class="feedback-stars" role="group" aria-label="امتیاز کیفیت خدمت از یک تا پنج">
            <button v-for="value in 5" :key="value" type="button" :aria-label="`${value} ستاره`" :aria-pressed="rating === value ? 'true' : 'false'" @click="rating = value"><v-icon :color="rating >= value ? '#bc751c' : '#a1b2bd'" size="28">{{ rating >= value ? 'mdi-star' : 'mdi-star-outline' }}</v-icon></button>
          </div>
          <v-textarea v-model="note" outlined auto-grow rows="2" counter="1000" maxlength="1000" label="توضیح شما درباره خدمت (اختیاری)" class="feedback-note" />
          <v-checkbox v-model="received" :disabled="!!(feedback && feedback.received_at)" label="دریافت خدمت را تأیید می‌کنم" hide-details class="feedback-receipt" />
          <span v-if="feedback && feedback.received_at" class="feedback-confirmed"><v-icon size="17" color="#277960">mdi-check-circle</v-icon>دریافت خدمت در {{ date(feedback.received_at) }} تأیید شده است.</span>
          <v-alert v-if="feedbackMessage" type="success" text role="status" class="mt-3">{{ feedbackMessage }}</v-alert>
          <v-btn color="primary" block :loading="feedbackSaving" :disabled="feedbackSaving || !feedbackDirty" @click="saveFeedback">ثبت نظر</v-btn>
        </div>
      </section>
      <router-link :to="{ name: 'clientSupport', query: { visit: visit.id } }" class="detail-support-link"><v-icon color="#1a6683" size="23">mdi-lifebuoy</v-icon><span><strong>درباره این خدمت پرسشی دارید؟</strong><small>با پشتیبانی گفتگو کنید</small></span><v-icon color="#36758b" size="20">mdi-arrow-left</v-icon></router-link>
    </div>
  </main>
</template>

<script>
import { errorMessage } from '@/utils/clientRequests';

export default {
  name: 'ClientVisitDetail',
  data: () => ({ visit: null, loading: false, error: '', sequence: 0, pdfLoading: false, pdfError: '', feedback: null, feedbackLoading: false, feedbackSaving: false, feedbackError: '', feedbackMessage: '', rating: 0, note: '', received: false }),
  mounted() { this.load(); },
  beforeDestroy() { this.sequence += 1; },
  watch: {
    '$route.params.id'() { this.load(); },
    project() { this.load(); },
  },
  computed: {
    project() { return this.$STORE.state.userConfig.selectedProject; },
    feedbackDirty() {
      if (this.feedbackLoading || this.feedbackError) return false;
      return this.rating !== (this.feedback?.rating || 0)
        || this.note.trim() !== (this.feedback?.note || '')
        || (this.received && !this.feedback?.received_at);
    },
  },
  methods: {
    date(value) { if (!value) return 'هنوز مشخص نشده'; const parsed = new Date(value); return Number.isNaN(parsed.getTime()) ? 'نامشخص' : parsed.toLocaleDateString('fa-IR', { year: 'numeric', month: 'long', day: 'numeric' }); },
    status(visit) { return visit.is_pending_request ? 'در انتظار بررسی' : ({ '0': 'در انتظار مراجعه', '1': 'در حال انجام', '2': 'انجام شده', '3': 'تأیید شده', '4': 'رد شده', '5': 'نیاز به مراجعه مجدد', '6': 'متوقف شده' }[visit.status] || 'در حال پیگیری'); },
    explanation(visit) {
      if (visit.is_pending_request) return 'درخواست شما ثبت شده است. شرکت پس از بررسی، زمان مراجعه و کارشناس را مشخص می‌کند.';
      return ({ '0': 'مراجعه ثبت شده و در انتظار شروع است.', '1': 'کارشناس در حال انجام خدمت است.', '2': 'خدمت انجام شده و گزارش آن در دسترس است.', '3': 'خدمت تأیید شده و گزارش آن در دسترس است.', '4': 'این مراجعه رد شده است؛ برای پیگیری با پشتیبانی تماس بگیرید.', '5': 'برای این خدمت مراجعه دوباره لازم است.', '6': 'انجام این خدمت فعلاً متوقف شده است.' })[visit.status] || 'وضعیت این خدمت در حال پیگیری است.';
    },
    answerText(answer) {
      const values = [answer.dropdown, answer.radio, ...(answer.multichoice || []), answer.text, answer.description];
      if (answer.number !== null && answer.number !== undefined) values.push(Number(answer.number).toLocaleString('fa-IR'));
      if (answer.bool === true) values.push('بله');
      if (answer.bool === false) values.push('خیر');
      return values.filter(value => value !== null && value !== undefined && value !== '').join('، ') || 'پاسخی ثبت نشده';
    },
    async load() {
      const sequence = ++this.sequence;
      this.loading = true; this.error = ''; this.visit = null; this.feedback = null; this.feedbackMessage = '';
      try {
        const response = await this.$ApiServiceLayer.get(`core/api/client/visits/${this.$route.params.id}/?p=${this.project}`);
        if (sequence !== this.sequence) return;
        if (response.status !== 200) { this.error = errorMessage(response); return; }
        this.visit = response.data;
        if (['2', '3'].includes(this.visit.status)) await this.loadFeedback(sequence);
      } catch (_) { if (sequence === this.sequence) this.error = 'دریافت جزئیات ممکن نشد. دوباره تلاش کنید.'; }
      finally { if (sequence === this.sequence) this.loading = false; }
    },
    feedbackUrl() { return `core/api/client/visits/${this.$route.params.id}/feedback/?p=${this.project}`; },
    async downloadReport() {
      if (!this.visit || !this.visit.report_version || this.pdfLoading) return;
      if (!navigator.onLine) { this.pdfError = 'برای دریافت فایل به اینترنت وصل شوید.'; return; }
      this.pdfLoading = true; this.pdfError = '';
      try {
        const response = await this.$ApiServiceLayer.getBlob(`core/api/client/visits/${this.visit.id}/report.pdf?p=${this.project}`);
        if (response.status !== 200 || !(response.data instanceof Blob)) { this.pdfError = 'دریافت گزارش ممکن نشد. دوباره تلاش کنید.'; return; }
        const url = URL.createObjectURL(response.data);
        const anchor = document.createElement('a');
        anchor.href = url; anchor.download = `saan-visit-${this.visit.id}-v${this.visit.report_version}.pdf`;
        document.body.appendChild(anchor); anchor.click(); anchor.remove();
        window.setTimeout(() => URL.revokeObjectURL(url), 60000);
      } catch (_) { this.pdfError = 'دریافت گزارش ممکن نشد. دوباره تلاش کنید.'; }
      finally { this.pdfLoading = false; }
    },
    async loadFeedback(sequence) {
      this.feedbackLoading = true; this.feedbackError = '';
      try {
        const response = await this.$ApiServiceLayer.get(this.feedbackUrl());
        if (sequence !== this.sequence) return;
        if (response.status !== 200) { this.feedbackError = errorMessage(response); return; }
        this.feedback = response.data;
        this.rating = response.data.rating || 0;
        this.note = response.data.note || '';
        this.received = !!response.data.received_at;
      } catch (_) { if (sequence === this.sequence) this.feedbackError = 'دریافت بازخورد ممکن نشد.'; }
      finally { if (sequence === this.sequence) this.feedbackLoading = false; }
    },
    async saveFeedback() {
      if (this.feedbackSaving) return;
      const payload = {};
      if (this.rating !== (this.feedback?.rating || 0)) payload.rating = this.rating;
      if (this.note.trim() !== (this.feedback?.note || '')) payload.note = this.note.trim();
      if (this.received && !(this.feedback && this.feedback.received_at)) payload.received = true;
      if (!Object.keys(payload).length) return;
      this.feedbackSaving = true; this.feedbackError = ''; this.feedbackMessage = '';
      try {
        const response = await this.$ApiServiceLayer.post(this.feedbackUrl(), '', payload);
        if (![200, 201].includes(response.status)) { this.feedbackError = errorMessage(response); return; }
        this.feedback = response.data; this.received = !!response.data.received_at;
        this.rating = response.data.rating || 0; this.note = response.data.note || '';
        this.feedbackMessage = 'نظر شما ثبت شد.';
      } catch (_) { this.feedbackError = 'ثبت نظر ممکن نشد. دوباره تلاش کنید.'; }
      finally { this.feedbackSaving = false; }
    },
  },
};
</script>

<style scoped>
.client-visit-detail { padding: 0 0 calc(110px + env(safe-area-inset-bottom)); background: #f4f8fb; }
.detail-hero { padding: calc(19px + env(safe-area-inset-top)) 20px 29px; color: #fff; background: linear-gradient(140deg, #102f4d, #1b6487); border-radius: 0 0 28px 28px; box-shadow: 0 12px 28px #10395720; }
.detail-back { display: inline-flex; align-items: center; gap: 6px; min-height: 44px; color: #e9f7fb; text-decoration: none; font-size: 13px; }
.detail-eyebrow { display: block; margin-top: 24px; color: #bce6ef; font-size: 12px; font-weight: 700; }
.detail-hero h1 { color: #fff; margin: 6px 0; font-size: 26px; line-height: 1.45; }
.detail-hero p { margin: 0; color: #e0f1f5; font-size: 14px; }
.detail-code { display: inline-block; margin-right: 8px; direction: ltr; unicode-bidi: isolate; font-size: 11px; color: #c9e9f1; }
.detail-status { display: inline-flex; align-items: center; gap: 5px; margin-top: 22px; padding: 7px 12px; border-radius: 11px; border: 1px solid #ffffff50; background: #ffffff21; font-size: 12px; font-weight: 700; }
.detail-body { display: grid; gap: 16px; padding: 23px 20px; }
.detail-panel { padding: 19px; border: 1px solid #e0eaf0; border-radius: 18px; background: #fff; box-shadow: 0 4px 18px #183f6009; }
.detail-section-title { display: flex; align-items: center; gap: 10px; }
.detail-section-title small { color: #367994; font-size: 11px; font-weight: 700; }
.detail-section-title h2 { color: #14364f; font-size: 17px; margin: 1px 0 0; }
.detail-section-icon { display: grid; place-items: center; width: 42px; height: 42px; flex: none; border-radius: 12px; background: #e7f3f7; }
.detail-explain { margin: 17px 0; padding: 12px 14px; border-radius: 12px; background: #f1f7f9; color: #315c70; font-size: 13px; }
.detail-facts { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 15px 12px; border-top: 1px solid #eaf1f4; padding-top: 16px; }
.detail-facts div { display: grid; gap: 2px; min-width: 0; }.detail-facts span { color: #668093; font-size: 11px; }.detail-facts strong { color: #173b52; font-size: 13px; overflow-wrap: anywhere; }
.detail-building { display: flex; justify-content: space-between; align-items: center; margin-top: 16px; color: #1c678a; font-size: 14px; font-weight: 700; text-decoration: none; }
.detail-elevators { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 16px; }.detail-elevators span { display: inline-flex; align-items: center; gap: 5px; padding: 7px 9px; border-radius: 9px; background: #eff5f8; color: #385f73; font-size: 12px; }
.detail-report { margin-top: 15px; }.detail-answer { display: grid; gap: 5px; border-top: 1px solid #edf2f5; padding: 13px 0; }.detail-answer strong { font-size: 13px; color: #173b52; }.detail-answer span { color: #405f72; font-size: 13px; overflow-wrap: anywhere; }
.detail-report-version { margin: 14px 0 0; color: #31738a; font-size: 12px; font-weight: 700; }
.feedback-form { margin-top: 15px; }.feedback-stars { display: flex; gap: 4px; margin-bottom: 13px; }.feedback-stars button { width: 44px; height: 44px; display: grid; place-items: center; border: 1px solid #e4edf1; border-radius: 10px; background: #fffaf1; }.feedback-stars button:focus-visible { outline: 3px solid #328fbc; }.feedback-note { margin-top: 8px !important; }.feedback-receipt { margin: 0 0 17px !important; }.feedback-confirmed { display: inline-flex; align-items: center; gap: 5px; margin-bottom: 14px; color: #24705a; font-size: 12px; }
.detail-support-link { display: flex; align-items: center; gap: 11px; min-height: 72px; padding: 13px 16px; border: 1px solid #cde4ec; border-radius: 16px; background: #eaf5f7; color: #17445d; text-decoration: none; }.detail-support-link span { flex: 1; display: grid; gap: 3px; }.detail-support-link strong { font-size: 13px; }.detail-support-link small { color: #56788a; font-size: 11px; }
.detail-muted { color: #607e90; font-size: 13px; margin: 16px 0 0; }.detail-text-link { color: #21678a; font-size: 13px; font-weight: 700; }
.client-visit-detail a:focus-visible { outline: 3px solid #4da2c8; outline-offset: 3px; }
@media(max-width:350px){.detail-body{padding-left:14px;padding-right:14px}.detail-hero{padding-left:16px;padding-right:16px}.detail-panel{padding:15px}}
</style>
