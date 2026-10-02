<template>
  <span class="navigation-icon" aria-hidden="true">
    <img v-if="source && !failed" :src="source" :class="{ inverse }" alt="" @error="failed = true" />
    <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.65" stroke-linecap="round" stroke-linejoin="round">
      <path v-for="(path, index) in paths" :key="index" :d="path" />
    </svg>
  </span>
</template>
<script>
const icons = {
  dashboard: ['M3 3h7v7H3zM14 3h7v7h-7zM3 14h7v7H3zM14 14h7v7h-7z'],
  user: ['M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8M22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75'],
  visit: ['M9 5H5v16h14V5h-4M9 3h6v4H9zM8 12h8M8 16h5'],
  survey: ['M9 3h6v4H9zM9 5H5v16h14V5h-4M8 12l2 2 4-4M8 18h8'],
  store: ['M3 10h18l-2-7H5zM4 10v11h16V10M9 21v-7h6v7M3 10a3 3 0 0 0 6 0 3 3 0 0 0 6 0 3 3 0 0 0 6 0'],
  ticket: ['M4 13v-2a8 8 0 0 1 16 0v6a4 4 0 0 1-4 4h-3M4 11H2v6h4v-6zM20 11h2v6h-4v-6z'],
  warehouse: ['M12 3l9 5v9l-9 5-9-5V8zM3 8l9 5 9-5M12 13v9M7.5 5.5l9 5'],
  customer: ['M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8M5 21v-2a5 5 0 0 1 5-5h4a5 5 0 0 1 5 5v2'],
  media: ['M3 3h18v18H3zM3 16l5-5 5 5 3-3 5 5M16 7h.01'],
  wallet: ['M3 6h17v15H3zM3 6V3h15v3M16 11h5v5h-5zM17.5 13.5h.01'],
  building: ['M5 21V3h14v18M3 21h18M9 7h.01M15 7h.01M9 11h.01M15 11h.01M10 21v-6h4v6'],
  settings: ['M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8M12 2v3M12 19v3M2 12h3M19 12h3M5 5l2 2M17 17l2 2M5 19l2-2M17 7l2-2'],
  folder: ['M3 5h6l2 2h10v14H3z'],
};
export default {
  name: 'NavigationIcon',
  props: { source: String, route: String, name: String, group: Boolean, inverse: Boolean },
  data() { return { failed: false }; },
  watch: { source() { this.failed = false; } },
  computed: {
    paths() {
      const key = (this.route || '') + ' ' + (this.name || '');
      const matches = [
        ['dashboard', /dashboard|داشبورد/], ['user', /usermanagement|role|کاربر|نقش/],
        ['customer', /customer|client|مشتری/], ['survey', /survey|suvey|نظرسنجی/],
        ['ticket', /ticket|تیکت|پشتیبان/], ['warehouse', /warehouse|ware|انبار|کالا/],
        ['wallet', /wallet|account|credit|حساب|مالی|کیف/], ['media', /media|photo|رسانه|تصویر/],
        ['store', /store|outlet|فروشگاه/], ['building', /elevator|building|آسانسور|ساختمان/],
        ['visit', /visit|action|ویزیت|عملیات|برنامه/], ['settings', /setting|config|تنظیم/],
      ];
      const found = matches.find(([, pattern]) => pattern.test(key));
      return icons[found ? found[0] : (this.group ? 'folder' : 'visit')];
    },
  },
};
</script>
<style scoped>
.navigation-icon { width: 22px; height: 22px; flex: 0 0 22px; display: inline-flex; align-items: center; justify-content: center; }
img, svg { width: 100%; height: 100%; object-fit: contain; }
.inverse { filter: none; }
</style>
