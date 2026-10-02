<template>
  <main class="vf-page visit-detail" dir="rtl">
    <VisitTopBar
      :title="buildingName"
      :eyebrow="visit ? `مأموریت ${faId(visit.id)} · ${typeName}` : 'جزئیات مأموریت'"
      :fallback="{ name: 'tasks' }"
    >
      <div v-if="visit" class="visit-hero-meta">
        <span class="vf-chip" :class="'vf-tone-' + status.tone"><v-icon size="15">{{ status.icon }}</v-icon>{{ status.label }}</span>
        <span class="vf-chip hero-chip" :class="'is-' + due.tone"><v-icon size="15">mdi-calendar-blank-outline</v-icon>{{ due.label }}</span>
        <span v-if="priorityLevel" class="vf-chip hero-chip" :class="'is-priority-' + priorityLevel.key"><v-icon size="15">mdi-flag-variant</v-icon>اولویت {{ priorityLevel.label }}</span>
      </div>
      <div v-if="visit && totalSteps" class="visit-hero-progress" aria-live="polite">
        <div class="visit-hero-progress-label"><span>مراحل الزامی</span><strong>{{ faNumber(doneSteps) }} از {{ faNumber(totalSteps) }}</strong></div>
        <div class="vf-progress hero-progress" role="progressbar" :aria-valuenow="progressPercent" aria-valuemin="0" aria-valuemax="100"><span :style="{ width: progressPercent + '%' }" /></div>
      </div>
    </VisitTopBar>

    <div v-if="loading && !visit" class="vf-body" role="status" aria-label="در حال دریافت جزئیات مأموریت">
      <v-skeleton-loader class="vf-skeleton" type="article" /><v-skeleton-loader class="vf-skeleton" type="list-item-two-line, list-item-two-line, list-item-two-line" />
    </div>

    <div v-else-if="error && !visit" class="vf-body">
      <div class="vf-banner vf-banner-danger" role="alert">
        <v-icon color="#a33a35">mdi-alert-circle-outline</v-icon>
        <div><strong>جزئیات مأموریت دریافت نشد</strong><p>{{ error }}</p>
          <button type="button" class="vf-banner-action" @click="load"><v-icon size="16">mdi-refresh</v-icon>تلاش دوباره</button></div>
      </div>
    </div>

    <div v-else-if="visit" class="vf-body">
      <!-- Status explanation: what happened and what to do next -->
      <div v-if="!page.is_assignee" class="vf-banner vf-banner-info" role="note">
        <v-icon color="#1d4f6d">mdi-eye-outline</v-icon>
        <div><strong>نمای فقط‌خواندنی</strong><p>شما مجری این مأموریت نیستید؛ پاسخ‌ها و عکس‌ها فقط قابل مشاهده‌اند.</p></div>
      </div>
      <div v-else-if="visit.status === '5'" class="vf-banner vf-banner-warn" role="note">
        <v-icon color="#7a4d0f">mdi-backup-restore</v-icon>
        <div><strong>گزارش برای اصلاح برگشت خورده است</strong>
          <p v-if="visit.rejection_reason" class="reason-text">«{{ visit.rejection_reason }}»</p>
          <p class="vf-muted reason-by">{{ reviewerLine }}</p>
          <p>موارد خواسته‌شده را اصلاح کنید و دوباره «ثبت و پایان» را بزنید.</p></div>
      </div>
      <div v-else-if="visit.status === '4'" class="vf-banner vf-banner-danger" role="note">
        <v-icon color="#8a2f2a">mdi-close-octagon-outline</v-icon>
        <div><strong>گزارش این مأموریت رد شده است</strong>
          <p v-if="visit.rejection_reason" class="reason-text">«{{ visit.rejection_reason }}»</p>
          <p class="vf-muted reason-by">{{ reviewerLine }}</p></div>
      </div>
      <div v-else-if="visit.status === '3'" class="vf-banner vf-banner-ok" role="note">
        <v-icon color="#1b6247">mdi-check-decagram</v-icon>
        <div><strong>گزارش تأیید شد</strong><p>{{ reviewerLine || 'این مأموریت بسته شده است.' }}</p></div>
      </div>
      <div v-else-if="visit.status === '2'" class="vf-banner vf-banner-info" role="note">
        <v-icon color="#1d4f6d">mdi-timer-sand</v-icon>
        <div><strong>گزارش ثبت شد و در انتظار بررسی است</strong>
          <p>{{ page.report_version ? `نسخه ${faNumber(page.report_version)} گزارش برای مدیر ساختمان و شرکت ثبت شد.` : 'نتیجه بررسی به شما اعلام می‌شود.' }}</p></div>
      </div>
      <div v-else-if="visit.status === '6'" class="vf-banner vf-banner-warn" role="note">
        <v-icon color="#7a4d0f">mdi-pause-circle-outline</v-icon>
        <div><strong>مأموریت متوقف شده است</strong><p>برای ادامه کار، «ادامه مأموریت» را بزنید.</p></div>
      </div>
      <div v-else-if="visit.status === '0' && awaitingAcceptance" class="vf-banner vf-banner-warn accept-banner" role="note">
        <v-icon color="#7a4d0f">mdi-account-question-outline</v-icon>
        <div><strong>این مأموریت به شما ارجاع شده است</strong>
          <p>اگر در موعد امکان انجام آن را دارید بپذیرید؛ در غیر این صورت با ذکر دلیل به برنامه‌ریزی برگردانید تا به کارشناس دیگری سپرده شود.</p>
          <div class="accept-actions">
            <button type="button" class="vf-btn vf-btn-success vf-btn-small" :disabled="busy" @click="respond('accept')"><v-icon color="white" size="18">mdi-check</v-icon>می‌پذیرم</button>
            <button type="button" class="vf-btn vf-btn-danger vf-btn-small" :disabled="busy" @click="declineOpen = true"><v-icon size="18">mdi-undo-variant</v-icon>بازگرداندن</button>
          </div></div>
      </div>
      <div v-else-if="visit.status === '0'" class="vf-banner vf-banner-info" role="note">
        <v-icon color="#1d4f6d">mdi-information-outline</v-icon>
        <div><strong>{{ accepted ? 'مأموریت را پذیرفته‌اید' : 'مأموریت هنوز شروع نشده است' }}</strong><p>در محل حاضر شوید و «شروع مأموریت» را بزنید؛ سپس مراحل را به ترتیب کامل کنید.</p></div>
      </div>

      <section v-if="visit.visit_comment" class="vf-card note-card" aria-labelledby="note-heading">
        <div class="vf-card-title"><h2 id="note-heading"><v-icon color="#1d608b" size="19">mdi-message-text-outline</v-icon> یادداشت شرکت</h2><small v-if="publisher">{{ publisher }}</small></div>
        <p class="note-text">{{ visit.visit_comment }}</p>
      </section>

      <section class="vf-card" aria-labelledby="place-heading">
        <div class="vf-card-title"><h2 id="place-heading">محل خدمت</h2><span class="vf-chip vf-tone-muted vf-ltr">{{ visit.building.code }}</span></div>
        <p class="place-address"><v-icon size="18" color="#5d788a">mdi-map-marker-outline</v-icon>{{ visit.building.address || 'آدرس ثبت نشده است.' }}</p>
        <div class="place-actions">
          <button type="button" class="vf-btn vf-btn-ghost vf-btn-small" :disabled="!hasLocation" @click="openMap"><v-icon size="18">mdi-navigation-variant-outline</v-icon>{{ hasLocation ? 'مسیریابی' : 'موقعیت ثبت نشده' }}</button>
          <button v-if="page.is_assignee" type="button" class="vf-btn vf-btn-ghost vf-btn-small" @click="openChat"><v-icon size="18">mdi-chat-processing-outline</v-icon>گفتگو با مدیر ساختمان</button>
          <button type="button" class="vf-btn vf-btn-ghost vf-btn-small" @click="openSupport"><v-icon size="18">mdi-lifebuoy</v-icon>گفتگو با پشتیبانی</button>
        </div>
      </section>

      <section class="vf-card" aria-labelledby="elevators-heading">
        <div class="vf-card-title"><h2 id="elevators-heading">{{ visitElevators.length ? 'آسانسورهای این مأموریت' : 'آسانسورهای ساختمان' }}</h2><small>{{ faNumber(elevators.length) }} مورد</small></div>
        <EmptyState v-if="!elevators.length" kind="building" size="sm" inline title="آسانسوری ثبت نشده" description="برای این ساختمان آسانسوری ثبت نشده است." />
        <div v-else class="elevator-list">
          <button v-for="elevator in elevators" :key="elevator.id" type="button" class="elevator-item" @click="showElevator(elevator)">
            <span class="elevator-icon"><v-icon color="#1d608b" size="21">mdi-elevator-passenger-outline</v-icon></span>
            <span class="elevator-copy"><strong>{{ elevator.title || 'آسانسور' }}</strong><small>{{ elevatorSummary(elevator) }}</small></span>
            <v-icon size="19" color="#7c9aa9">mdi-chevron-left</v-icon>
          </button>
        </div>
        <p v-if="!visitElevators.length && elevators.length" class="vf-muted elevator-note">برای این مأموریت آسانسور مشخصی انتخاب نشده؛ همه آسانسورهای ساختمان نمایش داده می‌شود.</p>
      </section>

      <section v-if="buildingHistory.length" class="vf-card" aria-labelledby="history-heading">
        <div class="vf-card-title"><h2 id="history-heading"><v-icon color="#1d608b" size="19">mdi-history</v-icon> سوابق اخیر این ساختمان</h2></div>
        <ul class="recent-list">
          <li v-for="row in buildingHistory" :key="row.id">
            <span class="vf-chip" :class="'vf-tone-' + statusOf(row.status).tone">{{ statusOf(row.status).label }}</span>
            <span class="recent-copy"><strong>{{ row.type || 'خدمت' }}</strong><small>{{ faDate(row.date) }}{{ row.expert ? ' · ' + row.expert : '' }}</small>
              <small v-if="row.note" class="recent-note">{{ row.note }}</small></span>
          </li>
        </ul>
      </section>

      <div class="vf-section-label"><h2>مراحل پرسشنامه</h2><span v-if="questionSteps.length">{{ faNumber(questionSteps.filter(s => s.done).length) }} از {{ faNumber(questionSteps.length) }} تکمیل</span></div>
      <EmptyState v-if="!questionSteps.length" kind="documents" size="sm" inline title="پرسشنامه‌ای تعریف نشده" description="برای این خدمت پرسشنامه‌ای تعریف نشده است." />
      <div v-else>
        <button v-for="step in questionSteps" :key="'q' + step.id" type="button" class="vf-step"
                :class="{ 'is-done': step.done, 'is-missing': step.missing }" :disabled="!!opening" @click="openQuestions(step)">
          <span class="vf-step-icon"><v-icon :color="step.done ? '#1a7154' : step.missing ? '#a33a35' : '#1d608b'" size="22">{{ step.done ? 'mdi-check-circle-outline' : 'mdi-clipboard-text-outline' }}</v-icon></span>
          <span class="vf-step-copy">
            <strong>{{ step.title }}</strong>
            <span class="vf-step-meta">
              <span>{{ faNumber(step.answered) }} از {{ faNumber(step.total) }} پاسخ</span>
              <span v-if="step.required && step.remaining && editable" class="vf-chip vf-required">{{ faNumber(step.remaining) }} الزامی باقی‌مانده</span>
              <span v-else-if="step.required" class="vf-chip vf-tone-done">{{ faNumber(step.required) }} الزامی</span>
              <span v-else class="vf-chip vf-tone-muted">اختیاری</span>
            </span>
            <span class="vf-progress" aria-hidden="true"><span :style="{ width: step.percent + '%' }" /></span>
          </span>
          <v-progress-circular v-if="opening === 'q' + step.id" indeterminate size="20" width="2" color="#1d608b" />
          <v-icon v-else size="20" color="#7c9aa9">mdi-chevron-left</v-icon>
        </button>
      </div>

      <div class="vf-section-label"><h2>عکس‌ها</h2><span v-if="photoSteps.length">{{ faNumber(photoSteps.filter(s => s.done).length) }} از {{ faNumber(photoSteps.length) }} تکمیل</span></div>
      <EmptyState v-if="!photoSteps.length" kind="photos" size="sm" inline title="مرحله عکسی تعریف نشده" description="" />
      <div v-else>
        <button v-for="step in photoSteps" :key="'p' + step.id" type="button" class="vf-step"
                :class="{ 'is-done': step.done, 'is-missing': step.missing }" :disabled="!!opening" @click="openPhotos(step)">
          <span class="vf-step-icon"><v-icon :color="step.done ? '#1a7154' : step.missing ? '#a33a35' : '#1d608b'" size="22">{{ step.done ? 'mdi-image-check-outline' : 'mdi-camera-outline' }}</v-icon></span>
          <span class="vf-step-copy">
            <strong>{{ step.title }}</strong>
            <span class="vf-step-meta">
              <span>{{ faNumber(step.count) }} عکس ثبت‌شده</span>
              <span v-if="step.min" class="vf-chip" :class="step.missing ? 'vf-required' : 'vf-tone-done'">حداقل {{ faNumber(step.min) }}</span>
              <span v-else class="vf-chip vf-tone-muted">اختیاری</span>
              <span v-if="step.max">حداکثر {{ faNumber(step.max) }}</span>
            </span>
          </span>
          <v-progress-circular v-if="opening === 'p' + step.id" indeterminate size="20" width="2" color="#1d608b" />
          <v-icon v-else size="20" color="#7c9aa9">mdi-chevron-left</v-icon>
        </button>
      </div>

      <template v-if="surveys.length || addIns.length || hasWare || page.is_assignee">
        <div class="vf-section-label"><h2>کارهای تکمیلی</h2></div>
        <div>
          <button v-for="survey in surveys" :key="'s' + survey.id" type="button" class="vf-step" :disabled="!!opening" @click="openSurvey(survey)">
            <span class="vf-step-icon"><v-icon color="#1d608b" size="22">mdi-account-voice</v-icon></span>
            <span class="vf-step-copy"><strong>{{ survey.verbose_name || survey.name }}</strong>
              <span class="vf-step-meta"><span>پرسشنامه مدیر ساختمان</span>
                <span class="vf-chip" :class="surveyState(survey).tone">{{ surveyState(survey).label }}</span></span></span>
            <v-progress-circular v-if="opening === 's' + survey.id" indeterminate size="20" width="2" color="#1d608b" />
            <v-icon v-else size="20" color="#7c9aa9">mdi-chevron-left</v-icon>
          </button>
          <button v-for="add in addIns" :key="'a' + add.id" type="button" class="vf-step" @click="openAddIn(add)">
            <span class="vf-step-icon"><v-icon color="#1d608b" size="22">{{ add.key === 'UID' ? 'mdi-card-account-details-outline' : 'mdi-cash-multiple' }}</v-icon></span>
            <span class="vf-step-copy"><strong>{{ add.verbose_name || add.name }}</strong><span class="vf-step-meta">{{ add.key === 'UID' ? 'احراز هویت' : 'هزینه و فاکتور' }}</span></span>
            <v-icon size="20" color="#7c9aa9">mdi-chevron-left</v-icon>
          </button>
          <button v-if="hasWare" type="button" class="vf-step" @click="openWares">
            <span class="vf-step-icon"><v-icon color="#1d608b" size="22">mdi-toolbox-outline</v-icon></span>
            <span class="vf-step-copy"><strong>قطعات و مواد مصرفی</strong><span class="vf-step-meta">موجودی قابل استفاده شما: {{ faNumber(wareCount || 0) }} عدد</span></span>
            <v-icon size="20" color="#7c9aa9">mdi-chevron-left</v-icon>
          </button>
          <button v-if="page.is_assignee" type="button" class="vf-step" @click="openParts">
            <span class="vf-step-icon"><v-icon color="#1d608b" size="22">mdi-package-variant-plus</v-icon></span>
            <span class="vf-step-copy"><strong>درخواست قطعه از انبار</strong><span class="vf-step-meta">قطعه یدکی لازم را درخواست دهید؛ پس از تأیید به موجودی شما منتقل می‌شود.</span></span>
            <v-icon size="20" color="#7c9aa9">mdi-chevron-left</v-icon>
          </button>
        </div>
      </template>
      <p v-if="actionError" class="vf-banner vf-banner-danger action-error" role="alert"><v-icon color="#8a2f2a">mdi-alert-circle-outline</v-icon><span>{{ actionError }}</span></p>
    </div>

    <footer v-if="visit && page.is_assignee" class="vf-actionbar">
      <template v-if="canStart">
        <p class="vf-actionbar-note">{{ startNote }}</p>
        <button type="button" class="vf-btn vf-btn-primary vf-btn-block" :disabled="busy" @click="start()">
          <v-progress-circular v-if="busy" indeterminate size="20" width="2" color="white" />
          <template v-else><v-icon color="white" size="21">{{ visit.status === '0' ? 'mdi-play' : 'mdi-play-pause' }}</v-icon>{{ startLabel }}</template>
        </button>
      </template>
      <template v-else-if="visit.status === '1'">
        <p class="vf-actionbar-note" :class="{ 'is-danger': gapsText }">{{ gapsText || 'همه موارد الزامی کامل است؛ می‌توانید مأموریت را پایان دهید.' }}</p>
        <button type="button" class="vf-btn vf-btn-success vf-btn-block" :disabled="busy || !!gapsText" @click="confirmFinish = true">
          <v-icon color="white" size="21">mdi-flag-checkered</v-icon>ثبت و پایان مأموریت
        </button>
      </template>
      <template v-else>
        <div class="vf-actionbar-row">
          <router-link :to="{ name: 'visitHistory' }" class="vf-btn vf-btn-ghost"><v-icon size="19">mdi-history</v-icon>سوابق من</router-link>
          <router-link :to="{ name: 'tasks' }" class="vf-btn vf-btn-primary"><v-icon color="white" size="19">mdi-clipboard-check-outline</v-icon>مأموریت‌های باز</router-link>
        </div>
      </template>
    </footer>

    <v-dialog v-model="confirmFinish" max-width="420">
      <div class="vf-card finish-dialog" role="alertdialog" aria-labelledby="finish-title">
        <v-icon color="#1a7154" size="40">mdi-flag-checkered</v-icon>
        <h2 id="finish-title">پایان مأموریت ثبت شود؟</h2>
        <p>پس از ثبت، پاسخ‌ها و عکس‌ها برای بررسی شرکت و مدیر ساختمان ثبت می‌شوند و دیگر قابل ویرایش نیستند، مگر آنکه برای اصلاح برگشت داده شوند.</p>
        <label v-if="needsCode" class="code-field">کد تأیید مدیر ساختمان
          <input v-model="clientCode" type="text" inputmode="numeric" autocomplete="one-time-code" maxlength="6" pattern="\d{6}"
                 placeholder="––––––" class="vf-ltr" :aria-invalid="codeError ? 'true' : 'false'" @input="clientCode = asciiDigits(clientCode)">
          <small>این کد در اپ مدیر ساختمان، در جزئیات همین خدمت نمایش داده می‌شود.</small>
          <small v-if="codeError" class="code-error" role="alert">{{ codeError }}</small>
        </label>
        <div class="vf-actionbar-row">
          <button type="button" class="vf-btn vf-btn-ghost" :disabled="busy" @click="confirmFinish = false">بازبینی دوباره</button>
          <button type="button" class="vf-btn vf-btn-success" :disabled="busy || (needsCode && clientCode.length !== 6)" @click="finish">
            <v-progress-circular v-if="busy" indeterminate size="20" width="2" color="white" /><template v-else>ثبت نهایی</template>
          </button>
        </div>
      </div>
    </v-dialog>
    <v-dialog v-model="declineOpen" max-width="440">
      <form class="vf-card finish-dialog" role="alertdialog" aria-labelledby="decline-title" @submit.prevent="respond('decline')">
        <v-icon color="#a33a35" size="38">mdi-undo-variant</v-icon>
        <h2 id="decline-title">بازگرداندن مأموریت به برنامه‌ریزی</h2>
        <p>مأموریت از فهرست شما خارج می‌شود و برنامه‌ریز برای تخصیص دوباره مطلع می‌شود.</p>
        <label class="code-field">دلیل
          <textarea v-model="declineReason" rows="3" maxlength="500" placeholder="مثلاً: در تاریخ موعد مرخصی هستم" />
        </label>
        <div class="vf-actionbar-row">
          <button type="button" class="vf-btn vf-btn-ghost" :disabled="busy" @click="declineOpen = false">انصراف</button>
          <button type="submit" class="vf-btn vf-btn-danger" :disabled="busy || declineReason.trim().length < 5">بازگرداندن</button>
        </div>
      </form>
    </v-dialog>
    <ElevatorSheet v-model="elevatorOpen" :elevator="selectedElevator" :context="selectedContext" />
    <v-snackbar v-model="toast" :timeout="2600" top color="#15364f">{{ toastText }}</v-snackbar>
  </main>
</template>

<script>
import VisitTopBar from '@/components/Visit/VisitTopBar.vue';
import ElevatorSheet from '@/components/Visit/ElevatorSheet.vue';
import { errorMessage } from '@/utils/clientRequests';
import EmptyState from '@/components/EmptyState/index.vue';
import { dueInfo, elevatorValue, faDate, faId, faNumber, hasGaps, personName, requirementText,
  startVisit, visitStatus, withProject } from '@/utils/visitFlow';

export default {
  name: 'VisitDetail',
  components: { EmptyState, VisitTopBar, ElevatorSheet },
  data: () => ({
    page: {}, visit: null, loading: true, error: '', busy: false, opening: '', actionError: '',
    confirmFinish: false, elevatorOpen: false, selectedElevator: null, hasWare: false, wareCount: null,
    toast: false, toastText: '', sequence: 0, fillOuts: [], context: null,
    declineOpen: false, declineReason: '', clientCode: '', codeError: '',
  }),
  computed: {
    id() { return this.$route.params.id; },
    buildingName() { const b = this.visit && this.visit.building; return (b && (b.verbose_name || b.name)) || 'جزئیات مأموریت'; },
    typeName() { const t = this.visit && this.visit.type; return (t && (t.verbose_name || t.title)) || 'خدمت'; },
    status() { return visitStatus(this.visit && this.visit.status); },
    due() { return dueInfo(this.visit); },
    priorityLevel() { return this.visit && this.visit.priority ? this.visit.priority.level : null; },
    editable() { return !!this.page.editable; },
    canStart() { return this.editable && ['0', '5', '6'].includes(this.visit.status); },
    startLabel() { return { '0': 'شروع مأموریت', '5': 'شروع اصلاح گزارش', '6': 'ادامه مأموریت' }[this.visit.status]; },
    startNote() {
      return {
        '5': 'با شروع اصلاح، می‌توانید پاسخ‌ها و عکس‌ها را ویرایش کنید.',
        '6': 'با ادامه، مأموریت دوباره «در حال انجام» می‌شود و پاسخ‌های قبلی حفظ می‌شوند.',
      }[this.visit.status] || 'با شروع، زمان آغاز کار ثبت و مراحل برای ثبت پاسخ باز می‌شود.';
    },
    publisher() { return personName(this.visit && this.visit.comment_publisher); },
    assignment() { return (this.visit && this.visit.assignment) || {}; },
    awaitingAcceptance() { return this.page.is_assignee && this.assignment.state === 'pending'; },
    accepted() { return this.assignment.state === 'accepted'; },
    needsCode() { return !!(this.visit && this.visit.type && this.visit.type.requires_client_code); },
    buildingHistory() { return (this.context && this.context.building_history) || []; },
    selectedContext() {
      if (!this.context || !this.selectedElevator) return null;
      return this.context.elevators.find(row => row.id === this.selectedElevator.id) || null;
    },
    reviewerLine() {
      const name = personName(this.visit && this.visit.checked_by);
      return name ? `بررسی‌کننده: ${name} · ${faDate(this.visit.datetime_last_change, true)}` : '';
    },
    visitElevators() { return (this.visit && this.visit.elevator) || []; },
    elevators() {
      if (this.visitElevators.length) return this.visitElevators;
      const rows = (this.visit && this.visit.building && this.visit.building.elevators) || [];
      return rows.map(row => row.elevator).filter(Boolean);
    },
    gaps() { return this.page.requirements || {}; },
    questionSteps() {
      return (this.page.questions || []).map(type => {
        const total = type.question_count || 0;
        const answered = type.answered_count || 0;
        const required = type.required_count || 0;
        return {
          id: type.id, title: type.verbose_name || type.name, total, answered, required,
          remaining: type.missing_required || 0,
          done: total > 0 && answered >= total,
          missing: this.editable && ((type.missing_required || 0) > 0
            || (this.gaps.empty_required_question_types || []).includes(type.id)),
          percent: total ? Math.round((answered / total) * 100) : 0,
        };
      });
    },
    photoSteps() {
      const missing = new Set((this.gaps.photo_types || []).map(item => item.type));
      return (this.page.photos || []).map(type => {
        const min = Math.max(type.min || 0, type.is_mandatory ? 1 : 0);
        return { id: type.id, title: type.verbose_name || type.name, count: type.count || 0, min, max: type.max,
          done: (type.count || 0) >= Math.max(min, 1), missing: this.editable && missing.has(type.id) };
      });
    },
    surveys() { return this.page.surveys || []; },
    addIns() { return this.page.add_ins || []; },
    // The hero bar tracks required steps only — the same rule that gates finishing.
    requiredSteps() {
      return [...this.questionSteps.filter(step => step.required).map(step => !step.remaining),
        ...this.photoSteps.filter(step => step.min).map(step => step.count >= step.min)];
    },
    totalSteps() { return this.requiredSteps.length; },
    doneSteps() { return this.requiredSteps.filter(Boolean).length; },
    progressPercent() { return this.totalSteps ? Math.round((this.doneSteps / this.totalSteps) * 100) : 0; },
    gapsText() { return hasGaps(this.gaps) ? requirementText(this.gaps) : ''; },
    hasLocation() {
      const b = this.visit && this.visit.building;
      return !!b && b.latitude != null && b.longitude != null && Number.isFinite(Number(b.latitude)) && Number.isFinite(Number(b.longitude));
    },
  },
  watch: { id() { this.load(); } },
  created() { this.load(); },
  activated() { this.load(); },
  beforeDestroy() { this.sequence++; },
  methods: {
    faNumber, faId,
    notify(text) { this.toastText = text; this.toast = true; },
    async load() {
      const sequence = ++this.sequence;
      this.loading = true; this.error = '';
      try {
        const response = await this.$ApiServiceLayer.get(
          withProject(this.$PATH.RELATIVE_PATH.GET.VISIT_PAGE_SETTING + this.id + '/'), this.$PATH.SERVICE_NAME.AUTH);
        if (sequence !== this.sequence) return;
        if (response.status !== 200 || !response.data || !response.data.visit || !response.data.visit.building) {
          this.error = response.status === 404 ? 'این مأموریت پیدا نشد یا به شما تخصیص داده نشده است.' : errorMessage(response);
          return;
        }
        this.page = response.data;
        this.visit = response.data.visit;
        this.loadWares(sequence);
        this.loadFillOuts(sequence);
        this.loadContext(sequence);
      } catch (_) {
        if (sequence === this.sequence) this.error = 'اتصال برقرار نشد. اینترنت را بررسی و دوباره تلاش کنید.';
      } finally {
        if (sequence === this.sequence) this.loading = false;
      }
    },
    async loadWares(sequence) {
      if (!this.page.is_assignee) { this.hasWare = false; return; }
      try {
        const response = await this.$ApiServiceLayer.get(
          withProject(this.$PATH.RELATIVE_PATH.GET.WAREHOUSE_VISIT_PAGE_SETTING, { visit: this.id }), this.$PATH.SERVICE_NAME.EMPTY);
        if (sequence !== this.sequence || response.status !== 200) return;
        this.hasWare = response.data.has_wares === true;
        this.wareCount = response.data.total_count;
      } catch (_) { this.hasWare = false; }
    },
    async loadContext(sequence) {
      try {
        const response = await this.$ApiServiceLayer.get(
          withProject(`/api/promoter/visit/${this.id}/assets/`), this.$PATH.SERVICE_NAME.AUTH);
        if (sequence === this.sequence && response.status === 200) this.context = response.data;
      } catch (_) { /* context is a convenience; the visit stays usable without it */ }
    },
    async respond(action) {
      if (this.busy) return;
      this.busy = true; this.actionError = '';
      try {
        const response = await this.$ApiServiceLayer.post(withProject(`/api/promoter/visit/${this.visit.id}/assignment/`),
          this.$PATH.SERVICE_NAME.AUTH, { action, reason: action === 'decline' ? this.declineReason.trim() : '' });
        if (response.status !== 200) { this.actionError = errorMessage(response); this.declineOpen = false; return; }
        if (action === 'decline') {
          this.declineOpen = false;
          this.$router.replace({ name: 'tasks', query: { notice: 'declined' } }).catch(() => {});
          return;
        }
        this.notify('مأموریت را پذیرفتید.');
        await this.load();
      } catch (_) {
        this.actionError = 'ثبت پاسخ ممکن نشد. اتصال را بررسی و دوباره تلاش کنید.';
      } finally { this.busy = false; }
    },
    async loadFillOuts(sequence) {
      if (!(this.page.surveys || []).length) { this.fillOuts = []; return; }
      try {
        const response = await this.$ApiServiceLayer.get(
          withProject(this.$PATH.RELATIVE_PATH.MULTI.SURVEY_FILL_OUT, { visit: this.id }), this.$PATH.SERVICE_NAME.AUTH);
        if (sequence !== this.sequence || response.status !== 200) return;
        this.fillOuts = Array.isArray(response.data) ? response.data : response.data.results || [];
      } catch (_) { this.fillOuts = []; }
    },
    surveyState(survey) {
      const fill = this.fillOuts.find(row => (row.survey && (row.survey.id || row.survey)) === survey.id && !row.is_deleted);
      if (!fill) return { label: 'شروع نشده', tone: 'vf-tone-muted' };
      return fill.is_closed ? { label: 'ارسال شده', tone: 'vf-tone-done' } : { label: 'در حال تکمیل', tone: 'vf-tone-progress' };
    },
    async start(silent = false) {
      if (this.busy) return false;
      this.busy = true; this.actionError = '';
      const result = await startVisit(this.$ApiServiceLayer, this.$PATH, this.visit.id);
      this.busy = false;
      if (!result.ok) { this.actionError = result.message; return false; }
      if (!silent) this.notify(this.visit.status === '5' ? 'اصلاح گزارش شروع شد.' : 'مأموریت شروع شد.');
      await this.load();
      return true;
    },
    // Opening a step of an open visit starts it first, so answers and photos are accepted.
    async ensureStarted() {
      if (!this.canStart) return true;
      return this.start(true);
    },
    async openQuestions(step) {
      this.opening = 'q' + step.id;
      try {
        if (!(await this.ensureStarted())) return;
        await this.$router.push({ name: 'shelfQuestion', params: { type: step.id, id: this.visit.id } });
      } finally { this.opening = ''; }
    },
    async openPhotos(step) {
      this.opening = 'p' + step.id;
      try {
        if (!(await this.ensureStarted())) return;
        await this.$router.push({ name: 'pickImage', params: { type: step.id, id: this.visit.id, minImg: step.min } });
      } finally { this.opening = ''; }
    },
    async openSurvey(survey) {
      this.opening = 's' + survey.id; this.actionError = '';
      try {
        const path = this.$PATH.RELATIVE_PATH.MULTI.SURVEY_FILL_OUT;
        const existing = await this.$ApiServiceLayer.get(withProject(path, { visit: this.visit.id, survey: survey.id }), this.$PATH.SERVICE_NAME.AUTH);
        const rows = existing.status === 200 ? (Array.isArray(existing.data) ? existing.data : existing.data.results || []) : [];
        let fillId = rows.length ? rows[0].id : null;
        if (!fillId) {
          if (!this.editable) { this.actionError = 'برای این مأموریت پرسشنامه‌ای ثبت نشده است.'; return; }
          const created = await this.$ApiServiceLayer.post(withProject(path), this.$PATH.SERVICE_NAME.AUTH, { survey: survey.id, visit: this.visit.id });
          if (created.status !== 201) { this.actionError = errorMessage(created); return; }
          fillId = created.data.id;
        }
        await this.$router.push({ name: 'surveyDetailInVisit', params: { fill_id: fillId, visit_id: this.visit.id } });
      } catch (_) {
        this.actionError = 'باز کردن پرسشنامه ممکن نشد. دوباره تلاش کنید.';
      } finally { this.opening = ''; }
    },
    openAddIn(add) {
      if (add.key === 'UID') this.$router.push({ name: 'verifyProfile', params: { id: this.visit.id } });
      else this.$router.push({ name: 'costs', params: { id: this.visit.id } });
    },
    openWares() { this.$router.push({ name: 'visitWares', query: { visit: this.visit.id } }); },
    // Persian and Arabic keyboards type ۰-۹ / ٠-٩; the API expects ASCII digits.
    asciiDigits(value) {
      return String(value || '').replace(/[۰-۹]/g, d => '۰۱۲۳۴۵۶۷۸۹'.indexOf(d)).replace(/[٠-٩]/g, d => '٠١٢٣٤٥٦٧٨٩'.indexOf(d))
        .replace(/\D/g, '').slice(0, 6);
    },
    openChat() { this.$router.push({ name: 'visitChat', params: { id: this.visit.id } }); },
    openParts() { this.$router.push({ name: 'visitParts', params: { id: this.visit.id } }); },
    statusOf: visitStatus,
    faDate,
    openSupport() { this.$router.push({ name: 'onlineChat', params: { id: this.visit.id } }); },
    openMap() {
      if (!this.hasLocation) return;
      const b = this.visit.building;
      window.open(`https://maps.google.com/?q=${Number(b.latitude)},${Number(b.longitude)}`, '_blank', 'noopener,noreferrer');
    },
    showElevator(elevator) { this.selectedElevator = elevator; this.elevatorOpen = true; },
    elevatorSummary(elevator) {
      const context = this.context && this.context.elevators.find(row => row.id === elevator.id);
      const parts = [elevatorValue(elevator.elevator_type), elevator.number_of_floors ? `${faNumber(elevator.number_of_floors)} طبقه` : '',
        elevator.capacity ? `${faNumber(elevator.capacity)} نفر` : '',
        context && context.installed.length ? `${faNumber(context.installed.length)} قطعه ثبت‌شده` : ''].filter(Boolean);
      return parts.join(' · ') || 'مشاهده مشخصات فنی';
    },
    async finish() {
      if (this.busy) return;
      this.busy = true; this.actionError = '';
      try {
        this.codeError = '';
        const payload = this.needsCode ? { status: '2', client_code: this.clientCode } : { status: '2' };
        const response = await this.$ApiServiceLayer.put(
          withProject(this.$PATH.RELATIVE_PATH.MULTI.GET_STATUS_QUESTIONS + this.visit.id + '/'), this.$PATH.SERVICE_NAME.AUTH, payload);
        if (response.status === 400 && response.data && response.data.client_code) {
          const detail = response.data.client_code;
          this.codeError = Array.isArray(detail) ? detail.join(' ') : detail;
          return;  // keep the dialog open to retry the code
        }
        this.confirmFinish = false;
        this.clientCode = '';
        if (response.status === 200) {
          this.notify('گزارش ثبت شد و برای بررسی ارسال شد.');
          await this.load();
          return;
        }
        if (response.status === 400 && response.data && response.data.requirements) {
          this.page = { ...this.page, requirements: response.data.requirements };
          this.actionError = requirementText(response.data.requirements) || 'شرایط پایان هنوز کامل نیست.';
          return;
        }
        this.actionError = errorMessage(response);
      } catch (_) {
        this.actionError = 'ثبت پایان انجام نشد. اتصال را بررسی و دوباره تلاش کنید.';
      } finally { this.busy = false; }
    },
  },
};
</script>

<style scoped>
.visit-hero-meta { display: flex; flex-wrap: wrap; gap: 7px; margin-top: 14px; }
.hero-chip { background: #ffffff1f; color: #e8f5fb; border: 1px solid #ffffff3a; }
.hero-chip.is-danger { background: #ffd9d5; color: #8a2f2a; border-color: transparent; }
.hero-chip.is-warning { background: #ffefcc; color: #7a4d0f; border-color: transparent; }
.hero-chip.is-priority-critical { background: #ffd9d5; color: #8a2f2a; border-color: transparent; }
.hero-chip.is-priority-high { background: #ffe3d4; color: #8a3d16; border-color: transparent; }
.visit-hero-progress { margin-top: 14px; }
.visit-hero-progress-label { display: flex; justify-content: space-between; font-size: 12px; color: #d4eaf5; margin-bottom: 6px; }
.visit-hero-progress-label strong { color: #fff; }
.hero-progress { background: #ffffff2e; }
.reason-text { font-weight: 700; margin: 4px 0 !important; }
.reason-by { margin: 0 0 4px !important; }
.note-text { margin: 0; white-space: pre-line; font-size: 13.5px; color: #2a4b60; }
.vf-card-title h2 { display: flex; align-items: center; gap: 6px; }
.place-address { display: flex; gap: 6px; align-items: flex-start; margin: 0 0 12px; color: #33566b; font-size: 13px; line-height: 1.8; }
.place-address .v-icon { margin-top: 3px; flex: none; }
.place-actions { display: flex; flex-wrap: wrap; gap: 8px; }
.place-actions .vf-btn { flex: 1 1 140px; }
.elevator-list { display: grid; gap: 8px; }
.elevator-item { display: flex; align-items: center; gap: 11px; width: 100%; min-height: 60px; padding: 10px 12px; text-align: right;
  border: 1px solid var(--vf-line); border-radius: 14px; background: #fbfdfe; color: var(--vf-ink); }
.elevator-item:hover { border-color: #9cc3d8; }
.elevator-icon { flex: none; width: 40px; height: 40px; border-radius: 12px; display: grid; place-items: center; background: var(--vf-brand-soft); }
.elevator-copy { flex: 1; min-width: 0; display: grid; }
.elevator-copy strong { font-size: 13.5px; line-height: 1.5; }
.elevator-copy small { color: var(--vf-muted); font-size: 11.5px; }
.elevator-note { margin: 10px 2px 0; line-height: 1.7; }
.vf-step:disabled { cursor: progress; }
.action-error { margin: 0; align-items: center; }
.finish-dialog { text-align: center; padding: 24px 20px 20px; }
.finish-dialog h2 { font-size: 17px; font-weight: 800; margin: 8px 0 6px; }
.finish-dialog p { color: var(--vf-muted); font-size: 13px; line-height: 1.9; margin: 0 0 18px; }
.code-field { display: grid; gap: 6px; margin: -6px 0 16px; text-align: right; font-size: 12.5px; font-weight: 700; color: #33566b; }
.code-field input, .code-field textarea { min-height: 48px; padding: 10px 12px; border: 1px solid #c9dbe5; border-radius: 12px; background: #fff;
  font: inherit; color: var(--vf-ink); }
.code-field input { font-size: 22px; letter-spacing: 8px; text-align: center; }
.code-field input:focus, .code-field textarea:focus { outline: 3px solid #9fd0ea; border-color: var(--vf-brand); }
.code-field small { font-weight: 400; color: var(--vf-muted); font-size: 11.5px; line-height: 1.7; }
.code-field .code-error { color: var(--vf-danger); font-weight: 700; }
.accept-actions { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px; }
.recent-list { list-style: none; margin: 0; padding: 0; display: grid; gap: 10px; }
.recent-list li { display: flex; gap: 10px; align-items: flex-start; padding-bottom: 10px; border-bottom: 1px solid #edf2f5; }
.recent-list li:last-child { border-bottom: 0; padding-bottom: 0; }
.recent-list .vf-chip { flex: none; }
.recent-copy { display: grid; min-width: 0; }
.recent-copy strong { font-size: 13px; }
.recent-copy small { color: var(--vf-muted); font-size: 11.5px; }
.recent-copy .recent-note { color: #7a4d0f; }
a.vf-btn { text-decoration: none; }
</style>
