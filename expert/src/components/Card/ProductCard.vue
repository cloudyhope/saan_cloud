<template>
  <v-card
    class="product-card"
    elevation="0"
    @click="$emit('click', item)"
    style="cursor: pointer"
  >
    <div class="d-flex">
      <div class="image-section">
        <v-img
          :src="item.image_1"
          contain
          height="110"
          width="110"
          class="product-image"
        />
      </div>
      <div class="content-section">
        <div class="text-right">
          <div class="title-section">{{ item.title }}</div>
          <div class="subtitle-section">{{ item.title_fa }}</div>
          <div class="tag-container" v-if="item.tags">
            <span 
              v-for="(tag, index) in item.tags" 
              :key="index"
              class="tag"
            >
              {{ tag }}
            </span>
          </div>
        </div>
      </div>
     
    </div>
  </v-card>
</template>

<script>
export default {
  name: 'ProductCard',
  props: {
    item: {
      type: Object,
      required: true
    }
  },
  emits: ['click']
}
</script>

<style scoped>
.product-card {
  border-radius: 12px !important;
  box-shadow: 0px 0px 3px 0px rgba(16, 24, 40, 0.1) !important;
  padding: 16px;
}

.content-section {
  /* flex: 1; */
  padding-right: 16px;
}

.title-section {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 8px;
}

.subtitle-section {
  color: #64748B;
  font-size: 14px;
  margin-bottom: 24px;
}

.tag-container {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  background-color: #F4F9FF;
  padding: 12px;
  border-radius: 8px;
}

.tag {
  color: #0F60FF;
  font-size: 14px;
}

.image-section {
  width: 140px;
}

.product-image {
  border-radius: 12px;
  box-shadow: 0px 0px 3px 0px rgba(16, 24, 40, 0.1);
}
</style>