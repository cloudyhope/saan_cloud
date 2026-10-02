<template>
    <div>
      <BaseTopBar title="اطلاعات شخصی"/>
      <v-card class="detail" elevation="0">
        <VutifyInput label="نام" v-model="model.extended.first_name" />
        <VutifyInput label="نام خانوادگی" v-model="model.extended.last_name" />
        <VutifyInput  label="کدملی" v-model="model.extended.national_code" />
        <VutifyInput label="شغل" v-model="model.extended.job" />
        <!-- <VutifyInput label="ایمیل" v-model="model.email" /> -->
      </v-card>
      <v-card class="empty-container"> </v-card>
      <OverlayButton
        @click="savePersonalInfo"
        :disabled="enablePersonal"
        class="save-info"
        title="ذخیره"
        :loading="loading"
      />
      <v-snackbar
        width="100%"
        height="80px"
        :color="snackbarColor"
        v-model="warningSnackbar"
      >
        {{ snackBarText }}
      </v-snackbar>
    </div>
  </template>
  <script>
  import VutifyInput from "@/components/VutifyInput/index.vue";
  import OverlayButton from "../../components/Button/overlayButton.vue";
  import BaseTopBar from "@/components/Topbar/BaseTopbar.vue";
  
  export default {
    name: "Profile",
    components: {
        BaseTopBar,
      VutifyInput,
      OverlayButton,
  
    },
    data() {
      return {
        noProfile: false,
        loading: false,
        warningSnackbar: false,
        snackBarText: "",
        snackbarColor: "",
        model: {
          extended :{
            first_name: null,
            last_name: null,
            national_code: null,
            job: null,
  
          }
        },
      };
    },
    computed: {
      enablePersonal() {
        if (
          this.model.extended.first_name === "" ||
          this.model.extended.first_name === null ||
          this.model.extended.last_name === "" ||
          this.model.extended.last_name === null ||
          this.model.extended.national_code === "" ||
          this.model.extended.national_code === null ||
          this.model.extended.job === "" ||
          this.model.extended.job === null
  
        ) {
          return true;
        } else {
          return false;
        }
      },
    },
    created() {
      this.getProfileInfo();
    },
    methods: {
      async getProfileInfo() {
        const res = await this.$ApiServiceLayer.get(
          this.$PATH.RELATIVE_PATH.MULTI.STORE_SETTING,
          ""
        );
        if (res.status === 200) {
          this.model = res.data[0];
        }
      },
      async savePersonalInfo() {
        const data = {
          first_name: this.model.extended.first_name,
          last_name: this.model.extended.last_name,
          national_code: this.model.extended.national_code,
          job: this.model.extended.job,
        }
        const res = await this.$ApiServiceLayer.post(
          this.$PATH.RELATIVE_PATH.MULTI.STORE_SETTING,
          "",
          data
        );
        console.log(res)
        if (res.status === 201) {
          this.$router.push({ name: "setting" });
          this.getProfileInfo();
        }
      },
    },
  };
  </script>
  
  <style scoped>
  .detail {
    z-index: 0;
    margin: 24px;
  
    border-radius: 4px;
    padding: 16px 12px;
  }
  
  .empty-container {
    height: 70px;
    box-shadow: none !important;
    background: none !important;
  }
  
  </style>
  