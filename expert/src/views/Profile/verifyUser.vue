<template>
  <div>
    <Topbar title="سوالات" />
    <div class="containers">
      <input
        placeholder="کد ملی"
        type="number"
        class="input__styles"
        v-model="nationalCode"
      />
      <input
        placeholder="شماره تماس"
        type="number"
        class="input__styles"
        v-model="phoneNumber"
      />
      <div class="input-container">
        <input
          placeholder="شماره شبا"
          type="number"
          class="input__styles_sheba"
          v-model="shebaNumber"
        />
        <span class="prefix">IR</span>
      </div>
      <date-picker
        placeholder="انتخاب تاریخ تولد"
        color="#357AE1"
        v-model="dateOfBirth"
        format="jYYYY/jMM/jDD"
        display-format="jYYYY/jMM/jD"
      />
    </div>
    <OverlayButton
      :disabled="disableSubmitButton"
      title="ثبت"
      @click="submitHandler"
      :loading="loading"
    />

    <v-snackbar :color="snackbarColor" v-model="responseAlert" :timeout="timeout">
      <span>{{ response }}</span>
    </v-snackbar>
  </div>
</template>
<script>
import Topbar from "../../components/Topbar/backTopBar.vue";
import Button from "../../components/Button/Button.vue";
import OverlayButton from "../../components/Button/overlayButton.vue";
import VuePersianDatetimePicker from "vue-persian-datetime-picker";

export default {
  name: "Profile",
  components: {
    Topbar,
    Button,
    OverlayButton,
    // FullLoading,
    datePicker: VuePersianDatetimePicker,
  },
  data() {
    return {
      nationalCode: "",
      phoneNumber: "",
      shebaNumber: "",
      dateOfBirth: "",
      loading: false,
      responseAlert: false,
      timeout: 2000,
      response: "",
      snackbarColor:'#CACACA'
    };
  },
  computed: {
    disableSubmitButton() {
      if (
        this.nationalCode === "" ||
        this.nationalCode === null ||
        this.phoneNumber === "" ||
        this.phoneNumber === null ||
        this.shebaNumber === null ||
        this.shebaNumber === "" ||
        this.dateOfBirth === ""
      ) {
        return true;
      } else {
        return false;
      }
    },
  },
  mounted() {},
  methods: {
    async submitHandler() {
      this.loading = true;
      const data = {
        phone_number: this.phoneNumber,
        national_id: this.nationalCode,
        birth_date: this.dateOfBirth,
        sheba_number: "IR" + this.shebaNumber,
        survey_fillout: this.$route.params.id,
      };
      const res = await this.$ApiServiceLayer.post(
        this.$PATH.RELATIVE_PATH.POST.PERSONAL_INFO_VALIDATE,
        this.$PATH.SERVICE_NAME.EMPTY,
        data
      );
      if (res.status === 201) {
        this.loading = false;
        if (res.data.response === "تطابق کامل") {
          const res1 = await this.$ApiServiceLayer.patch(
            this.$PATH.RELATIVE_PATH.MULTI.PERSONAL_INFO_SET_MAIN +
              res.data.id +
              "/",
            this.$PATH.SERVICE_NAME.EMPTY,
            {
              is_main: true,
            }
          );
          if (res1.status === 200) {
            this.response = res.data.response;
            this.snackbarColor = 'green'
            this.responseAlert = true;
            setTimeout(() => {
              this.$router.push({
                name: "surveyDetail",
                params: { id: this.$route.params.id },
              });
            }, 2000);
          }
        } else {
          this.response = res.data.response;
          this.responseAlert = true;
           this.snackbarColor = 'red'
        }
      }
      this.loading = false;
    },
  },
};
</script>
<style lang="scss" scoped>
.containers {
  padding: 24px;
  margin-top: 40px;
}
</style>
<style lang="scss">
.vpd-input-group {
  box-shadow: 0px 1px 2px 0px rgba(16, 24, 40, 0.05);
  height: 44px;
  background: #fff;
  label {
    width: 50px;
    border-radius: 0 8px 8px 0;
  }
  input {
    border-radius: 8px 0 0 8px;
  }
}
.input-container {
  display: flex;
  align-items: center;
  position: relative;
}

.prefix {
  background-color: #e8e5e5;
  color: #000;
  padding: 0.5rem;
  border-top-left-radius: 8px;
  border-bottom-left-radius: 8px;
  margin-bottom: 32px;
  height: 44px;
  border: 1px solid var(--Gray-300, #d0d5dd);
  display: flex;
  align-items: center;
}

.input__styles {
  border: 1px solid var(--Gray-300, #d0d5dd);
  background: var(--Base-White, #fff);
  box-shadow: 0px 1px 2px 0px rgba(16, 24, 40, 0.05);
  width: 100%;
  height: 44px;
  text-indent: 10px;
  margin-bottom: 32px;
}
.input__styles_sheba {
  border-radius: 0 8px 8px 0;
  border: 1px solid var(--Gray-300, #d0d5dd);
  background: var(--Base-White, #fff);
  box-shadow: 0px 1px 2px 0px rgba(16, 24, 40, 0.05);
  width: 100%;
  height: 44px;
  text-indent: 10px;
  margin-bottom: 32px;

  direction: ltr;
}
</style>
