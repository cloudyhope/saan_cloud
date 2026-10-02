<template>
  <div class="containers">
    <Skeleton v-if="initialLoading" type="list" :count="4" two-line />

    <div v-else-if="superVisorLists.length === 0">
      <v-card class="pa-12 d-flex flex-column align-center">
        <v-img
          max-width="187"
          class="empty-state-img"
          src="../../assets/images/empty-visit.svg"
        />
        <span class="empty-state-txt"
          >درحال حاضر نیرویی برای سرکشی به شما اختصاص داده نشده است</span
        >
      </v-card>
    </div>
    <div v-else class="position-fixed">
      <v-card color="#EAF2F9" class="cards">
        <div class="d-flex flex-column mb-4">
          <label class="label-title">نام پروموتر:</label>
          <select
            @change="promoterHandler"
            v-model="pickPromoter"
            class="form-select"
          >
            <option
              v-for="promoter in promoterLists"
              :value="promoter.promoter.id"
              :key="'promoter' + promoter.id"
            >
              {{ promoter.promoter.first_name }}
              {{ promoter.promoter.last_name }}
            </option>
          </select>
        </div>
        <div class="d-flex justify-space-between">
          <div
            @click="superVisiorVisitHistoryHandler"
            class="text-decoration-underline"
          >
            مشاهده اکشن پلن ها
          </div>
          <div>
            <img src="@/assets/images/Icons/left-icon.svg" />
          </div>
        </div>
      </v-card>
      <v-divider
        style="border-width: thin 0 2px 0"
        color="#D3E3FD"
        class="my-4"
      />
    </div>
    <div class="content-container">
      <v-card
        v-for="superVisor in superVisorLists"
        :key="superVisor.id"
        @click="superVisionModal(superVisor)"
        class="cards pa-5 mt-2"
      >
        <div class="d-flex justify-space-between">
          <div class="d-flex align-center">
            <div class="img-container">
              <v-img max-width="36" :src="superVisor.outlet.category.icon" />
            </div>
            <div class="contents">
              <span class="header mb-1">{{ superVisor.outlet.name }}</span>
              <div class="mb-1">
                <span class="details">کد:</span>
                <span class="font-weight-medium mr-1">{{
                  superVisor.outlet.code
                }}</span>
              </div>
              <div>
                <span class="details">نوع مشتری:</span>
                <span class="font-weight-medium mr-1">{{
                  superVisor.outlet.category.verbose_name
                }}</span>
              </div>
            </div>
          </div>
          <div class="d-flex align-center">
            <span
              v-if="superVisor.supervision_status === '0'"
              class="status invisited"
            >
              سرکشی نشده
            </span>
            <span
              v-if="superVisor.supervision_status === '1'"
              class="status inprogress"
            >
              در حال سرکشی
            </span>
          </div>
        </div>
        <v-divider class="my-4" />
        <div>
          <div>
            <span class="details">آدرس:</span>
            <span class="font-weight-medium mr-1"
              >{{ superVisor.outlet.address }}
            </span>
          </div>
        </div>
      </v-card>
      <v-bottom-sheet :retain-focus="false" max-width="576px" v-model="sheet">
        <v-sheet height="148" class="pa-5" :retain-focus="false">
          <div class="supervision-btn" @click="superVisionHandler">
            <img
              class="ml-3"
              src="../../assets/images/Icons/supervision-image.svg"
            />
            <span>انجام سرکشی</span>
          </div>
          <hr />
          <div @click="superVisionPromoterHandler" class="confirm-report">
            <img
              class="ml-3"
              src="../../assets/images/Icons/confirm-promoter-report.svg"
            />
            <span>تایید گزارش پروموتر</span>
          </div>
        </v-sheet>
      </v-bottom-sheet>
    </div>
    <button class="action__plan__btn" @click="submitActionPlanHandler">
      <v-img
        width="16"
        class="ml-2"
        src="../../assets/images/Icons/action-plus.svg"
      />

      <span>برنامه جدید</span>
    </button>
    <EmptyContainer />
  </div>
</template>
<script>
import EmptyContainer from "../../components/emptyContainer.vue";
import Skeleton from "../../components/Skeleton/index.vue";

export default {
  components: {
    EmptyContainer,
    Skeleton,
  },
  data() {
    return {
      promoterLists: [],
      counter: 0,
      flag: false,
      pickPromoter: "",
      superVisorLists: [],
      sheet: false,
      supervisionData: {},
      initialLoading: true,
    };
  },
  mounted() {
    this.fetchPromoterLists();
    this.getData();
    window.addEventListener("scroll", this.handleScroll);
  },
  beforeDestroy() {
    window.removeEventListener("scroll", this.handleScroll);
  },
  methods: {
    async fetchPromoterLists() {
      const res = await this.$ApiServiceLayer.get(
        this.$PATH.RELATIVE_PATH.MULTI.SUPERVISOR_LIST_CREATE +
          "?p=" +
          this.$STORE.state.userConfig.selectedProject +
          "&me=true",

        this.$PATH.SERVICE_NAME.AUTH,
      );
      if (res.status === 200) {
        this.promoterLists = res.data;
      }
    },
    visitHistoryHandler() {},
    submitActionPlanHandler() {
      this.$router.push({ name: "actionPlan" });
    },
    async getData() {
      this.initialLoading = true;
      const res = await this.$ApiServiceLayer.get(
        this.$PATH.RELATIVE_PATH.MULTI.SUPERVISION_VISIT_LIST +
          "?p=" +
          this.$STORE.state.userConfig.selectedProject +
          "&offset=" +
          this.counter +
          "&limit=10" +
          "&promoter=" +
          this.pickPromoter +
          "&is_deleted=false" +
          "&today=true" +
          "&ordering=-id",

        this.$PATH.SERVICE_NAME.AUTH,
      );
      if (res.status === 200) {
        this.superVisorLists = res.data.results;
        this.counter = this.superVisorLists.length;
      }
      this.initialLoading = false;
    },
    async loadMoreResults() {
      const res = await this.$ApiServiceLayer.get(
        this.$PATH.RELATIVE_PATH.MULTI.SUPERVISION_VISIT_LIST +
          "?p=" +
          this.$STORE.state.userConfig.selectedProject +
          "&offset=" +
          this.counter +
          "&limit=10" +
          "&promoter=" +
          this.pickPromoter +
          "&is_deleted=false" +
          "&today=true" +
          "&ordering=-id",
        this.$PATH.SERVICE_NAME.AUTH,
      );
      if (res.status === 200) {
        this.superVisorLists = [...this.superVisorLists, ...res.data.results];

        // Update the counter
        this.counter = this.superVisorLists.length;
        this.flag = false;
      }
    },
    handleScroll() {
      const scrollY = window.scrollY || window.pageYOffset;
      const threshold =
        document.documentElement.scrollHeight - window.innerHeight - 200;
      if (scrollY > threshold) {
        if (this.flag === false) {
          this.loadMoreResults();
        }
        this.flag = true;
      }
    },
    superVisiorVisitHistoryHandler() {
      this.$router.push({
        name: "superVisorVisitHistory",
      });
    },
    promoterHandler() {
      this.counter = 0;
      this.getData();
    },
    superVisionModal(value) {
      this.supervisionData = value;
      this.sheet = !this.sheet;
    },
    superVisionHandler() {
      this.$router.push({
        name: "superVisorDetail",
        params: { id: this.supervisionData.id },
      });
    },
    superVisionPromoterHandler() {
      this.$router.push({
        name: "superVisorPromoterView",
        params: { id: this.supervisionData.id },
      });
    },
  },
};
</script>
<style scoped lang="scss">
.containers {
  margin: 24px;
  //   .position-fixed {
  //     position: fixed;
  //     top: 45px;
  //     left: 0;
  //     right: 0;
  //     z-index: 2;
  //     width: 100%;
  //     margin: auto;
  //     max-width: 560px;
  //     background: #fff;
  //   }
  //   .content-container {
  //     position: relative;
  //     top: 145px;
  //   }
  .empty-state-img {
    margin: 48px 70px;
  }
  .label-title {
    font-size: 14px;
    margin-bottom: 8px;
  }
  select {
    -webkit-appearance: listbox !important;
    border-left: 8px solid transparent;
    background: #fff;
    padding: 8px;
    border-radius: 4px;
  }
  .cards {
    padding: 12px;
    margin-top: 12px;
    box-shadow: 0px 0px 5px rgba(196, 196, 196, 0.3) !important;
    .img-container {
      background: #eaf1fb;
      border-radius: 2px;
      padding: 14px;
      max-width: 64px;
      max-height: 64px;
    }
    .contents {
      display: flex;
      flex-direction: column;
      margin-right: 12px;
    }
    .status {
      font-size: 10px;
      font-weight: 700;
      padding: 8px;
      border-radius: 8px;
      min-width: 70px;
    }
    .invisited {
      background: #e7e7e7;
    }
    .inprogress {
      background: #fdf7c5;
    }
    .details {
      color: #828282;
    }
  }
}
.supervision-btn {
  display: flex;
  align-items: center;
}

hr {
  height: 1px;
  background-color: #d9d9d9;
  border: none;
  margin: 24px 0;
}
.confirm-report {
  display: flex;
  align-items: center;
  color: #357ae1;
}
.action__plan__btn {
  display: flex;
  align-items: center;
  border-radius: 8px;
  background: #357ae1;
  padding: 10px;
  position: fixed;
  bottom: 85px;
  color: #fff;
}
</style>
