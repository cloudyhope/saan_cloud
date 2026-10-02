<template>
  <div class="visit-skeleton-list">
    <v-card
      v-for="n in count"
      :key="'visit-skeleton-' + n"
      class="visit-card"
      elevation="0"
    >
      <div class="skeleton-header">
        <v-skeleton-loader type="avatar" class="skeleton-avatar" />
        <div class="skeleton-text-block">
          <v-skeleton-loader type="text" width="65%" />
          <v-skeleton-loader type="text" width="35%" class="mt-2" />
        </div>
        <v-skeleton-loader type="chip" width="72" height="28" />
      </div>
      <div class="skeleton-body">
        <v-skeleton-loader type="text" width="25%" />
        <v-skeleton-loader type="text" class="mt-2" />
        <v-skeleton-loader type="text" width="25%" class="mt-4" />
        <v-skeleton-loader type="text" width="55%" class="mt-2" />
      </div>
      <v-skeleton-loader type="button" class="skeleton-action mt-4" height="44" />
    </v-card>
  </div>
</template>

<script>
export default {
  name: "VisitCardSkeleton",
  props: {
    count: {
      type: Number,
      default: 3,
    },
  },
};
</script>

<style scoped>
.visit-skeleton-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.visit-card {
  background: white;
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0px 2px 12px rgba(0, 0, 0, 0.06);
  border: 1px solid rgba(53, 122, 225, 0.08);
}

.skeleton-header {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 16px;
}

.skeleton-avatar {
  flex-shrink: 0;
}

.skeleton-text-block {
  flex: 1;
  min-width: 0;
}

.skeleton-action {
  border-radius: 12px;
}
</style>
