<template>
    <div class="containers">
      <v-card class="login">
        <div class="d-flex justify-center">
          <img src="../../assets/images/Login/GroupF.svg" alt="" />
        </div>
        <div class="login-box">
          <span class="d-flex justify-center login-title">ورود</span>
          <span class="text-number">با شماره همراه و رمز عبور وارد حساب شوید.</span>
          <Materialnput
            label="شماره همراه"
            v-model="userPhoneNumber"
            inputType="number"
          />
          <Materialnput
            label="رمزعبور"
            v-model="userPassword"
            inputType="password"
          />
          <div class="rules">
            <span class="condition" @click="otpAuth">ورود با رمز یک‌بار مصرف ></span>
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
          @click="passwordLogin"
          :disabled="disabled"
          :class="{ button: disabled }"
          title="ورود"
          :loading="loading"
        />
    </div>
  </template>
  <script>
  import Materialnput from "../../components/MaterialInput/indx.vue";
  import OverlayButton from "../../components/Button/overlayButton.vue";
  import { enterSession } from '@/utils/fieldSession';
  
  export default {
    components: {
      Materialnput,
      OverlayButton,
    },
    data() {
      return {
        userPhoneNumber: "",
        userPassword: "",
        loading: false,
        snackbar: false,
        timeout: 3000,
        errorMessage: "ورود انجام نشد. اطلاعات ورود را بررسی کنید.",
      };
    },
    computed: {
      disabled() {
        if (this.loading || !this.userPassword || this.userPhoneNumber === "" || this.userPhoneNumber.length < 11) {
          return true;
        } else {
          return false;
        }
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
      async passwordLogin() {
        if (this.disabled) return;
        this.loading = true;
        try {
          const res = await this.$ApiServiceLayer.auth_post(
            this.$PATH.RELATIVE_PATH.POST.PASSWORD_AUTH,
            "api",
            { username: this.userPhoneNumber, password: this.userPassword }
          );
          if (!res || res.status !== 200) {
            this.errorMessage = res && [400, 401].includes(res.status)
              ? "اطلاعات ورود صحیح نیست یا حساب شما فعال نیست."
              : "ارتباط با سرور برقرار نشد. دوباره تلاش کنید.";
            this.snackbar = true;
            return;
          }

          this.$STORE.commit("userConfig/setAccessToken", "Bearer " + res.data.access);
          this.$STORE.commit('userConfig/setRefreshToken', res.data.refresh);
          const route = await enterSession(this.$ApiServiceLayer);
          await this.$router.push({ name: route });
        } catch (error) {
          this.$STORE.commit("userConfig/clearAllConfigs");
          this.errorMessage = "ورود انجام نشد. ارتباط با سرور را بررسی کنید.";
          this.snackbar = true;
        } finally {
          this.loading = false;
        }
      },
      otpAuth() {
        this.$router.push({ name: "login" });
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
  .login {
    display: flex;
    flex-direction: column;
    width: 100%;
    margin: 24px;
    overflow: hidden !important;
    padding: 40px 0;
    border-radius: 8px;
    box-shadow: 0px 4px 4px rgba(214, 214, 214, 0.6) !important;
  
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
