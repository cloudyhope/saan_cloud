<template>
  <div>
    <BaseTopBar title=" QR کد اختصاصی شما" />
    <div class="containers" dir="rtl">
      <p>لطفا از خریدار بخواهید QR کد پایین را جهت پرداخت فاکتور صادر شده اسکن کند.</p>
      <v-progress-circular v-if="loading" indeterminate color="primary" aria-label="در حال ساخت کد پرداخت" />
      <v-alert v-else-if="error" type="error" outlined role="alert">{{ error }} <v-btn text color="error" @click="loadQr">تلاش دوباره</v-btn></v-alert>
      <img v-else-if="imageUrl" class="qrImage" :src="imageUrl" alt="کد پرداخت این فاکتور" />
    </div>
    <OverlayButton
      title="بستن"
      @click="buttonHandler"
    />
  </div>
</template>

<script>
import BaseTopBar from "@/components/Topbar/BaseTopbar.vue";
import OverlayButton from "@/components/Button/overlayButton.vue";

export default {
  name: "merchantQrCode",
  components: {
    BaseTopBar,
    OverlayButton
  },
  data() {
    return {
      imageUrl: "",
      loading: false,
      error: '',
    };
  },
  mounted() {
    this.loadQr();
  },
  beforeDestroy() { if (this.imageUrl) URL.revokeObjectURL(this.imageUrl); },
  methods: {
    async loadQr() {
      this.loading = true;
      this.error = '';
      try {
        const path = this.$PATH.RELATIVE_PATH.GET.WALLET_GET_QR_CODE +
          this.$route.params.id + '/?p=' + this.$STORE.state.userConfig.selectedProject;
        const response = await this.$ApiServiceLayer.getBlob(path);
        if (response.status !== 200 || !response.data || response.data.type !== 'image/png') {
          this.error = 'کد پرداخت این فاکتور در دسترس نیست.';
          return;
        }
        if (this.imageUrl) URL.revokeObjectURL(this.imageUrl);
        this.imageUrl = URL.createObjectURL(response.data);
      } catch (_) {
        this.error = 'دریافت کد پرداخت ممکن نشد. دوباره تلاش کنید.';
      } finally {
        this.loading = false;
      }
    },
    buttonHandler() {
      this.$router.push({ name: "tasks"});
    }
  },
};
</script>

<style lang="scss" scoped>
.containers {
  margin-top: 72px;
  padding: 20px;
  display: flex;
  align-items: center;
  flex-direction: column;
  min-height: 230px;
  p{
    font-size: 16px;
    text-align: center;
    margin-bottom: 32px;
  }
  .qrImage {
    width: min(100%, 260px);
    padding: 14px;
    border: 1px solid #dce9ef;
    border-radius: 18px;
    background: white;
    box-shadow: 0 12px 30px #173f5814;
  }
}
</style>
