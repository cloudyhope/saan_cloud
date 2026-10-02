<template>
  <div class="chat-history-skeleton">
    <div
      v-for="n in count"
      :key="'chat-history-skeleton-' + n"
      class="cards"
    >
      <div class="d-flex align-center flex-grow-1">
        <v-skeleton-loader type="avatar" width="40" height="40" class="ml-2" />
        <div class="skeleton-lines flex-grow-1 mr-2">
          <v-skeleton-loader type="text" width="55%" />
          <v-skeleton-loader type="text" width="80%" class="mt-2" />
        </div>
      </div>
      <div class="d-flex flex-column align-end">
        <v-skeleton-loader type="text" width="48" />
        <v-skeleton-loader type="avatar" width="18" height="18" class="mt-2" />
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: "ChatHistorySkeleton",
  props: {
    count: {
      type: Number,
      default: 4,
    },
  },
};
</script>

<style lang="scss" scoped>
.cards {
  display: flex;
  align-items: center;
  padding: 12px;
  justify-content: space-between;
  border-bottom: 1px solid var(--darken-color, #e0e0e0);
}
</style>
