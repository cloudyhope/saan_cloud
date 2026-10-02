<template>
  <div>
    <div class="topbar">
      <v-toolbar fixed class="topbar" color="#fff" dense>
        <v-toolbar-title class="title-name">اکشن پلن ها</v-toolbar-title>
        <v-spacer></v-spacer>
        <v-btn @click="backHandler" icon>
          <v-img max-width="20" src="@/assets/images/Icons/back.svg" />
        </v-btn>
      </v-toolbar>
    </div>
    <div class="containers">
      <!-- <div v-if="superVisorLists.length === 0">
      </div> -->
      <div class="content-container">
        <v-card
          v-for="superVisor in superVisorLists"
          :key="superVisor.id"
          @click="superVisionModal(superVisor)"
          class="cards pa-5 mt-2"
        >
          <div class="d-flex align-center justify-space-between">
            <div class="d-flex align-center">
              <div class="img-container">
                <v-img max-width="36" :src="superVisor.outlet.category.icon" />
              </div>
              <div class="contents">
                <span class="header mb-1">{{ superVisor.outlet.name }}</span>
                <div class="mb-1">
                  <span class="details">کد:</span>
                  <span class="font-weight-medium  mr-1">{{
                    superVisor.outlet.code
                  }}</span>
                </div>
                <div class="mb-1">
                  <label for="due-date">تاریخ اجرا:</label>
                  <span dir="ltr" class=" mr-1">{{
                    superVisor.due_date
                  }}</span>
                </div>
                <div>
                  <span>نوبت ویزیت:</span>
                  <span dir="ltr" class=" mr-1">{{
                    superVisor.visit_turn
                  }}</span>
                </div>
              </div>
            </div>
            <div
              @click="deleteModalHandler(superVisor)"
              class="d-flex flex-column align-center"
            >
              <img src="@/assets/images/Icons/green_delete_icon.svg" />
              <div class="delete-text">حذف ویزیت</div>
            </div>
          </div>
        </v-card>
        <v-bottom-sheet
          :retain-focus="false"
          max-width="576px"
          v-model="deleteModal"
        >
          <v-sheet :retain-focus="false" class="pt-4 px-6" height="128px">
            <span class="address-detail"
              >آیا از حذف این ویزیت اطمینان دارید؟</span
            >
            <div class="d-flex justify-space-between mt-5">
              <Button
                @click="deleteVisitHistorySuperVisior"
                class="delete-button ml-4"
                title="حذف"
              />
              <Button
                @click="deleteModal = !deleteModal"
                class="decline-button ml-0"
                title="خیر"
              />
            </div>
          </v-sheet>
        </v-bottom-sheet>
      </div>
      <EmptyContainer />
    </div>
  </div>
</template>
<script>
import EmptyContainer from "../../components/emptyContainer.vue";
import Topbar from "../../components/Topbar/index.vue";
import VuePersianDatetimePicker from "vue-persian-datetime-picker";
import Button from "../../components/Button/Button.vue";

export default {
  components: {
    EmptyContainer,
    Topbar,
    Button,
    datePicker: VuePersianDatetimePicker,
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
      deleteModal: false,
      ids: "",
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
          this.$STORE.state.userConfig.selectedProject,

        this.$PATH.SERVICE_NAME.AUTH
      );
      if (res.status === 200) {
        this.promoterLists = res.data;
      }
    },
    deleteModalHandler(data) {
      this.ids = data.id;
      this.deleteModal = true;
    },
    async deleteVisitHistorySuperVisior() {
      const res = await this.$ApiServiceLayer.delete(
        this.$PATH.RELATIVE_PATH.MULTI.VISIT_DETAIL_EDIT + this.ids + "/",
        this.$PATH.SERVICE_NAME.AUTH,
        {}
      );
      if (res.status === 204) {
        this.deleteModal = !this.deleteModal;
        this.counter = 0
        this.getData();
      }
    },
    backHandler() {
      this.$router.push({ name: "supervisor" });
    },
    visitHistoryHandler() {
      this.$router.push({
        name: "visitHistory",
        params: { id: this.supervisionData.id },
      });
    },
    submitActionPlanHandler() {
      this.$router.push({ name: "actionPlan" });
    },
    async getData() {
      const res = await this.$ApiServiceLayer.get(
        this.$PATH.RELATIVE_PATH.MULTI.SUPERVISION_VISIT_LIST +
          "?p=" +
          this.$STORE.state.userConfig.selectedProject +
          "&offset=" +
          this.counter +
          "&limit=10" +
          "&promoter=" +
          this.pickPromoter +
          "&my_promoters=true" +
          "&is_deleted=false" +"&ordering=-id",

        this.$PATH.SERVICE_NAME.AUTH
      );
      if (res.status === 200) {
        this.superVisorLists = res.data.results;
        this.counter = this.superVisorLists.length;
      }
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
          "&is_deleted=false" +"&ordering=-id",
        this.$PATH.SERVICE_NAME.AUTH
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
        name: "superVisorVisitHistory",
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
  margin: 72px 24px;
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
      background: #FDF7C5;
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
.delete-text {
  margin-top: 8px;
  color: #357AE1;
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
  color: #357AE1;
}
.action__plan__btn {
  display: flex;
  align-items: center;
  border-radius: 8px;
  background: #357AE1;
  padding: 10px;
  position: fixed;
  bottom: 85px;
  color: #fff;
}
.decline-button {
  border: 1px solid #357AE1;
  background: #fff;
  color: #357AE1;
}
.topbar {
  /* padding-right: 8px !important; */
  position: fixed;
  max-width: 570px;
  width: 100%;
  z-index: 2;
  box-shadow: 0px 0px 4px rgba(220, 220, 221, 0.6) !important;
}
</style>
