<template>
  <div class="containers">
    <v-card class="login">
      <div class="d-flex justify-center">
        <img class="logo" src="../../assets/images/Login/GroupF.svg" alt="" />
      </div>
      <div class="login-box">
        <span class="d-flex justify-center login-title">ورود</span>
        <span class="text-number"> شماره همراه خود را برای دریافت کد وارد کنید.</span>
        <Materialnput
          label="شماره همراه"
          v-model="userPhoneNumber"
          inputType="number"
        />
        <!-- <div class="rules">
          مشاهده
          <span class="condition" @click="rules">راهنمای استفاده</span> از
          اپلیکیشن
        </div> -->
        <div class="rules">
          <span class="condition" @click="passwordAuth">ورود با رمزعبور ></span>
        </div>
      </div>
      <v-snackbar
      v-model="snackbar"
      :timeout="timeout"
      color="red"
    >
    {{ errorMessage }}
    </v-snackbar>
     
    </v-card>
    <OverlayButton
        @click="submitPhone"
        :disabled="disabled"
        :class="{ button: disabled }"
        title="دریافت کد"
        :loading="loading"
      />
  </div>
</template>
<script>
import Materialnput from "../../components/MaterialInput/indx.vue";
import OverlayButton from "../../components/Button/overlayButton.vue";

export default {
  components: {
    Materialnput,
    OverlayButton,
  },
  data() {
    return {
      userPhoneNumber: "",
      loading: false,
      snackbar: false,
      errorMessage: '',
      timeout: 3000,
    };
  },
  computed: {
    disabled() {
      return !/^09\d{9}$/.test(this.userPhoneNumber) || this.loading;
    },
  },
  mounted() {
    //   ("asdfadsfsdgfs");
    // history.pushState(null, null, location.href);
    // window.onpopstate = function () {
    //   history.go(1);
    // };
  },
  methods: {
    async submitPhone() {
      if (this.disabled) return;
      this.loading = true;
      try {
        const res = await this.$ApiServiceLayer.auth_post(
          this.$PATH.RELATIVE_PATH.POST.PHONE_NUMBER_OTP_REQ,
          this.$PATH.SERVICE_NAME.AUTH,
          { phone_number: this.userPhoneNumber }
        );
        if (res.status === 201) {
          this.$STORE.commit("userConfig/setOtpId", res.data.id);
          this.$STORE.commit("userConfig/setLoginTempToken", res.data.verification_token);
          this.$STORE.commit("userConfig/setUserPhoneNumber", this.userPhoneNumber);
          await this.$router.push({ name: "verify" });
          return;
        }
        this.errorMessage = res.status === 429
          ? 'درخواست کد زیاد بوده است. کمی بعد دوباره تلاش کنید.'
          : res.status === 400
            ? 'شماره شما به عنوان کاربر سان‌اپ ثبت نشده است. با مدیر پروژه تماس بگیرید.'
            : (res.data && res.data.detail) || 'دریافت کد انجام نشد. دوباره تلاش کنید.';
        this.snackbar = true;
      } catch (_) {
        this.errorMessage = 'دریافت کد انجام نشد. دوباره تلاش کنید.';
        this.snackbar = true;
      } finally {
        this.loading = false;
      }
    },
    passwordAuth() {
      this.$router.push({ name: "password-login" });
    },
  },
};
</script>

<style lang="scss" scoped>
.containers {
 
  height: 80%;
  display: flex;
  align-items: center;
}
.logo {
  width: 100px;
}
.login {
  display: flex;
  flex-direction: column;
  width: 100%;
  margin: 24px;
  overflow: hidden !important;
  padding: 40px 0;
  border-radius: 8px;
  box-shadow: 0px 0px 3px 0px rgba(16, 24, 40, 0.1) !important;


  .text {
    font-size: 18px;
    margin-top: 30px;
  }
  .login-box {
    color: #404041;
    display: flex;
    flex-direction: column;
    background: #fff;
    padding: 40px 24px 0 24px;
    .login-title {
      font-weight: 700;
      font-size: 18px;
      margin-bottom: 24px;
    }
    .phone-input {
      width: 100%;
      height: 50px;
      border: 1px solid #c4c4c4;
      background-color: #fff;
      border-radius: 4px;
      margin: 24px;
      text-indent: 10px;
      &:focus {
        outline: none;
      }
    }
    ::placeholder {
      font-size: 14px;
    }
    .text-number {
      font-size: 12px;
    }
    .rules {
      font-weight: 700;
      .condition {
        color: #357AE1;
        cursor: pointer;
      }
    }
  }
}
</style>
