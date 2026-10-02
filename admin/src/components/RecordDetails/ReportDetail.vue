<template>
  <div class="record-detail">
    <div v-if="loading" class="detail-state" role="status">
      <b-spinner small /><span>در حال دریافت جزئیات…</span>
    </div>
    <div v-else-if="error" class="detail-state" role="alert">
      <p>{{ error }}</p>
      <button class="accept" @click="load">تلاش دوباره</button>
    </div>
    <template v-else>
      <section class="detail-hero">
        <div class="detail-hero-top">
          <div>
            <span class="detail-eyebrow"
              >{{ survey ? 'پرسشنامه تکمیل‌شده' : supervision ? 'گزارش نظارت' : 'گزارش ویزیت' }} ·
              {{ record.id }}</span
            >
            <h2>{{ title }}</h2>
            <p v-if="record.building && record.building.address">{{ record.building.address }}</p>
          </div>
          <router-link class="detail-back" :to="backRoute"
            >بازگشت به فهرست <span aria-hidden="true">←</span></router-link
          >
        </div>
        <div class="detail-summary">
          <span class="detail-badge" :class="'status-' + currentStatus">{{ statusLabel }}</span
          ><span>{{ answers.length }} پاسخ ثبت‌شده</span><span>{{ photos.length }} تصویر</span
          ><span>{{ groups.length }} گروه سؤال</span>
        </div>
        <p v-if="!survey && record.rejection_reason && ['4', '5'].includes(currentStatus)" class="detail-reason" role="note">
          <strong>{{ currentStatus === '5' ? 'دلیل بازگشت برای اصلاح:' : 'دلیل رد:' }}</strong> {{ record.rejection_reason }}
        </p>
        <InfoGrid :fields="metadata" />
      </section>
      <nav class="detail-section-nav" aria-label="بخش‌های گزارش">
        <a href="#report-answers"
          >پاسخ‌ها <span>{{ answers.length }}</span></a
        ><a href="#report-photos"
          >تصاویر <span>{{ photos.length }}</span></a
        ><a v-if="!survey" href="#report-feedback">بازخورد</a>
      </nav>
      <section v-if="survey && profileInfo" class="detail-section">
        <div class="detail-section-heading"><h2>اطلاعات استعلام‌شده</h2></div>
        <InfoGrid
          :fields="[
            { label: 'کد ملی', value: profileInfo.national_id, ltr: true },
            { label: 'شماره همراه', value: profileInfo.phone_number, ltr: true },
            { label: 'شماره شبا', value: profileInfo.sheba_number, ltr: true },
            { label: 'تاریخ تولد', value: profileInfo.birth_date },
          ]"
        />
      </section>
      <section id="report-answers" class="detail-section">
        <div class="detail-section-heading">
          <div>
            <h2>پاسخ‌های ثبت‌شده</h2>
            <p>اطلاعات گزارش به تفکیک گروه سؤال</p>
          </div>
          <button v-if="!readOnly" class="reject" :disabled="busy" @click="loadUnanswered">
            افزودن پاسخ
          </button>
        </div>
        <EmptyState v-if="!groups.length" kind="documents" size="sm" inline title="هنوز پاسخی ثبت نشده" description="پاسخ‌های کارشناس پس از ثبت اینجا دیده می‌شوند." />
        <section v-for="group in groups" :key="group.id" class="answer-group">
          <header>
            <span class="section-symbol" aria-hidden="true">≡</span>
            <h3>{{ group.title }}</h3>
            <span class="detail-count">{{ group.answers.length }} سؤال</span>
          </header>
          <AnswerCard
            v-for="(answer, index) in group.answers"
            :key="answer.id"
            :answer="answer"
            :index="index"
            :editable="!readOnly"
            @edit="editAnswer"
          />
        </section>
      </section>
      <section id="report-photos" class="detail-section">
        <div class="detail-section-heading">
          <div>
            <h2>تصاویر و مستندات</h2>
            <p>تصاویر، وضعیت بررسی و اطلاعات ثبت</p>
          </div>
          <button v-if="!readOnly" class="reject" :disabled="busy" @click="uploadOpen = true">
            افزودن تصویر
          </button>
        </div>
        <EmptyState v-if="!photos.length" kind="photos" size="sm" inline title="تصویری ثبت نشده" description="" />
        <div class="detail-photo-grid">
          <article v-for="photo in photos" :key="photo.id" class="detail-photo-card">
            <button
              class="photo-preview"
              :aria-label="'مشاهده تصویر: ' + photoTitle(photo)"
              @click="selectedPhoto = photo"
            >
              <img
                v-if="photo.link && !photo.imageUnavailable"
                :src="photo.link"
                :alt="photoTitle(photo)"
                loading="lazy"
                @error="$set(photo, 'imageUnavailable', true)"
              />
              <span v-else class="photo-unavailable">تصویر در دسترس نیست</span>
            </button>
            <div class="photo-card-body">
              <h3>{{ photoTitle(photo) }}</h3>
              <DisplayDate :value="photo.datetime_created" showTime />
              <div class="photo-badges">
                <span class="detail-badge" :class="'photo-status-' + photo.supervision_confirm">{{
                  confirmations[photo.supervision_confirm] || 'بررسی نشده'
                }}</span
                ><span v-if="photo.is_favourite" class="detail-badge">تصویر منتخب</span>
              </div>
              <dl class="photo-metadata">
                <div>
                  <dt>بررسی موقعیت</dt>
                  <dd>{{ confirmations[photo.supervision_location_confirm] || 'بررسی نشده' }}</dd>
                </div>
                <div v-if="photo.distance !== undefined">
                  <dt>فاصله</dt>
                  <dd>{{ distance(photo.distance) }}</dd>
                </div>
                <div>
                  <dt>پردازش تصویر</dt>
                  <dd>{{ recognition[photo.recognition_status] || 'بررسی نشده' }}</dd>
                </div>
              </dl>
              <div class="photo-actions">
                <a
                  v-if="hasLocation(photo)"
                  :href="mapLink(photo)"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="detail-text-link"
                  >مشاهده موقعیت</a
                ><button
                  v-if="!readOnly"
                  class="icon-action danger-action"
                  :aria-label="'حذف تصویر: ' + photoTitle(photo)"
                  @click="deletePhoto = photo"
                >
                  <ActionIcon name="delete" /></button
                ><button
                  v-if="survey && !readOnly"
                  class="detail-text-link"
                  :disabled="busy"
                  @click="toggleFavourite(photo)"
                >
                  {{ photo.is_favourite ? 'حذف از منتخب‌ها' : 'انتخاب تصویر' }}
                </button>
              </div>
            </div>
          </article>
        </div>
      </section>
      <section v-if="!survey" id="report-feedback" class="detail-section">
        <div class="detail-section-heading">
          <div>
            <h2>بازخورد ویزیت</h2>
            <p>{{ publisher ? 'ثبت‌کننده: ' + publisher : 'یادداشت درباره اجرای ویزیت' }}</p>
          </div>
        </div>
        <label class="detail-field-label" for="visit-feedback">متن بازخورد</label
        ><textarea
          id="visit-feedback"
          v-model="feedback"
          rows="4"
          :readonly="readOnly"
          placeholder="بازخوردی ثبت نشده است."
        />
        <div v-if="!readOnly" class="detail-form-actions">
          <button
            class="accept"
            :disabled="busy || feedback === originalFeedback"
            @click="saveFeedback"
          >
            ذخیره بازخورد
          </button>
        </div>
      </section>
      <FieldOpsPanel v-if="!survey && !supervision" :visit-id="id" />
      <section v-if="!readOnly" class="detail-review-bar">
        <div>
          <h2>بررسی نهایی گزارش</h2>
          <p>{{ reviewHint }}</p>
        </div>
        <div class="detail-form-actions">
          <button
            v-if="!survey && !supervision"
            class="reject"
            :disabled="busy || !reviewable"
            @click="review = 'return'"
          >
            بازگشت برای اصلاح</button
          ><button
            v-if="!survey"
            class="reject danger-action"
            :disabled="busy || !reviewable"
            @click="review = 'reject'"
          >
            رد ویزیت</button
          ><button
            class="accept"
            :disabled="busy || (survey ? currentStatus === '2' : !reviewable)"
            @click="review = 'accept'"
          >
            {{ survey ? 'تأیید پرسشنامه' : 'تأیید ویزیت' }}
          </button>
        </div>
      </section>
    </template>
    <b-modal
      v-model="editorOpen"
      :title="editingId ? 'ویرایش پاسخ' : 'افزودن پاسخ'"
      hide-footer
      centered
      header-close-label="بستن"
      ><form @submit.prevent="saveAnswer">
        <h3 class="editor-question">{{ editingQuestion.text }}</h3>
        <p v-if="editingQuestion.description" class="detail-muted">
          {{ editingQuestion.description }}
        </p>
        <div v-for="type in editingQuestion.answer_type" :key="type.id" class="detail-editor-field">
          <label :for="'answer-field-' + type.id">{{ typeLabels[type.name] || type.name }}</label
          ><select
            v-if="type.name === 'YesNo' || type.name === 'Triple'"
            :id="'answer-field-' + type.id"
            v-model="draft.bool"
          >
            <option :value="null">{{ type.name === 'Triple' ? 'نامشخص' : 'پاسخ ثبت نشده' }}</option>
            <option :value="true">بله</option>
            <option :value="false">خیر</option></select
          ><select
            v-else-if="type.name === 'Score'"
            :id="'answer-field-' + type.id"
            v-model="draft.score"
          >
            <option :value="null">پاسخ ثبت نشده</option>
            <option v-for="n in 5" :key="n" :value="n">{{ n }} از ۵</option></select
          ><select
            v-else-if="type.name === 'DropDownList'"
            :id="'answer-field-' + type.id"
            v-model="draft.dropdown"
          >
            <option :value="null">انتخاب کنید</option>
            <option
              v-for="choice in editingQuestion.dropdown_choices"
              :key="choice.id"
              :value="choice.id"
            >
              {{ choice.answer }}
            </option>
          </select>
          <fieldset
            v-else-if="type.name === 'RadioChoice' || type.name === 'Multichoice'"
            class="answer-choice-list"
          >
            <legend class="sr-only">{{ editingQuestion.text }}</legend>
            <label
              v-for="choice in type.name === 'RadioChoice'
                ? editingQuestion.radio_choices
                : editingQuestion.answer_choices"
              :key="choice.id"
              ><input
                v-if="type.name === 'RadioChoice'"
                v-model="draft.radio"
                type="radio"
                :value="choice.id"
                :name="'answer-radio-' + type.id"
              /><input v-else v-model="draft.multichoice" type="checkbox" :value="choice.id" />{{
                choice.answer
              }}</label
            >
          </fieldset>
          <textarea
            v-else-if="type.name === 'Description'"
            :id="'answer-field-' + type.id"
            v-model="draft.description"
            rows="5"
          /><input
            v-else-if="type.name === 'Input'"
            :id="'answer-field-' + type.id"
            v-model="draft.text"
            maxlength="255"
          /><input
            v-else-if="type.name === 'Number' || type.name === 'Price'"
            :id="'answer-field-' + type.id"
            v-model="draft[type.name === 'Price' ? 'price' : 'number']"
            type="number"
            step="1"
          />
        </div>
        <p v-if="actionError" class="detail-error" role="alert">{{ actionError }}</p>
        <div class="detail-form-actions">
          <button type="button" class="reject" :disabled="busy" @click="editorOpen = false">
            انصراف</button
          ><button class="accept" :disabled="busy">
            {{ busy ? 'در حال ذخیره…' : 'ذخیره پاسخ' }}
          </button>
        </div>
      </form></b-modal
    >
    <b-modal
      v-model="unansweredOpen"
      title="سؤال‌های بدون پاسخ"
      hide-footer
      centered
      header-close-label="بستن"
      ><div v-if="busy" role="status">در حال دریافت سؤال‌ها…</div>
      <p v-else-if="!unanswered.length" class="detail-empty">تمام سؤال‌ها پاسخ داده شده‌اند.</p>
      <div v-for="item in unanswered" :key="item.question.id" class="unanswered-question">
        <span>{{ item.question.text }}</span
        ><button class="reject" @click="createAnswer(item.question)">افزودن پاسخ</button>
      </div>
      <p v-if="actionError" class="detail-error" role="alert">{{ actionError }}</p></b-modal
    >
    <b-modal
      :visible="!!selectedPhoto"
      :title="selectedPhoto ? photoTitle(selectedPhoto) : 'تصویر'"
      size="lg"
      hide-footer
      centered
      @hidden="selectedPhoto = null"
      header-close-label="بستن"
      ><img
        v-if="selectedPhoto && selectedPhoto.link && !selectedPhoto.imageUnavailable"
        class="detail-lightbox"
        :src="selectedPhoto.link"
        :alt="photoTitle(selectedPhoto)"
        @error="$set(selectedPhoto, 'imageUnavailable', true)"
      />
      <p v-else class="detail-empty">تصویر در دسترس نیست.</p></b-modal
    >
    <b-modal
      v-model="uploadOpen"
      title="افزودن تصویر"
      hide-footer
      centered
      header-close-label="بستن"
      ><p v-if="!photoTypes.length" class="detail-empty">
        نوع تصویری برای این گزارش تعریف نشده است.
      </p>
      <form v-else @submit.prevent="uploadPhoto">
        <label for="report-photo-type">نوع تصویر</label
        ><select id="report-photo-type" v-model="photoType" required>
          <option :value="null" disabled>انتخاب کنید</option>
          <option v-for="type in photoTypes" :key="type.id" :value="type.id">
            {{ type.verbose_name || type.name }}
          </option></select
        ><label for="report-photo-file" class="mt-3">فایل تصویر</label
        ><input id="report-photo-file" ref="photoFile" type="file" accept="image/*" required />
        <p v-if="actionError" class="detail-error" role="alert">{{ actionError }}</p>
        <div class="detail-form-actions">
          <button type="button" class="reject" @click="uploadOpen = false">انصراف</button
          ><button class="accept" :disabled="busy">بارگذاری تصویر</button>
        </div>
      </form></b-modal
    >
    <b-modal
      :visible="!!deletePhoto"
      title="حذف تصویر"
      hide-footer
      centered
      @hidden="deletePhoto = null"
      header-close-label="بستن"
      ><p>تصویر «{{ deletePhoto && photoTitle(deletePhoto) }}» حذف شود؟</p>
      <p v-if="actionError" class="detail-error" role="alert">{{ actionError }}</p>
      <div class="detail-form-actions">
        <button class="reject" @click="deletePhoto = null">انصراف</button
        ><button class="accept" :disabled="busy" @click="removePhoto">حذف تصویر</button>
      </div></b-modal
    >
    <b-modal
      :visible="!!review"
      :title="{ reject: 'رد ویزیت', return: 'بازگشت برای اصلاح', accept: 'تأیید گزارش' }[review] || 'بررسی گزارش'"
      hide-footer
      centered
      @hidden="review = ''"
      header-close-label="بستن"
      ><p>
        {{
          {
            reject: 'دلیل رد این ویزیت را بنویسید. ویزیت ردشده بسته می‌شود و به کارشناس بازنمی‌گردد.',
            return: 'آنچه کارشناس باید اصلاح کند را بنویسید. ویزیت به فهرست مأموریت‌های کارشناس برمی‌گردد.',
          }[review] || 'نتیجه بررسی این گزارش تأیید شود؟'
        }}
      </p>
      <div v-if="review === 'reject' || review === 'return'" class="review-form"
        ><label for="rejection-reason">{{ review === 'return' ? 'موارد اصلاح' : 'دلیل رد' }}</label
        ><textarea
          id="rejection-reason"
          v-model="rejectionReason"
          rows="5"
          :placeholder="review === 'return' ? 'مثلاً: عکس تابلو فرمان ناخواناست؛ دوباره ثبت شود.' : 'دلیل رد را بنویسید.'"
        />
      </div>
      <p v-if="actionError" class="detail-error" role="alert">{{ actionError }}</p>
      <div class="detail-form-actions">
        <button class="reject" @click="review = ''">انصراف</button
        ><button
          class="accept"
          :disabled="busy || (review !== 'accept' && !rejectionReason.trim())"
          @click="saveReview"
        >
          ثبت نتیجه
        </button>
      </div></b-modal
    >
    <b-modal
      v-model="ratingOpen"
      title="امتیاز اجرای ویزیت"
      hide-footer
      centered
      header-close-label="بستن"
      ><label for="visit-rating">امتیاز اجرا</label
      ><select id="visit-rating" v-model="rating">
        <option v-for="n in 5" :key="n" :value="n">{{ n }} از ۵</option>
      </select>
      <p v-if="actionError" class="detail-error" role="alert">{{ actionError }}</p>
      <div class="detail-form-actions">
        <button class="reject" @click="ratingOpen = false">بعداً</button
        ><button class="accept" :disabled="busy" @click="saveRating">ثبت امتیاز</button>
      </div></b-modal
    >
  </div>
</template>
<script>
import InfoGrid from './InfoGrid.vue';
import AnswerCard from './AnswerCard.vue';
import DisplayDate from '@/components/DisplayDate/index.vue';
import FieldOpsPanel from './FieldOpsPanel.vue';
import { questionOf, answerDraft, answerPayload } from '@/utils/detailValues';
import EmptyState from '@/components/EmptyState/index.vue';
const rows = (data) => (Array.isArray(data) ? data : data.results || []);
const person = (value) =>
  value ? [value.first_name, value.last_name].filter(Boolean).join(' ') || value.username : '';
export default {
  components: { EmptyState, InfoGrid, AnswerCard, DisplayDate, FieldOpsPanel },
  props: { survey: Boolean, supervision: Boolean, readOnly: Boolean },
  data: () => ({
    profileInfo: null,
    loading: true,
    error: '',
    record: {},
    answers: [],
    photos: [],
    photoTypes: [],
    feedback: '',
    originalFeedback: '',
    busy: false,
    actionError: '',
    editorOpen: false,
    editingQuestion: {},
    editingId: null,
    draft: answerDraft(),
    unansweredOpen: false,
    unanswered: [],
    selectedPhoto: null,
    deletePhoto: null,
    uploadOpen: false,
    photoType: null,
    review: '',
    rejectionReason: '',
    ratingOpen: false,
    rating: 5,
    confirmations: { NOT_CHECKED: 'بررسی نشده', CONFIRMED: 'تأیید شده', REJECTED: 'رد شده' },
    recognition: {
      1: 'نقص پروفایل',
      2: 'چهره تشخیص داده نشد',
      3: 'عدم تطابق',
      4: 'تطابق تأیید شد',
    },
    typeLabels: {
      YesNo: 'بله / خیر',
      Triple: 'بله / خیر / نامشخص',
      Score: 'امتیاز',
      RadioChoice: 'انتخاب یک گزینه',
      DropDownList: 'انتخاب از فهرست',
      Multichoice: 'انتخاب گزینه‌ها',
      Input: 'پاسخ کوتاه',
      Description: 'توضیحات',
      Number: 'مقدار عددی',
      Price: 'مبلغ (ریال)',
    },
  }),
  computed: {
    id() {
      return this.$route.params.id;
    },
    project() {
      return this.$STORE.state.userConfig.setProjectId;
    },
    backRoute() {
      return this.survey
        ? '/suveymanagment/lists'
        : this.supervision
        ? '/supervisionmanagment/lists'
        : '/visitmanagment/lists';
    },
    currentStatus() {
      return this.supervision ? this.record.supervision_status : this.record.status;
    },
    title() {
      return this.survey
        ? (this.record.survey || {}).verbose_name || 'جزئیات پرسشنامه'
        : (this.record.building || {}).verbose_name ||
            (this.record.building || {}).name ||
            'جزئیات ویزیت';
    },
    publisher() {
      return person(this.record.comment_publisher);
    },
    statusLabel() {
      return (
        (this.survey
          ? { 0: 'در حال تکمیل', 1: 'تکمیل‌شده', 2: 'تأیید شده' }
          : {
              0: 'شروع نشده',
              1: 'در حال اجرا',
              2: 'تکمیل‌شده',
              3: 'تأیید شده',
              4: 'رد شده',
              5: 'برگشت برای اصلاح',
              6: 'معلق',
            })[this.currentStatus] || 'نامشخص'
      );
    },
    reviewable() {
      // Only a finished report can be approved, rejected or returned.
      return this.supervision ? !['3', '4'].includes(this.currentStatus) : this.currentStatus === '2';
    },
    reviewHint() {
      if (this.survey) return 'پس از بررسی پاسخ‌ها و مستندات، نتیجه را ثبت کنید.';
      if (this.reviewable) return 'پس از بررسی پاسخ‌ها و عکس‌ها، گزارش را تأیید، رد یا برای اصلاح به کارشناس برگردانید.';
      return {
        '0': 'کارشناس هنوز این مأموریت را شروع نکرده است.',
        '1': 'کارشناس در حال انجام کار است؛ پس از ثبت پایان قابل بررسی است.',
        '3': 'این گزارش تأیید شده است.',
        '4': 'این گزارش رد شده است.',
        '5': 'گزارش برای اصلاح به کارشناس برگشته است.',
        '6': 'این مأموریت متوقف شده است.',
      }[this.currentStatus] || 'این گزارش در وضعیت قابل بررسی نیست.';
    },
    metadata() {
      const r = this.record;
      const b = r.building || {};
      return this.survey
        ? [
            { label: 'پاسخ‌دهنده', value: person(r.user) },
            { label: 'شماره تماس', value: r.phone_number || (r.user || {}).username, ltr: true },
            { label: 'استان', value: (r.province || {}).name },
            { label: 'شهر', value: (r.city || {}).name },
            { label: 'تاریخ ثبت', value: this.date(r.datetime_created) },
            { label: 'تأیید شماره تماس', value: r.phone_verified },
          ]
        : [
            { label: 'نیروی اجرایی', value: person(r.promoter) },
            {
              label: 'کارشناس',
              value: person(r.expert_details || (typeof r.expert === 'object' ? r.expert : null)),
            },
            { label: 'زمان شروع', value: this.date(r.start_datetime) },
            { label: 'کد ساختمان', value: b.code },
            { label: 'شهر', value: (b.city || {}).name },
            { label: 'نوبت ویزیت', value: r.visit_turn },
            ...(r.has_due_date ? [{ label: 'مهلت انجام', value: this.date(r.due_date) }] : []),
          ];
    },
    groups() {
      const groups = new Map();
      this.answers.forEach((answer) => {
        const q = questionOf(answer);
        const category = q.report_category || q.survey_report_category || {};
        const id = category.id || 'other';
        if (!groups.has(id))
          groups.set(id, {
            id,
            title: category.verbose_name || category.name || 'سایر سؤال‌ها',
            answers: [],
          });
        groups.get(id).answers.push(answer);
      });
      return [...groups.values()];
    },
  },
  watch: {
    id: { immediate: true, handler: 'load' },
    editorOpen(value) {
      if (value) this.actionError = '';
    },
    uploadOpen(value) {
      if (value) {
        this.actionError = '';
        this.photoType = null;
      }
    },
    review(value) {
      if (value) this.actionError = '';
    },
    deletePhoto(value) {
      if (value) this.actionError = '';
    },
    ratingOpen(value) {
      if (value) this.actionError = '';
    },
  },
  methods: {
    url(path, query = '') {
      return path + (path.includes('?') ? '&' : '?') + 'p=' + this.project + query;
    },
    async get(path, query = '') {
      const res = await this.$ApiServiceLayer.get(this.url(path, query), '/core');
      if (res.status !== 200) throw new Error(this.$ApiServiceLayer.getErrorMessage(res));
      return res.data;
    },
    async load() {
      const id = this.id;
      this.loading = true;
      this.error = '';
      try {
        const filter = '&question__question_type__is_for_supervision=' + this.supervision;
        const photoFilter = '&type__is_for_supervision=' + this.supervision;
        const result = await Promise.all([
          this.get(
            this.survey
              ? '/api/admin/survey_fill_out/edits/' + id + '/'
              : '/api/admin/visit_edit/' + id + '/'
          ),
          this.get(
            this.survey ? '/api/admin/survey_answer/list_create/' : '/api/admin/answer_list/',
            this.survey
              ? '&survey_fill_out=' + id + '&ordering=survey_question__priority'
              : '&visit=' + id + '&ordering=question__priority' + filter
          ),
          this.get(
            this.survey ? '/api/admin/survey_photo/list_create/' : '/api/admin/photo_list',
            (this.survey ? '&survey_fill_out=' : '&visit=') + id + (this.survey ? '' : photoFilter)
          ),
          this.get(
            (this.survey
              ? '/api/promoter/survey_page_settings/'
              : '/api/promoter/visit_page_settings/') +
              id +
              '/' +
              (this.supervision ? '?s=true' : '')
          ),
        ]);
        if (id !== this.id) return;
        [this.record, this.answers, this.photos, this.photoTypes] = [
          result[0],
          rows(result[1]),
          rows(result[2]),
          result[3].photos || [],
        ];
        this.feedback = this.record.visit_comment || '';
        this.originalFeedback = this.feedback;
        this.profileInfo = null;
        if (this.survey) this.loadProfile(id);
      } catch (e) {
        if (id === this.id) this.error = e.message;
      } finally {
        if (id === this.id) this.loading = false;
      }
    },
    date(value) {
      if (!value || !Number.isFinite(new Date(value).getTime())) return 'ثبت نشده';
      return new Intl.DateTimeFormat('fa-IR', {
        dateStyle: 'medium',
        ...(value.length > 10 ? { timeStyle: 'short' } : {}),
      }).format(new Date(value));
    },
    photoTitle(photo) {
      return (photo.type || photo.survey_photo_type || {}).verbose_name || 'تصویر گزارش';
    },
    distance(value) {
      return value >= 0
        ? Math.round(value).toLocaleString('fa-IR') + ' متر'
        : {
            '-1': 'موقعیت ساختمان ثبت نشده',
            '-2': 'موقعیت تصویر ثبت نشده',
            '-3': 'موقعیت تصویر ثبت نشده',
            '-4': 'قابل محاسبه نیست',
          }[value] || 'ثبت نشده';
    },
    hasLocation(photo) {
      return (
        photo.latitude !== null &&
        photo.latitude !== undefined &&
        photo.longitude !== null &&
        photo.longitude !== undefined &&
        Number(photo.latitude) !== 0 &&
        Number(photo.longitude) !== 0
      );
    },
    mapLink(photo) {
      return (
        'https://maps.google.com/?q=' + encodeURIComponent(photo.latitude + ',' + photo.longitude)
      );
    },
    editAnswer(answer) {
      this.editingQuestion = questionOf(answer);
      this.editingId = answer.id;
      this.draft = answerDraft(answer);
      this.actionError = '';
      this.editorOpen = true;
    },
    createAnswer(question) {
      this.editingQuestion = question;
      this.editingId = null;
      this.draft = answerDraft();
      this.unansweredOpen = false;
      this.actionError = '';
      this.editorOpen = true;
    },
    async mutate(method, path, data) {
      this.busy = true;
      this.actionError = '';
      try {
        const res = await this.$ApiServiceLayer[method](
          this.url(path),
          '/core',
          ...(method === 'delete' ? [] : [data])
        );
        if (res.status < 200 || res.status >= 300) {
          const detail = res.data && res.data.detail;
          throw new Error(
            res.status === 400
              ? detail || 'مقادیر واردشده معتبر نیستند.'
              : this.$ApiServiceLayer.getErrorMessage(res)
          );
        }
        return true;
      } catch (e) {
        this.actionError = e.message;
        this.$notify({ group: 'tc', type: 'danger', text: e.message });
        return false;
      } finally {
        this.busy = false;
      }
    },
    async saveAnswer() {
      const path = this.editingId
        ? (this.survey ? '/api/admin/survey_answer/edits/' : '/api/admin/answer_edit/') +
          this.editingId +
          '/'
        : this.survey
        ? '/api/admin/survey_answer/list_create/'
        : '/api/admin/visit_answer/create/';
      const payload = answerPayload(this.draft, this.editingQuestion, this.id, this.survey);
      if (await this.mutate(this.editingId ? 'patch' : 'post', path, payload)) {
        this.editorOpen = false;
        await this.load();
        this.notify('پاسخ با موفقیت ذخیره شد.');
      }
    },
    async loadUnanswered() {
      this.unansweredOpen = true;
      this.busy = true;
      this.actionError = '';
      try {
        const data = await this.get(
          (this.survey
            ? '/api/promoter/survey_question/list/'
            : '/api/promoter/questions/list/visit/') +
            this.id +
            '/',
          this.survey ? '' : '&question_type__is_for_supervision=' + this.supervision
        );
        this.unanswered = rows(data).filter(
          (item) => !item.submitted_answer || !item.submitted_answer.id
        );
      } catch (e) {
        this.actionError = e.message;
      } finally {
        this.busy = false;
      }
    },
    notify(text) {
      this.$notify({ group: 'tc', type: 'success', text });
    },
    async loadProfile(id) {
      const res = await this.$ApiServiceLayer.get(
        '/api/micro/personalinfo/validate/?survey_fillout=' +
          id +
          '&is_main=true&p=' +
          this.project,
        ''
      );
      if (id === this.id && res.status === 200) this.profileInfo = rows(res.data)[0] || null;
    },
    async saveFeedback() {
      if (
        await this.mutate('put', '/api/admin/vist/place_comment/' + this.id + '/', {
          visit_comment: this.feedback,
        })
      ) {
        this.originalFeedback = this.feedback;
        this.notify('بازخورد ذخیره شد.');
      }
    },
    async uploadPhoto() {
      const file = this.$refs.photoFile.files[0];
      if (!file || !this.photoType) return;
      const data = new FormData();
      data.append('link', file);
      data.append('latitude', 'null');
      data.append('longitude', 'null');
      data.append(this.survey ? 'survey_fill_out' : 'visit', this.id);
      data.append(this.survey ? 'survey_photo_type' : 'type', this.photoType);
      if (
        await this.mutate(
          'post',
          this.survey
            ? '/api/promoter/upload_survey_photo/'
            : '/api/promoter/open_visit/upload_image/',
          data
        )
      ) {
        this.uploadOpen = false;
        await this.load();
        this.notify('تصویر بارگذاری شد.');
      }
    },
    async removePhoto() {
      if (
        await this.mutate(
          'delete',
          (this.survey ? '/api/admin/survey_photo/edits/' : '/api/admin/photo_edit/') +
            this.deletePhoto.id +
            '/'
        )
      ) {
        this.deletePhoto = null;
        await this.load();
        this.notify('تصویر حذف شد.');
      }
    },
    async toggleFavourite(photo) {
      if (
        await this.mutate('patch', '/api/admin/survey_photo/edits/' + photo.id + '/', {
          is_favourite: !photo.is_favourite,
        })
      )
        photo.is_favourite = !photo.is_favourite;
    },
    async saveReview() {
      const accept = this.review === 'accept';
      const path = this.survey
        ? '/api/admin/survey_fill_out/edits/'
        : this.supervision
        ? '/api/admin/supervision_visit_status_change/'
        : '/api/admin/visit_status_change/';
      const data = this.survey
        ? { status: '2' }
        : {
            [this.supervision ? 'supervision_status' : 'status']: accept ? '3' : this.review === 'return' ? '5' : '4',
            ...(accept ? {} : { rejection_reason: this.rejectionReason.trim() }),
          };
      if (await this.mutate(this.survey ? 'patch' : 'put', path + this.id + '/', data)) {
        const returned = this.review === 'return';
        this.review = '';
        this.rejectionReason = '';
        await this.load();
        this.notify(returned ? 'ویزیت برای اصلاح به کارشناس برگشت.' : 'نتیجه بررسی ثبت شد.');
        if (!this.survey && accept) this.ratingOpen = true;
      }
    },
    async saveRating() {
      if (
        await this.mutate('post', '/api/v1/visit_rate/list_create/', {
          visit: Number(this.id),
          rate: this.rating,
        })
      ) {
        this.ratingOpen = false;
        this.notify('امتیاز ثبت شد.');
      }
    },
  },
};
</script>
