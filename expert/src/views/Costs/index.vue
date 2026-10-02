<template>
  <div>
    <BaseTopBar title="هزینه انجام کار" />
    <div class="costs-container">
      <CustomAlert bgColor="#fff" borderColor="#357AE1" icon="flag.svg">
        این قسمت را در حضور مشتری تکمیل نمائید.
      </CustomAlert>
      <v-alert v-if="error" type="error" outlined role="alert" class="mt-4">{{ error }} <v-btn v-if="!visitDetail.id" text color="error" @click="getVisitDetail">تلاش دوباره</v-btn></v-alert>
      <div class="costs-item">
        <div class="mb-6">
          <p>دستمزد انجام کار</p>
          <div class="input-group">
            <div class="amount-input">
              <input
                :disabled="requestChange"
                type="text"
                v-model="formattedWage"
                @input="formatWage"
              />
              <span class="currency">ریال</span>
            </div>
            <button @click="requestChangeHandler" class="change-btn">
              درخواست تغییر
            </button>
          </div>
          <span>مطابق توافق طرفین</span>
        </div>
        <!-- <div class="mb-6">
          <div class="mb-2">شماره مشتری</div>
          <input type="number" v-model="clientNumber" class="detail-box" />
        </div> -->
        <!-- <div class="mb-6">
          <p>هزینه وسایل</p>
          <div class="amount-input mb-1">
            <input type="text" value="100,000" />
            <span class="currency">ریال</span>
          </div>
          <span>مطابق فاکتور</span>
        </div> -->
        <div class="mb-6">
          <p>توضیح</p>
          <textarea
            v-model="visitDetail.description"
            class="detail-box"
          ></textarea>
        </div>
        <div class="mb-6">
          <span>نحوه پرداخت</span>
          <v-radio-group v-model="paymentMethod" column>
            <v-radio color="#357AE1" label="اعتباری" value="CREDIT"></v-radio>
            <v-radio color="#357AE1" label="نقدی" value="CASH"></v-radio>
          </v-radio-group>
        </div>
        <!-- <div class="mb-6">
          <div class="image-uploader" @click="triggerFileInput">
            <input
              type="file"
              ref="fileInput"
              class="file-input"
              accept="image/*"
              @change="handleFileUpload"
            />
            <div class="upload-placeholder">
              <div class="upload-content">
                <span class="plus-icon">+</span>
                <span class="upload-text">افزودن تصویر فاکتور</span>
              </div>
            </div>
          </div>
        </div> -->
      </div>
    </div>
    <div class="total-price">
      <div class="gray-color">مبلغ فاکتور</div>
      <div>{{ formattedWage }} <span class="gray-color">ریال</span></div>
    </div>
    <OverlayButton
      :disabled="disabled"
      :loading="loading"
      @click="saveCostsHandler"
      title="ثبت"
    />
  </div>
</template>

<script>
import BaseTopBar from "@/components/Topbar/BaseTopbar.vue";
import CustomAlert from "@/components/CustomAlert/CustomAlert.vue";
import OverlayButton from "@/components/Button/overlayButton.vue";
import { errorMessage, persistentRequestKey, clearRequestKey } from '@/utils/clientRequests';

export default {
  name: "Costs",
  components: {
    BaseTopBar,
    CustomAlert,
    OverlayButton,
  },
  data() {
    return {
      visitDetail: {},
      selectedFile: null,
      isUploading: false,
      formattedWage: "",
      paymentMethod: "",
      requestChange: true,
      // clientNumber: "",
      loading: false,
      error: '',
    };
  },
  mounted() {
    this.getVisitDetail();
  },
  computed: {
    disabled() {
      const amount = Number(this.visitDetail.total_wage);
      return this.loading || !this.visitDetail.id || !this.paymentMethod ||
        !Number.isSafeInteger(amount) || amount <= 0;
    },
  },
  methods: {
    requestChangeHandler() {
      this.requestChange = !this.requestChange;
    },
    async getVisitDetail() {
      this.error = '';
      try {
        const res = await this.$ApiServiceLayer.get(
          this.$PATH.RELATIVE_PATH.GET.VISIT_RETRIEVE +
            this.$route.params.id + "/?p=" + this.$STORE.state.userConfig.selectedProject,
          this.$PATH.SERVICE_NAME.CORE
        );
        if (res.status !== 200) { this.error = errorMessage(res); return; }
        this.visitDetail = res.data;
        this.formattedWage = this.formatNumberWithCommas(this.visitDetail.total_wage || "");
      } catch (_) { this.error = 'دریافت خدمت ممکن نشد. دوباره تلاش کنید.'; }
    },
    formatWage(event) {
      const value = event.target.value.replace(/\D/g, "");

      this.formattedWage = this.formatNumberWithCommas(value);

      this.visitDetail.total_wage = value;
    },
    formatNumberWithCommas(number) {
      const numStr = String(number).replace(/,/g, "");

      return numStr.replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    },
    async saveCostsHandler() {
      if (this.disabled) return;
      this.loading = true;
      this.error = '';
      try {
        const project = this.$STORE.state.userConfig.selectedProject;
        const user = this.$STORE.state.userConfig.userInfo.user.id;
        const scope = `invoice.${user}.${project}.${this.$route.params.id}`;
        const payload = { visit: this.$route.params.id, amount_rials: Number(this.visitDetail.total_wage),
          description: this.visitDetail.description || '', type: this.paymentMethod };
        payload.request_key = persistentRequestKey(scope, payload);
        const res = await this.$ApiServiceLayer.post(
          this.$PATH.RELATIVE_PATH.MULTI.WALLET_INVOICE_EXPERT_LIST_CREATE +
            "?p=" + project,
          this.$PATH.SERVICE_NAME.EMPTY,
          payload
        );
        if (res.status !== 201) { this.error = errorMessage(res); return; }
        clearRequestKey(scope, payload.request_key);
        await this.$router.push({ name: 'qrCode', params: { id: res.data.id } });
      } catch (_) { this.error = 'ثبت فاکتور ممکن نشد. دوباره تلاش کنید.'; }
      finally { this.loading = false; }
    },
    // triggerFileInput() {
    //   this.$refs.fileInput.click();
    // },
    // async handleFileUpload(event) {
    //   const file = event.target.files[0];
    //   if (!file) return;

    //   if (!file.type.startsWith("image/")) {
    //     alert("لطفا یک تصویر انتخاب کنید");
    //     return;
    //   }

    //   if (file.size > 5 * 1024 * 1024) {
    //     alert("حجم فایل نباید بیشتر از 5 مگابایت باشد");
    //     return;
    //   }

    //   try {
    //     this.isUploading = true;
    //     this.selectedFile = file;

    //     // const formData = new FormData();
    //     // formData.append('image', file);
    //   } catch (error) {
    //     console.error("Error uploading file:", error);
    //     alert("خطا در آپلود فایل");
    //   } finally {
    //     this.isUploading = false;
    //   }
    // },
  },
};
</script>
<style lang="scss" scoped>
.costs-container {
  padding: 20px;
}

.costs-item {
  margin-top: 16px;

  p {
    color: #464646;
    margin-bottom: 12px;
  }
}

.input-group {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 4px;
}

.amount-input {
  flex: 1;
  position: relative;
  display: flex;
  align-items: center;
  box-shadow: 0px 0px 3px 0px rgba(16, 24, 40, 0.1);
  border-radius: 8px;
  padding: 8px 12px;
  background: #fff;

  input {
    border: none;
    outline: none;
    width: 100%;
    // padding-right: 45px;
    background: transparent;
  }

  .currency {
    position: absolute;
    left: 12px;
    color: #757575;
  }
}

.change-btn {
  background: #fff;
  border: 1px solid #357ae1;
  color: #357ae1;
  padding: 8px 16px;
  border-radius: 8px;
  cursor: pointer;
  white-space: nowrap;

  &:hover {
    background: #f5f9ff;
  }
}
.detail-box {
  border: 1px solid rgba(192, 214, 246, 1);
  border-radius: 8px;
  padding: 12px;
  text-align: justify;
  width: 100%;
}

.image-uploader {
  border: 1px dashed #ebf2fc;
  border-style: dashed;
  border-spacing: 4px;
  border-radius: 8px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;

  .file-input {
    display: none;
  }

  .upload-placeholder {
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .upload-content {
    display: flex;
    // align-items: center;
    gap: 8px;
    color: #357ae1;
  }

  .plus-icon {
    font-size: 24px;
    line-height: 1;
  }

  .upload-text {
    font-size: 14px;
  }
}
.total-price {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  background: #ebf2fc;
  position: fixed;
  bottom: 90px;
  width: 100%;
  max-width: 567px;
}
</style>
