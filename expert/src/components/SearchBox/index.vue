<template>
  <div class="search-box-container">
    <v-dialog
      v-model="dialog"
      hide-overlay
      transition="dialog-bottom-transition"
      max-width="576px"
      content-class="product-dialog"
      class="pa-6"
    >
      <template v-slot:activator="{ on, attrs }">
        <v-toolbar elevation="0" :style="inputBackground" class="fix-search">
          <v-toolbar-title class="search-input">
            <button v-if="iconSearchBtn" class="search-feild">
              <v-icon>{{ showIcon }}</v-icon>
            </button>
            <button @click="backButton" v-if="iconBackBtn" class="search-feild">
              <v-icon>{{ showIcon }}</v-icon>
            </button>
            <v-text-field
              type="button"
              class="inputs"
              hide-details="false"
              label="جستجوی شناسه پروژه، نام ساختمان ..."
              solo
              dense
              flat
              v-bind="attrs"
              v-on="on"
              readonly
            >
            </v-text-field>
          </v-toolbar-title>
        </v-toolbar>
      </template>

      <v-card color="#F0F0F1" height="auto" min-height="100%" max-width="576px">
        <div class="search d-flex align-center">
          <v-btn class="search-icon" plain @click="dialog = false">
            <v-icon color="#041E49">mdi-chevron-right</v-icon>
          </v-btn>
          <input
            type="text"
            class="inner-search"
            placeholder="جستجوی شناسه پروژه، نام ساختمان ..."
            v-model="searchQuery"
            @keyup="textSearch()"
          />
        </div>

        <v-sheet class="pa-3" v-if="skeleton">
          <v-skeleton-loader
            class="mx-auto"
            min-height="20%"
            max-height="20%"
            type="card"
          ></v-skeleton-loader>
          <v-skeleton-loader
            class="mt-4"
            min-height="20%"
            max-height="20%"
            type="card"
          ></v-skeleton-loader>
        </v-sheet>

        <div v-if="emptyState && skeleton === false">
          <v-card
            class="empty-card d-flex justify-center align-center mx-6 mt-4"
            height="320"
          >
            <div class="not-found">
              <v-img
                max-width="150"
                src="@/assets/images/emptySearchResult.png"
              ></v-img>
              <span class="empty-text">مشتری مورد نظر شما یافت نشد.</span>
            </div>
          </v-card>
        </div>

        <v-card
          v-for="visit in searchResult"
          :key="visit.id"
          @click="storeDetail(visit)"
          elevation="0"
          class="pa-5 mt-2 mx-6"
        >
          <div class="d-flex justify-space-between align-center">
            <!-- <div class="img-container">
                <v-img max-width="36" :src="visit.outlet.category.icon" />
              </div> -->
            <span class="header mb-1">{{ visit.building.verbose_name }}</span>
            <!-- <div class="mb-1">
                  <span class="details">کد:</span>
                  <span class="font-weight-medium persian mr-1">{{
                    visit.outlet.code
                  }}</span>
                </div> -->

            <!-- <span class="details">نوع مشتری:</span> -->
            <div class="d-flex align-center">
              <span v-if="visit.status === '0'" class="status invisited">
                ویزیت نشده
              </span>
              <span v-if="visit.status === '1'" class="status inprogress">
                تکمیل نشده
              </span>
            </div>
          </div>
          <div>
            <v-divider class="my-4" />

            <div class="mb-1">
              <span class="details">آدرس:</span>
              <span class="font-weight-medium mr-1">{{
                visit.building.address
              }}</span>
            </div>
            <div class="details d-flex justify-space-between">
              <span class="mr-1">{{ formatDate(visit.datetime_created) }}</span>
              <span class="mr-1">{{ visit.building.code }}</span>
            </div>
          </div>
        </v-card>
        <div
          class="mx-8 mt-4"
          v-if="showMoreButton && skeleton === false && searchResult.count > 4"
        >
          <Button @click="showMoreProduct" title="مشاهده بیشتر" />
        </div>
      </v-card>
    </v-dialog>
  </div>
</template>
<script>
import Button from "../Button/Button.vue";
import Loading from "../../components/Loading/index.vue";
import moment from "moment-jalaali";

export default {
  components: { Button, Loading },
  props: ["iconName", "backgroundColor"],
  data() {
    return {
      dialog: false,
      searchQuery: "",
      searchResult: [],
      skeleton: false,
      showMoreButton: false,
      emptyState: false,
      showLoading: false,
      iconSearchBtn: false,
      iconBackBtn: false,
      searchIcon: "mdi-magnify",
      backIcon: "mdi-chevron-right",
      fixBackground: "#F0F0F1",
      showLoading: false,
      toShoppingTimer: null,
      timer: null,
      showMore: false,
      search: "",
    };
  },
  mounted() {
    this.showIcon;
  },
  computed: {
    showIcon() {
      if (this.iconName === "search") {
        this.iconBtn();
        return this.searchIcon;
      } else {
        this.iconBtn();
        return this.backIcon;
      }
    },
    inputBackground() {
      if (this.backgroundColor === undefined) {
        return "background: " + this.fixBackground;
      } else {
        return "background: " + this.backgroundColor;
      }
    },
  },
  methods: {
    storeDetail(visit) {
      this.$router.push({ name: "storeDetail", params: { id: visit.id } });
    },
    iconBtn() {
      if (this.iconName === "search") {
        this.iconSearchBtn = true;
      } else {
        this.iconBackBtn = true;
      }
    },
    backButton() {
      history.back();
    },
    textSearch() {
      this.skeleton = true;
      if (this.searchQuery === "") {
        this.searchResult = [];
        return;
      }
      clearTimeout(this.timer);
      this.timer = setTimeout(() => {
        if (this.searchQuery.length >= 1) {
          this.$ApiServiceLayer
            .get(
              this.$PATH.RELATIVE_PATH.GET.VISIT_LIST,
              this.$PATH.SERVICE_NAME.AUTH,
              {},
              `?search=${this.searchQuery}` +
                "&p=" +
                this.$STORE.state.userConfig.selectedProject
            )
            .then((response) => {
              if (response.status === 200) {
                this.skeleton = false;
                this.searchResult = response.data;
                if (this.searchResult.length === 0) {
                  this.emptyState = true;
                } else {
                  this.skeleton = false;
                  this.emptyState = false;
                }
              }
            });
        }
      }, 1000);
    },
    formatDate(dateString) {
      const m = moment(dateString);
      const jDate = m.format("jYYYY/jMM/jDD");
      const weekDay = this.toPersianWeekDay(m.day());
      const time = m.format("HH:mm");
      return this.toPersianNumbers(`${jDate} ${weekDay} ساعت ${time}`);
    },
    toPersianWeekDay(day) {
      const weekDays = [
        "یکشنبه",
        "دوشنبه",
        "سه‌شنبه",
        "چهارشنبه",
        "پنج‌شنبه",
        "جمعه",
        "شنبه",
      ];
      return weekDays[day];
    },
    toPersianNumbers(str) {
      const persianNumbers = ["۰", "۱", "۲", "۳", "۴", "۵", "۶", "۷", "۸", "۹"];
      return str.replace(/[0-9]/g, function (w) {
        return persianNumbers[+w];
      });
    },
    toShopping(id) {
      this.showLoading = true;
      this.toShoppingTimer = setTimeout(() => {
        this.$router.push({ name: "shopping", params: { id: id } });
      }, 1000);
    },
    showMoreProduct() {
      this.$router.push({
        name: "productList",
        query: { search: this.searchQuery },
      });
    },
  },
};
</script>
<style>
/* .theme--light.v-text-field--solo > .v-input__control > .v-input__slot {
  background: #eaf1fb !important;
} */
.v-text-field.v-text-field--solo .v-label {
  font-size: 12px !important;
  color: #8f8c8c !important;
}
.v-input .v-label {
  color: #041e49;
}
.fix-search {
  width: 100%;
  max-width: 100%;
  position: relative;
  z-index: 4;
  background: transparent !important;
  border-radius: 12px;
  padding: 0 16px;
}
.append-search {
  height: 100%;
  width: 100%;
  display: flex;
  align-items: flex-end;
  justify-content: center;
  padding-bottom: 20px;
}
.product-dialog {
  height: 100% !important;
  margin: 0 !important;
}
.v-dialog:not(.v-dialog--fullscreen) {
  max-height: 100% !important;
}

.search-input {
  display: flex;
  width: 100%;
  background: white;
  border-radius: 12px;
  padding: 8px;
}
.inputs {
  /* border-radius: 12px !important; */
  background: white !important;
}

.inner-search {
  border: none;
  width: 100%;
  font-size: 16px !important;
  height: 36px;
  border-radius: 8px 0 0 8px;
  color: #041e49;
}
.inner-search::placeholder {
  color: #8f8c8c !important;
  font-size: 12px;
}
.inner-search:focus {
  outline: none;
}
.search {
  /* padding: 20px; */
  height: 56px;
  background: #fff;
}
.search-result-card {
  display: flex;
  margin: 0 24px;
  border: 1px solid #e7e7e7 !important;
}
.search-result-title {
  color: #828282;
  margin-left: 8px;
}
.search-feild {
  background: #fff;
  border-radius: 0px 8px 8px 0;
  padding-right: 15px;
}
.mdi-magnify {
  color: #041e49 !important;
  margin-left: 10px;
}
.search-icon {
  border-radius: 0 8px 8px 0 !important;
}
.empty-text {
  margin-top: 40px;
  font-weight: 700;
  font-size: 18px;
}
.empty-card {
  box-shadow: 0px 0px 3px 0px rgba(16, 24, 40, 0.1);

  border-radius: 8px !important;
}
.append-text {
  font-weight: 700;
  color: #404041;
  font-size: 14px;
}
.not-found {
  display: flex;
  flex-direction: column;
  width: 100%;
  align-items: center;
}
.titles {
  font-size: 16px;
  font-weight: 700;
}
/* .img-container {
  background: #f0f0f1;
  border-radius: 2px;
  padding: 14px;
  max-width: 64px;
  max-height: 64px;
} */
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
  font-size: 10px;
  font-weight: 700;
  padding: 8px;
  border-radius: 4px;
  min-width: 70px;
}
.invisited {
  background: #e7e7e7;
}
.inprogress {
  background: #fdf7c5;
}

.search-box-container {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 1000;
  margin: 15px auto;
  max-width: 576px;
}
</style>
