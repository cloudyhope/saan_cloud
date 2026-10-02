<template>
  <svg
    class="action-symbol"
    :class="{ 'is-danger': name === 'delete' }"
    viewBox="0 0 24 24"
    aria-hidden="true"
  >
    <path v-for="(path, index) in paths" :key="index" :d="path" />
  </svg>
</template>
<script>
const icons = {
  view: ['M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12Z', 'M12 9a3 3 0 1 0 0 6 3 3 0 0 0 0-6'],
  delete: ['M3 6h18M9 6V3h6v3M5 6l1 15h12l1-15M10 10v7M14 10v7'],
  edit: ['M12 20H4V4h8M15 4l5 5M9 15l1-5L18 2l4 4-8 8-5 1Z'],
  lock: ['M5 10h14v11H5zM8 10V6a4 4 0 0 1 8 0v4M12 14v3'],
  elevator: ['M5 3h14v18H5zM3 21h18M12 3v18M8 8h1M15 8h1M8 13h1M15 13h1'],
};
export default {
  props: { name: { type: String, default: 'view' } },
  computed: {
    paths() {
      return icons[this.name] || icons.view;
    },
  },
};
</script>
<style scoped>
.action-symbol {
  width: 18px;
  height: 18px;
  fill: none;
  stroke: var(--admin-primary);
  stroke-width: 1.65;
  stroke-linecap: round;
  stroke-linejoin: round;
}
.action-symbol.is-danger {
  stroke: var(--admin-danger);
}
</style>
