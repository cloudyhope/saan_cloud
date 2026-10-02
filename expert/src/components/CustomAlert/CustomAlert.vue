<template>
  <div class="custom-alert mb-4" :style="{ backgroundColor: bgColor,  borderRightColor: borderColor }">
    <div class="alert-content">
      <img
        width="24"
        :src="require(`@/assets/images/Icons/${icon}`)"
        alt="alert icon"
      />
      <span class="alert-message"><slot></slot></span>
    </div>
  </div>
</template>

<script>
export default {
  name: 'CustomAlert',
  props: {
    icon: {
      type: String,
    },
    bgColor: {
      type: String,
      default: 'rgba(233, 173, 18, 0.1)'
    },
    borderColor: {
        type: String,
      default: '#E9AD12'
    }
  }
}
</script>

<style lang="scss" scoped>
.alert-content {
  display: flex;
  align-items: center;
  gap: 10px;
}
.custom-alert {
  border-right: 4px solid;
  padding: 6px 12px;
  border-radius: 4px;
}
</style> 