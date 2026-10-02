<template>
  <div>
    <BaseTopBar title="بارگزاری عکس ورود" />

    <FullLoading v-if="loading" />
    <div class="mx-6 my-3">
      <!-- <span class="titles">حداقل {{ minImg }} عکس</span> -->
      <div class="desc">
        <span>{{ desc }}</span>
      </div>
      <v-card
        v-if="isCaptureSupported"
        elevation="0"
        color="#FFF"
        class="imagess pa-6 my-3"
      >
        <div @click="uploadImage" class="upload-img">
          <v-img max-width="36" src="@/assets/images/Icons/ic_round-plus.svg" />
        </div>
        <div v-for="image in images" :key="image.id" class="image">
          <div class="parent">
            <img class="img" :src="image.link" />
            <div @click="postId(image.id)" class="text-block">
              <img class="trash-icon" src="@/assets/images/Icons/trash.svg" />
            </div>
          </div>
        </div>
        <v-bottom-sheet
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
        </v-bottom-sheet>
        <input
          v-if="isCaptureSupported"
          type="file"
          capture="user"
          accept="image/*"
          id="fileUpload"
          @change="func($event)"
          hidden
        />
        <v-snackbar v-model="snackbar" :timeout="timeout" top>
          {{ snackbarText }}
        </v-snackbar>
      </v-card>
      <h3 v-else>لطفا از طریق مرورگر chrome وارد SaanApp شوید!</h3>
    </div>
  </div>
</template>
<script>
import Topbar from "../../components/Topbar/backTopBar.vue";
import Button from "../../components/Button/Button.vue";
import FullLoading from "../../components/Loading/fullLoading.vue";
import Compressor from "compressorjs";
import BaseTopBar from "@/components/Topbar/BaseTopbar.vue";

export default {
  name: "Profile",
  components: {
    Topbar,
    Button,
    FullLoading,
    BaseTopBar,
  },
  data() {
    return {
      images: [],
      visitId: null,
      latitude: null,
      longitude: null,
      minImg: null,
      deleteImage: false,
      snackbar: false,
      snackbarText: '',
      timeout: 2000,
      loading: false,
      idImg: null,
      desc: null,
      deleteAddress: false,
      imageUrl: "",
    };
  },

  computed: {
    isCaptureSupported() {
      const input = document.createElement("input");
      input.type = "file";
      return input.type === "file";
    },
  },

  mounted() {
    this.getImages();
    this.getDescription();
  },
  methods: {
    async locateForUpload() {
      if (!navigator.geolocation) return;
      await new Promise((resolve) => {
        navigator.geolocation.getCurrentPosition(
          (position) => {
            this.latitude = position.coords.latitude;
            this.longitude = position.coords.longitude;
            resolve();
          },
          () => resolve(),
          { timeout: 5000, maximumAge: 60000 }
        );
      });
    },
    postId(id) {
      this.idImg = id;
      this.deleteImage = !this.deleteImage;
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
        res;
        this.images = res.data;
      }
    },
    async getDescription() {
      const url = window.location.href;
      const type = url.split("/").slice(-2)[0];
      const res = await this.$ApiServiceLayer.get(
        this.$PATH.RELATIVE_PATH.GET.PHOTO_DESC + type + "/" + "?p=" + this.$STORE.state.userConfig.selectedProject,
        this.$PATH.SERVICE_NAME.AUTH,
        {}
      );
      if (res.status === 200) {
        this.desc = res.data.description;
      }
    },
    uploadImage() {
      document.getElementById("fileUpload").click();
    },
    async changeStatus() {
      const res = await this.$ApiServiceLayer.put(
        this.$PATH.RELATIVE_PATH.MULTI.GET_STATUS_QUESTIONS +
          this.visitId +
          "/" +
          "?p=" +
          this.$STORE.state.userConfig.selectedProject,
        this.$PATH.SERVICE_NAME.AUTH,
        { status: "1" }
      );
      "status:", res;
    },
    // async func(event) {
    //   this.loading = true;
    //   const file = event.target.files[0];
    //   const options = {
    //     quality: 0.7, // set compression quality
    //     success: async (compressedResult) => {
    //       const formData = new FormData();
    //       formData.append("link", compressedResult, compressedResult.name);
    //       const url = window.location.href;
    //       const lastParam = url.split("/").slice(-2)[0];
    //       formData.append("latitude", this.latitude);
    //       // formData.append("latitude", "10");
    //       formData.append("longitude", this.longitude);
    //       // formData.append("longitude", "10");
    //       formData.append("visit", this.visitId);
    //       formData.append("type", lastParam);
    //       const res = await this.$ApiServiceLayer.post(
    //         this.$PATH.RELATIVE_PATH.POST.UPLOAD_IMAGE,
    //         this.$PATH.SERVICE_NAME.AUTH,
    //         formData,
    //         {
    //           "Content-Type": "multipart/form-data",
    //         }
    //       );
    //       (res);
    //       if (res.status === 200) {
    //         this.loading = false;
    //         this.snackbar = true;
    //         this.changeStatus();
    //         this.getImages();
    //       }
    //     },
    //   };
    //   new Compressor(file, options);
    // },
    async func(event) {
      const file = event.target.files[0];
      if (!file) return;
      this.loading = true;
      await this.locateForUpload();

      // Create a canvas element to convert the image to WebP format
      const canvas = document.createElement("canvas");
      const ctx = canvas.getContext("2d");
      const img = new Image();
      const imageUrl = URL.createObjectURL(file);

      img.onload = async () => {
        // Desired maximum width and height for the image
        const MAX_WIDTH = 1920; // Higher max width for better resolution
        const MAX_HEIGHT = 1080; // Higher max height for better resolution

        // Calculate the scaling factor to maintain the aspect ratio
        let width = img.width;
        let height = img.height;

        if (width > height) {
          if (width > MAX_WIDTH) {
            height *= MAX_WIDTH / width;
            width = MAX_WIDTH;
          }
        } else {
          if (height > MAX_HEIGHT) {
            width *= MAX_HEIGHT / height;
            height = MAX_HEIGHT;
          }
        }

        // Set canvas dimensions to the resized image
        canvas.width = width;
        canvas.height = height;

        // Draw the resized image onto the canvas
        ctx.drawImage(img, 0, 0, width, height);
        URL.revokeObjectURL(imageUrl);

        // Convert the canvas content to WebP format with higher quality
        canvas.toBlob(
          async (webpBlob) => {
            if (!webpBlob) {
              this.loading = false;
              this.snackbarText = 'پردازش عکس انجام نشد.';
              this.snackbar = true;
              return;
            }
            const options = {
              quality: 0.6,
              success: async (compressedResult) => {
                const formData = new FormData();
                const fileName = file.name
                  ? file.name.replace(/\.[^/.]+$/, ".webp")
                  : "image.webp";

                formData.append("link", compressedResult, fileName); // Ensure the filename ends with .webp
                const url = window.location.href;
                const lastParam = url.split("/").slice(-2)[0];
                formData.append("latitude", this.latitude);
                formData.append("longitude", this.longitude);
                formData.append("visit", this.visitId);
                formData.append("type", lastParam);

                const res = await this.$ApiServiceLayer.post(
                  this.$PATH.RELATIVE_PATH.POST.UPLOAD_IMAGE +
                    "?p=" +
                    this.$STORE.state.userConfig.selectedProject,
                  this.$PATH.SERVICE_NAME.AUTH,
                  formData,
                  {
                    "Content-Type": "multipart/form-data",
                  }
                );

                if (res.status === 200) {
                  this.loading = false;
                  this.snackbarText = 'عکس با موفقیت ارسال شد.';
                  this.snackbar = true;
                  this.changeStatus();
                  this.getImages();
                } else {
                  this.loading = false;
                  this.snackbarText = 'ارسال عکس انجام نشد. فایل یا دسترسی مأموریت را بررسی کنید.';
                  this.snackbar = true;
                }
              },
              error: () => {
                this.loading = false;
                this.snackbarText = 'پردازش عکس انجام نشد.';
                this.snackbar = true;
              },
            };

            // Use the Compressor library to compress the WebP blob
            new Compressor(webpBlob, options);
          },
          "image/webp",
          0.6
        ); // Set quality to 0.9 for less compression loss
      };
      img.onerror = () => {
        URL.revokeObjectURL(imageUrl);
        this.loading = false;
        this.snackbarText = 'فایل عکس قابل خواندن نیست.';
        this.snackbar = true;
      };
      img.src = imageUrl;
    },

    deleteImg(id) {
      this.$ApiServiceLayer
        .delete(
          this.$PATH.RELATIVE_PATH.DELETE.DELETE_IMAGE +
            id +
            "/" +
            "?p=" +
            this.$STORE.state.userConfig.selectedProject,
          this.$PATH.SERVICE_NAME.AUTH
        )
        .then((response) => {
          if (response.status === 204) {
            this.deleteImage = false;
            this.getImages();
          }
        });
    },
  },
};
</script>
<style scoped>
.containers {
  margin: 24px;
}
/* .titles {
  font-size: 16px;
} */
.desc {
  margin-top: 12px;
  padding: 16px;
  background: #eaf2f9;
  border-radius: 4px;
  padding: 12px;
}
.upload-img {
  display: flex;
  justify-content: center;
  align-items: center;
  background-image: url("@/assets/images/Icons/border.svg");
  border-radius: 4px !important;
  height: 129px;
  width: 129px;
  padding: 80px;
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
  border: 1px solid #357ae1;
  background: #fff;
  color: #357ae1;
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
