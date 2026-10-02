<template>
  <div class="topbar-wrapper" :style="{ paddingTop: paddingTop + 'px' }">
    <header class="topbar" :style="{ zIndex: zIndex }">
      <SearchBox v-if="variant === 'search'" />
      <h1 v-else-if="variant === 'default'" class="topbar-title">{{ title }}</h1>      
      <button v-if="variant === 'default'" class="back-button" @click="goBack">
        <img v-if="arrow" src="@/assets/images/Icons/right-arrow.svg" alt="back" />
      </button>
    </header>
  </div>
</template>

<script>
import SearchBox from '../SearchBox/index.vue'

export default {
  components: {
    SearchBox
  },
  props: {
    title: {
      type: String,
      default: ''
    },
    variant: {
      type: String,
      default: 'default' // 'search', 'empty', 'default'
    },
    paddingTop: {
      type: Number,
      default: 120
    },
    zIndex: {
      type: Number,
      default: 2
    },
    arrow: {
      type: Boolean,
      default: true
    }
  },
  methods: {
    goBack() {
      this.$router.go(-1)
    }
  }
}
</script>

<style scoped>
.topbar {
  position: fixed;
  top: 0;
  width: 100%;
  max-width: 576px;
  height: 100px;
  background-color: #357AE1;
  padding: 0 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 0px 0px 12px 12px;
}

.topbar-title {
  color: white;
  font-size: 18px;
  font-weight: 700;
  margin: 0;
  text-align: center;
}

.back-button {
    display: flex;
  position: absolute;
  right: 20px;
  background: none;
  border: none;
  padding: 0;
  cursor: pointer;
}

.back-button img {
  width: 20px;
  height: 20px;
}
</style> 