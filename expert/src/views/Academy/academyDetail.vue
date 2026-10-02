<template>
  <div>
    <BaseTopBar :title="academyDetail.length ? type : ''" />
    <div class="academy-detail-container">
      <product-card
        v-for="(product, index) in academyDetail"
        :key="index"
        :item="product"
        class="mb-4"
        @click="goToTutorial(product.redirect_url)"
      />
    </div>
  </div>
</template>

<script>
import BaseTopBar from "@/components/Topbar/BaseTopbar.vue";
import ProductCard from "@/components/Card/ProductCard.vue";
export default {
  name: "AcademyDetail",
  components: {
    BaseTopBar,
    ProductCard,
  },
  data() {
    return {
      academyDetail: [],
      isLoading: false,
      type: "",
    };
  },
  created() {
    if (!this.isLoading) {
      this.getAcademyDetail();
    }
  },
  methods: {
    async getAcademyDetail() {
      if (this.isLoading) return;
      
      try {
        this.isLoading = true;
        const res = await this.$ApiServiceLayer.get(
          this.$PATH.RELATIVE_PATH.GET.MEDIA_LIST +
            "?p=" +
            this.$STORE.state.userConfig.selectedProject + '&type=' + this.$route.params.id,
          this.$PATH.SERVICE_NAME.EMPTY
        );
        if (res.status === 200) {
          this.academyDetail = res.data;
          this.type = res.data[0].type.title_fa;
        }
      } catch (error) {
        console.error('Failed to fetch academy details:', error);
      } finally {
        this.isLoading = false;
      }
    },
    goToTutorial(url) {
      if (url) {
        window.location.href = url;
      }
    },
  },
};
</script>

<style lang="scss" scoped>
.academy-detail-container {
  padding: 20px;
}
</style>
