<template>
  <div>
    <Topbar />
    <FullLoading v-if="loading" />
    <div class="mx-6 my-3">
      <v-card elevation="0" color="transparent" class="imagess pa-6 my-3">
        <div v-for="image in images" :key="image.id" class="image">
          <div @click="submitHandler(image)" class="parent">
            <img class="img" :src="image.link" />
            <div class="d-flex justify-space-between align-center mb-3">
              <div>
                <!-- <img src="@/assets/images/Icons/location-icon.svg" /> -->
                <span>لوکیشن</span>
              </div>
              <div
                v-if="supervisionStatus(image.supervision_location_confirm)"
                class="boxes"
                :class="supervisionStatus(image.supervision_location_confirm).class"
              >
                {{ supervisionStatus(image.supervision_location_confirm).label }}
              </div>
            </div>
            <div class="d-flex justify-space-between align-center">
              <div>
                <!-- <img src="@/assets/images/Icons/image-icon.svg" /> -->
                <span>تصویر</span>
              </div>
              <div
                v-if="supervisionStatus(image.supervision_confirm)"
                class="boxes"
                :class="supervisionStatus(image.supervision_confirm).class"
              >
                {{ supervisionStatus(image.supervision_confirm).label }}
              </div>
            </div>
          </div>
        </div>
        <v-bottom-sheet :retain-focus="false" max-width="576px" v-model="sheet">
          <v-sheet height="248" class="pa-5" :retain-focus="false">
            <div class="questions__wrapper">
              <div class="questions__container">
                <div class="d-flex align-center">
                  <span>تایید تصویر</span>
                  <div @click="dialog = true" class="imge__prev">
                    (مشاهده تصاویر)
                  </div>
                </div>
                <div class="d-flex">
                  <v-checkbox
                    @change="handleChangeImage('checkboxLocationTrue')"

                    v-model="checkboxImageTrue"
                    label="بله"
                    color="#357AE1"
                  ></v-checkbox>
                  <v-checkbox
                    @change="handleChangeImage('checkboxLocationFalse')"

                    v-model="checkboxImageFalse"
                    label="خیر"
                    color="#357AE1"
                  ></v-checkbox>
                </div>
              </div>
              <div class="questions__container">
                <div class="d-flex align-center">
                  <span>تایید لوکیشن</span>
                  <div @click="showLocationModal" class="imge__prev">
                    (مشاهده لوکیشن)
                  </div>
                </div>
                <div class="d-flex">
                  <v-checkbox
                  
                  @change="handleChangeLocation('checkboxLocationTrue')"
                    v-model="checkboxLocationTrue"
                    label="بله"
                    color="#357AE1"
                  ></v-checkbox>
                  <v-checkbox
                    @change="handleChangeLocation('checkboxLocationFalse')"
                    v-model="checkboxLocationFalse"
                    label="خیر"
                    color="#357AE1"
                  ></v-checkbox>
                </div>
              </div>
            </div>
          </v-sheet>
          <OverlayButton @click="submitQuestionsHandler" title="ثبت" />
        </v-bottom-sheet>
        <v-row justify="center">
          <v-dialog v-model="dialog" max-width="290">
            <v-img :src="clickedImage.link" />
          </v-dialog>
        </v-row>
        <v-snackbar v-model="alertDirection" top>
          لوکیشن برای این تصویر ثبت نشده است!
        </v-snackbar>
      </v-card>
    </div>
  </div>
</template>
<script>
import Topbar from "../../components/Topbar/backTopBar.vue";
import Button from "../../components/Button/Button.vue";
import FullLoading from "../../components/Loading/fullLoading.vue";
import OverlayButton from "../../components/Button/overlayButton.vue";

const SUPERVISION_STATUS = {
  NOT_CHECKED: { class: "not__checked__color", label: "در انتظار تایید" },
  REJECTED: { class: "rejected__color", label: "تایید نشده" },
  CONFIRMED: { class: "confirmed__color", label: "تایید شده" },
};

export default {
  name: "Profile",
  components: {
    Topbar,
    Button,
    FullLoading,
    OverlayButton,
  },
  data() {
    return {
      images: [],
      visitId: null,
      minImg: null,
      loading: false,
      sheet: false,
      clickedImage: {},
      checkboxLocationTrue: false,
      checkboxLocationFalse: false,
      selectedLocationCheckBox: "NOT_CHECKED",
      checkboxImageFalse: false,
      checkboxImageTrue: false,
      selectedImageCheckBox: "NOT_CHECKED",
      imageModal: false,
      dialog: false,
      alertDirection: false,
    };
  },

  mounted() {
    this.getImages();
  },
  methods: {
    supervisionStatus(status) {
      return SUPERVISION_STATUS[status] || null;
    },
    async getImages() {
      const url = window.location.href;
      const type = url.split("/").slice(-2)[0];
      this.visitId = url.split("/").slice(-1)[0];
      this.minImg = url.split("/").slice(-3)[0];
      "typessss", type;
      const res = await this.$ApiServiceLayer.get(
        this.$PATH.RELATIVE_PATH.GET.GET_IMAGES_ALBUM +
          "?type=" +
          type +
          "&p=" +
          this.$STORE.state.userConfig.selectedProject +
          "&visit=" +
          this.visitId,
        this.$PATH.SERVICE_NAME.AUTH
      );
      if (res.status === 200) {
        this.images = res.data;
      }
    },

    submitHandler(value) {
      this.sheet = !this.sheet;
      this.clickedImage = value;
      console.log(value);
    },
    showLocationModal() {
      if (
        (this.clickedImage.longitude === null ||
          this.clickedImage.longitude == 0) &&
        (this.clickedImage.latitude === null || this.clickedImage.latitude == 0)
      ) {
        this.alertDirection = true;
      } else {
        const newWindow = window.open(
          `https://maps.google.com/?q=${this.clickedImage.latitude},${this.clickedImage.longitude}`
        );
        newWindow.focus();
      }
    },
    handleChangeLocation(checkboxLocationValue) {
      if (checkboxLocationValue === "checkboxLocationTrue") {
        this.checkboxLocationFalse = false;
        this.checkboxLocationTrue = true;
        this.selectedLocationCheckBox = "CONFIRMED";
      } else {
        this.checkboxLocationTrue = false;
        this.checkboxLocationFalse = true;
        this.selectedLocationCheckBox = "REJECTED";
      }
    },

    handleChangeImage(checkboxImageValue) {
      if (checkboxImageValue === "checkboxLocationTrue") {
        this.checkboxImageFalse = false;
        this.checkboxImageTrue = true;
        this.selectedImageCheckBox = "CONFIRMED";
      } else {
        this.checkboxImageTrue = false;
        this.checkboxImageFalse = true;
        this.selectedImageCheckBox = "REJECTED";
      }
    },
    async submitQuestionsHandler() {
      const res = await this.$ApiServiceLayer.patch(
        this.$PATH.RELATIVE_PATH.MULTI.PHOTO_EDIT + this.clickedImage.id + "/",
        this.$PATH.SERVICE_NAME.AUTH,
        {
          supervision_location_confirm: this.selectedLocationCheckBox,
          supervision_confirm: this.selectedImageCheckBox,
        }
      );
      if (res.status === 200) {
       this.sheet = false;
       this.getImages();
      }
    },
    // async changeStatus() {
    //   const res = await this.$ApiServiceLayer.patch(
    //     this.$PATH.RELATIVE_PATH.MULTI.GET_STATUS_QUESTIONS +
    //       this.visitId +
    //       "/",
    //     this.$PATH.SERVICE_NAME.AUTH,
    //     { supervision_status: "1" }
    //   );
    //   "status:", res;
    // },
  },
};
</script>
<style scoped>
.containers {
  margin: 24px;
}

.imagess {
  display: flex;
  justify-content: space-between;
  flex-wrap: wrap;
  margin-bottom: 6px;
}

.parent {
  padding: 8px 7px 8px 8px;
  position: relative;
  background: #fff;
  border-radius: 8px;
  margin-bottom: 16px;
}
.img {
  height: 129px;
  width: 129px;
  margin-bottom: 4px;
  border-radius: 4px;
}

.boxes {
  padding: 4px;
  font-size: 8px;
  border-radius: 8px;
}
.confirmed__color {
  background: #f2fff7;
  color: #46a175;
}
.rejected__color {
  color: #ed1c24;
  background: #ffeff0;
}
.not__checked__color {
  background: #efece1;
  color: #c2aa65;
}
.questions__wrapper {
  display: flex;
  justify-content: space-between;
  flex-direction: column;
}
.imge__prev {
  color: #0000ee;
  font-size: 10px;
  margin-right: 4px;
}
.questions__container {
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
