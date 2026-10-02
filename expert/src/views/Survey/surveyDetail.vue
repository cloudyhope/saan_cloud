<template>
  <div>
    <FullLoading v-if="loading" />
    <BaseTopBar :title="surveyDetailQuestions.survey_fill_out.survey.verbose_name" />
    
    <div class="survey-container">
      <!-- Survey Description Card -->
      <v-card class="survey-description-card">
        <div class="sms-text">
          {{ surveyDetailQuestions.survey_fill_out.survey.sms_text }}
        </div>
      </v-card>

      <!-- Verification Status Alerts -->
      <v-alert
        v-if="
          surveyDetailQuestions.survey_fill_out.phone_verified === false &&
          surveyDetailQuestions.survey_fill_out.survey.has_phone_verification === true
        "
        class="verification-alert warning-alert"
        border="left"
        color="#F8F0D6"
      >
        <div class="d-flex align-center">
          <v-img
            max-width="20"
            src="@/assets/images/Icons/circle-slice-3.svg"
            class="alert-icon"
          />
          <span class="warning-message">احراز هویت انجام نشده است.</span>
        </div>
      </v-alert>
      
      <v-alert
        v-if="
          surveyDetailQuestions.survey_fill_out.phone_verified === true &&
          surveyDetailQuestions.survey_fill_out.survey.has_phone_verification === true
        "
        class="verification-alert success-alert"
        border="left"
        color="#B3EADB"
      >
        <div class="d-flex align-center">
          <v-img
            max-width="20"
            src="@/assets/images/Icons/check-circle-outline.svg"
            class="alert-icon"
          />
          <span class="success-message">احراز هویت با موفقیت انجام شد.</span>
        </div>
      </v-alert>

      <!-- Province/City Selection Card -->
      <v-card v-if="isMandatory" class="location-card">
        <div class="card-header">
          <h3 class="card-title">انتخاب موقعیت</h3>
        </div>
        
        <div class="form-group">
          <label class="form-label">استان:</label>
          <select
            @change="getCityOnChange"
            v-model="pickProvince"
            class="form-select"
          >
            <option
              v-for="province in provinceLists"
              :value="province.id"
              :key="'province' + province.id"
            >
              {{ province.name }}
            </option>
          </select>
        </div>
        
        <div class="form-group">
          <label class="form-label">شهر:</label>
          <select v-model="pickCity" class="form-select" @change="onChangeCity">
            <option
              v-for="city in cityList"
              :value="city.id"
              :key="'city' + city.id"
            >
              {{ city.name }}
            </option>
          </select>
        </div>
        
        <div
          v-if="
            surveyDetailQuestions.survey_fill_out.survey.has_phone_verification === null
          "
          class="form-group"
        >
          <label class="form-label">شماره همراه پرسش شونده:</label>
          <div class="phone-input-group">
            <input
              maxlength="11"
              type="number"
              oninput="javascript: if (this.value.length > this.maxLength) this.value = this.value.slice(0, this.maxLength);"
              v-model="surveyDetailQuestions.survey_fill_out.phone_number"
              class="phone-input"
              placeholder="شماره همراه را وارد کنید"
            />
            <button
              @click="onChangeCity"
              class="send-button"
              :disabled="checkPhoneNumber"
            >
              <v-img
                max-width="18"
                src="@/assets/images/Icons/quill_send.svg"
              />
            </button>
          </div>
        </div>
      </v-card>

      <!-- Survey Items -->
      <div class="survey-items">
        <!-- Questions -->
        <div
          v-for="survey in surveyDetailQuestions.questions"
          :key="'survey' + survey.id"
          @click="questionPage(survey.id)"
          class="survey-item"
        >
          <div class="item-content">
            <div class="item-icon">
              <v-img max-width="24" src="@/assets/images/Icons/doc.svg" />
            </div>
            <span class="item-title">{{ survey.verbose_name }}</span>
          </div>
          <div class="item-arrow">
            <v-img
              v-if="survey.status === false"
              max-width="20"
              src="@/assets/images/Icons/chevron-left-rounded.svg"
            />
            <v-img
              max-width="20"
              v-if="survey.status === true"
              src="@/assets/images/Icons/material-symbols_keyboard-arrow-up-rounded.svg"
            />
          </div>
        </div>

        <!-- Photos -->
        <div
          v-for="photos in surveyDetailQuestions.photos"
          :key="'photos' + photos.id"
          class="survey-item"
          @click="imageCondition(photos)"
        >
          <div class="item-content">
            <div class="item-icon">
              <v-img max-width="24" src="@/assets/images/Icons/camera.svg" />
            </div>
            <span class="item-title">{{ photos.verbose_name }}</span>
          </div>
          <div class="item-arrow">
            <v-img
              v-if="photos.status === false"
              max-width="20"
              src="@/assets/images/Icons/chevron-left-rounded.svg"
            />
            <v-img
              max-width="20"
              v-if="photos.status === true"
              src="@/assets/images/Icons/material-symbols_keyboard-arrow-up-rounded.svg"
            />
          </div>
        </div>

        <!-- Add-ins -->
        <div
          v-for="add in surveyDetailQuestions.add_ins"
          :key="'add' + add.id"
          class="survey-item"
          @click="veifyProfileHandler()"
        >
          <div class="item-content">
            <div class="item-icon">
              <v-img max-width="24" src="@/assets/images/Icons/camera.svg" />
            </div>
            <span class="item-title">{{ add.verbose_name }}</span>
          </div>
          <div class="item-arrow">
            <v-img
              max-width="20"
              src="@/assets/images/Icons/material-symbols_keyboard-arrow-up-rounded.svg"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- Bottom Spacing -->
    <div class="bottom-spacing"></div>

    <!-- Action Buttons -->
    <div
      class="action-buttons"
      v-if="
        surveyDetailQuestions.survey_fill_out.phone_verified === false &&
        surveyDetailQuestions.survey_fill_out.survey.has_phone_verification === true
      "
    >
      <button type="button" :disabled="true" class="action-button disabled-button">
        <span>ارسال</span>
      </button>
      <button @click="verifySheet = true" type="button" class="action-button verify-button">
        <span>احراز هویت</span>
      </button>
    </div>

    <!-- Verification Bottom Sheet -->
    <v-bottom-sheet
      :retain-focus="false"
      max-width="576px"
      v-model="verifySheet"
    >
      <v-sheet
        :retain-focus="false"
        class="verification-sheet"
        height="320px"
      >
        <div class="sheet-header">
          <h3 class="sheet-title">احراز هویت</h3>
        </div>

        <div class="sheet-content">
          <div class="verification-step">
            <p class="step-description">شماره همراه شخص را برای دریافت کد وارد کنید.</p>
            <div class="phone-input-group">
              <input 
                v-model="phoneNumber" 
                class="verification-input" 
                type="number" 
                placeholder="شماره همراه"
              />
              <button
                @click="sendOtpCode"
                :disabled="sendOtpNumber"
                class="send-button"
              >
                <v-img
                  v-if="sendOtpIcon === true && sendCodeTrue === false"
                  max-width="18"
                  src="@/assets/images/Icons/quill_send.svg"
                />
                <span
                  v-if="sendOtpIcon === true && sendCodeTrue === true"
                  class="timer"
                >{{ timerCount }}</span>
                <v-img
                  v-if="sendOtpIcon === false && sendCodeTrue === false"
                  max-width="18"
                  src="@/assets/images/Icons/quill_send_white.svg"
                />
              </button>
            </div>
          </div>

          <div class="verification-step">
            <p class="step-description">کد ارسال‌شده را وارد کنید.</p>
            <div class="otp-container">
              <input
                inputmode="decimal"
                type="number"
                class="otp-input"
                v-model="codeOtp"
                maxlength="5"
                @keyup.enter="submitOTP"
                @input="checkVerify"
                :disabled="otpInputs"
                placeholder="کد تایید"
              />
              <div class="otp-display">
                <div class="otp-digit" :class="{ active: fakeInput[4] }">
                  {{ fakeInput[4] }}
                </div>
                <div class="otp-digit" :class="{ active: fakeInput[3] }">
                  {{ fakeInput[3] }}
                </div>
                <div class="otp-digit" :class="{ active: fakeInput[2] }">
                  {{ fakeInput[2] }}
                </div>
                <div class="otp-digit" :class="{ active: fakeInput[1] }">
                  {{ fakeInput[1] }}
                </div>
                <div class="otp-digit" :class="{ active: fakeInput[0] }">
                  {{ fakeInput[0] }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </v-sheet>
    </v-bottom-sheet>

    <!-- Submit Button -->
    <OverlayButton
      v-if="
        surveyDetailQuestions.survey_fill_out.phone_verified === true ||
        surveyDetailQuestions.survey_fill_out.survey.has_phone_verification === false
      "
      @click="finishSurvey"
      :disabled="disableFinishSurvey"
      title="ارسال"
    />

    <!-- Error Snackbar -->
    <v-snackbar v-model="errorSnackBar" :timeout="4000" color="red">
      شماره همراه وارد شده تکراری است.
    </v-snackbar>
  </div>
</template>
<script>
import OverlayButton from "../../components/Button/overlayButton.vue";
import EmptyContainer from "../../components/emptyContainer.vue";
import FullLoading from "../../components/Loading/fullLoading.vue";
import BaseTopBar from "@/components/Topbar/BaseTopbar.vue";
export default {
  name: "Profile",
  components: {
    OverlayButton,
    EmptyContainer,
    FullLoading,
    BaseTopBar
  },
  data() {
    return {
      sheet: false,
      surveyDetailQuestions: [],
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
      provinceLists: [],
      cityList: [],
      pickProvince: "",
      pickCity: "",
      selectedkCity: "",
      surveyId: null,
      verifySheet: false,
      codeOtp: "",
      phoneNumber: "",
      veificationData: {},
      otpInputs: true,
      sendOtpIcon: true,
      timerCount: 0,
      sendCodeTrue: false,
      disableSendOtp: false,
      errorSnackBar: false,
      visitId: null,
      isMandatory: false,
    };
  },
  created() {
    this.getProvince();
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
  async mounted() {
    await this.getSurveyDetail();
    this.submitedExistsProvince();
  },
  computed: {
    checkQuestion() {
      for (let x of this.surveyDetailQuestions.questions) {
        if (x.status === false) {
          return true;
        }
      }
      return false;
    },
    checkPhotos() {
      for (let i of this.surveyDetailQuestions.photos) {
        if (i.status === false) {
          return true;
        }
      }
      return false;
    },
    fakeInput() {
      return this.codeOtp;
    },
    disableFinishSurvey() {
      if (
        this.checkPhotos === true ||
        this.checkQuestion === true
      ) {
        return true;
      } else {
        return false;
      }
    },
    sendOtpNumber() {
      if (this.disableSendOtp === true) {
        return true;
      }
      if (this.phoneNumber.length < 11) {
        return true;
      } else {
        return false;
      }
    },
    checkPhoneNumber() {
      if (this.surveyDetailQuestions.survey_fill_out.phone_number === null) {
        return true;
      }
      if (this.surveyDetailQuestions.survey_fill_out.phone_number.length < 11) {
        return true;
      } else {
        return false;
      }
    },
  },
  methods: {
    async getSurveyDetail() {
      const url = window.location.href;
      this.surveyId = url.split("/").slice(-1)[0];
      if (url.includes("invisit")) {
        this.visitId = url.split("/").slice(-2)[0];
        "sd", this.visitId;
      }
      const res = await this.$ApiServiceLayer.get(
        this.$PATH.RELATIVE_PATH.MULTI.SURVEY_QUESTION_TYPE +
          this.surveyId +
          "/" +
          "?p=" +
          this.$STORE.state.userConfig.selectedProject,
        this.$PATH.SERVICE_NAME.AUTH
      );
      if (res.status === 200) {
        this.isMandatory = res.data.survey_fill_out.survey.is_mandatory_city;
        this.surveyDetailQuestions = res.data;
        if (res.data.survey_fill_out.province !== null) {
          this.pickProvince = res.data.survey_fill_out.province.id;
        }
        if (res.data.survey_fill_out.city !== null) {
          this.pickCity = res.data.survey_fill_out.city.id;
        }
      }
    },
    submitedExistsProvince() {
      if (this.pickCity !== null) {
        this.getCity();
      }
    },
    async getProvince() {
      const res = await this.$ApiServiceLayer.get(
        this.$PATH.RELATIVE_PATH.GET.PROVINCE_LIST +
          "?p=" +
          this.$STORE.state.userConfig.selectedProject,
        this.$PATH.SERVICE_NAME.AUTH
      );
      if (res.status === 200) {
        this.provinceLists = res.data;
      }
    },
    async finishSurvey() {
      const res = await this.$ApiServiceLayer.patch(
        this.$PATH.RELATIVE_PATH.MULTI.SURVEY_FILL_OUT_EDIT +
          this.surveyId +
          "/" + '?p=' + this.$STORE.state.userConfig.selectedProject,
        this.$PATH.SERVICE_NAME.AUTH,
        { is_closed: true }
      );
      if (res.status === 200) {
        this.provinceLists = res.data;
        const url = window.location.href;
        if (url.includes("invisit")) {
          this.$router.push({
            name: "storeDetail",
            params: { id: this.visitId },
          });
        } else {
          this.$router.push({ name: "survey" });
        }
      }
    },
    async getCity() {
      const res = await this.$ApiServiceLayer.get(
        this.$PATH.RELATIVE_PATH.GET.CITY_LIST +
          "?province=" +
          this.selectedkCity +
          "&p=" +
          this.$STORE.state.userConfig.selectedProject,
        this.$PATH.SERVICE_NAME.AUTH
      );
      if (res.status === 200) {
        this.cityList = res.data;
      }
    },
    async onChangeCity() {
      this.loading = true;
      const res = await this.$ApiServiceLayer.patch(
        this.$PATH.RELATIVE_PATH.MULTI.SURVEY_FILL_OUT_EDIT +
          this.surveyId +
          "/" + '?p=' + this.$STORE.state.userConfig.selectedProject,
        this.$PATH.SERVICE_NAME.AUTH,
        {
          city: this.pickCity,
          province: this.pickProvince,
          phone_number: this.surveyDetailQuestions.survey_fill_out.phone_number,
        }
      );
      if (res.status === 200) {
        this.loading = false;
      } else {
        this.loading = false;
        this.errorSnackBar = true;
      }
    },
    getCityOnChange() {
      this.selectedkCity = this.pickProvince;
      this.getCity();
      this.pickCity = "";
    },
    checkVerify() {
      if (this.codeOtp.length == 5) {
        this.submitOTP();
      }
    },
    async sendOtpCode() {
      this.disableSendOtp = true;
      this.sendCodeTrue = true;
      this.timerCount = 30;
      const res = await this.$ApiServiceLayer.post(
        this.$PATH.RELATIVE_PATH.POST.SURVEY_VERIFICATION_SEND_CODE,
        this.$PATH.SERVICE_NAME.AUTH,
        { phone_number: this.phoneNumber, survey_fill_out: this.surveyId }
      );
      if (res.status === 201) {
        this.veificationData = res.data;
        this.otpInputs = false;
      } else {
        this.verifySheet = false;
        this.errorSnackBar = true;
        this.timerCount = 0;
        this.sendCodeTrue = false;
      }
    },
    async submitOTP() {
      this.loading = true;
      const res = await this.$ApiServiceLayer.post(
        this.$PATH.RELATIVE_PATH.POST.SURVEY_OTP_VALIDATE_VERIFICATION,
        this.$PATH.SERVICE_NAME.AUTH,
        {
          // code: this.veificationData.code,
          code: this.codeOtp,
          verification_token: this.veificationData.verification_token,
          id: this.veificationData.id,
          phone_number: this.veificationData.phone_number,
        }
      );
      if (res.status === 200) {
        this.loading = false;
        this.getSurveyDetail();
      } else {
        this.warning = res.status === 419
          ? "کد منقضی شده است؛ کد تازه دریافت کنید"
          : (res.data && res.data.detail) || "کد ورود معتبر نیست";
        this.codeOtp = "";
        this.loading = false;
      }
    },
    veifyProfileHandler() {
      this.$router.push({
        name: "verifyProfile",
        params: { id: this.surveyId },
      });
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
      this.$router.push({
        name: "surveyImage",
        params: { surveyId: this.surveyId, id: e.id },
      });
    },
    questionPage(id) {
      this.$router.push({
        name: "surveyQuestions",
        params: { surveyId: this.surveyId, id: id },
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
  },
  watch: {
    timerCount: {
      handler(value) {
        if (value > 0) {
          setTimeout(() => {
            this.timerCount--;
          }, 1000);
        }
        if (value <= 0) {
          this.disableSendOtp = false;
          this.sendCodeTrue = false;
        }
      },
      immediate: true, // This ensures the watcher is triggered upon creation
    },
  },
};
</script>
<style lang="scss" scoped>
// Main Container
.survey-container {
  margin: 0 24px;
  padding-top: 24px;
}

// Survey Description Card
.survey-description-card {
  margin-bottom: 24px;
  box-shadow: 0px 0px 3px 0px rgba(16, 24, 40, 0.1) !important;
  border-radius: 12px !important;
  overflow: hidden;
}

.sms-text {
  font-size: 14px;
  color: #404041;
  font-weight: 400;
  line-height: 1.5;
  background: linear-gradient(135deg, #cddff5 0%, #e8f2ff 100%);
  padding: 16px;
  margin: 0;
}

// Verification Alerts
.verification-alert {
  margin-bottom: 16px;
  border-radius: 12px !important;
  border: none !important;
  
  &.warning-alert {
    background: linear-gradient(135deg, #F8F0D6 0%, #FFF8E1 100%) !important;
  }
  
  &.success-alert {
    background: linear-gradient(135deg, #B3EADB 0%, #E8F5E8 100%) !important;
  }
}

.alert-icon {
  margin-left: 12px;
}

.warning-message {
  color: #c2aa65;
  font-size: 14px;
  font-weight: 500;
}

.success-message {
  color: #46a175;
  font-size: 14px;
  font-weight: 500;
}

// Location Card
.location-card {
  margin-bottom: 24px;
  box-shadow: 0px 0px 3px 0px rgba(16, 24, 40, 0.1) !important;
  border-radius: 12px !important;
  overflow: hidden;
}

.card-header {
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  padding: 16px 20px;
  border-bottom: 1px solid #e9ecef;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: #404041;
  margin: 0;
}

.form-group {
  padding: 20px;
  border-bottom: 1px solid #f1f3f4;
  
  &:last-child {
    border-bottom: none;
  }
}

.form-label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: #404041;
  margin-bottom: 8px;
}

.form-select {
  width: 100%;
  padding: 12px 16px;
  border: 1px solid #e1e5e9;
  border-radius: 8px;
  background: #fff;
  font-size: 14px;
  color: #404041;
  transition: all 0.2s ease;
  box-shadow: 0px 0px 3px 0px rgba(16, 24, 40, 0.1);
  
  &:focus {
    outline: none;
    border-color: #357AE1;
    box-shadow: 0px 0px 0px 3px rgba(53, 122, 225, 0.1);
  }
}

// Phone Input Group
.phone-input-group {
  display: flex;
  gap: 12px;
  align-items: center;
}

.phone-input {
  flex: 1;
  padding: 12px 16px;
  border: 1px solid #e1e5e9;
  border-radius: 8px;
  background: #fff;
  font-size: 14px;
  color: #404041;
  transition: all 0.2s ease;
  box-shadow: 0px 0px 3px 0px rgba(16, 24, 40, 0.1);
  
  &::placeholder {
    color: #9ca3af;
  }
  
  &:focus {
    outline: none;
    border-color: #357AE1;
    box-shadow: 0px 0px 0px 3px rgba(53, 122, 225, 0.1);
  }
}

.send-button {
  display: flex;
  justify-content: center;
  align-items: center;
  background: #357AE1;
  border: none;
  border-radius: 8px;
  min-width: 48px;
  height: 48px;
  cursor: pointer;
  transition: all 0.2s ease;
  
  &:hover:not(:disabled) {
    background: #2d6bb8;
    transform: translateY(-1px);
  }
  
  &:disabled {
    background: #f1f1f1;
    cursor: not-allowed;
  }
}

// Survey Items
.survey-items {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.survey-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #fff;
  padding: 16px 20px;
  border-radius: 12px;
  box-shadow: 0px 0px 3px 0px rgba(16, 24, 40, 0.1) !important;
  cursor: pointer;
  transition: all 0.2s ease;
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0px 4px 12px 0px rgba(16, 24, 40, 0.15) !important;
  }
}

.item-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.item-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #eaf1fb 0%, #f4f9ff 100%);
  border-radius: 8px;
  padding: 12px;
  min-width: 48px;
  height: 48px;
}

.item-title {
  font-size: 14px;
  color: #404041;
  font-weight: 500;
}

.item-arrow {
  display: flex;
  align-items: center;
}

// Bottom Spacing
.bottom-spacing {
  height: 120px;
}

// Action Buttons
.action-buttons {
  position: fixed;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 100%;
  max-width: 576px;
  background: #fff;
  padding: 20px 24px;
  display: flex;
  gap: 16px;
  box-shadow: 0px -4px 12px 0px rgba(16, 24, 40, 0.1);
  border-radius: 16px 16px 0 0;
}

.action-button {
  flex: 1;
  padding: 16px 24px;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 600;
  border: none;
  cursor: pointer;
  transition: all 0.2s ease;
  
  &.disabled-button {
    background: #f1f1f1;
    color: #9ca3af;
    cursor: not-allowed;
  }
  
  &.verify-button {
    background: #357AE1;
    color: #fff;
    
    &:hover {
      background: #2d6bb8;
      transform: translateY(-1px);
    }
  }
}

// Verification Sheet
.verification-sheet {
  border-radius: 16px 16px 0 0 !important;
  padding: 0;
}

.sheet-header {
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  padding: 20px 24px;
  border-bottom: 1px solid #e9ecef;
}

.sheet-title {
  font-size: 18px;
  font-weight: 600;
  color: #404041;
  margin: 0;
}

.sheet-content {
  padding: 24px;
}

.verification-step {
  margin-bottom: 24px;
  
  &:last-child {
    margin-bottom: 0;
  }
}

.step-description {
  font-size: 14px;
  color: #6b7280;
  margin-bottom: 16px;
  line-height: 1.5;
}

.verification-input {
  flex: 1;
  padding: 12px 16px;
  border: 1px solid #e1e5e9;
  border-radius: 8px;
  background: #fff;
  font-size: 14px;
  color: #404041;
  transition: all 0.2s ease;
  box-shadow: 0px 0px 3px 0px rgba(16, 24, 40, 0.1);
  
  &::placeholder {
    color: #9ca3af;
  }
  
  &:focus {
    outline: none;
    border-color: #357AE1;
    box-shadow: 0px 0px 0px 3px rgba(53, 122, 225, 0.1);
  }
}

.timer {
  font-size: 16px;
  font-weight: 600;
  color: #357AE1;
}

// OTP Container
.otp-container {
  position: relative;
  width: 100%;
}

.otp-input {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  opacity: 0;
  z-index: 10;
  cursor: pointer;
}

.otp-display {
  display: flex;
  gap: 12px;
  justify-content: center;
}

.otp-digit {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 56px;
  height: 56px;
  border: 2px solid #e1e5e9;
  border-radius: 12px;
  background: #fff;
  font-size: 20px;
  font-weight: 600;
  color: #404041;
  transition: all 0.2s ease;
  
  &.active {
    border-color: #357AE1;
    background: #f8f9ff;
    color: #357AE1;
    transform: scale(1.05);
  }
}

// Responsive Design
@media (max-width: 480px) {
  .survey-container {
    margin: 0 16px;
  }
  
  .action-buttons {
    padding: 16px 20px;
  }
  
  .otp-digit {
    width: 48px;
    height: 48px;
    font-size: 18px;
  }
}
</style>

