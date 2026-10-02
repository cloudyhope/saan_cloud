<template>
  <div>
    <FullLoading v-if="loading" />
    <div class="topbar">
      <v-toolbar fixed class="topbar" color="#fff" dense>
        <v-toolbar-title class="title-name">{{
          visitDetail.outlet.name
        }}</v-toolbar-title>
        <v-spacer></v-spacer>
        <v-btn @click="backHandler" icon>
          <v-img max-width="20" src="@/assets/images/Icons/back.svg" />
        </v-btn>
      </v-toolbar>
    </div>
    <div class="ma-6">
      <div class="store-detail">
        <div class="d-flex justify-space-between align-center">
          <div>
            <span class="font-weight-medium">کد مشتری:</span>
            <span class="font-weight-bold mr-1">{{
              visitDetail.outlet.code
            }}</span>
          </div>
          <div>
            <!-- <v-img
              @click="sheet = !sheet"
              max-width="32"
              src="@/assets/images/Icons/info.svg"
            /> -->
            <button @click="sheet = !sheet" class="direction-btn">
              <div class="ml-2">اطلاعات مشتری</div>
              <img src="../../assets/images/Icons/information.svg" />
            </button>
            <v-bottom-sheet
              :retain-focus="false"
              max-width="576px"
              v-model="sheet"
            >
              <v-sheet :retain-focus="false">
                <div class="px-7 py-4">
                  <div class="d-flex justify-space-between">
                    <div>
                      <span class="more-info"> اطلاعات بیشتر </span>
                    </div>
                    <div @click="sheet = !sheet">
                      <v-img
                        max-width="14"
                        src="@/assets/images/Icons/cross.svg"
                      />
                    </div>
                  </div>
                  <div class="mt-2 d-flex flex-column">
                    <span class="mb-2"
                      >نام مشتری: {{ visitDetail.outlet.name }}</span
                    >
                    <span class="mb-2"
                      >کد مشتری: {{ visitDetail.outlet.code }}</span
                    >
                    <span class="mb-2"
                      >نام نیروی اجرایی: {{ visitDetail.outlet.owner_name }}</span
                    >
                    <div class="mb-2">
                      <span>شماره تماس مشتری:</span>
                      <span dir="ltr">{{
                        visitDetail.outlet.phone
                      }}</span>
                    </div>

                    <span
                      v-if="visitDetail.outlet.category.name === 'BrandShop'"
                      class="mb-2"
                      >نوع مشتری:برند شاپ</span
                    >
                    <span class="mb-2"
                      >آدرس کامل:{{ visitDetail.outlet.address }}</span
                    >
                  </div>
                </div>
              </v-sheet>
            </v-bottom-sheet>
          </div>
        </div>
        <div class="d-flex align-center">
          <span class="font-weight-medium">نوبت ویزیت:</span>
          <span class="font-weight-bold mr-1">{{
            visitDetail.visit_turn
          }}</span>
        </div>

        <div class="d-flex justify-space-between align-center">
          <div>
            <span class="font-weight-medium mt-3"
              >زمان شروع ویزیت:</span
            >
            <span class="font-weight-bold mr-1">{{ data.start_time }}</span>
          </div>

          <button @click="directionHandler" class="direction-btn">
            <div class="ml-2">مسیر یابی</div>
            <img src="../../assets/images/Icons/map-icon.svg" />
          </button>
          <v-snackbar v-model="alertDirection" top>
            لوکیشن برای این مشتری ثبت نشده است!
          </v-snackbar>
        </div>
      </div>
      <div
        v-for="question in storeDetailQuestions"
        :key="question.question_type"
        @click="questionPage(question.id, visitDetail.id)"
        class="documnets"
      >
        <div class="d-flex align-center">
          <div class="img-box">
            <v-img max-width="24" src="@/assets/images/Icons/doc.svg" />
          </div>
          <span class="doc-title">{{ question.verbose_name }}</span>
        </div>
        <div>
          <v-img
            max-width="24"
            v-if="question.status === false"
            src="@/assets/images/Icons/chevron-left-rounded.svg"
          />
          <v-img
            max-width="24"
            v-if="question.status === true"
            src="@/assets/images/Icons/material-symbols_keyboard-arrow-up-rounded.svg"
          />
        </div>
      </div>
      <div
        v-for="photos in storeDetailPhotos"
        :key="photos.id"
        class="documnets"
        @click="imageCondition(photos)"
      >
        <div class="d-flex align-center">
          <div class="img-box">
            <v-img max-width="24" src="@/assets/images/Icons/camera.svg" />
          </div>
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
          <input
            type="file"
            hidden
            capture="user"
            accept="image/*"
            id="fileUpload"
            @change="func($event, photos)"
          />
          <v-snackbar v-model="snackbar" :timeout="timeout" top>
            عکس با موفقیت آرسال شد.
          </v-snackbar>
        </div>
        <div>
          <v-img
            max-width="24"
            v-if="photos.status === false"
            src="@/assets/images/Icons/chevron-left-rounded.svg"
          />
          <v-img
            max-width="24"
            v-if="photos.status === true"
            src="@/assets/images/Icons/material-symbols_keyboard-arrow-up-rounded.svg"
          />
        </div>
      </div>

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
        <h4 class="my-4">پرسشنامه ها</h4>
        <v-card
          v-for="survey in storeDetailSurvey"
          :key="survey.id"
          @click="surveyVisitDetail(survey)"
          class="cards-shadow pa-5 mt-2"
        >
          <div class="d-flex justify-space-between align-center">
            <div class="d-flex align-center">
              <div class="img-container">
                <v-img max-width="36" :src="survey.icon" />
              </div>
              <div class="contents">
                <span class="header mb-1">{{ survey.verbose_name }}</span>
              </div>
            </div>
            <div>
              <v-img src="../../assets/images/Icons/chevron-left-rounded.svg" />
            </div>
          </div>
        </v-card>
      </div>
    </div>
    <EmptyContainer />
    <!-- <OverlayButton
        @click="finishVisit"
        :disabled="disableFinishVisit"
        title="اتمام ویزیت"
      /> -->
  </div>
</template>
<script>
import OverlayButton from "../../components/Button/overlayButton.vue";
import EmptyContainer from "../../components/emptyContainer.vue";
import FullLoading from "../../components/Loading/fullLoading.vue";

export default {
  name: "Profile",
  components: {
    OverlayButton,
    EmptyContainer,
    FullLoading,
  },
  data() {
    return {
      sheet: false,
      storeDetailPhotos: [],
      storeDetailQuestions: [],
      storeDetailSurvey: [],
      visitDetail: {},
      data: {},
      captureImg: null,
      latitude: null,
      longitude: null,
      snackbar: false,
      timeout: 2000,
      loading: false,
      x: false,
      y: false,
      alertDirection: false,
    };
  },
  created() {
    this.getStoreDetail();
    const success = (position) => {
      this.latitude = position.coords.latitude;
      this.longitude = position.coords.longitude;
      // Do something with the position
    };

    const error = (err) => {
      err;
    };
    // This will open permission popup
    navigator.geolocation.getCurrentPosition(success, error);
  },
  computed: {
    checkQuestion() {
      for (let x of this.storeDetailQuestions) {
        if (x.status === false) {
          return true;
        }
      }
      return false;
    },
    checkPhotos() {
      for (let i of this.storeDetailPhotos) {
        if (i.status === false) {
          return true;
        }
      }
      return false;
    },
    disableFinishVisit() {
      if (this.checkPhotos === true || this.checkQuestion === true) {
        return true;
      } else {
        return false;
      }
    },
  },
  methods: {
    async getStoreDetail() {
      const url = window.location.href;
      const lastParam = url.split("/").slice(-1)[0];
      const res = await this.$ApiServiceLayer.get(
        this.$PATH.RELATIVE_PATH.GET.VISIT_PAGE_SETTING +
          lastParam +
          "/" +
          "?p=" +
          this.$STORE.state.userConfig.selectedProject,
        this.$PATH.SERVICE_NAME.AUTH
      );
      if (res.status === 200) {
        res.data;
        this.storeDetailPhotos = res.data.photos;
        this.storeDetailQuestions = res.data.questions;
        this.storeDetailSurvey = res.data.surveys;
        this.visitDetail = res.data.visit;
        this.data = res.data;
      }
    },
    async surveyVisitDetail(survey) {
      const url = window.location.href;
      const lastParam = url.split("/").slice(-1)[0];
      const res = await this.$ApiServiceLayer.post(
        this.$PATH.RELATIVE_PATH.MULTI.SURVEY_FILL_OUT,
        this.$PATH.SERVICE_NAME.AUTH,
        { survey: survey.id, visit: lastParam }
      );
      if (res.status === 201) {
        this.$router.push({
          name: "surveyDetailInVisit",
          params: { fill_id: res.data.id, visit_id: lastParam },
        });
      }
    },
    backHandler() {
      this.$router.push({ name: "supervisor" });
    },
    directionHandler() {
      if (
        this.data.visit.outlet.latitude === null ||
        this.data.visit.outlet.longitude === null
      ) {
        this.alertDirection = true;
      } else {
        window.open(
          `https://maps.google.com/?q=${this.data.visit.outlet.latitude},${this.data.visit.outlet.longitude}`,
          "_blank"
        );
      }
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
        name: "superVisorImageView",
        params: { type: e.id, id: this.visitDetail.id, minImg: e.min },
      });
    },
    questionPage(questionType, id) {
      "Questions!:", questionType, id;
      this.$router.push({
        name: "superVisiorQuestionsView",
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
    async finishVisit() {
      const res = await this.$ApiServiceLayer.patch(
        this.$PATH.RELATIVE_PATH.MULTI.GET_STATUS_QUESTIONS +
          this.visitDetail.id +
          "/" +
          "?p=" +
          this.$STORE.state.userConfig.selectedProject,
        this.$PATH.SERVICE_NAME.AUTH,
        { supervision_status: "2" }
      );
      if (res.status === 200) {
        this.$router.push({
          name: "supervisor",
        });
      }
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
.v-sheet {
  box-shadow: none !important;
}
.direction-btn {
  color: #000;
  display: flex;
  background: #fff;
  border-radius: 8px;
  padding: 8px;
}
.topbar {
  /* padding-right: 8px !important; */
  position: fixed;
  max-width: 570px;
  width: 100%;
  z-index: 2;
  box-shadow: 0px 0px 4px rgba(220, 220, 221, 0.6) !important;
}
.store-detail {
  display: flex;
  flex-direction: column;
  padding: 16px;
  margin-top: 70px;
  background: #EAF2F9;
  border-radius: 8px;
}
.documnets {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-radius: 8px;
  background: #fff;
  padding: 12px;
  margin-top: 24px;
  box-shadow: 0px 4px 4px rgba(214, 214, 214, 0.6);
}
.img-box {
  border-radius: 8px;
  background: #eaf1fb;
  padding: 12px;
}
.doc-title {
  font-size: 14px;
  color: #616162;
  margin-right: 11px;
}
.more-info {
  font-weight: 700;
  font-size: 14px;
}

.cards-shadow {
  box-shadow: 0px 4px 4px rgba(214, 214, 214, 0.6) !important;
}
.titles {
  font-size: 16px;
  font-weight: 700;
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
  flex-direction: column;
  margin-right: 12px;
}
.header {
  font-size: 12px;
  font-weight: 700;
}
</style>
