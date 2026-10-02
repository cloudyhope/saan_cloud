<template>
  <div :style="boxStyle" class="custom-box" @click="handleClick">
    <img
      :src="require(`@/assets/images/Icons/${icon}`)"
      alt="icon"
      class="box-image"
    />
    <p class="box-text">{{ text }}</p>
  </div>
</template>

<script>
export default {
  name: "CustomBox",
  props: {
    icon: {
      type: String,
      default: "",
    },
    text: {
      type: String,
      required: true,
    },
    background: {
      type: String,
      default: "#ffffff",
    },
  },
  computed: {
    boxStyle() {
      return {
        backgroundColor: this.background,
        // margin: "14px",
        borderRadius: "8px",
        minWidth: "160px",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        padding: "20px",
      };
    },
  },
  methods: {
    handleClick() {
      this.$emit('box-clicked');
    },
  },
};
</script>

<style scoped>
.custom-box {
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.box-image {
  width: 40px;
  height: 40px;
  margin-bottom: 10px;
}

.box-text {
  margin: 0;
  font-size: 14px;
  text-align: center;
  color: #000000;
}
</style>
