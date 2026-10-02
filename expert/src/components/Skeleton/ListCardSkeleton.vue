<template>
  <div class="list-skeleton">
    <v-card
      v-for="n in count"
      :key="'list-skeleton-' + n"
      class="cards-shadow pa-4"
      :class="{ 'mt-2': n > 1 }"
      elevation="0"
    >
      <div class="d-flex justify-space-between align-center">
        <div class="d-flex align-center flex-grow-1">
          <v-skeleton-loader type="avatar" class="skeleton-icon" />
          <div class="skeleton-lines mr-4 flex-grow-1">
            <v-skeleton-loader type="text" width="70%" />
            <v-skeleton-loader
              v-if="twoLine"
              type="text"
              width="40%"
              class="mt-2"
            />
          </div>
        </div>
        <v-skeleton-loader type="avatar" width="24" height="24" />
      </div>
    </v-card>
  </div>
</template>

<script>
export default {
  name: "ListCardSkeleton",
  props: {
    count: {
      type: Number,
      default: 4,
    },
    twoLine: {
      type: Boolean,
      default: false,
    },
  },
};
</script>

<style scoped>
.cards-shadow {
  box-shadow: 0px 0px 3px 0px rgba(16, 24, 40, 0.1) !important;
  border-radius: 8px;
}

.skeleton-icon >>> .v-skeleton-loader__avatar {
  width: 48px;
  height: 48px;
  border-radius: 2px;
}
</style>
