<template>
  <div class="list-row-skeleton box-container">
    <template v-for="n in count">
      <div :key="'row-skeleton-' + n" class="box">
        <v-skeleton-loader type="text" width="60%" />
        <v-skeleton-loader type="avatar" width="20" height="20" />
      </div>
      <v-divider
        v-if="n < count"
        :key="'divider-skeleton-' + n"
        class="my-0"
      />
    </template>
  </div>
</template>

<script>
export default {
  name: "ListRowSkeleton",
  props: {
    count: {
      type: Number,
      default: 5,
    },
  },
};
</script>

<style lang="scss" scoped>
.box-container {
  box-shadow: 0px 0px 3px 0px rgba(16, 24, 40, 0.1);
  border-radius: 8px;
  background-color: #fff;
  overflow: hidden;
}

.box {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
}
</style>
