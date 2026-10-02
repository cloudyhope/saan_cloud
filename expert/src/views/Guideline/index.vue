<template>
  <div>
    <BaseTopBar title="راهنمای استفاده"  />

    <div class="guide-line-container">
      <Skeleton v-if="initialLoading" type="list" :count="3" two-line />

      <v-card v-else-if="guidelineLists.length === 0" class="empty-state">
        <v-img max-width="128" src="@/assets/images/Icons/Empty-guide.svg" />
        <span class="guide-line-epty-state-text"
          >فایل آموزشی برای پروژه شما در دسترس نمی باشد.</span
        >
      </v-card>
      <template v-else>
      <v-card
        v-for="guide in guidelineLists"
        @click="downloadFile(guide.file)"
        :key="guide.id"
        class="cards"
      >
        <div class="d-flex">
          <div class="icon-container">
            <v-img
              max-width="36"
              :src="guide.icon"
              class="icon-img"
            />
          </div>
          <div class="d-flex flex-column justify-center">
            <div class="title-text">{{ guide.name }}</div>
            <span class="desc-text">{{ guide.description }}</span>
          </div>
        </div>
        <div class="d-flex flex-column justify-center align-center">
          <img
            class="download-icon"
            src="@/assets/images/Icons/download-icon.svg"
          />
          <span class="download-file-text">دریافت فایل</span>
          <v-snackbar v-model="snackbar" :timeout="timeout">
            {{ text }}
          </v-snackbar>
        </div>
      </v-card>
      </template>
    </div>
  </div>
</template>
<script>
// import Topbar from "../../components/Topbar/backPrps.vue";
import BaseTopBar from "../../components/Topbar/BaseTopbar.vue";
import Skeleton from "../../components/Skeleton/index.vue";
export default {
  components: {
    BaseTopBar,
    Skeleton,
  },
  data() {
    return {
      guidelineLists: [],
      initialLoading: true,
      snackbar: false,
      text: "دانلود فایل آغاز شد.",
      timeout: 2000,
    };
  },

  mounted() {
    this.getGuideline();
  },

  methods: {
    async getGuideline() {
      this.initialLoading = true;
      const res = await this.$ApiServiceLayer.get(
        this.$PATH.RELATIVE_PATH.GET.GET_GUIDELINE +
          "?p=" +
          this.$STORE.state.userConfig.selectedProject,
        this.$PATH.SERVICE_NAME.EMPTY
      );
      if (res.status === 200) {
        this.guidelineLists = res.data;
      }
      this.initialLoading = false;
    },
    downloadFile(e) {
      this.snackbar = true;
      const url = e; // Replace with your file URL

      // Create a temporary anchor element
      const link = document.createElement("a");
      link.href = url;
      link.download = "filename"; // Replace with your desired file name

      // Programmatically trigger the download
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    },
  },
};
</script>
<style lang="scss" scoped>
.guide-line-container {
  padding: 24px;
  .cards {
    display: flex;
    justify-content: space-between;
    padding: 16px;
    margin-bottom: 24px;
    box-shadow: 0px 4px 4px rgba(214, 214, 214, 0.6) !important;
    .icon-container {
      background: #eaf1fb;
      margin-left: 16px;
      padding: 14px;
      border-radius: 8px;
    }

    .title-text {
      font-weight: 700;
      font-size: 12px;
      color: #474849;
      margin-bottom: 4px;
    }
    .desc-text {
      color: #828282;
      font-size: 10px;
    }
    .download-icon {
      max-width: 14px;
      margin-bottom: 4px;
    }
    .download-file-text {
      font-size: 10px;
      color: #abb5be;
    }
  }
  .empty-state {
    display: flex;
    align-items: center;
    justify-content: center;
    flex-direction: column;
    padding: 78px;
    box-shadow: 0px 4px 4px rgba(214, 214, 214, 0.6) !important;
    .guide-line-epty-state-text {
      font-size: 18px;
    }
  }
}
</style>
