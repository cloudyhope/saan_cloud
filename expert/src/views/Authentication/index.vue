<template>
  <div>
    <Topbar />
    <FullLoading v-if="loading" />
    <div class="mx-6 my-3">
      <span class="titles">حداقل ۴ تصویر با شرایط زیر گرفته شود</span>
      <div class="desc">
        <ul>
          <li>دو تصویر با دوربین سلفی در نور خوب و تمام رخ</li>
          <li>دو تصویر با دوربین اصلی در نور خوب و تمام رخ</li>
          <li>
            در صورت ایجاد تغییر ظاهری در صورت (تغییر در آرایش ریش و سیبیل، جراحی
            زیبایی و...)
          </li>
        </ul>
      </div>
      <v-card elevation="0" color="#FFF" class="imagess pa-6 my-3">
        <div @click="uploadImage" class="upload-img">
          <v-img max-width="21" src="@/assets/images/Icons/plus.svg" />
        </div>
        <div v-for="image in images" :key="image.id" class="image">
          <div class="parent">
            <img class="img" :src="image.image" />
            <!-- <div @click="postId(image.id)" class="text-block">
              <img class="trash-icon" src="@/assets/images/Icons/trash.svg" />
            </div> -->
          </div>
        </div>
        <!-- <v-bottom-sheet
          :retain-focus="false"
          max-width="576px"
          v-model="deleteImage"
        >
          <v-sheet
            :retain-focus="false"
            class="modals pt-4 px-6"
            height="128px"
          >
            <span class="address-detail"
              >آیا از حذف این عکس اطمینان دارید؟</span
            >
            <div class="d-flex justify-space-between mt-5">
              <Button
                @click="deleteImg(idImg)"
                class="delete-button ml-4"
                title="حذف"
              />
              <Button
                @click="deleteImage = !deleteImage"
                class="decline-button ml-0"
                title="خیر"
              />
            </div>
          </v-sheet>
        </v-bottom-sheet> -->
        <input
          type="file"
          hidden
          capture="user"
          accept="image/*"
          id="fileUpload"
          @change="func($event)"
        />
        <v-snackbar v-model="snackbar" :timeout="timeout" top>
          عکس با موفقیت ارسال شد.
        </v-snackbar>
      </v-card>
    </div>
    <OverlayButton
      title="ثبت"
      @click="submitHandler"
    />
    <EmptyContainer />
  </div>
</template>
<script>
import Topbar from "../../components/Topbar/backTopBar.vue";
import OverlayButton from "../../components/Button/overlayButton.vue";
import FullLoading from "../../components/Loading/fullLoading.vue";
import Compressor from "compressorjs";
import Button from "../../components/Button/Button.vue";
import EmptyContainer from "../../components/emptyContainer.vue";

export default {
  name: "Profile",
  components: {
    Topbar,
    OverlayButton,
    FullLoading,
    Button,
    EmptyContainer
  },
  data() {
    return {
      images: [],
      visitId: null,
      latitude: null,
      longitude: null,
      deleteImage: false,
      snackbar: false,
      timeout: 2000,
      loading: false,
      idImg: null,
      deleteAddress: false,
      imageUrl: "",
    };
  },

  created() {
    const success = (position) => {
      this.latitude = position.coords.latitude;
      this.longitude = position.coords.longitude;
      // Do something with the position
    };

    const error = (err) => {
      (err);
    };

    // This will open permission popup
    navigator.geolocation.getCurrentPosition(success, error);
  },
  mounted() {
      this.getImages();
  },
  computed: {
    // disable() {
    //     if(this.images.length < 4 ) {
    //         return true
    //     } else {
    //         return false
    //     }
    // }
  },
  methods: {
    submitHandler() {
        this.$router.push({name: "profile",});
    },
    // postId(id) {
    //   this.idImg = id;
    //   this.deleteImage = !this.deleteImage;
    // },
    async getImages() {
      const res = await this.$ApiServiceLayer.get(
        this.$PATH.RELATIVE_PATH.MULTI.AUTH_IMAGE +
          "?p=" +
          this.$STORE.state.userConfig.selectedProject,
        this.$PATH.SERVICE_NAME.AUTH
      );
      if (res.status === 200) {
        (res);
        this.images = res.data;
      }
    },

    uploadImage() {
      document.getElementById("fileUpload").click();
    },

    async func(event) {
      this.loading = true;
      const file = event.target.files[0];
      const options = {
        quality: 0.7, // set compression quality
        success: async (compressedResult) => {
          const formData = new FormData();
          formData.append("image", compressedResult, compressedResult.name);

          const res = await this.$ApiServiceLayer.post(
            this.$PATH.RELATIVE_PATH.MULTI.AUTH_IMAGE,
            this.$PATH.SERVICE_NAME.AUTH,
            formData,
            {
              "Content-Type": "multipart/form-data",
            }
          );
          (res);
          if (res.status === 201) {
            this.loading = false;
            this.snackbar = true;
            this.getImages();
          }
        },
      };
      new Compressor(file, options);
    },
    // deleteImg(id) {
    //   this.$ApiServiceLayer
    //     .delete(
    //       this.$PATH.RELATIVE_PATH.DELETE.DELETE_IMAGE + id + "/",
    //       this.$PATH.SERVICE_NAME.AUTH
    //     )
    //     .then((response) => {
    //       if (response.status === 204) {
    //         this.deleteImage = false;
    //         this.getImages();
    //       }
    //     });
    // },
  },
};
</script>
<style scoped>
.containers {
  margin: 24px;
}
.titles {
  font-size: 16px;
  font-weight: 700;
}
.desc {
  display: flex;
  flex-direction: column;
  margin-top: 12px;
  padding: 16px;
  background: #eaf2f9;
  border-radius: 4px;
  padding: 12px 24px;
}
.upload-img {
  display: flex;
  justify-content: center;
  align-items: center;
  background-image: url("data:image/svg+xml,%3csvg width='100%25' height='100%25' xmlns='http://www.w3.org/2000/svg'%3e%3crect width='100%25' height='100%25' fill='none' rx='4' ry='4' stroke='%23828282FF' stroke-width='2' stroke-dasharray='6%2c 14' stroke-dashoffset='0' stroke-linecap='square'/%3e%3c/svg%3e");
  border-radius: 4px !important;
  height: 129px;
  width: 129px;
}
.imagess {
  display: flex;
  justify-content: space-between;
  flex-wrap: wrap;
  margin-bottom: 6px;
  box-shadow: 0px 4px 4px rgba(214, 214, 214, 0.6) !important;
}
.modals {
  border-radius: 8px 8px 0 0;
}
.parent {
  position: relative;
}
.img {
  height: 129px;
  width: 129px;
  margin-bottom: 4px;
  border-radius: 4px;
}
.decline-button {
  border: 1px solid #357AE1;
  background: #fff;
  color: #357AE1;
}
.text-block {
  position: absolute;
  bottom: 0px;
  width: 100%;
  background-color: #fff;
  opacity: 0.8;
  color: white;
  display: flex;
  justify-content: center;
  height: 36px;
  padding-bottom: 10px;
}
.trash-icon {
  width: 20px;
}
</style>
