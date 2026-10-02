<template>
  <nav v-if="pageCount > 1" class="list-pagination" aria-label="صفحه‌بندی">
    <button
      type="button"
      class="edge-page"
      :disabled="value <= 1 || disabled"
      aria-label="صفحه اول"
      title="صفحه اول"
      @click="go(1)"
    >
      <svg viewBox="0 0 24 24"><path d="m6 6 6 6-6 6m6-12 6 6-6 6" /></svg>
    </button>
    <button
      type="button"
      :disabled="value <= 1 || disabled"
      aria-label="صفحه قبلی"
      title="صفحه قبلی"
      @click="go(value - 1)"
    >
      <svg viewBox="0 0 24 24"><path d="m9 6 6 6-6 6" /></svg>
    </button>
    <button
      v-for="page in pages"
      :key="page"
      type="button"
      :class="{ active: page === value }"
      :aria-current="page === value ? 'page' : null"
      :aria-label="'صفحه ' + page.toLocaleString('fa-IR')"
      :disabled="disabled"
      @click="go(page)"
    >
      {{ page.toLocaleString('fa-IR') }}
    </button>
    <button
      type="button"
      :disabled="value >= pageCount || disabled"
      aria-label="صفحه بعدی"
      title="صفحه بعدی"
      @click="go(value + 1)"
    >
      <svg viewBox="0 0 24 24"><path d="m15 6-6 6 6 6" /></svg>
    </button>
    <button
      type="button"
      class="edge-page"
      :disabled="value >= pageCount || disabled"
      aria-label="صفحه آخر"
      title="صفحه آخر"
      @click="go(pageCount)"
    >
      <svg viewBox="0 0 24 24"><path d="m18 6-6 6 6 6m-6-12-6 6 6 6" /></svg>
    </button>
  </nav>
</template>
<script>
export default {
  props: {
    value: { type: Number, default: 1 },
    records: { type: Number, default: 0 },
    perPage: { type: Number, default: 20 },
    disabled: Boolean,
  },
  computed: {
    pageCount() {
      return Math.max(1, Math.ceil(this.records / this.perPage));
    },
    pages() {
      const start = Math.max(1, Math.min(this.value - 1, this.pageCount - 2));
      return Array.from({ length: Math.min(3, this.pageCount) }, (_, index) => start + index);
    },
  },
  methods: {
    go(page) {
      if (this.disabled || page < 1 || page > this.pageCount || page === this.value) return;
      this.$emit('input', page);
      this.$nextTick(() => this.$emit('paginate', page));
    },
  },
};
</script>
<style scoped>
.list-pagination {
  display: flex;
  align-items: center;
  gap: 5px;
}
button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  padding: 0;
  border: 1px solid var(--admin-border);
  border-radius: 8px;
  background: #fff;
  color: #617089;
  font-size: 13px;
  font-family: 'IRANYekanfa', sans-serif;
}
button:hover:not(:disabled):not(.active) {
  background: var(--admin-primary-soft);
  border-color: #b6c5ee;
}
button.active {
  background: var(--admin-primary);
  border-color: var(--admin-primary);
  color: #fff;
  box-shadow: 0 2px 6px #345de02b;
}
button:disabled {
  opacity: 0.4;
  background: #f7f9fc;
}
svg {
  width: 16px;
  height: 16px;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.6;
  stroke-linecap: round;
  stroke-linejoin: round;
}
@media (max-width: 575px) {
  button {
    width: 44px;
    height: 44px;
  }
  .edge-page {
    display: none;
  }
}
</style>
