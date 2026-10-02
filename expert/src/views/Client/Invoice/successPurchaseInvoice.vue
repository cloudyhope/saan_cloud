<template>
  <main class="receipt-page" dir="rtl">
    <BaseTopBar title="رسید پرداخت" />
    <section class="receipt-card" aria-live="polite">
      <template v-if="loading">
        <v-progress-circular indeterminate color="primary" aria-label="در حال دریافت رسید" />
        <p>در حال دریافت رسید پرداخت…</p>
      </template>
      <template v-else-if="error">
        <div class="receipt-icon error-icon">!</div>
        <h1>رسید در دسترس نیست</h1>
        <p role="alert">{{ error }}</p>
        <button class="retry-button" @click="getResult">تلاش دوباره</button>
      </template>
      <template v-else-if="results">
        <div class="receipt-icon success-icon" aria-hidden="true">✓</div>
        <h1>پرداخت با موفقیت ثبت شد</h1>
        <p class="receipt-lead">فاکتور شما پرداخت و بسته شد.</p>
        <div class="receipt-amount">
          <span>مبلغ پرداختی</span>
          <strong>{{ formatBalance(results.amount_rials) }} <small>ریال</small></strong>
        </div>
        <dl class="receipt-details">
          <div><dt>شماره فاکتور</dt><dd class="ltr">{{ results.id }}</dd></div>
          <div v-if="results.transaction"><dt>شماره تراکنش</dt><dd>{{ results.transaction.id || 'ثبت شده' }}</dd></div>
          <div><dt>نیروی اجرایی</dt><dd>{{ expertName }}</dd></div>
          <div><dt>زمان ثبت</dt><dd>{{ formattedDate }}</dd></div>
          <div v-if="results.description"><dt>شرح</dt><dd>{{ results.description }}</dd></div>
        </dl>
      </template>
    </section>
    <OverlayButton title="بازگشت به خانه" @click="closeHandler" />
  </main>
</template>

<script>
import BaseTopBar from '@/components/Topbar/BaseTopbar.vue';
import OverlayButton from '@/components/Button/overlayButton.vue';

export default {
  name: 'SuccessPurchaseInvoice',
  components: { BaseTopBar, OverlayButton },
  data() { return { results: null, loading: false, error: '' }; },
  computed: {
    expertName() {
      if (!this.results || !this.results.expert) return '—';
      return [this.results.expert.first_name, this.results.expert.last_name].filter(Boolean).join(' ') || 'نیروی اجرایی';
    },
    formattedDate() {
      const raw = this.results && this.results.datetime_last_change;
      if (!raw) return '—';
      try { return new Intl.DateTimeFormat('fa-IR', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(raw)); }
      catch (_) { return raw; }
    },
  },
  mounted() { this.getResult(); },
  methods: {
    async getResult() {
      this.loading = true;
      this.error = '';
      try {
        const response = await this.$ApiServiceLayer.get(
          this.$PATH.RELATIVE_PATH.GET.WALLET_RECEIPT_RETRIEVE + this.$route.params.id +
            '/?p=' + this.$STORE.state.userConfig.selectedProject,
          this.$PATH.SERVICE_NAME.WALLET
        );
        if (response.status === 200 && response.data && response.data.is_closed) this.results = response.data;
        else this.error = 'برای این فاکتور رسید پرداختی پیدا نشد. وضعیت فاکتور را بررسی کنید.';
      } catch (_) { this.error = 'دریافت رسید انجام نشد. دوباره تلاش کنید.'; }
      finally { this.loading = false; }
    },
    formatBalance(value) { return Number(value || 0).toLocaleString('fa-IR'); },
    closeHandler() { this.$router.push({ name: 'home' }).catch(() => {}); },
  },
};
</script>

<style scoped>
.receipt-page { min-height: 100vh; padding: 88px 20px 110px; background: #f7fafc; }
.receipt-card { max-width: 560px; margin: 0 auto; padding: 28px 22px; background: #fff; border: 1px solid #e4ebf1; border-radius: 24px; box-shadow: 0 16px 42px rgba(25, 64, 87, .08); text-align: center; }
.receipt-icon { width: 68px; height: 68px; display: grid; place-items: center; border-radius: 50%; margin: 0 auto 18px; font-size: 36px; font-weight: 800; }
.success-icon { color: #0b7f5b; background: #e8f7ef; }
.error-icon { color: #b42318; background: #fff0ed; }
h1 { font-size: 21px; color: #18364d; line-height: 1.5; }
.receipt-lead { margin-top: 8px; color: #60788a; }
.receipt-amount { margin: 26px 0; padding: 20px; display: grid; gap: 8px; border-radius: 18px; background: #eef8f5; color: #0b624b; }
.receipt-amount strong { font-size: 27px; }
.receipt-amount small { font-size: 15px; }
.receipt-details { margin: 0; text-align: right; }
.receipt-details div { display: flex; justify-content: space-between; gap: 16px; padding: 14px 0; border-bottom: 1px solid #edf1f4; }
.receipt-details dt { color: #657b89; flex: none; }
.receipt-details dd { margin: 0; color: #18364d; overflow-wrap: anywhere; text-align: left; }
.ltr { direction: ltr; }
.retry-button { margin-top: 18px; padding: 10px 20px; border-radius: 12px; background: #e9f3fc; color: #1964aa; }
</style>
