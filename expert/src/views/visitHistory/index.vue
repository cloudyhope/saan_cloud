<template>
  <div>
    <Topbar />
    <div class="ma-6">
      <Skeleton v-if="initialLoading" type="list" :count="4" two-line />

      <template v-else>
      <v-card
        v-for="visit in visitHistoryList"
        :key="visit.id"
        class="pa-5 mt-2 cards"
      >
        <div class="d-flex justify-space-between">
          <div class="d-flex align-center">
            <!-- <div class="img-container">
              <v-img max-width="36" :src="visit.building.category.icon" />
            </div> -->
            <div class="contents">
              <span class="header mb-1">{{ visit.building.name }}</span>
              <div class="mb-1">
                <span class="details">کد:</span>
                <span class="font-weight-medium  mr-1">{{
                  visit.building.code
                }}</span>
              </div>
              <div class="mb-1">
                  <label for="due-date" class="details">تاریخ اجرا:</label>
                  <span dir="ltr" class=" mr-1">{{
                    formatToJalali(visit.due_date)
                  }}</span>
                </div>
              <div>
                <span class="details">نوبت ویزیت :</span>

                <span class="font-weight-medium  mr-1">
                  {{ visit.visit_turn }}</span
                >
              </div>
              <!-- <div>
                <span class="details">نوع مشتری:</span>
                <span
                  v-if="visit.building.category.name === 'BrandShop'"
                  class="font-weight-medium mr-1"
                  >برند شاپ</span
                >
                <span
                  v-if="visit.building.category.name === 'ChainStore'"
                  class="font-weight-medium mr-1"
                  >مشتری زنجیره ای</span
                >
                <span
                  v-if="visit.building.category.name === 'MultiBrand'"
                  class="font-weight-medium mr-1"
                  >مولتی برند</span
                >
              </div> -->
            </div>
          </div>
          <div class="d-flex flex-column align-center">
            <div class="d-flex align-center">
              <!-- <span v-if="visit.status === '2'" class="status completed">
                تکمیل شده
              </span> -->
              <span v-if="visit.status === '3'" class="status confirm">
                تایید شده
              </span>
              <span v-if="visit.status === '4'" class="status rejected">
                رد شده
              </span>
              <!-- <span  v-if="visit.status === '1'" class="status inprogress"> تکمیل نشده </span> -->
            </div>
            <div class="d-flex align-center mt-2" v-if="visit.rate !== null">
              <img
                class="star_icon"
                src="@/assets/images/Icons/Star_solid.svg"
              />
              <span class=" rate_text">{{ visit.rate }}</span>
            </div>
            <div class="no_score" v-else>بدون امتیاز</div>
          </div>
        </div>
        <div class="no_score" v-if="visit.visit_comment">
          بازخورد : {{ visit.visit_comment }}
        </div>
      </v-card>
      </template>
      <EmptyContainer />
    </div>
  </div>
</template>

<script>
import EmptyContainer from "../../components/emptyContainer.vue";
import Loading from "../../components/Loading/index.vue";
import Topbar from "../../components/Topbar/backTopBar.vue";
import moment from 'moment-jalaali'
import Skeleton from "../../components/Skeleton/index.vue";

export default {
  components: {
    EmptyContainer,
    Loading,
    Topbar,
    Skeleton,
  },
  data() {
    return {
      showLoading: false,
      visitHistoryList: [],
      loadBrandList: false,
      latitude: null,
      longitude: null,
      counter: 0,
      flag: false,
      count: null,
      loading: false,
      initialLoading: true,
    };
  },

  created() {
    this.getData();
    window.addEventListener("scroll", this.handleScroll);
  },
  beforeDestroy() {
    window.removeEventListener("scroll", this.handleScroll);
  },
  methods: {
    async getData() {
      this.initialLoading = true;
      const res = await this.$ApiServiceLayer.get(
        this.$PATH.RELATIVE_PATH.GET.GET_VISIT_HISTORY +
          "?p=" +
          this.$STORE.state.userConfig.selectedProject +
          "&offset=" +
          this.counter +
          "&limit=10" + "&is_deleted=false",
        this.$PATH.SERVICE_NAME.AUTH
      );
      if (res.status === 200) {
        this.visitHistoryList = res.data.results;
        this.counter = this.visitHistoryList.length;
        this.count = res.data.count;
      }
      this.initialLoading = false;
    },
    async loadMoreResults() {
      if (!this.loading) {
        const res = await this.$ApiServiceLayer.get(
          this.$PATH.RELATIVE_PATH.GET.GET_VISIT_HISTORY +
            "?p=" +
            this.$STORE.state.userConfig.selectedProject +
            "&offset=" +
            this.counter +
            "&limit=10",
          this.$PATH.SERVICE_NAME.AUTH
        );
        if (res.status === 200) {
          this.visitHistoryList = [
            ...this.visitHistoryList,
            ...res.data.results,
          ];

          // Update the counter
          this.counter = this.visitHistoryList.length;
          this.flag = false;
        }
        this.loading = false;
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
    formatToJalali(date) {
      if (!date) return '';  // Return empty string if date is null or undefined
      
      const m = moment(date);
      return m.isValid() ? m.format('jYYYY/jMM/jDD') : '';
    },
  },
};
</script>

<style scoped>
.cards {
  box-shadow: 0px 4px 4px rgba(214, 214, 214, 0.6) !important;
}
.titles {
  font-size: 16px;
  font-weight: 700;
}
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
.header {
  font-size: 12px;
  font-weight: 700;
}
.details {
  color: #828282;
}

.status {
  display: flex;
  justify-content: center;
  font-size: 10px;
  font-weight: 700;
  padding: 8px;
  border-radius: 4px;
  min-width: 70px;
  
}
.completed {
  background: rgba(21, 133, 37, 0.8);
  color: #fff;
}
.confirm {
  background: #357AE1;
  color: #fff;
}
.rejected {
  background: rgba(219, 34, 34, 0.8);
  color: #fff;
}
.no_score {
  margin-top: 8px;
  font-size: 10px;
}
.star_icon {
  width: 18px;
}
.rate_text {
  font-size: 14px;
}
</style>
