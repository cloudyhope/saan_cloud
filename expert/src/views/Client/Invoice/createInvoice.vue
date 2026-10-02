<template>
  <div>
    <BaseTopBar title="پرداخت فاکتور" />
    <div v-if="loadingInvoice" class="containers" role="status">در حال دریافت فاکتور…</div>
    <div v-else-if="!invoiceData" class="containers invoice-empty" role="alert">
      <span class="invoice-empty-icon" aria-hidden="true"><v-icon size="30" color="#3775ae">mdi-file-document-alert-outline</v-icon></span>
      <h2>فاکتور در دسترس نیست</h2>
      <p>{{ error || 'اطلاعات فاکتور دریافت نشد.' }}</p>
      <button class="req_code" @click="getInvoceHandler">تلاش دوباره</button>
    </div>
    <div v-else class="containers payment-content">
      <div class="payment-intro"><span class="payment-lock"><v-icon size="24" color="#0b7057">mdi-lock-check-outline</v-icon></span><div><span class="payment-eyebrow">تأیید و پرداخت</span><h2>جزئیات فاکتور را بررسی کنید</h2><p>پس از بررسی مبلغ و نام نیروی اجرایی، کد پرداخت را درخواست کنید.</p></div></div>
      <section class="invoice-details-card" aria-label="مشخصات فاکتور">
        <div class="invoice-amount"><span>مبلغ قابل پرداخت</span><strong>{{ formatBalance(invoiceData.amount_rials) }} <small>ریال</small></strong></div>
        <dl class="invoice-facts">
          <div><dt>نیروی اجرایی</dt><dd>{{ expertName }}</dd></div>
          <div><dt>شماره فاکتور</dt><dd class="invoice-id">{{ invoiceData.id }}</dd></div>
        </dl>
        <div v-if="invoiceData.description" class="invoice-description"><span>شرح فاکتور</span><p>{{ invoiceData.description }}</p></div>
      </section>
      <section class="payment-code-card" aria-labelledby="code-heading">
        <h3 id="code-heading"><span class="step-number">۲</span> کد یک‌بارمصرف پرداخت</h3>
        <p>کد ۵ رقمی به شماره همراه حساب شما ارسال می‌شود و ۲ دقیقه اعتبار دارد.</p>
        <div class="code-actions">
          <label class="code-input-label" for="payment-code">کد پرداخت</label>
          <input id="payment-code" v-model="otpCode" placeholder="ـــــ" class="input-field" type="text" inputmode="numeric" autocomplete="one-time-code" maxlength="5" />
          <button :disabled="timerCount > 0 || requestingCode || !invoiceData" @click="reqOtpCodeHandler" class="req_code" :class="{ disabled: timerCount > 0 }">{{ requestingCode ? 'در حال ارسال…' : timerCount === 0 ? 'دریافت کد' : timerCount + ' ثانیه' }}</button>
        </div>
        <div v-if="alertCard" class="alert_card" role="status">کد ارسال شد. فقط در صورت درست‌بودن اطلاعات فاکتور، آن را برای پرداخت وارد کنید.</div>
      </section>
      <p v-if="error" class="payment-error" role="alert">{{ error }}</p>
    </div>
    <OverlayButton v-if="invoiceData"
      :disabled="isButtonDisabled"
      title="پرداخت"
      @click="submitInvoceHandler"
      :loading="loading"
    />
  </div>
</template>
<script>
import BaseTopBar from "@/components/Topbar/BaseTopbar.vue";
import OverlayButton from "@/components/Button/overlayButton.vue";

export default {
  name: "createInvoice",
  components: {
    BaseTopBar,
    OverlayButton,
  },

  data() {
    return {
      invoiceData: null,
      otpCode: '',
      postData: null,
      timerCount: 0,
      alertCard: false,
      loading: false,
      loadingInvoice: false,
      requestingCode: false,
      error: '',
    };
  },
  computed: {
    expertName() {
      if (!this.invoiceData || !this.invoiceData.expert) return 'نیروی اجرایی';
      return [this.invoiceData.expert.first_name, this.invoiceData.expert.last_name].filter(Boolean).join(' ') || 'نیروی اجرایی';
    },
    isButtonDisabled() {
      return this.loading || !this.invoiceData || !this.postData || this.timerCount === 0 || !/^\d{5}$/.test(this.otpCode);
    },
  },
  mounted() {
    this.getInvoceHandler();
  },
  methods: {
    formatBalance(balance) {
      return Number(balance || 0).toLocaleString('fa-IR');
    },
    async reqOtpCodeHandler() {
      if (this.requestingCode || this.timerCount > 0 || !this.invoiceData) return;
      this.requestingCode = true;
      this.error = '';
      try {
        const res = await this.$ApiServiceLayer.post(
          this.$PATH.RELATIVE_PATH.POST.INVOICE_CODE_REQUEST + '?p=' + this.$STORE.state.userConfig.selectedProject,
          this.$PATH.SERVICE_NAME.WALLET,
          { wallet_invoice: this.$route.params.id }
        );
        if (res.status === 201) {
          this.postData = res.data;
          this.otpCode = '';
          this.timerCount = 120;
          this.alertCard = true;
        } else {
          this.error = this.responseError(res, 'ارسال کد پرداخت انجام نشد.');
        }
      } catch (_) {
        this.error = 'ارسال کد پرداخت انجام نشد.';
      } finally {
        this.requestingCode = false;
      }
    },
    async getInvoceHandler() {
      this.loadingInvoice = true;
      this.error = '';
      try {
        const res = await this.$ApiServiceLayer.get(
          this.$PATH.RELATIVE_PATH.GET.WALLET_INVOICE_BUYER_RETRIEVE +
            this.$route.params.id + "/?p=" + this.$STORE.state.userConfig.selectedProject,
          this.$PATH.SERVICE_NAME.WALLET
        );
        if (res.status === 200 && res.data && res.data.expert) this.invoiceData = res.data;
        else this.error = this.responseError(res, 'فاکتور در دسترس نیست.');
      } catch (_) {
        this.error = 'دریافت فاکتور انجام نشد.';
      } finally {
        this.loadingInvoice = false;
      }
    },
    async submitInvoceHandler() {
      if (this.isButtonDisabled) return;
      this.loading = true;
      this.error = '';
      try {
        const res = await this.$ApiServiceLayer.post(
          this.$PATH.RELATIVE_PATH.POST.INVOICE_CODE_VALIDATE + '?p=' + this.$STORE.state.userConfig.selectedProject,
          this.$PATH.SERVICE_NAME.WALLET,
          { id: this.postData.id, wallet_invoice: this.$route.params.id,
            verification_token: this.postData.verification_token, code: this.otpCode }
        );
        if (res.status === 200 && res.data.status === true) {
          this.$router.push({ name: 'successPurchaseInvoice', params: { id: this.$route.params.id } });
        } else {
          this.error = this.responseError(res, 'پرداخت انجام نشد؛ فاکتور باز است.');
        }
      } catch (_) {
        this.error = 'ارتباط برقرار نشد. وضعیت فاکتور را بررسی کنید.';
      } finally {
        this.loading = false;
      }
    },
    responseError(response, fallback) {
      if (response && response.status === 404) return 'فاکتور پیدا نشد یا به حساب شما تعلق ندارد.';
      if (response && response.status === 403) return 'دسترسی به این فاکتور برای حساب شما فعال نیست.';
      if (response && response.status === 429) return 'برای درخواست دوباره کد کمی صبر کنید.';
      const detail = response && response.data && response.data.detail;
      return typeof detail === 'string' && /[\u0600-\u06ff]/.test(detail) ? detail : fallback;
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
        if (value === 0) {
          this.alertCard = false;
        }
      },
      immediate: true, // This ensures the watcher is triggered upon creation
    },
  },
};
</script>

<style scoped>
.containers { padding: 20px; }
.payment-content { max-width: 576px; margin: auto; padding: 4px 18px calc(110px + env(safe-area-inset-bottom)); color: #17364c; }
.payment-intro { display: flex; align-items: flex-start; gap: 12px; padding: 10px 0 20px; }
.payment-lock { width: 46px; height: 46px; flex: none; display: grid; place-items: center; border-radius: 15px; background: #e7f6ef; }
.payment-eyebrow { color: #1b7a64; font-size: 12px; font-weight: 700; }
.payment-intro h2 { font-size: 20px; line-height: 1.45; margin: 3px 0 5px; }
.payment-intro p, .payment-code-card > p { margin: 0; color: #60788b; font-size: 13px; line-height: 1.75; }
.invoice-details-card, .payment-code-card { background: #fff; border: 1px solid #e1eaf0; border-radius: 20px; box-shadow: 0 7px 24px #173c5710; overflow: hidden; }
.invoice-amount { display: grid; gap: 7px; padding: 20px; background: linear-gradient(135deg,#e9f7f0,#eff9f7); color: #0b6550; }
.invoice-amount span { font-size: 13px; }
.invoice-amount strong { font-size: 28px; line-height: 1.4; }
.invoice-amount small { font-size: 15px; }
.invoice-facts { margin: 0; padding: 5px 18px; }
.invoice-facts div { display: flex; justify-content: space-between; gap: 12px; padding: 15px 0; border-bottom: 1px solid #edf2f5; font-size: 13px; }
.invoice-facts dt { color: #617789; white-space: nowrap; }
.invoice-facts dd { margin: 0; color: #183b53; font-weight: 700; text-align: left; overflow-wrap: anywhere; }
.invoice-id { max-width: 60%; direction: ltr; font-size: 11px; }
.invoice-description { padding: 14px 18px 19px; }
.invoice-description span { color: #617789; font-size: 13px; }
.invoice-description p { margin: 6px 0 0; font-size: 13px; line-height: 1.8; overflow-wrap: anywhere; }
.payment-code-card { margin-top: 17px; padding: 18px; }
.payment-code-card h3 { display: flex; align-items: center; gap: 8px; margin: 0 0 8px; font-size: 16px; }
.step-number { width: 28px; height: 28px; display: grid; place-items: center; border-radius: 10px; color: #fff; background: #247ba8; font-size: 14px; }
.code-actions { display: grid; grid-template-columns: minmax(0,1fr) auto; gap: 10px; margin-top: 19px; }
.code-input-label { grid-column: 1/-1; color: #284a60; font-size: 13px; font-weight: 700; }
.input-field { width: 100%; min-width: 0; height: 48px; padding: 8px 12px; color: #17364c; border: 1px solid #cbdde7; outline: none; border-radius: 12px; background: #fff; font-family: "IRANYekanfa" !important; text-align: center; direction: ltr; letter-spacing: .28em; }
.input-field:focus-visible { border-color: #267cab; box-shadow: 0 0 0 3px #267cab2b; }
.req_code { min-width: 116px; min-height: 48px; border-radius: 12px; padding: 8px 12px; border: 1px solid #7aaed0; background: #ecf6fc; color: #1e6494; font-size: 12px; font-weight: 700; font-family: "IRANYekanfa" !important; }
.req_code:focus-visible { outline: 3px solid #267cab; outline-offset: 2px; }
.disabled { background: #f1f3f5; border-color: #e0e5e9; color: #778a97; cursor: not-allowed; }
.alert_card { margin-top: 14px; padding: 12px; border-radius: 12px; border: 1px solid #beded0; background: #eff9f3; color: #28644f; font-size: 12px; line-height: 1.8; }
.payment-error { margin: 16px 0; padding: 12px; color: #a32922; background: #fff0ed; border: 1px solid #f2cbc5; border-radius: 12px; line-height: 1.8; }
.invoice-empty { max-width: 430px; margin: 95px auto 0; display: flex; align-items: center; flex-direction: column; gap: 14px; text-align: center; }
.invoice-empty-icon { display: grid; place-items: center; width: 62px; height: 62px; border-radius: 19px; background: #e8f3fb; }
.invoice-empty h2 { font-size: 19px; color: #18364d; }
.invoice-empty p { margin: 0; color: #5c7280; line-height: 1.8; }
.invoice-empty .req_code { min-width: 140px; margin-top: 6px; }
</style>
