<template>
  <main class="vf-page photo-page" dir="rtl">
    <VisitTopBar :title="title" :eyebrow="eyebrow" :fallback="overviewRoute" back-label="بازگشت به پرسشنامه">
      <div class="photo-hero-meta">
        <span class="vf-chip" :class="enough ? 'vf-tone-done' : 'vf-tone-warning'"><v-icon size="15">{{ enough ? 'mdi-check-circle-outline' : 'mdi-camera-plus-outline' }}</v-icon>{{ faNumber(images.length) }} عکس ثبت‌شده</span>
        <span class="vf-chip hero-chip">{{ minimum ? 'حداقل ' + faNumber(minimum) : 'اختیاری' }}</span>
        <span v-if="maximum" class="vf-chip hero-chip">حداکثر {{ faNumber(maximum) }}</span>
      </div>
    </VisitTopBar>

    <div class="vf-body">
      <div v-if="loadError" class="vf-banner vf-banner-danger" role="alert">
        <v-icon color="#8a2f2a">mdi-alert-circle-outline</v-icon>
        <div><strong>عکس‌ها دریافت نشد</strong><p>{{ loadError }}</p>
          <button type="button" class="vf-banner-action" @click="load"><v-icon size="16">mdi-refresh</v-icon>تلاش دوباره</button></div>
      </div>
      <div v-else-if="settingsLoaded && !editable" class="vf-banner vf-banner-info" role="note">
        <v-icon color="#1d4f6d">mdi-lock-outline</v-icon><div><strong>فقط مشاهده</strong><p>این پرسشنامه ارسال شده است.</p></div>
      </div>
      <section v-if="guide" class="vf-card"><div class="vf-card-title"><h2><v-icon size="19" color="#1d608b">mdi-lightbulb-on-outline</v-icon> راهنمای عکس</h2></div><p class="guide-text">{{ guide }}</p></section>
      <div v-if="uploadError" class="vf-banner vf-banner-danger" role="alert"><v-icon color="#8a2f2a">mdi-alert-circle-outline</v-icon><div><strong>عکس ثبت نشد</strong><p>{{ uploadError }}</p></div></div>

      <div class="vf-section-label gallery-label"><h2>عکس‌های ثبت‌شده</h2><span v-if="maximum">{{ faNumber(images.length) }} از {{ faNumber(maximum) }}</span></div>
      <div v-if="loading && !images.length" class="gallery"><v-skeleton-loader v-for="n in 3" :key="n" class="tile-skeleton" type="image" /></div>
      <div v-else class="gallery">
        <template v-if="canAdd">
          <button type="button" class="add-tile is-camera" :disabled="uploading" @click="pick('camera')"><v-icon size="30" color="#1d608b">mdi-camera-outline</v-icon><span>گرفتن عکس</span></button>
          <button type="button" class="add-tile" :disabled="uploading" @click="pick('gallery')"><v-icon size="28" color="#4f7389">mdi-image-multiple-outline</v-icon><span>انتخاب از گالری</span></button>
        </template>
        <div v-if="uploading" class="photo-tile is-uploading" role="status"><v-progress-circular indeterminate size="28" width="3" color="#1d608b" /><span>در حال ارسال…</span></div>
        <button v-for="(image, index) in images" :key="image.id" type="button" class="photo-tile" :aria-label="'نمایش عکس ' + faNumber(index + 1)" @click="open(index)">
          <img :src="image.link" :alt="title + ' ' + faNumber(index + 1)" loading="lazy" /><span class="tile-badge">{{ faNumber(index + 1) }}</span>
        </button>
      </div>
      <EmptyState v-if="!loading && !images.length && !canAdd" kind="photos" size="sm" title="عکسی ثبت نشده" description="" />
      <input ref="camera" type="file" accept="image/*" capture="environment" hidden @change="onFiles" />
      <input ref="gallery" type="file" accept="image/jpeg,image/png,image/webp" hidden @change="onFiles" />
    </div>

    <footer v-if="settingsLoaded" class="vf-actionbar">
      <p v-if="editable && !enough" class="vf-actionbar-note is-danger">برای تکمیل این بخش {{ faNumber(minimum - images.length) }} عکس دیگر لازم است.</p>
      <div class="vf-actionbar-row">
        <button type="button" class="vf-btn vf-btn-ghost" @click="$router.push(overviewRoute)"><v-icon size="19">mdi-format-list-checks</v-icon>همه بخش‌ها</button>
        <button v-if="nextStep" type="button" class="vf-btn vf-btn-primary" @click="goNext">بخش بعد<v-icon color="white" size="19">mdi-arrow-left</v-icon></button>
      </div>
    </footer>

    <v-dialog v-model="viewer" fullscreen hide-overlay transition="dialog-bottom-transition">
      <div v-if="current" class="viewer" role="dialog" aria-label="نمایش عکس">
        <div class="viewer-top">
          <button type="button" class="viewer-btn" aria-label="بستن" @click="viewer = false"><v-icon color="white">mdi-close</v-icon></button>
          <span>{{ faNumber(viewerIndex + 1) }} از {{ faNumber(images.length) }}</span>
          <button v-if="editable" type="button" class="viewer-btn danger" aria-label="حذف عکس" :disabled="deleting" @click="remove"><v-icon color="white">mdi-trash-can-outline</v-icon></button>
          <span v-else class="viewer-spacer" />
        </div>
        <div class="viewer-stage"><img :src="current.link" :alt="title" /></div>
      </div>
    </v-dialog>
    <v-snackbar v-model="toast" :timeout="2400" top color="#15364f">{{ toastText }}</v-snackbar>
  </main>
</template>

<script>
import VisitTopBar from '@/components/Visit/VisitTopBar.vue';
import { errorMessage } from '@/utils/clientRequests';
import { faNumber, withProject } from '@/utils/visitFlow';
import { locate, shrinkImage, uploadName } from '@/utils/photoUpload';

import EmptyState from '@/components/EmptyState/index.vue';
export default {
  name: 'SurveyPhotoStep',
  components: { EmptyState, VisitTopBar },
  data: () => ({ images: [], settings: null, settingsLoaded: false, type: {}, loading: true, loadError: '', uploadError: '', uploading: false,
    viewer: false, viewerIndex: 0, deleting: false, toast: false, toastText: '' }),
  computed: {
    fillId() { return this.$route.params.surveyId; },
    typeId() { return Number(this.$route.params.id); },
    visitId() { return this.$route.query.visit || (this.settings && this.settings.survey_fill_out && this.settings.survey_fill_out.visit) || null; },
    overviewRoute() { return this.visitId ? { name: 'surveyDetailInVisit', params: { visit_id: this.visitId, fill_id: this.fillId } } : { name: 'surveyDetail', params: { id: this.fillId } }; },
    editable() { return !!(this.settings && this.settings.survey_fill_out && !this.settings.survey_fill_out.is_closed); },
    settingsType() { return this.settings ? (this.settings.photos || []).find(item => item.id === this.typeId) || {} : {}; },
    info() { return { ...this.type, ...this.settingsType }; },
    title() { return this.info.verbose_name || this.info.name || 'عکس پرسشنامه'; },
    guide() { return (this.info.description || '').trim(); },
    minimum() { return Math.max(Number(this.info.min) || 0, this.info.is_mandatory ? 1 : 0); },
    maximum() { return Number(this.info.max) || 0; },
    enough() { return this.images.length >= this.minimum; },
    canAdd() { return this.editable && (!this.maximum || this.images.length < this.maximum); },
    current() { return this.images[this.viewerIndex] || null; },
    steps() { return this.settings ? [...(this.settings.questions || []).map(item => ({ kind: 'question', item })), ...(this.settings.photos || []).map(item => ({ kind: 'photo', item }))] : []; },
    stepIndex() { return this.steps.findIndex(step => step.kind === 'photo' && step.item.id === this.typeId); },
    nextStep() { return this.stepIndex >= 0 ? this.steps[this.stepIndex + 1] || null : null; },
    eyebrow() {
      const survey = this.settings && this.settings.survey_fill_out && this.settings.survey_fill_out.survey;
      const name = survey ? (survey.verbose_name || survey.name) : 'پرسشنامه';
      return this.stepIndex >= 0 ? `بخش ${faNumber(this.stepIndex + 1)} از ${faNumber(this.steps.length)} · ${name}` : name;
    },
  },
  watch: { '$route.params': { handler: 'load' } },
  created() { this.load(); },
  methods: {
    faNumber,
    notify(text) { this.toastText = text; this.toast = true; },
    async load() {
      this.loading = true; this.loadError = '';
      try {
        const [settings, photos, type] = await Promise.all([
          this.$ApiServiceLayer.get(withProject(this.$PATH.RELATIVE_PATH.MULTI.SURVEY_QUESTION_TYPE + this.fillId + '/'), this.$PATH.SERVICE_NAME.AUTH),
          this.$ApiServiceLayer.get(withProject(this.$PATH.RELATIVE_PATH.GET.GET_SURVEY_IMAGE, { survey_photo_type: this.typeId, survey_fill_out: this.fillId, ordering: 'id' }), this.$PATH.SERVICE_NAME.AUTH),
          this.$ApiServiceLayer.get(withProject(this.$PATH.RELATIVE_PATH.GET.GT_SURVEY_IMAGE_DESC + this.typeId + '/'), this.$PATH.SERVICE_NAME.AUTH),
        ]);
        if (settings.status === 200) { this.settings = settings.data; this.settingsLoaded = true; }
        if (type.status === 200) this.type = type.data || {};
        if (photos.status !== 200) { this.loadError = errorMessage(photos); return; }
        const rows = Array.isArray(photos.data) ? photos.data : photos.data.results || [];
        this.images = rows.filter(row => !row.is_deleted);
      } catch (_) { this.loadError = 'اتصال برقرار نشد. دوباره تلاش کنید.'; }
      finally { this.loading = false; }
    },
    pick(source) { this.uploadError = ''; const input = this.$refs[source]; if (input) { input.value = ''; input.click(); } },
    async onFiles(event) {
      const file = (event.target.files || [])[0];
      if (!file || this.uploading) return;
      this.uploading = true; this.uploadError = '';
      try {
        let blob;
        try { blob = await shrinkImage(file); } catch (_) { this.uploadError = 'فایل عکس قابل خواندن نیست.'; return; }
        const position = await locate();
        const form = new FormData();
        form.append('link', blob, uploadName(file, blob));
        form.append('survey_photo_type', this.typeId);
        form.append('survey_fill_out', this.fillId);
        form.append('latitude', position.latitude == null ? '' : position.latitude);
        form.append('longitude', position.longitude == null ? '' : position.longitude);
        const response = await this.$ApiServiceLayer.post(withProject(this.$PATH.RELATIVE_PATH.POST.UPLOAD_SURVEY_PHOTOS),
          this.$PATH.SERVICE_NAME.AUTH, form, { 'Content-Type': 'multipart/form-data' });
        if (response.status !== 200 && response.status !== 201) { this.uploadError = errorMessage(response); return; }
        this.notify('عکس ثبت شد.');
        await this.load();
      } catch (_) { this.uploadError = 'ارسال عکس انجام نشد. دوباره تلاش کنید.'; }
      finally { this.uploading = false; }
    },
    open(index) { this.viewerIndex = index; this.viewer = true; },
    async remove() {
      if (!this.current || this.deleting) return;
      if (!window.confirm('این عکس حذف شود؟')) return;
      this.deleting = true;
      try {
        const response = await this.$ApiServiceLayer.delete(withProject(this.$PATH.RELATIVE_PATH.MULTI.SURVEY_DELETE_IMG + this.current.id + '/'), this.$PATH.SERVICE_NAME.AUTH);
        if (response.status === 204) { this.viewer = false; this.notify('عکس حذف شد.'); await this.load(); }
        else { this.viewer = false; this.uploadError = errorMessage(response); }
      } catch (_) { this.uploadError = 'حذف عکس انجام نشد.'; }
      finally { this.deleting = false; }
    },
    goNext() {
      const step = this.nextStep;
      if (!step) return this.$router.push(this.overviewRoute);
      const name = step.kind === 'photo' ? 'surveyImage' : 'surveyQuestions';
      return this.$router.push({ name, params: { surveyId: this.fillId, id: step.item.id }, query: this.visitId ? { visit: this.visitId } : {} });
    },
  },
};
</script>

<style scoped>
.photo-hero-meta { display: flex; flex-wrap: wrap; gap: 7px; margin-top: 14px; }
.hero-chip { background: #ffffff1f; color: #e8f5fb; border: 1px solid #ffffff3a; }
.vf-card-title h2 { display: flex; align-items: center; gap: 6px; }
.guide-text { margin: 0; font-size: 13.5px; color: #2a4b60; line-height: 1.9; white-space: pre-line; }
.gallery-label { margin-bottom: 10px; }
.gallery { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 9px; }
@media (max-width: 360px) { .gallery { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
.add-tile, .photo-tile, .tile-skeleton { aspect-ratio: 1 / 1; border-radius: 16px; overflow: hidden; }
.add-tile { display: grid; place-content: center; justify-items: center; gap: 4px; border: 2px dashed #b9d0dd; background: #f8fbfd; color: #33566b; font-size: 12px; font-weight: 800; }
.add-tile.is-camera { border-color: #6ea9cb; background: #eef7fc; color: #1d608b; }
.photo-tile { position: relative; padding: 0; border: 1px solid var(--vf-line); background: #e9f0f4; }
.photo-tile img { width: 100%; height: 100%; object-fit: cover; display: block; }
.photo-tile.is-uploading { display: grid; place-content: center; justify-items: center; gap: 6px; color: var(--vf-muted); font-size: 11px; font-weight: 700; }
.tile-badge { position: absolute; top: 6px; right: 6px; min-width: 24px; height: 24px; padding: 0 6px; border-radius: 8px; background: #102f4dcc; color: #fff; font-size: 11.5px; font-weight: 800; display: grid; place-items: center; }
.viewer { min-height: 100vh; background: #0b1a26; color: #fff; display: flex; flex-direction: column; }
.viewer-top { display: flex; align-items: center; justify-content: space-between; padding: calc(12px + env(safe-area-inset-top)) 14px 10px; font-weight: 700; }
.viewer-btn { width: 44px; height: 44px; border-radius: 13px; background: #ffffff1c; display: grid; place-items: center; }
.viewer-btn.danger { background: #a33a35; }
.viewer-spacer { width: 44px; }
.viewer-stage { flex: 1; display: flex; align-items: center; justify-content: center; padding: 0 12px 24px; }
.viewer-stage img { max-width: 100%; max-height: 78vh; object-fit: contain; border-radius: 12px; }
</style>
