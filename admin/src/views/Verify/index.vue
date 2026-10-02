<template>
  <main class="verify-container">
    <section class="verify-card">
      <img :src="$PATH.GET_IMAGE_PATH('logo.svg')" alt="سان" class="logo" />
      <h1>تأیید شماره همراه</h1>
      <p>کد ورود به شماره <bdi>{{ phoneNumber }}</bdi> ارسال شده است.</p>
      <router-link to="/login" class="change-phone">ویرایش شماره همراه</router-link>
      <form @submit.prevent="submitOTP">
        <label for="verification-code">کد پنج‌رقمی ورود</label>
        <input id="verification-code" ref="codeInput" type="text" inputmode="numeric" autocomplete="one-time-code" maxlength="5" dir="ltr" v-model="codeOtp" :disabled="loading" />
        <p v-if="errorMessage" class="error-message" role="alert">{{ errorMessage }}</p>
        <button type="submit" class="btn btn-primary" :disabled="loading || codeOtp.length !== 5">{{ loading ? 'در حال بررسی…' : 'تأیید و ورود' }}</button>
      </form>
      <div class="resend"><span v-if="timerCount > 0">ارسال مجدد تا {{ timerCount }} ثانیه</span><button v-else type="button" @click="resendCodeClick" :disabled="loading">ارسال مجدد کد</button></div>
    </section>
  </main>
</template>
<script>
export default {
  data() { return { codeOtp: '', loading: false, timerCount: 120, errorMessage: '' }; },
  computed: { phoneNumber() { return this.$STORE.state.userConfig.userPhoneNumber; } },
  watch: {
    codeOtp(value) {
      const normalized = value.replace(/[۰-۹]/g, d => '۰۱۲۳۴۵۶۷۸۹'.indexOf(d)).replace(/[٠-٩]/g, d => '٠١٢٣٤٥٦٧٨٩'.indexOf(d)).replace(/\D/g, '').slice(0, 5);
      if (value !== normalized) this.codeOtp = normalized;
    },
  },
  mounted() { this.$refs.codeInput.focus(); this.startTimer(); },
  beforeDestroy() { clearInterval(this.countdown); },
  methods: {
    startTimer() {
      clearInterval(this.countdown);
      this.countdown = setInterval(() => { if (this.timerCount > 0) this.timerCount--; else clearInterval(this.countdown); }, 1000);
    },
    async resendCodeClick() {
      if (this.loading || this.timerCount > 0) return;
      this.loading = true; this.errorMessage = '';
      try {
        const res = await this.$ApiServiceLayer.post(this.$PATH.RELATIVE_PATH.POST.PHONE_NUMBER_OTP_REQ, this.$PATH.SERVICE_NAME.AUTH, { phone_number: this.phoneNumber }, {}, false);
        if (res.status === 201) {
          this.$STORE.commit('userConfig/setOtpId', res.data.id);
          this.$STORE.commit('userConfig/setLoginTempToken', res.data.verification_token);
          this.timerCount = 120; this.codeOtp = ''; this.startTimer();
        } else this.errorMessage = 'ارسال مجدد کد انجام نشد. دوباره تلاش کنید.';
      } finally { this.loading = false; }
    },
    async submitOTP() {
      if (this.loading || !/^[0-9]{5}$/.test(this.codeOtp)) return;
      this.loading = true; this.errorMessage = '';
      try {
        const res = await this.$ApiServiceLayer.post(this.$PATH.RELATIVE_PATH.POST.OTP_VERIFY, this.$PATH.SERVICE_NAME.AUTH, { code: this.codeOtp, verification_token: this.$STORE.state.userConfig.loginTempToken, id: this.$STORE.state.userConfig.otpId, phone_number: this.phoneNumber }, {}, false);
        if (res.status === 200 && res.data.tokens) {
          this.$STORE.commit('userConfig/setAccessToken', 'Bearer ' + res.data.tokens.access);
          this.$STORE.commit('userConfig/setRefreshToken', res.data.tokens.refresh);
          this.$STORE.commit('userConfig/setUserInfo', res.data.user);
          this.$STORE.commit('userConfig/setUserRole', res.data.role ? res.data.role.role : null);
          this.$STORE.commit('userConfig/setProjectInfo', null);
          this.$STORE.commit('userConfig/setOtpId', '');
          this.$STORE.commit('userConfig/setLoginTempToken', '');
          this.$router.push({ name: 'projects' });
        } else this.errorMessage = res.status === 0 ? 'ارتباط با سرور برقرار نشد.' : 'کد معتبر نیست یا منقضی شده است. دوباره بررسی کنید.';
      } finally { this.loading = false; }
    },
  },
};
</script>
<style scoped>
.verify-container { min-height: 100vh; min-height: 100dvh; display: grid; place-items: center; padding: 24px; background: var(--admin-bg); }
.verify-card { width: 440px; max-width: 100%; border: 1px solid var(--admin-border); border-radius: 16px; background: #fff; box-shadow: var(--admin-shadow); padding: 36px; }
.logo { width: 100px; height: 48px; margin-bottom: 24px; }
h1 { font-size: 22px; font-weight: 700; margin-bottom: 16px; } p { font-size: 13px; color: var(--admin-muted); }
.change-phone { display: inline-block; color: var(--admin-primary); font-size: 12px; padding: 8px 0; margin-bottom: 20px; }
label { display: block; font-size: 12px; margin-bottom: 8px; }
input { width: 100%; min-height: 52px; border: 1px solid #cbd5e1; border-radius: 8px; text-align: center; letter-spacing: 12px; font-size: 24px; padding: 8px; margin-bottom: 20px; }
.btn { width: 100%; } .error-message { color: var(--admin-danger); }
.resend { margin-top: 20px; text-align: center; font-size: 12px; color: var(--admin-muted); }
.resend button { border: 0; background: transparent; color: var(--admin-primary); min-height: 44px; }
@media(max-width: 767px) { .verify-card { padding: 24px; } }
</style>

<style scoped>
.logo-container img, .login-logo, .logo { filter: brightness(0) saturate(100%) opacity(.75); }
</style>
