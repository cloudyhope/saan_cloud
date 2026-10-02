<template>
  <main class="wallet-page" dir="rtl">
    <BaseTopBar title="کیف پول" />
    <section class="wallet-hero">
      <span class="wallet-eyebrow">حساب شما</span>
      <h1>کیف پول سان اپ</h1>
      <p>مانده‌های ثبت‌شده و پرداخت فاکتورهای خدمات را اینجا دنبال کنید.</p>
      <button type="button" class="scan-action" @click="scanQrCodeHandler"><v-icon size="23" color="#124467">mdi-qrcode-scan</v-icon><span>اسکن کد فاکتور</span><v-icon size="19" color="#124467">mdi-arrow-left</v-icon></button>
    </section>

    <section class="wallet-balances" aria-labelledby="balance-heading">
      <div class="wallet-section-head"><div><span>نمای مالی</span><h2 id="balance-heading">مانده کیف پول</h2></div><button type="button" :disabled="loading" aria-label="به‌روزرسانی مانده" @click="loadBalances"><v-icon>mdi-refresh</v-icon></button></div>
      <div v-if="loading" class="wallet-state" role="status"><v-progress-circular indeterminate color="primary" size="26" /> در حال دریافت مانده…</div>
      <div v-else-if="error" class="wallet-state wallet-error" role="alert">{{ error }} <button type="button" @click="loadBalances">تلاش دوباره</button></div>
      <div v-else-if="!balances.length" class="wallet-state">هنوز مانده‌ای برای این حساب ثبت نشده است.</div>
      <div v-else class="balance-list"><div v-for="balance in balances" :key="balance.key" class="balance-card"><span class="balance-symbol"><v-icon color="#176f63">mdi-wallet-outline</v-icon></span><div><strong>{{ balance.label }}</strong><small>{{ balance.walletName }}</small></div><b>{{ formatAmount(balance.amount) }} <small>ریال</small></b></div></div>
    </section>
  </main>
</template>

<script>
import BaseTopBar from '@/components/Topbar/BaseTopbar.vue';

export default {
  name: 'ClientWallet',
  components: { BaseTopBar },
  data() { return { wallets: [], loading: false, error: '', sequence: 0 }; },
  computed: {
    project() { return this.$STORE.state.userConfig.selectedProject; },
    balances() {
      const rows = [];
      this.wallets.forEach((wallet, walletIndex) => {
        (wallet.balances || []).forEach((item, balanceIndex) => {
          if (!item.currency || item.currency.abbreviation !== 'IRR') return;
          rows.push({ key: `${walletIndex}-${balanceIndex}`, amount: item.balance || 0,
            label: (item.layer && (item.layer.verbose_name || item.layer.title)) || 'مانده ثبت‌شده',
            walletName: (wallet.type && (wallet.type.name_fa || wallet.type.name_en)) || 'کیف پول' });
        });
      });
      return rows;
    },
  },
  mounted() { this.loadBalances(); },
  beforeDestroy() { this.sequence += 1; },
  watch: {
    project() {
      this.sequence += 1;
      this.wallets = []; this.loading = false; this.error = '';
      this.loadBalances();
    },
  },
  methods: {
    async loadBalances() {
      if (!this.project || this.loading) return;
      const project = this.project;
      const sequence = ++this.sequence;
      this.loading = true;
      this.error = '';
      try {
        const response = await this.$ApiServiceLayer.get(
          this.$PATH.RELATIVE_PATH.GET.WALLET_SIGNATURE + '?p=' + project,
          this.$PATH.SERVICE_NAME.EMPTY
        );
        if (sequence !== this.sequence || project !== this.project) return;
        if (response.status === 200) this.wallets = Array.isArray(response.data.wallets) ? response.data.wallets : [];
        else this.error = response.status === 403 ? 'نمایش مانده برای حساب شما فعال نیست.' : 'دریافت مانده انجام نشد.';
      } catch (_) { if (sequence === this.sequence && project === this.project) this.error = 'ارتباط برقرار نشد. دوباره تلاش کنید.'; }
      finally { if (sequence === this.sequence && project === this.project) this.loading = false; }
    },
    scanQrCodeHandler() { this.$router.push({ name: 'qrCodeScanner' }).catch(() => {}); },
    formatAmount(value) { return Number(value || 0).toLocaleString('fa-IR'); },
  },
};
</script>

<style scoped>
.wallet-page { min-height: 100vh; background: #f5f8fb; padding-bottom: calc(110px + env(safe-area-inset-bottom)); color: #17364c; }
.wallet-hero { margin: 0 17px; padding: 23px 20px; border-radius: 22px; background: linear-gradient(135deg,#123650,#246c86); box-shadow: 0 12px 30px #123b5422; color: #fff; }
.wallet-eyebrow { font-size: 12px; color: #bbe4e9; }
.wallet-hero h1 { margin: 5px 0 6px; color: #fff; font-size: 22px; }
.wallet-hero p { margin: 0 0 21px; color: #e0f0f4; font-size: 13px; line-height: 1.75; }
.scan-action { display: flex; align-items: center; gap: 10px; width: 100%; min-height: 50px; padding: 10px 14px; border-radius: 13px; background: #d6f2bd; color: #124467; font-weight: 800; }
.scan-action span { flex: 1; text-align: right; }
.wallet-balances { padding: 30px 17px; }
.wallet-section-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.wallet-section-head span { font-size: 12px; color: #2b7486; }
.wallet-section-head h2 { margin: 3px 0 0; font-size: 18px; }
.wallet-section-head button { width: 44px; height: 44px; border-radius: 13px; border: 1px solid #dce8ee; background: #fff; }
.wallet-state { padding: 23px; border: 1px dashed #cadae3; border-radius: 16px; background: #fff; color: #5c7384; line-height: 1.8; }
.wallet-error { color: #a32922; border-color: #edcbc6; }
.wallet-error button { display: block; color: #246c9d; margin-top: 10px; }
.balance-list { display: grid; gap: 11px; }
.balance-card { display: flex; flex-wrap: wrap; align-items: center; gap: 10px; padding: 16px; background: #fff; border: 1px solid #e1eaf0; border-radius: 17px; }
.balance-symbol { display: grid; place-items: center; width: 42px; height: 42px; border-radius: 12px; background: #e6f5ed; }
.balance-card div { display: grid; gap: 2px; flex: 1; min-width: 90px; }
.balance-card strong { font-size: 13px; }
.balance-card small { color: #688092; font-size: 11px; }
.balance-card b { font-size: 17px; white-space: nowrap; color: #145e53; }
.balance-card b small { font-size: 11px; }
.scan-action:focus-visible,.wallet-section-head button:focus-visible,.wallet-error button:focus-visible { outline: 3px solid #42a3bf; outline-offset: 3px; }
</style>
