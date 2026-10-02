<template>
  <div class="store-detail">
    <div class="d-flex justify-space-between mb-3">
      <span>{{ buildingName }}</span>
      <div>
        <span style="color: #9fa2cd">شناسه پروژه:</span>
        <span>{{ buildingCode }}</span>
      </div>
    </div>
    <div @click="$emit('direction-click')" class="d-flex align-center" style="gap: 8px">
      <img src="../../assets/images/Icons/map.svg" />
      <span style="color: #4285f4">{{ address }}</span>
    </div>
  </div>
</template>

<script>
export default {
  name: 'StoreDetailCard',
  props: {
    buildingName: {
      type: String,
      required: true
    },
    buildingCode: {
      type: String,
      required: true
    },
    address: {
      type: String,
      required: true
    }
  },
  emits: ['direction-click']
}
</script>

<style scoped>
.store-detail {
  display: flex;
  flex-direction: column;
  padding: 16px;
  box-shadow: 0px 0px 3px 0px rgba(16, 24, 40, 0.1);
  border-radius: 8px;
}
</style> 