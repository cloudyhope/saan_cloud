<template>
  <div>
    <FullLoading v-if="loading" />
    <v-alert v-if="error" type="error" outlined role="alert" class="ma-6">
      {{ error }} <v-btn text color="error" @click="getStoreDetail">تلاش دوباره</v-btn>
    </v-alert>
    <template v-if="!loading && visitDetail && visitDetail.building">

    <!-- <v-toolbar fixed class="topbar" color="#fff" dense>
        <v-toolbar-title class="title-name">{{
          visitDetail.building.verbose_name
        }}</v-toolbar-title>
        <v-spacer></v-spacer>
        <v-btn @click="backHome" icon>
          <v-img max-width="20" src="@/assets/images/Icons/back.svg" />
        </v-btn>
      </v-toolbar> -->
    <BaseTopBar :title="visitDetail.building.verbose_name" />

    <div class="ma-6">
      <StoreDetailCard
        :building-name="visitDetail.building.verbose_name"
        :building-code="visitDetail.building.code"
        :address="visitDetail.building.address"
        @direction-click="directionHandler"
      />
      <v-alert v-if="directionError" type="info" outlined class="mt-3" role="status">{{ directionError }}</v-alert>
      <button class="btn-asansor" @click="asansorList = !asansorList">
        لیست آسانسور
      </button>
      <!-- <h2 class="my-3">مراحل کار</h2> -->
      <v-card @click="visitWares" class="cards-shadow pa-6 mt-4" v-if="hasWare">
        <h4 class="mb-2">ابزار و تجهیزات</h4>
        <div class="d-flex justify-space-between align-center">
          <div class="d-flex align-center">
            <div class="img-container-gift">
              <v-img
                max-width="36"
                src="../../assets/images/Icons/settings.png"
              />
            </div>
            <div class="contents">
              <span class="ml-1">موجودی</span>
              <span v-if="totalCount === null">0 عدد</span>
              <span v-else>{{ totalCount }} عدد</span>
            </div>
          </div>
          <div>
            <!-- <v-img src="../../assets/images/Icons/left-chev.svg" /> -->
            <Button
              height="32px"
              textColor="#2EA1FF"
              padding="7px 12px"
              background="#F4F9FF"
              borderColorProps="#357AE1"
              title="نمایش جزئیات"
            />
          </div>
        </div>
      </v-card>
      <h2 class="my-4">ویزارد شروع خدمات</h2>
      <p v-if="visitDetail.status !== '1'" class="visit-guidance">
        {{ visitDetail.status === '0' ? 'برای پایان خدمت، ابتدا مراحل ویزارد را شروع کنید.' : 'این مأموریت در وضعیت قابل پایان نیست.' }}
      </p>
      <p v-if="!storeDetailQuestions.length" class="visit-empty">برای این خدمت مرحله پرسشنامه‌ای تعریف نشده است.</p>
      <button
        v-for="question in storeDetailQuestions"
        :key="question.id"
        type="button"
        @click="questionPage(question.id, visitDetail.id)"
        class="documnets"
      >
        <div class="d-flex align-center">
          <!-- <div class="img-box">
            <v-img max-width="24" src="@/assets/images/Icons/doc.svg" />
          </div> -->
          <span class="doc-title">{{ question.verbose_name }}</span>
        </div>
        <div>
          <!-- <v-img
            max-width="24"
            v-if="question.status === false"
            src="@/assets/images/Icons/left-chev.svg"
          /> -->
          <span class="visit-step-action" :class="{ done: question.status }">{{ question.status ? 'ثبت شده' : 'شروع' }}</span>
        </div>
      </button>
      <h2 class="my-4">تصاویر</h2>
      <p v-if="!storeDetailPhotos.length" class="visit-empty">برای این خدمت مرحله تصویری تعریف نشده است.</p>
      <button
        v-for="photos in storeDetailPhotos"
        :key="photos.id"
        type="button"
        class="documnets"
        @click="imageCondition(photos)"
      >
        <div class="d-flex align-center">
          <!-- <div class="img-box">
            <v-img max-width="24" src="@/assets/images/Icons/camera.svg" />
          </div> -->
          <!-- <span v-if="photos.name === 'StoreFront'" class="doc-title"
            >تصویر سردرب</span
          >
          <span v-if="photos.name === 'Selfie'" class="doc-title"
            >تصویر خروج</span
          >
          <span v-if="photos.name === 'Vitrin'" class="doc-title"
            >تصویر ویترین</span
          >
          <span v-if="photos.name === 'Inside'" class="doc-title"
            >تصاویر داخل مشتری</span
          >
          <span v-if="photos.name === 'Stands'" class="doc-title"
            >تصاویر استند</span
          >
          <span v-if="photos.name === 'CounterDesk'" class="doc-title"
            >تصاویر کانتر</span
          > -->
          <span class="doc-title">{{ photos.verbose_name }}</span>
        </div>
        <div>
          <!-- <v-img
            max-width="24"
            v-if="photos.status === false"
            src="@/assets/images/Icons/left-chev.svg"
          /> -->
          <span class="visit-step-action" :class="{ done: photos.status }">{{ photos.status ? 'ثبت شده' : 'شروع' }}</span>
        </div>
      </button>
      <h2 v-if="addIns.length" class="my-4">افزونه‌ها</h2>
      <button
        v-for="add in addIns"
        :key="'add' + add.id"
        type="button"
        class="documnets"
        @click="add.key === 'UID' ? veifyProfileHandler() : costHandler()"
      >
        <div class="d-flex align-center">
          <span class="doc-title">{{ add.verbose_name }}</span>
        </div>
        <div>
          <v-img
            width="18"
            src="@/assets/images/Icons/chevron-left-rounded.svg"
          />
          <!-- <v-img
              max-width="24"
              v-if="photos.status === true"
              src="@/assets/images/Icons/material-symbols_keyboard-arrow-up-rounded.svg"
            /> -->
        </div>
      </button>
      <!-- <div @click="pickImg()" class="documnets">
        <div class="d-flex align-center">
          <div class="img-box">
            <v-img max-width="24" src="@/assets/images/Icons/camera.svg" />
          </div>
          <span class="doc-title">تصویر</span>
        </div>
        <div>
          <v-img max-width="24" src="@/assets/images/Icons/cancel-btn.svg" />
        </div>
      </div> -->
      <div v-if="storeDetailSurvey.length > 0">
        <h2 class="my-4">پرسشنامه ها</h2>
        <v-card
          v-for="survey in storeDetailSurvey"
          :key="survey.id"
          @click="surveyVisitDetail(survey)"
          class="cards-shadow pa-3 mt-2"
        >
          <div class="d-flex justify-space-between align-center">
            <div class="d-flex align-center">
              <!-- <div class="img-container">
                <v-img max-width="36" :src="survey.icon" />
              </div> -->
              <div class="contents">
                <span class="header-title mb-1">{{ survey.verbose_name }}</span>
              </div>
            </div>
            <div>
              <!-- <v-img src="../../assets/images/Icons/left-chev.svg" /> -->
              <Button
                height="32px"
                textColor="#2EA1FF"
                padding="7px 12px"
                background="#F4F9FF"
                borderColorProps="#357AE1"
                title="شروع"
              />
            </div>
          </div>
        </v-card>
      </div>
    </div>
    <!-- <OverlayButton
      @click="finishVisit"
      :disabled="disableFinishVisit"
      title="اتمام ویزیت"
    /> -->
    <v-alert v-if="finishError" type="error" outlined role="alert" class="mx-6 mb-4">{{ finishError }}</v-alert>
    <EmptyContainer />
    <OverlayTwoButton
      title-left="اتمام کار"
      title-right="چت با پشتیبان"
      btn-type-left="outline-primary"
      btn-type-right="outline-secondary"
      btn-text-color-right="#4285F4"
      :disabled-left="disableFinishVisit"
      :loading-left="finishing"
      :disabled-right="false"
      :style-obj-left="{ 'background-color': '#fff' }"
      :style-obj-right="{
        'background-color': '#F4F9FF',
        'border-color': '#357AE1',
      }"
      @click-left="finishVisit"
      @click-right="chatConversationHandler(visitDetail)"
    />
    <v-bottom-sheet
      :retain-focus="false"
      max-width="576px"
      v-model="asansorList"
    >
      <v-sheet :retain-focus="false" class="pt-4 px-6" height="auto">
        <h3 class="mb-4">لیست آسانسور</h3>
        <div class="visit-type-list">
          <div
            v-for="elevator in elevatorList"
            :key="elevator.id"
            class="visit-type-item"
          >
            <span>{{ elevator.elevator.title }}</span>
            <Button
              @click="showElevatorDetails(elevator.elevator)"
              height="32px"
              textColor="#2EA1FF"
              padding="7px 12px"
              background="#F4F9FF"
              borderColorProps="#357AE1"
              title="مشاهده مشخصات"
              style="width: 150px;"
            />
          </div>
        </div>

        <EmptyContainer />
      </v-sheet>
      <!-- <OverlayButton :disabled="selectedVisitType === null" :loading="loading" @click="submitRequest" title="تایید" /> -->
    </v-bottom-sheet>

    <!-- Elevator Details Modal -->
    <v-dialog v-model="elevatorDetailsModal" max-width="600px" persistent>
      <v-card class="elevator-details-card">
        <v-card-title class="elevator-modal-header">
          <h3>مشخصات آسانسور</h3>
          <v-btn icon @click="elevatorDetailsModal = false">
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-card-title>
        
        <v-card-text class="elevator-modal-content">
          <div v-if="selectedElevator" class="elevator-details-grid">
            <div class="detail-item">
              <span class="detail-label">عنوان:</span>
              <span class="detail-value">{{ selectedElevator.title }}</span>
            </div>
            
            <div class="detail-item">
              <span class="detail-label">نوع:</span>
              <span class="detail-value">{{ selectedElevator.type || 'نامشخص' }}</span>
            </div>
            
            <div class="detail-item">
              <span class="detail-label">ظرفیت:</span>
              <span class="detail-value">{{ selectedElevator.capacity || 'نامشخص' }}</span>
            </div>
            
            <div class="detail-item">
              <span class="detail-label">تعداد طبقات:</span>
              <span class="detail-value">{{ selectedElevator.number_of_floors || 'نامشخص' }}</span>
            </div>
            
            <div class="detail-item">
              <span class="detail-label">نوع آسانسور:</span>
              <span class="detail-value">{{ selectedElevator.elevator_type || 'نامشخص' }}</span>
            </div>
            
            <div class="detail-item">
              <span class="detail-label">نوع استفاده:</span>
              <span class="detail-value">{{ selectedElevator.usage_type || 'نامشخص' }}</span>
            </div>
            
            <div class="detail-item">
              <span class="detail-label">ظرفیت کابین (کیلوگرم):</span>
              <span class="detail-value">{{ selectedElevator.cabin_capacity_kg || 'نامشخص' }}</span>
            </div>
            
            <div class="detail-item">
              <span class="detail-label">تعداد توقف:</span>
              <span class="detail-value">{{ selectedElevator.stops_count || 'نامشخص' }}</span>
            </div>
            
            <div class="detail-item">
              <span class="detail-label">نوع عملیات:</span>
              <span class="detail-value">{{ selectedElevator.operation_type || 'نامشخص' }}</span>
            </div>
            
            <div class="detail-item">
              <span class="detail-label">نوع موتور:</span>
              <span class="detail-value">{{ selectedElevator.motor_type || 'نامشخص' }}</span>
            </div>
            
            <div class="detail-item">
              <span class="detail-label">برند موتور:</span>
              <span class="detail-value">{{ selectedElevator.motor_brand || 'نامشخص' }}</span>
            </div>
            
            <div class="detail-item">
              <span class="detail-label">قدرت موتور (کیلووات):</span>
              <span class="detail-value">{{ selectedElevator.motor_power_kw || 'نامشخص' }}</span>
            </div>
            
            <div class="detail-item">
              <span class="detail-label">سرعت آسانسور (متر بر ثانیه):</span>
              <span class="detail-value">{{ selectedElevator.elevator_speed_mps || 'نامشخص' }}</span>
            </div>
            
            <div class="detail-item">
              <span class="detail-label">برند پنل کنترل:</span>
              <span class="detail-value">{{ selectedElevator.control_panel_brand || 'نامشخص' }}</span>
            </div>
            
            <div class="detail-item">
              <span class="detail-label">سریال پنل کنترل:</span>
              <span class="detail-value">{{ selectedElevator.control_panel_serial || 'نامشخص' }}</span>
            </div>
            
            <div class="detail-item">
              <span class="detail-label">نوع پنل کنترل:</span>
              <span class="detail-value">{{ selectedElevator.control_panel_type || 'نامشخص' }}</span>
            </div>
            
            <div class="detail-item">
              <span class="detail-label">برند درب:</span>
              <span class="detail-value">{{ selectedElevator.door_brand || 'نامشخص' }}</span>
            </div>
            
            <div class="detail-item">
              <span class="detail-label">تعداد درب:</span>
              <span class="detail-value">{{ selectedElevator.door_count || 'نامشخص' }}</span>
            </div>
            
            <div class="detail-item">
              <span class="detail-label">نوع درب 1:</span>
              <span class="detail-value">{{ selectedElevator.door1_type || 'نامشخص' }}</span>
            </div>
            
            <div class="detail-item">
              <span class="detail-label">ولتاژ درب 1:</span>
              <span class="detail-value">{{ selectedElevator.door1_voltage || 'نامشخص' }}</span>
            </div>
            
            <div class="detail-item">
              <span class="detail-label">نوع درب 2:</span>
              <span class="detail-value">{{ selectedElevator.door2_type || 'نامشخص' }}</span>
            </div>
            
            <div class="detail-item">
              <span class="detail-label">ولتاژ درب 2:</span>
              <span class="detail-value">{{ selectedElevator.door2_voltage || 'نامشخص' }}</span>
            </div>
            
            <div class="detail-item">
              <span class="detail-label">نوع درب 3:</span>
              <span class="detail-value">{{ selectedElevator.door3_type || 'نامشخص' }}</span>
            </div>
            
            <div class="detail-item">
              <span class="detail-label">ولتاژ درب 3:</span>
              <span class="detail-value">{{ selectedElevator.door3_voltage || 'نامشخص' }}</span>
            </div>
            
            <div class="detail-item">
              <span class="detail-label">نوع اینورتر:</span>
              <span class="detail-value">{{ selectedElevator.inverter_type || 'نامشخص' }}</span>
            </div>
            
            <div class="detail-item">
              <span class="detail-label">قدرت اینورتر:</span>
              <span class="detail-value">{{ selectedElevator.inverter_power || 'نامشخص' }}</span>
            </div>
            
            <div class="detail-item">
              <span class="detail-label">نوع سیستم کنترل:</span>
              <span class="detail-value">{{ selectedElevator.control_system_type || 'نامشخص' }}</span>
            </div>
            
            <div class="detail-item">
              <span class="detail-label">نوع سیستم اضطراری:</span>
              <span class="detail-value">{{ selectedElevator.emergency_system_type || 'نامشخص' }}</span>
            </div>
            
            <div class="detail-item">
              <span class="detail-label">ولتاژ ورودی:</span>
              <span class="detail-value">{{ selectedElevator.input_voltage || 'نامشخص' }}</span>
            </div>
            
            <div class="detail-item">
              <span class="detail-label">سنسور وزن:</span>
              <span class="detail-value">{{ selectedElevator.weight_sensor || 'نامشخص' }}</span>
            </div>
            
            <div class="detail-item">
              <span class="detail-label">حالت آتش نشانی:</span>
              <span class="detail-value">{{ selectedElevator.firefighter_mode || 'نامشخص' }}</span>
            </div>
            
            <div class="detail-item">
              <span class="detail-label">نوع استاندارد:</span>
              <span class="detail-value">{{ selectedElevator.standard_type || 'نامشخص' }}</span>
            </div>
            
            <div class="detail-item">
              <span class="detail-label">نوع ارتباط فراخوانی:</span>
              <span class="detail-value">{{ selectedElevator.landing_call_comm_type || 'نامشخص' }}</span>
            </div>
          </div>
        </v-card-text>
        
        <v-card-actions class="elevator-modal-actions">
          <Button
            @click="elevatorDetailsModal = false"
            height="40px"
            textColor="#fff"
            padding="12px 24px"
            background="#357AE1"
            borderColorProps="#357AE1"
            title="بستن"
          />
        </v-card-actions>
      </v-card>
    </v-dialog>
    </template>
  </div>
</template>
<script>
import OverlayTwoButton from "../../components/Button/overlayTwoButton.vue";
import EmptyContainer from "../../components/emptyContainer.vue";
import FullLoading from "../../components/Loading/fullLoading.vue";
import BaseTopBar from "@/components/Topbar/BaseTopbar.vue";
import Button from "@/components/Button/Button.vue";
import StoreDetailCard from "../../components/Store/StoreDetailCard.vue";
import { errorMessage } from '@/utils/clientRequests';

export default {
  name: "Profile",
  components: {
    OverlayTwoButton,
    EmptyContainer,
    FullLoading,
    BaseTopBar,
    Button,
    StoreDetailCard,
  },
  data() {
    return {
      storeDetailPhotos: [],
      storeDetailQuestions: [],
      storeDetailSurvey: [],
      visitDetail: null,
      data: {},
      error: '',
      finishError: '',
      finishing: false,
      captureImg: null,
      directionError: '',
      snackbar: false,
      timeout: 2000,
      loading: true,
      x: false,
      y: false,
      lastParam: null,
      totalCount: null,
      hasWare: false,
      addIns: [],
      asansorList: false,
      elevatorList: [],
      elevatorDetailsModal: false,
      selectedElevator: null,
    };
  },
  created() {
    this.getStoreDetail();
    this.getGiftStock();
  },
  computed: {
    disableFinishVisit() {
      return this.finishing || !this.visitDetail || this.visitDetail.status !== '1';
    },
  },
  methods: {
    async getStoreDetail() {
      this.lastParam = this.$route.params.id;
      this.loading = true;
      this.error = '';
      try {
      const res = await this.$ApiServiceLayer.get(
        this.$PATH.RELATIVE_PATH.GET.VISIT_PAGE_SETTING +
          this.lastParam +
          "/" +
          "?p=" +
          this.$STORE.state.userConfig.selectedProject,
        this.$PATH.SERVICE_NAME.AUTH
      );
      if (res.status !== 200 || !res.data || !res.data.visit || !res.data.visit.building) {
        this.error = 'دریافت جزئیات مأموریت ممکن نشد. دسترسی و اتصال خود را بررسی کنید.';
        return;
      }
      this.storeDetailPhotos = res.data.photos || [];
      this.storeDetailQuestions = res.data.questions || [];
      this.storeDetailSurvey = res.data.surveys || [];
      this.visitDetail = res.data.visit;
      this.addIns = res.data.add_ins || [];
      this.data = res.data;
      this.elevatorList = res.data.visit.building.elevators || [];
      } catch (_) {
        this.error = 'دریافت جزئیات مأموریت ممکن نشد. دوباره تلاش کنید.';
      } finally {
        this.loading = false;
      }
    },
    visitWares() {
      this.$router.push({ name: "visitWares", query: { visit: this.lastParam } });
    },
    directionHandler() {
      const building = this.visitDetail && this.visitDetail.building;
      const latitude = building && Number(building.latitude);
      const longitude = building && Number(building.longitude);
      if (!building || building.latitude == null || building.longitude == null ||
          !Number.isFinite(latitude) || !Number.isFinite(longitude)) {
        this.directionError = 'موقعیت مکانی این ساختمان هنوز ثبت نشده است.';
        return;
      }
      this.directionError = '';
      window.open(`https://maps.google.com/?q=${latitude},${longitude}`, '_blank', 'noopener,noreferrer');
    },
    chatConversationHandler(visitDetail) {
      this.$router.push({ name: "onlineChat", params: { id: visitDetail.id } });
      // window.location.href = `tel:${storePlan.store.phone}`;
    },
    async surveyVisitDetail(survey) {
      const res = await this.$ApiServiceLayer.post(
        this.$PATH.RELATIVE_PATH.MULTI.SURVEY_FILL_OUT,
        this.$PATH.SERVICE_NAME.AUTH,
        { survey: survey.id, visit: this.lastParam }
      );
      if (res.status === 201) {
        this.$router.push({
          name: "surveyDetailInVisit",
          params: { fill_id: res.data.id, visit_id: this.lastParam },
        });
      }
    },
    async getGiftStock() {
      const res = await this.$ApiServiceLayer.get(
        this.$PATH.RELATIVE_PATH.GET.WAREHOUSE_VISIT_PAGE_SETTING +
          "?visit=" +
          this.lastParam +
          "&p=" +
          this.$STORE.state.userConfig.selectedProject,
        this.$PATH.SERVICE_NAME.EMPTY,
        {}
      );
      if (res.status === 200) {
        if (res.data.has_wares === true) {
          this.hasWare = true;
        } else {
          this.hasWare = false;
        }
        this.totalCount = res.data.total_count;
      }
    },
    backHome() {
      this.$router.push({ name: "tasks" });
    },

    // async func(event, photos) {
    //   this.loading = true;
    //   const url = window.location.href;
    //   const lastParam = url.split("/").slice(-1)[0];
    //   let formData = new FormData();
    //   formData.append("link", event.target.files[0]);
    //   formData.append("latitude", this.latitude);
    //   formData.append("longitude", this.longitude);
    //   formData.append("visit", lastParam);
    //   formData.append("type", photos.id);
    //   const res = await this.$ApiServiceLayer.post(
    //     this.$PATH.RELATIVE_PATH.POST.UPLOAD_IMAGE,
    //     this.$PATH.SERVICE_NAME.AUTH,
    //     formData,
    //     {
    //       "Content-Type": "multipart/form-data",
    //     }
    //   );
    //   if (res.status === 200) {
    //     this.loading = false
    //     this.snackbar = true;
    //      this.changeStatus();
    //     this.getStoreDetail();
    //   }
    // },
    imageCondition(e) {
      // if (e.max === 1) {
      //   document.getElementById("fileUpload").click();
      //   document.getElementById("fileUpload").onchange = e.id;
      // } else {}
      this.$router.push({
        name: "pickImage",
        params: { type: e.id, id: this.visitDetail.id, minImg: e.min },
      });
    },
    questionPage(questionType, id) {
      this.$router.push({
        name: "shelfQuestion",
        params: { type: questionType, id: id },
      });
      // if (questionType === "SA") {
      //   ("SA");

      //   this.$router.push({
      //     name: "saleQuestion",
      //     params: { type: questionType, id: id },
      //   });
      // } else if (questionType === "GE") {
      //   ("GE");

      //   this.$router.push({
      //     name: "generalQuestion",
      //     params: { type: questionType, id: id },
      //   });
      // } else if (questionType === "SH") {
      //   ("SH");

      //   this.$router.push({
      //     name: "shelfQuestion",
      //     params: { type: questionType, id: id },
      //   });
      // }
    },
    veifyProfileHandler() {
      this.$router.push({
        name: "verifyProfile",
        params: { id: this.$route.params.id },
      });
    },
    costHandler() {
      this.$router.push({
        name: "costs",
        params: { visitId: this.$route.params.id },
      });
    },
    async finishVisit() {
      if (this.disableFinishVisit) return;
      this.finishing = true;
      this.finishError = '';
      try {
      const res = await this.$ApiServiceLayer.put(
        this.$PATH.RELATIVE_PATH.MULTI.GET_STATUS_QUESTIONS +
          this.visitDetail.id +
          "/" +
          "?p=" +
          this.$STORE.state.userConfig.selectedProject,
        this.$PATH.SERVICE_NAME.AUTH,
        { status: "2" }
      );
      if (res.status === 200) {
        await this.$router.push({ name: 'tasks' });
      } else if (res.status === 400 && res.data && res.data.requirements) {
        const gaps = res.data.requirements;
        const parts = [];
        if (gaps.questions && gaps.questions.length) parts.push(`${gaps.questions.length} پرسش اجباری`);
        if (gaps.photo_types && gaps.photo_types.length) parts.push(`${gaps.photo_types.length} نوع عکس`);
        if (gaps.empty_required_question_types && gaps.empty_required_question_types.length) parts.push(`${gaps.empty_required_question_types.length} بخش پرسشنامه بدون سؤال`);
        this.finishError = parts.length
          ? `برای پایان خدمت، ${parts.join('، ')} را تکمیل کنید.`
          : 'شرایط پایان خدمت هنوز کامل نیست. مراحل را بررسی کنید.';
      } else {
        this.finishError = errorMessage(res);
      }
      } catch (_) {
        this.finishError = 'پایان خدمت ثبت نشد. اتصال خود را بررسی و دوباره تلاش کنید.';
      } finally {
        this.finishing = false;
      }
    },
    showElevatorDetails(elevator) {
      this.selectedElevator = elevator;
      this.elevatorDetailsModal = true;
    },
  },
};
</script>
<style scoped>
/* .topbar {
  position: fixed;
  top: 0;
  z-index: 999;
} */
.title-name {
  font-size: 18px;
  margin-right: 16px;
  color: #404041;
  font-weight: 700;
}
.prop-tilte {
  font-weight: 400;
  font-size: 16px;
  margin-right: 26px;
}

.documnets {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  min-height: 64px;
  border: 1px solid #dce9ef;
  border-radius: 14px;
  background: #fff;
  padding: 13px 15px;
  margin-bottom: 10px;
  color: #17394e;
  text-align: right;
  box-shadow: 0 4px 16px rgba(18, 58, 82, .06);
  cursor: pointer;
}
.documnets:focus-visible{outline:3px solid #398fbc;outline-offset:3px}
.visit-step-action{display:inline-flex;align-items:center;min-height:32px;padding:5px 11px;border-radius:9px;background:#eaf3fa;color:#246f95;font-size:12px;font-weight:700;white-space:nowrap}
.visit-step-action.done{background:#e4f3e9;color:#1a7154}
.visit-empty{padding:14px 16px;border:1px dashed #cadae4;border-radius:12px;background:#f7fafb;color:#647f8d;font-size:12px;line-height:1.7}
.btn-asansor {
  background: #357ae1;
  color: #fff;
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 24px;
  text-align: center;
  width: 100%;
  margin: 16px 0;
}
/* .img-box {
  border-radius: 8px;
  background: #eaf1fb;
  padding: 12px;
} */
.doc-title {
  font-size: 14px;
  color: #24475b;
  margin-right: 11px;
}
.visit-guidance {
  margin: -8px 0 17px;
  color: #527187;
  font-size: 13px;
  line-height: 1.8;
}
.more-info {
  font-weight: 700;
  font-size: 14px;
}

.cards-shadow {
  box-shadow: 0px 0px 3px 0px rgba(16, 24, 40, 0.1) !important;
  border-radius: 8px;
}
.titles {
  font-size: 16px;
  font-weight: 700;
}
.img-container-gift {
  border-radius: 2px;
  max-width: 64px;
  max-height: 64px;
}
.img-container {
  background: #eaf1fb;
  border-radius: 2px;
  padding: 14px;
  max-width: 64px;
  max-height: 64px;
}
.contents {
  display: flex;
  flex-direction: row;
  margin-right: 12px;
}
.header-title {
  font-size: 12px;
  /* font-weight: 700; */
}
.direction-btn {
  color: #000;
  display: flex;
  background: #fff;
  border-radius: 8px;
  padding: 8px;
}

.visit-type-list {
  max-height: 400px;
  overflow-y: auto;
}

.visit-type-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  margin-bottom: 8px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

.visit-type-item span {
  font-size: 14px;
  color: #404041;
  font-weight: 500;
}

.elevator-details-card {
  border-radius: 12px;
}

.elevator-modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #e9ecef;
  background: #f8f9fa;
  margin-bottom: 16px;
}

.elevator-modal-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #404041;
}

.elevator-modal-content {
  padding: 24px;
  max-height: 60vh;
  overflow-y: auto;
}

.elevator-details-grid {
  display: grid;
  gap: 16px;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

.detail-label {
  font-weight: 600;
  color: #404041;
  font-size: 14px;
  min-width: 140px;
}

.detail-value {
  color: #616162;
  font-size: 14px;
  text-align: left;
  flex: 1;
  margin-right: 12px;
}

.elevator-modal-actions {
  display: flex;
  justify-content: center;
  padding: 20px 24px;
  border-top: 1px solid #e9ecef;
  background: #f8f9fa;
}
</style>
