<template>
  <v-card 
    @click="handleClick"
    class="explore-card d-flex justify-space-between align-center"
  >
    <div class="d-flex align-center">
      <v-img :max-width="18" :src="getIconPath" />
      <span :class="['mr-2', { 'exit-text': isExitCard }]">{{ title }}</span>
    </div>
    <div v-if="showArrow">
      <v-img max-width="18" src="@/assets/images/Icons/left-icon.svg" />
    </div>
  </v-card>
</template>

<script>
export default {
  name: 'ExploreCard',
  props: {
    icon: {
      type: String,
      required: true
    },
    title: {
      type: String,
      required: true
    },
    showArrow: {
      type: Boolean,
      default: false
    },
    isExitCard: {
      type: Boolean,
      default: false
    }
  },
  computed: {
    getIconPath() {
      return require(`@/assets/images/Icons/${this.icon}.svg`)
    }
  },
  methods: {
    handleClick() {
      this.$emit('click')
    }
  }
}
</script>

<style lang="scss" scoped>
.explore-card {
  display: flex;
  border-radius: 8px;
  margin: 12px 0;
  padding: 14px;
  box-shadow: 0px 0px 3px 0px rgba(16, 24, 40, 0.1) !important;
}

.exit-text {
  color: #ed1c24;
}
</style> 