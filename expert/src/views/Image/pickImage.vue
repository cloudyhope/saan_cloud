<template>
  <main class="vf-page photo-page" dir="rtl">
    <VisitTopBar
      :title="title"
      :eyebrow="eyebrow"
      :fallback="{ name: 'storeDetail', params: { id: visitId } }"
      back-label="بازگشت به مأموریت"
    >
      <div class="photo-hero-meta">
        <span class="vf-chip" :class="enough ? 'vf-tone-done' : 'vf-tone-warning'">
          <v-icon size="15">{{ enough ? 'mdi-check-circle-outline' : 'mdi-camera-plus-outline' }}</v-icon>
          {{ faNumber(images.length) }} عکس ثبت‌شده
        </span>
        <span v-if="minimum" class="vf-chip hero-chip">حداقل {{ faNumber(minimum) }}</span>
        <span v-else class="vf-chip hero-chip">اختیاری</span>
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
        <v-icon color="#1d4f6d">mdi-lock-outline</v-icon>
        <div><strong>فقط مشاهده</strong><p>{{ readonlyReason }}</p></div>
      </div>

      <section class="vf-card guide-card" aria-labelledby="guide-heading">
        <div class="vf-card-title"><h2 id="guide-heading"><v-icon size="19" color="#1d608b">mdi-lightbulb-on-outline</v-icon> راهنمای عکس</h2></div>
        <p class="guide-text">{{ guide }}</p>
        <ul class="guide-list">
          <li><v-icon size="16" color="#1a7154">mdi-check</v-icon>عکس واضح، با نور کافی و بدون لرزش بگیرید.</li>
          <li><v-icon size="16" color="#1a7154">mdi-check</v-icon>برای ثبت موقعیت، دسترسی مکان را در مرورگر مجاز کنید.</li>
          <li v-if="maximum"><v-icon size="16" color="#1a7154">mdi-check</v-icon>حداکثر {{ faNumber(maximum) }} عکس برای این بخش قابل ثبت است.</li>
        </ul>
      </section>

      <div v-if="uploadError" class="vf-banner vf-banner-danger" role="alert">
        <v-icon color="#8a2f2a">mdi-alert-circle-outline</v-icon><div><strong>عکس ثبت نشد</strong><p>{{ uploadError }}</p></div>
      </div>

      <section aria-labelledby="gallery-heading">
        <div class="vf-section-label gallery-label"><h2 id="gallery-heading">عکس‌های ثبت‌شده</h2><span v-if="maximum">{{ faNumber(images.length) }} از {{ faNumber(maximum) }}</span></div>
        <div v-if="loading && !images.length" class="gallery">
          <v-skeleton-loader v-for="n in 3" :key="n" class="tile-skeleton" type="image" />
        </div>
        <div v-else class="gallery">
          <template v-if="canAdd">
            <button type="button" class="add-tile is-camera" :disabled="uploading" @click="pick('camera')">
              <v-icon size="30" color="#1d608b">mdi-camera-outline</v-icon><span>گرفتن عکس</span>
            </button>
            <button type="button" class="add-tile" :disabled="uploading" @click="pick('gallery')">
              <v-icon size="28" color="#4f7389">mdi-image-multiple-outline</v-icon><span>انتخاب از گالری</span>
            </button>
          </template>
          <div v-for="item in uploadingTiles" :key="item.key" class="photo-tile is-uploading" role="status">
            <v-progress-circular indeterminate size="28" width="3" color="#1d608b" /><span>{{ item.label }}</span>
          </div>
          <button v-for="(image, index) in images" :key="image.id" type="button" class="photo-tile" @click="open(index)"
                  :aria-label="'نمایش عکس ' + faNumber(index + 1)">
            <img :src="image.link" :alt="title + ' ' + faNumber(index + 1)" loading="lazy" />
            <span class="tile-badge">{{ faNumber(index + 1) }}</span>
            <span v-if="image.latitude && image.longitude" class="tile-geo" title="موقعیت ثبت شده"><v-icon size="13" color="white">mdi-map-marker</v-icon></span>
          </button>
        </div>
        <EmptyState v-if="!loading && !images.length && !canAdd" kind="photos" size="sm" title="برای این بخش عکسی ثبت نشده" description="" />
        <p v-if="editable && maximum && images.length >= maximum" class="vf-muted max-note">به حداکثر تعداد عکس رسیده‌اید؛ برای عکس تازه، یکی را حذف کنید.</p>
      </section>
      <input ref="camera" type="file" accept="image/*" capture="environment" hidden @change="onFiles" />
      <input ref="gallery" type="file" accept="image/jpeg,image/png,image/webp" multiple hidden @change="onFiles" />
    </div>

    <footer v-if="settingsLoaded" class="vf-actionbar">
      <p v-if="editable && !enough" class="vf-actionbar-note is-danger">برای تکمیل این بخش {{ faNumber(minimum - images.length) }} عکس دیگر لازم است.</p>
      <div class="vf-actionbar-row">
        <button type="button" class="vf-btn vf-btn-ghost" @click="backToVisit"><v-icon size="19">mdi-format-list-checks</v-icon>مراحل مأموریت</button>
        <button v-if="nextStep" type="button" class="vf-btn vf-btn-primary" @click="goNext">بخش بعد<v-icon color="white" size="19">mdi-arrow-left</v-icon></button>
      </div>
    </footer>

    <v-dialog v-model="viewer" fullscreen hide-overlay transition="dialog-bottom-transition">
      <div v-if="current" class="viewer" role="dialog" aria-label="نمایش عکس">
        <div class="viewer-top">
          <button type="button" class="viewer-btn" aria-label="بستن" @click="viewer = false"><v-icon color="white">mdi-close</v-icon></button>
          <span>{{ faNumber(viewerIndex + 1) }} از {{ faNumber(images.length) }}</span>
          <button v-if="editable" type="button" class="viewer-btn danger" aria-label="حذف عکس" @click="confirmDelete = true"><v-icon color="white">mdi-trash-can-outline</v-icon></button>
          <span v-else class="viewer-spacer" />
        </div>
        <div class="viewer-stage">
          <button v-if="images.length > 1" type="button" class="viewer-nav" aria-label="عکس قبلی" @click="step(-1)"><v-icon color="white" size="30">mdi-chevron-right</v-icon></button>
          <img :src="current.link" :alt="title" />
          <button v-if="images.length > 1" type="button" class="viewer-nav" aria-label="عکس بعدی" @click="step(1)"><v-icon color="white" size="30">mdi-chevron-left</v-icon></button>
        </div>
        <p class="viewer-meta">{{ faDate(current.datetime_created, true) }} · {{ current.latitude && current.longitude ? 'با موقعیت مکانی' : 'بدون موقعیت مکانی' }}</p>
      </div>
    </v-dialog>

    <v-bottom-sheet v-model="confirmDelete" max-width="576px">
      <v-sheet class="vf-sheet">
        <div class="vf-sheet-handle" aria-hidden="true" />
        <div class="delete-sheet">
          <v-icon color="#a33a35" size="38">mdi-trash-can-outline</v-icon>
          <h2>این عکس حذف شود؟</h2>
          <p>عکس از گزارش این مأموریت حذف می‌شود.</p>
          <div class="vf-actionbar-row">
            <button type="button" class="vf-btn vf-btn-ghost" :disabled="deleting" @click="confirmDelete = false">انصراف</button>
            <button type="button" class="vf-btn vf-btn-danger" :disabled="deleting" @click="remove">
              <v-progress-circular v-if="deleting" indeterminate size="18" width="2" color="#a33a35" /><template v-else>حذف عکس</template>
            </button>
          </div>
        </div>
      </v-sheet>
    </v-bottom-sheet>
    <v-snackbar v-model="toast" :timeout="2400" top color="#15364f">{{ toastText }}</v-snackbar>
  </main>
</template>

<script>
import VisitTopBar from '@/components/Visit/VisitTopBar.vue';
import { errorMessage } from '@/utils/clientRequests';
import { faDate, faNumber, startVisit, withProject } from '@/utils/visitFlow';
import { locate, shrinkImage, uploadName } from '@/utils/photoUpload';

import EmptyState from '@/components/EmptyState/index.vue';
export default {
  name: 'PhotoStep',
  components: { EmptyState, VisitTopBar },
  data: () => ({
    images: [], photoType: null, settings: null, settingsLoaded: false, loading: true, loadError: '', uploadError: '',
    uploading: false, uploadingTiles: [], viewer: false, viewerIndex: 0, confirmDelete: false, deleting: false,
    toast: false, toastText: '', latitude: null, longitude: null, sequence: 0,
  }),
  computed: {
    visitId() { return this.$route.params.id; },
    typeId() { return Number(this.$route.params.type); },
    visit() { return this.settings && this.settings.visit; },
    settingsType() { return this.settings ? (this.settings.photos || []).find(item => item.id === this.typeId) : null; },
    type() { return this.settingsType || this.photoType || {}; },
    title() { return this.type.verbose_name || this.type.name || 'ثبت عکس'; },
    guide() { return (this.type.description || '').trim() || 'از بخش مشخص‌شده عکسی بگیرید که جزئیات کار به‌وضوح دیده شود.'; },
    minimum() { return Math.max(Number(this.type.min) || 0, this.type.is_mandatory ? 1 : 0); },
    maximum() { return Number(this.type.max) || 0; },
    enough() { return this.images.length >= this.minimum; },
    editable() { return !!(this.settings && this.settings.editable); },
    canAdd() { return this.editable && (!this.maximum || this.images.length + this.uploadingTiles.length < this.maximum); },
    current() { return this.images[this.viewerIndex] || null; },
    steps() {
      if (!this.settings) return [];
      return [...(this.settings.questions || []).map(item => ({ kind: 'question', item })),
        ...(this.settings.photos || []).map(item => ({ kind: 'photo', item }))];
    },
    stepIndex() { return this.steps.findIndex(step => step.kind === 'photo' && step.item.id === this.typeId); },
    nextStep() { return this.stepIndex >= 0 ? this.steps[this.stepIndex + 1] || null : null; },
    eyebrow() {
      const building = this.visit && this.visit.building;
      const name = building ? (building.verbose_name || building.name) : '';
      return this.stepIndex >= 0 ? `بخش ${faNumber(this.stepIndex + 1)} از ${faNumber(this.steps.length)}${name ? ' · ' + name : ''}` : name;
    },
    readonlyReason() {
      if (this.settings && !this.settings.is_assignee) return 'شما مجری این مأموریت نیستید.';
      const status = this.visit && this.visit.status;
      return status === '2' ? 'گزارش ثبت شده و در انتظار بررسی است؛ تغییر عکس ممکن نیست.'
        : status === '3' ? 'گزارش تأیید شده و بسته است.' : status === '4' ? 'گزارش رد شده و بسته است.'
          : 'این مأموریت برای ثبت عکس باز نیست.';
    },
  },
  watch: { '$route.params': { handler: 'load' }, images() { if (this.viewerIndex >= this.images.length) this.viewerIndex = Math.max(0, this.images.length - 1); } },
  created() { this.load(); },
  beforeDestroy() { this.sequence++; },
  methods: {
    faNumber, faDate,
    notify(text) { this.toastText = text; this.toast = true; },
    async load() {
      const sequence = ++this.sequence;
      this.loading = true; this.loadError = '';
      try {
        const [settings, photos, type] = await Promise.all([
          this.$ApiServiceLayer.get(withProject(this.$PATH.RELATIVE_PATH.GET.VISIT_PAGE_SETTING + this.visitId + '/'), this.$PATH.SERVICE_NAME.AUTH),
          this.$ApiServiceLayer.get(withProject(this.$PATH.RELATIVE_PATH.GET.GET_IMAGES_ALBUM, { type: this.typeId, visit: this.visitId, ordering: 'id' }), this.$PATH.SERVICE_NAME.AUTH),
          this.$ApiServiceLayer.get(withProject(this.$PATH.RELATIVE_PATH.GET.PHOTO_DESC + this.typeId + '/'), this.$PATH.SERVICE_NAME.AUTH),
        ]);
        if (sequence !== this.sequence) return;
        if (settings.status === 200) { this.settings = settings.data; this.settingsLoaded = true; }
        if (type.status === 200) this.photoType = type.data;
        if (photos.status !== 200) { this.loadError = errorMessage(photos); return; }
        this.images = Array.isArray(photos.data) ? photos.data : photos.data.results || [];
      } catch (_) {
        if (sequence === this.sequence) this.loadError = 'اتصال برقرار نشد. اینترنت را بررسی و دوباره تلاش کنید.';
      } finally {
        if (sequence === this.sequence) this.loading = false;
      }
    },
    pick(source) {
      this.uploadError = '';
      const input = this.$refs[source];
      if (input) { input.value = ''; input.click(); }
    },
    async onFiles(event) {
      const files = Array.from(event.target.files || []);
      if (!files.length || this.uploading) return;
      const room = this.maximum ? this.maximum - this.images.length : files.length;
      if (room <= 0) { this.uploadError = 'به حداکثر تعداد عکس این بخش رسیده‌اید.'; return; }
      const batch = files.slice(0, room);
      if (files.length > room) this.uploadError = `فقط ${faNumber(room)} عکس دیگر قابل ثبت است؛ بقیه کنار گذاشته شد.`;
      this.uploading = true;
      try {
        if (this.visit && ['0', '5', '6'].includes(this.visit.status)) {
          const started = await startVisit(this.$ApiServiceLayer, this.$PATH, this.visitId);
          if (!started.ok) { this.uploadError = started.message; return; }
          this.settings.visit = { ...this.visit, status: '1' };
        }
        ({ latitude: this.latitude, longitude: this.longitude } = await locate());
        let sent = 0;
        for (const [index, file] of batch.entries()) {
          const tile = { key: Date.now() + '-' + index, label: batch.length > 1 ? `ارسال ${faNumber(index + 1)} از ${faNumber(batch.length)}` : 'در حال ارسال…' };
          this.uploadingTiles.push(tile);
          try {
            const ok = await this.upload(file);
            if (ok) sent += 1;
          } finally {
            this.uploadingTiles = this.uploadingTiles.filter(item => item !== tile);
          }
        }
        if (sent) {
          this.notify(sent > 1 ? `${faNumber(sent)} عکس ثبت شد.` : 'عکس ثبت شد.');
          await this.load();
        }
      } finally {
        this.uploading = false;
      }
    },
    async upload(file) {
      if (!/^image\//.test(file.type || 'image/')) { this.uploadError = 'فقط فایل تصویر قابل ثبت است.'; return false; }
      let blob;
      try { blob = await shrinkImage(file); } catch (_) { this.uploadError = 'فایل عکس قابل خواندن نیست.'; return false; }
      const form = new FormData();
      form.append('link', blob, uploadName(file, blob));
      form.append('visit', this.visitId);
      form.append('type', this.typeId);
      form.append('latitude', this.latitude == null ? '' : this.latitude);
      form.append('longitude', this.longitude == null ? '' : this.longitude);
      try {
        const response = await this.$ApiServiceLayer.post(withProject(this.$PATH.RELATIVE_PATH.POST.UPLOAD_IMAGE),
          this.$PATH.SERVICE_NAME.AUTH, form, { 'Content-Type': 'multipart/form-data' });
        if (response.status === 200) return true;
        this.uploadError = response.status === 404 ? 'این مأموریت برای ثبت عکس باز نیست.' : errorMessage(response);
      } catch (_) {
        this.uploadError = 'ارسال عکس انجام نشد. اتصال را بررسی و دوباره تلاش کنید.';
      }
      return false;
    },
    open(index) { this.viewerIndex = index; this.viewer = true; },
    step(delta) { const count = this.images.length; this.viewerIndex = (this.viewerIndex + delta + count) % count; },
    async remove() {
      if (!this.current || this.deleting) return;
      this.deleting = true;
      try {
        const response = await this.$ApiServiceLayer.delete(
          withProject(this.$PATH.RELATIVE_PATH.DELETE.DELETE_IMAGE + this.current.id + '/'), this.$PATH.SERVICE_NAME.AUTH);
        if (response.status === 204) {
          this.confirmDelete = false;
          this.viewer = false;
          this.notify('عکس حذف شد.');
          await this.load();
        } else {
          this.confirmDelete = false;
          this.uploadError = response.status === 404 ? 'این عکس قابل حذف نیست؛ مأموریت بسته است یا عکس متعلق به شما نیست.' : errorMessage(response);
        }
      } catch (_) {
        this.uploadError = 'حذف عکس انجام نشد. دوباره تلاش کنید.';
      } finally { this.deleting = false; }
    },
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
.photo-hero-meta { display: flex; flex-wrap: wrap; gap: 7px; margin-top: 14px; }
.hero-chip { background: #ffffff1f; color: #e8f5fb; border: 1px solid #ffffff3a; }
.guide-card .vf-card-title h2 { display: flex; align-items: center; gap: 6px; }
.guide-text { margin: 0 0 10px; font-size: 13.5px; color: #2a4b60; line-height: 1.9; white-space: pre-line; }
.guide-list { list-style: none; padding: 0; margin: 0; display: grid; gap: 6px; }
.guide-list li { display: flex; gap: 6px; align-items: flex-start; font-size: 12.5px; color: var(--vf-muted); line-height: 1.7; }
.guide-list .v-icon { margin-top: 3px; }
.gallery-label { margin-bottom: 10px; }
.gallery { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 9px; }
@media (max-width: 360px) { .gallery { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
.add-tile, .photo-tile, .tile-skeleton { aspect-ratio: 1 / 1; border-radius: 16px; overflow: hidden; }
.add-tile { display: grid; place-content: center; justify-items: center; gap: 4px; border: 2px dashed #b9d0dd; background: #f8fbfd;
  color: #33566b; font-size: 12px; font-weight: 800; }
.add-tile.is-camera { border-color: #6ea9cb; background: #eef7fc; color: #1d608b; }
.add-tile:disabled { opacity: .6; }
.photo-tile { position: relative; padding: 0; border: 1px solid var(--vf-line); background: #e9f0f4; }
.photo-tile img { width: 100%; height: 100%; object-fit: cover; display: block; }
.photo-tile.is-uploading { display: grid; place-content: center; justify-items: center; gap: 6px; color: var(--vf-muted); font-size: 11px; font-weight: 700; }
.tile-badge { position: absolute; top: 6px; right: 6px; min-width: 24px; height: 24px; padding: 0 6px; border-radius: 8px; background: #102f4dcc;
  color: #fff; font-size: 11.5px; font-weight: 800; display: grid; place-items: center; }
.tile-geo { position: absolute; bottom: 6px; left: 6px; width: 22px; height: 22px; border-radius: 7px; background: #1a7154d9; display: grid; place-items: center; }
.max-note { margin: 10px 2px 0; }
.viewer { min-height: 100vh; background: #0b1a26; color: #fff; display: flex; flex-direction: column; }
.viewer-top { display: flex; align-items: center; justify-content: space-between; padding: calc(12px + env(safe-area-inset-top)) 14px 10px; font-weight: 700; }
.viewer-btn { width: 44px; height: 44px; border-radius: 13px; background: #ffffff1c; display: grid; place-items: center; }
.viewer-btn.danger { background: #a33a35; }
.viewer-spacer { width: 44px; }
.viewer-stage { flex: 1; display: flex; align-items: center; justify-content: center; gap: 6px; padding: 0 6px; }
.viewer-stage img { max-width: calc(100% - 100px); max-height: 74vh; object-fit: contain; border-radius: 12px; }
.viewer-nav { flex: none; width: 44px; height: 64px; border-radius: 13px; background: #ffffff14; display: grid; place-items: center; }
.viewer-meta { text-align: center; color: #b9d0dd; font-size: 12px; padding: 12px 16px calc(16px + env(safe-area-inset-bottom)); margin: 0; }
.delete-sheet { text-align: center; padding: 4px 4px 6px; }
.delete-sheet h2 { font-size: 17px; font-weight: 800; margin: 6px 0 4px; }
.delete-sheet p { color: var(--vf-muted); font-size: 13px; margin: 0 0 16px; }
</style>
