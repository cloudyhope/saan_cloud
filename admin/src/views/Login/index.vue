<template>
  <div class="login-container">
    <div class="content-wrapper">
      <section class="login-form" aria-labelledby="login-title">
        <img :src="$PATH.GET_IMAGE_PATH('logo.svg')" alt="سان" class="login-logo" />
        <span class="login-eyebrow">پنل مدیریت سان</span>
        <h1 id="login-title">ورود به بهسان آریان</h1>
        <p class="login-description">برای ادامه، وارد حساب کاربری خود شوید.</p>
        <div class="login-tabs" aria-label="روش ورود">
          <button type="button" :class="{ active: activeTab === 'mobile' }" :aria-pressed="activeTab === 'mobile'" @click="switchTab('mobile')" :disabled="loading">رمز یک‌بارمصرف</button>
          <button type="button" :class="{ active: activeTab === 'password' }" :aria-pressed="activeTab === 'password'" @click="switchTab('password')" :disabled="loading">رمز عبور</button>
        </div>
        <form @submit.prevent="submit">
          <label for="login-phone">شماره تلفن همراه</label>
          <input id="login-phone" v-model="userPhoneNumber" type="tel" inputmode="numeric" autocomplete="username" placeholder="۰۹۱۲۳۴۵۶۷۸۹" :disabled="loading" dir="ltr" />
          <template v-if="activeTab === 'password'">
            <label for="login-password">رمز عبور</label>
            <input id="login-password" v-model="userPassword" type="password" autocomplete="current-password" :disabled="loading" />
          </template>
          <p v-if="errorMessage" class="login-error" role="alert">{{ errorMessage }}</p>
          <button class="submit-btn" type="submit" :disabled="disabled" :aria-busy="loading">
            <span v-if="!loading">{{ activeTab === 'mobile' ? 'دریافت کد ورود' : 'ورود به پنل' }}</span>
            <span v-else><span class="spinner-border spinner-border-sm" aria-hidden="true"></span> در حال بررسی…</span>
          </button>
        </form>
        <p class="login-help" v-if="activeTab === 'mobile'">کد ورود به شماره تلفن همراه شما ارسال می‌شود.</p>
      </section>
      <div class="login-image"><img :src="$PATH.GET_IMAGE_PATH('login-img.webp')" alt="" /></div>
    </div>
  </div>
</template>
<script>
export default {
  data() {
    return { userPhoneNumber: '', userPassword: '', loading: false, activeTab: this.$route.name === 'password' ? 'password' : 'mobile', errorMessage: '' };
  },
  computed: {
    disabled() { return this.loading || !/^0?9[0-9]{9}$/.test(this.userPhoneNumber) || (this.activeTab === 'password' && !this.userPassword); },
  },
  watch: {
    userPhoneNumber(value) {
      const normalized = value.replace(/[۰-۹]/g, d => '۰۱۲۳۴۵۶۷۸۹'.indexOf(d)).replace(/[٠-٩]/g, d => '٠١٢٣٤٥٦٧٨٩'.indexOf(d)).replace(/\D/g, '').slice(0, 11);
      if (value !== normalized) this.userPhoneNumber = normalized;
      this.errorMessage = '';
    },
  },
  methods: {
    switchTab(tab) { this.activeTab = tab; this.userPassword = ''; this.errorMessage = ''; },
    submit() { if (!this.disabled) return this.activeTab === 'mobile' ? this.submitPhone() : this.passwordLogin(); },
    async passwordLogin() {
      if (this.disabled) return;
      this.loading = true; this.errorMessage = '';
      try {
        const res = await this.$ApiServiceLayer.post(this.$PATH.RELATIVE_PATH.POST.PASSWORD_AUTH, '/api', { username: this.userPhoneNumber, password: this.userPassword }, {}, false);
        if (res.status === 200) {
          this.$STORE.commit('userConfig/setAccessToken', 'Bearer ' + res.data.access);
          this.$STORE.commit('userConfig/setRefreshToken', res.data.refresh);
          this.$STORE.commit('userConfig/setProjectInfo', null);
          this.$router.push({ name: 'projects' });
        } else this.errorMessage = res.status === 0 ? 'ارتباط با سرور برقرار نشد. دوباره تلاش کنید.' : 'ورود انجام نشد. شماره همراه و رمز عبور را بررسی کنید.';
      } finally { this.loading = false; }
    },
    async submitPhone() {
      if (this.disabled) return;
      this.loading = true; this.errorMessage = '';
      try {
        const res = await this.$ApiServiceLayer.post(this.$PATH.RELATIVE_PATH.POST.PHONE_NUMBER_OTP_REQ, this.$PATH.SERVICE_NAME.AUTH, { phone_number: this.userPhoneNumber }, {}, false);
        if (res.status === 201) {
          this.$STORE.commit('userConfig/setOtpId', res.data.id);
          this.$STORE.commit('userConfig/setLoginTempToken', res.data.verification_token);
          this.$STORE.commit('userConfig/setUserPhoneNumber', this.userPhoneNumber);
          this.$STORE.commit('userConfig/setProjectInfo', null);
          this.$router.push({ name: 'verify' });
        } else this.errorMessage = 'دریافت کد انجام نشد. لطفاً دوباره تلاش کنید.';
      } finally { this.loading = false; }
    },
  },
};
</script>
<style scoped>
.login-container { min-height: 100vh; min-height: 100dvh; padding: 32px; display: grid; place-items: center; background: var(--admin-bg); }
.content-wrapper { display: flex; max-width: 960px; width: 100%; background: #fff; border: 1px solid var(--admin-border); border-radius: 20px; overflow: hidden; box-shadow: var(--admin-shadow); }
.login-form { flex: 1; padding: 48px; min-width: 0; }
.login-logo { width: 112px; height: 52px; object-fit: contain; display: block; margin-bottom: 24px; }
.login-eyebrow { display: block; color: var(--admin-muted); font-size: 12px; margin-bottom: 8px; }
h1 { font-size: 23px; font-weight: 700; color: var(--admin-text); margin-bottom: 12px; line-height: 1.6; }
.login-description { color: var(--admin-muted); font-size: 13px; margin-bottom: 28px; }
.login-tabs { display: flex; padding: 4px; background: #f1f5f9; border-radius: 10px; gap: 4px; margin-bottom: 24px; }
.login-tabs button { flex: 1; min-height: 44px; font-size: 12px; border: 0; border-radius: 7px; color: #475569; background: transparent; }
.login-tabs .active { background: #fff; color: var(--admin-primary); box-shadow: 0 1px 4px rgba(15,23,42,.08); font-weight: 700; }
label { display: block; font-size: 12px; margin: 0 0 8px; color: #475569; }
input { width: 100%; min-height: 48px; padding: 12px 14px; border: 1px solid #cbd5e1; border-radius: 8px; color: var(--admin-text); margin-bottom: 20px; background: #fff; }
input::placeholder { color: #94a3b8; } input:focus { border-color: var(--admin-primary); }
.submit-btn { width: 100%; min-height: 48px; border: 0; border-radius: 8px; background: var(--admin-primary); color: #fff; font-weight: 700; font-size: 13px; }
.submit-btn:hover:not(:disabled) { background: #1e528d; } .submit-btn:disabled { opacity: .5; }
.login-help { margin: 16px 0 0; color: var(--admin-muted); font-size: 11px; }
.login-error { color: var(--admin-danger); background: #fff1f2; border-radius: 8px; padding: 12px; font-size: 12px; margin-bottom: 16px; }
.login-image { width: 44%; background: #edf4fc; display: flex; }
.login-image img { width: 100%; height: 100%; object-fit: cover; }
@media (max-width: 767px) { .login-container { padding: 16px; } .login-form { padding: 28px 24px; } .login-image { display: none; } h1 { font-size: 20px; } }
</style>

<style scoped>
.logo-container img, .login-logo, .logo { filter: brightness(0) saturate(100%) opacity(.75); }
</style>
