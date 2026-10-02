<template>
  <div class="skeleton-container">
    <v-skeleton-loader
      v-for="n in count"
      :key="'chat-bubble-skeleton-' + n"
      type="card"
      :class="bubbleClass(n)"
      class="skeleton-bubble"
      :height="bubbleHeight"
      :max-width="maxWidth"
    />
  </div>
</template>

<script>
export default {
  name: "ChatBubbleSkeleton",
  props: {
    count: {
      type: Number,
      default: 6,
    },
    maxWidth: {
      type: String,
      default: "161px",
    },
    bubbleHeight: {
      type: String,
      default: "50px",
    },
  },
  methods: {
    bubbleClass(index) {
      return index % 2 === 0 ? "skeleton-left" : "skeleton-right";
    },
  },
};
</script>

<style lang="scss" scoped>
.skeleton-container {
  display: flex;
  flex-direction: column;
}

.skeleton-bubble {
  margin: 5px 0 20px 0;
  border-radius: 12px;
}

.skeleton-left {
  align-self: flex-start;
}

.skeleton-right {
  align-self: flex-end;
}
</style>
