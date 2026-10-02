<template>
  <div>
    <Topbar />
    <FullLoading v-if="loading" />
    <div class="mx-6 my-3">
      <span class="titles">{{ desc.verbose_name }}</span>
      <div class="desc">
        <div>
          <span class="font-weight-bold">توضیحات:</span>
          {{ desc.description }}
        </div>
        <div>
          <span class="font-weight-bold">شرایط: </span>
          <span>حداقل {{ desc.min }} عکس</span>
        </div>
      </div>
      <v-card v-if="isCaptureSupported" color="#FFF" class="imagess pa-6 my-3">
        <div @click="uploadImage" class="upload-img">
          <v-img max-width="21" src="@/assets/images/Icons/plus.svg" />
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
          <v-sheet :retain-focus="false" class="pt-4 px-6" height="128px">
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
      <h3 v-else>لطفا از طریق مرورگر chrome وارد SaanApp شوید!</h3>
    </div>
  </div>
</template>
<script>
import Topbar from "../../components/Topbar/backTopBar.vue";
import Button from "../../components/Button/Button.vue";
import FullLoading from "../../components/Loading/fullLoading.vue";
import Compressor from "compressorjs";

export default {
  name: "Profile",
  components: {
    Topbar,
    Button,
    FullLoading,
  },

  computed: {
    isCaptureSupported() {
      // TODO: check if capture tag is valid
      const userAgent = navigator.userAgent;
      // alert(userAgent.includes("Telegram"));
      const input = document.createElement("input");
      input.setAttribute("type", "file");
      const supportCapture = "capture" in input;
      const isSafari = /Safari/i.test(userAgent);
      if (isSafari) {
        const hasNoNumberAfterMobile = /Mobile /i.test(userAgent);
        const isThereVersion = /version/i.test(userAgent);
        return !(hasNoNumberAfterMobile && isThereVersion);
      } else {
        return supportCapture;
      }
    },
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
      timeout: 2000,
      loading: false,
      idImg: null,
      desc: null,
      deleteAddress: false,
      imageUrl: "",
      surveyId: "",
    };
  },

  created() {
    const success = (position) => {
      this.latitude = position.coords.latitude;
      this.longitude = position.coords.longitude;
      // Do something with the position
    };

    const error = (err) => {
      err;
    };

    // This will open permission popup
    navigator.geolocation.getCurrentPosition(success, error);
  },
  mounted() {
    this.getImages();
    this.getDescription();
  },
  methods: {
    postId(id) {
      this.idImg = id;
      this.deleteImage = !this.deleteImage;
    },
    async getImages() {
      const url = window.location.href;
      const id = url.split("/").slice(-1)[0];
      this.surveyId = url.split("/").slice(-2)[0];
      const res = await this.$ApiServiceLayer.get(
        this.$PATH.RELATIVE_PATH.GET.GET_SURVEY_IMAGE +
          "?survey_photo_type=" +
          id +
          "&" +
          "survey_fill_out=" +
          this.surveyId,
        this.$PATH.SERVICE_NAME.AUTH
      );
      if (res.status === 200) {
        res;
        this.images = res.data;
      }
    },
    async getDescription() {
      const url = window.location.href;
      const id = url.split("/").slice(-1)[0];
      const res = await this.$ApiServiceLayer.get(
        this.$PATH.RELATIVE_PATH.GET.GT_SURVEY_IMAGE_DESC + id + "/",
        this.$PATH.SERVICE_NAME.AUTH,
        {}
      );
      if (res.status === 200) {
        this.desc = res.data;
      }
    },
    uploadImage() {
      document.getElementById("fileUpload").click();
    },
    //   async changeStatus() {
    //     const res = await this.$ApiServiceLayer.put(
    //       this.$PATH.RELATIVE_PATH.MULTI.GET_STATUS_QUESTIONS +
    //         this.visitId +
    //         "/",
    //       this.$PATH.SERVICE_NAME.AUTH,
    //       { status: "1" }
    //     );
    //     ("status:", res);
    //   },
    // async func(event) {
    //   this.loading = true;
    //   const file = event.target.files[0];
    //   const options = {
    //     quality: 0.7, // set compression quality
    //     success: async (compressedResult) => {
    //       const formData = new FormData();
    //       formData.append("link", compressedResult, compressedResult.name);
    //       const url = window.location.href;
    //       const lastParam = url.split("/").slice(-1)[0];
    //       formData.append("latitude", this.latitude);
    //       // formData.append("latitude", "10");
    //       formData.append("longitude", this.longitude);
    //       // formData.append("longitude", "10");
    //       formData.append("survey_fill_out", this.surveyId);
    //       formData.append("survey_photo_type", lastParam);
    //       const res = await this.$ApiServiceLayer.post(
    //         this.$PATH.RELATIVE_PATH.POST.UPLOAD_SURVEY_PHOTOS,
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
    //         //   this.changeStatus();
    //         this.getImages();
    //       }
    //     },
    //   };
    //   new Compressor(file, options);
    // },
  async func(event) {
  this.loading = true;
  const file = event.target.files[0];

  // Create a canvas element to convert the image to WebP format
  const canvas = document.createElement('canvas');
  const ctx = canvas.getContext('2d');
  const img = new Image();
  img.src = URL.createObjectURL(file);

  img.onload = async () => {
    // Desired maximum width and height for the image
    const MAX_WIDTH = 1920;  // Higher max width for better resolution
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

    // Convert the canvas content to WebP format with higher quality
    canvas.toBlob(async (webpBlob) => {
      const options = {
        quality: 0.6,
        success: async (compressedResult) => {
          const formData = new FormData();
          const fileName = file.name ? file.name.replace(/\.[^/.]+$/, ".webp") : "image.webp";

          formData.append("link",compressedResult, fileName); // Ensure the filename ends with .webp
          const url = window.location.href;
          const lastParam = url.split("/").slice(-1)[0];
          formData.append("latitude", this.latitude);
          formData.append("longitude", this.longitude);
          formData.append("survey_photo_type", lastParam);
          formData.append("survey_fill_out", this.surveyId);
          
          const res = await this.$ApiServiceLayer.post(
            this.$PATH.RELATIVE_PATH.POST.UPLOAD_SURVEY_PHOTOS,
            this.$PATH.SERVICE_NAME.AUTH,
            formData,
            {
              "Content-Type": "multipart/form-data",
            }
          );

          if (res.status === 200) {
            this.loading = false;
            this.snackbar = true;
            // this.changeStatus();
            this.getImages();
          }
        },
      };

      // Use the Compressor library to compress the WebP blob
      new Compressor(webpBlob, options);
    }, 'image/webp', 0.6); // Set quality to 0.9 for less compression loss
  };
},



    deleteImg(id) {
      this.$ApiServiceLayer
        .delete(
          this.$PATH.RELATIVE_PATH.MULTI.SURVEY_DELETE_IMG + id + "/",
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
.titles {
  font-size: 16px;
  font-weight: 700;
}
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
  height: 129px;
  width: 129px;
  background-image: url("data:image/svg+xml,%3csvg width='100%25' height='100%25' xmlns='http://www.w3.org/2000/svg'%3e%3crect width='100%25' height='100%25' fill='none' rx='4' ry='4' stroke='%23828282FF' stroke-width='2' stroke-dasharray='6%2c 14' stroke-dashoffset='0' stroke-linecap='square'/%3e%3c/svg%3e");
  border-radius: 4px !important;
}
.imagess {
  display: flex;
  justify-content: space-between;
  flex-wrap: wrap;
  margin-bottom: 6px;
  box-shadow: 0px 0px 3px 0px rgba(16, 24, 40, 0.1) !important;
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
