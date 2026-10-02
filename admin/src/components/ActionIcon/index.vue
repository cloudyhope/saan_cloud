<template>
  <svg
    class="action-symbol"
    :class="{ 'is-danger': name === 'delete' && !inherit, inherit, dots: name === 'more' }"
    viewBox="0 0 24 24"
    aria-hidden="true"
  >
    <path v-for="(path, index) in paths" :key="index" :d="path" />
  </svg>
</template>
<script>
// One outline set (24px grid, 1.8 stroke, round caps) for every table action and menu entry.
const icons = {
  view: ['M2.06 12.35a1 1 0 0 1 0-.7 10.75 10.75 0 0 1 19.88 0 1 1 0 0 1 0 .7 10.75 10.75 0 0 1-19.88 0', 'M12 9a3 3 0 1 0 0 6 3 3 0 0 0 0-6'],
  edit: ['M12 3H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7', 'M18.4 2.6a2.1 2.1 0 0 1 3 3L12 15l-4 1 1-4z'],
  delete: ['M3 6h18', 'M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6', 'M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2', 'M10 11v6M14 11v6'],
  lock: ['M5 11h14a2 2 0 0 1 2 2v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2', 'M7 11V7a5 5 0 0 1 10 0v4'],
  elevator: ['M5 3h14v18H5z', 'M12 3v18', 'M7.5 10 9 8l1.5 2M13.5 14l1.5 2 1.5-2'],
  building: ['M6 22V4a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v18', 'M6 12H4a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2h2', 'M18 9h2a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2h-2', 'M10 6h4M10 10h4M10 14h4M10 18h4'],
  'building-plus': ['M6 22V4a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v7', 'M6 12H4a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2h2', 'M10 6h4M10 10h4M10 14h2', 'M19 15v6M16 18h6'],
  report: ['M8 2h8v4H8z', 'M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2', 'M12 11h4M12 16h4M8 11h.01M8 16h.01'],
  history: ['M3 12a9 9 0 1 0 3-6.7L3 8', 'M3 3v5h5', 'M12 7v5l3 2'],
  transfer: ['M4 8h14l-3-3M20 16H6l3 3'],
  plus: ['M12 5v14M5 12h14'],
  minus: ['M5 12h14'],
  download: ['M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4', 'M7 10l5 5 5-5M12 15V3'],
  file: ['M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z', 'M14 2v6h6M8 13h8M8 17h5'],
  image: ['M5 3h14a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2', 'M9 9.5a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3', 'M21 15l-5-5L5 21'],
  comment: ['M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z', 'M8 9h8M8 13h5'],
  play: ['M6 4l14 8-14 8z'],
  box: ['M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z', 'M3.3 7 12 12l8.7-5M12 22V12'],
  trash: ['M3 6h18', 'M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6', 'M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2'],
  user: ['M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2', 'M12 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8'],
  check: ['M20 6 9 17l-5-5'],
  close: ['M18 6 6 18M6 6l12 12'],
  more: ['M12 5v.01M12 12v.01M12 19v.01'],
};
export default {
  props: { name: { type: String, default: 'view' }, inherit: Boolean },
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
  stroke-width: 1.8;
  stroke-linecap: round;
  stroke-linejoin: round;
}
.action-symbol.dots { stroke-width: 3; }
.action-symbol.is-danger {
  stroke: var(--admin-danger);
}
.action-symbol.inherit {
  stroke: currentColor;
}
</style>
