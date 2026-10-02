<template>
  <div class="verify-container">
    <v-card class="login">
      <div class="d-flex justify-center">
        <img class="logo" src="../../assets/images/Login/GroupF.svg" alt="" />
      </div>
      <div class="verify-box">
        <span class="text d-flex justify-center"> تایید کد ورود </span>
        <p class="mb-0">
          کد تایید به شماره
          <span class="text-number">{{ phoneNumber }}</span>
          ارسال شده است.
        </p>
        <!-- <span class="error-warning">{{ warning }}</span> -->
        <div class="fake-input-container">
          <input
            inputmode="decimal"
            type="text"
            class="phone-input"
            v-model="codeOtp"
            maxlength="5"
            @keyup.enter="submitOTP"
            @input="checkVerify"
            autofocus
          />
          <div class="fake-item" :class="{ activeFake: fakeInput[4] }">
            {{ fakeInput[4] }}
          </div>
          <div class="fake-item" :class="{ activeFake: fakeInput[3] }">
            {{ fakeInput[3] }}
          </div>
          <div class="fake-item" :class="{ activeFake: fakeInput[2] }">
            {{ fakeInput[2] }}
          </div>
          <div class="fake-item" :class="{ activeFake: fakeInput[1] }">
            {{ fakeInput[1] }}
          </div>
          <div
            class="fake-item activeFake"
            :class="{ activeFake: fakeInput[0] }"
          >
            {{ fakeInput[0] }}
          </div>
        </div>
        <!-- <button :class="{ button: button }" :disabled="disabled">
              تایید
            </button> -->
        <span class="mt-6">ارسال مجدد کد تا {{ timerCount }} ثانیه</span>
        <div @click="editNumber" class="edit-phone">ویرایش شماره همراه</div>
      </div>
      <v-snackbar v-model="snackbar" :timeout="timeout" color="red">
        {{ errorMessage }}
      </v-snackbar>
    </v-card>
    <OverlayButton
      :disabled="resendCode"
      :class="{ button: button }"
      title="ارسال مجدد کد"
      :loading="loading"
      @click="resendCodeClick"
    />
  </div>
</template>

<script>
import OverlayButton from "../../components/Button/overlayButton.vue";
import { enterSession } from '@/utils/fieldSession';

export default {
  components: {
    OverlayButton,
  },
  data() {
    return {
      codeOtp: "",
      loading: false,
      isFocused: false,
      button: false,
      // warning: "",
      timerCount: 30,
      resendCode: true,
      snackbar: false,
      errorMessage: '',
      timerHandle: null,
      timeout: 3000,
    };
  },
  computed: {
    // disabled() {
    //   if (this.codeOtp && this.codeOtp.length === 5) {
    //     this.button = false;
    //     return false;
    //   } else {
    //     this.button = true;
    //     return true;
    //   }
    // },
    phoneNumber() {
      return this.$STORE.state.userConfig.userPhoneNumber;
    },
    fakeInput() {
      return this.codeOtp;
    },
  },
  methods: {
    async resendCodeClick() {
      if (this.loading || this.resendCode) return;
      this.loading = true;
      try {
      const res = await this.$ApiServiceLayer.auth_post(
        this.$PATH.RELATIVE_PATH.POST.PHONE_NUMBER_OTP_REQ,
        this.$PATH.SERVICE_NAME.AUTH,
        { phone_number: this.phoneNumber }
      );
      if (res.status === 201) {
        this.$STORE.commit("userConfig/setOtpId", res.data.id);
        this.$STORE.commit(
          "userConfig/setLoginTempToken",
          res.data.verification_token
        );
        this.timerCount = 30;
        this.resendCode = true;
      }
      else {
        this.errorMessage = res.status === 429 ? 'کمی بعد دوباره درخواست کنید.' : 'ارسال مجدد انجام نشد.';
        this.snackbar = true;
      }
      } finally { this.loading = false; }
    },
    checkVerify() {
      this.codeOtp = this.codeOtp.replace(/\D/g, '').slice(0, 5);
      if (this.codeOtp.length == 5) {
        this.submitOTP();
      }
    },
    async submitOTP() {
      if (this.loading || this.codeOtp.length !== 5) return;
      this.loading = true;
      try {
      const res = await this.$ApiServiceLayer.auth_post(
        this.$PATH.RELATIVE_PATH.POST.OTP_VERIFY,
        this.$PATH.SERVICE_NAME.AUTH,
        {
          code: this.codeOtp,
          verification_token: this.$STORE.state.userConfig.loginTempToken,
          id: this.$STORE.state.userConfig.otpId,
          phone_number: this.$STORE.state.userConfig.userPhoneNumber,
        }
      );
      if (res.status === 200) {
        this.$STORE.commit(
          "userConfig/setAccessToken",
          "Bearer " + res.data.tokens.access
        );
        this.$STORE.commit(
          "userConfig/setRefreshToken",
          res.data.tokens.refresh
        );
        this.$STORE.commit("userConfig/clearLoginToken");
        const route = await enterSession(this.$ApiServiceLayer);
        await this.$router.push({ name: route });
        // this.$router.push({ name: "tasks" });
      } else {
        this.errorMessage = res.status === 419 ? 'کد منقضی شده است. کد تازه‌ای درخواست کنید.' : 'کد وارد شده معتبر نیست.';
        this.snackbar = true;
        this.loading = false;
      }
      // if ( res.data.code === 406) {
      //   this.warning = "کد ورود اشتباه است";
      //   this.codeOtp = "";
      //   this.loading = false;
      // }
      } catch (error) { this.errorMessage = 'تأیید کد انجام نشد. دوباره تلاش کنید.'; this.snackbar = true; }
      finally { this.loading = false; }
    },
    editNumber() {
      this.$router.push({ name: "login" });
    },
  },
  mounted() {
    this.timerHandle = setInterval(() => {
      if (this.timerCount > 0) this.timerCount -= 1;
      if (this.timerCount === 0) this.resendCode = false;
    }, 1000);
  },
  beforeDestroy() {
    clearInterval(this.timerHandle);
  },
};
</script>

<style lang="scss" scoped>
button {
  height: 48px;
  color: #000;
  border: none;
  border-radius: 4px;
  background: #f6df4b;
  margin-bottom: 24px;
  font-size: 14px;
  font-weight: 700;
  width: 100%;
  &:disabled {
    background: #c4c4c4;
  }
}
.verify-container {
  height: 80%;
  display: flex;
  align-items: center;
  .fake-input-container {
    width: 100%;
    background-color: #fff;
    position: relative;
    margin-top: 32px;
    display: flex;
    justify-content: center;
    margin: 0 10px;
    .fake-item {
      margin: 10px 5px;
      border: 1px solid #c4c4c4;
      height: 48px;
      width: 48px;
      display: flex;
      justify-content: center;
      align-items: center;
    }
    .activeFake {
      border: 2px solid #000;
    }
    .phone-input {
      position: absolute;
      height: 100%;
      top: 0;
      left: 0;
      border-radius: 4px;
      border: none;
      text-indent: 10px;
      width: 100%;
      opacity: 0;
      z-index: 2222;

      &:focus {
        outline: none;
      }
    }
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

    .logo {
      margin-bottom: 40px;
    }
    // .error-warning {
    //   color: #d20032;
    //   font-weight: 700;
    // }
    .verify-box {
      display: flex;
      flex-direction: column;
      align-items: center;
      background: #fff;
      .text-number {
        font-size: 12px;
      }
      .input-container {
        display: flex;
        flex-direction: row;
      }

      .edit-phone {
        color: #357ae1;
        margin-top: 16px;
        cursor: pointer;
      }
    }
    .text {
      font-size: 18px;
      font-weight: 700;
      margin-bottom: 24px;
    }
    .fake-item {
      border: 1px solid #c4c4c4;
      height: 48px;
      width: 48px;
      display: flex;
      justify-content: center;
      align-items: center;
      margin: 24px 5px;
      border-radius: 8px;
    }
  }
}
</style>
