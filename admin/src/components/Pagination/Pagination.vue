<template>
  <nav aria-label="صفحه‌بندی" v-if="pagesCount > 1">
    <ul class="pagination" :style="{ justifyContent: position === 'start' ? 'flex-start' : position === 'end' ? 'flex-end' : 'center' }">
      <li class="page-item"><button type="button" class="page-link" :disabled="activePage === 1" @click="onPaginationClicked(activePage - 1)">قبلی</button></li>
      <li v-for="page in visiblePages" :key="page" class="page-item" :class="{ active: page === activePage }"><button type="button" class="page-link" :aria-current="page === activePage ? 'page' : null" :aria-label="'صفحه ' + page" @click="onPaginationClicked(page)">{{ page }}</button></li>
      <li class="page-item"><button type="button" class="page-link" :disabled="activePage === pagesCount" @click="onPaginationClicked(activePage + 1)">بعدی</button></li>
    </ul>
  </nav>
</template>
<script>
export default {
  props: {
    totalItemsCount: { required: true },
    customItemsPerPage: Number,
    itemsToShow: { default: 10 },
    activeColor: { type: String, default: 'primary' },
    position: { type: String, default: 'center' },
    itemsPerPage: { default: 10 },
  },
  data() { return { activePage: 1 }; },
  computed: {
    pagesCount() { return Math.max(1, Math.ceil((Number(this.totalItemsCount) || 0) / Math.max(1, Number(this.customItemsPerPage || this.itemsPerPage) || 10))); },
    visiblePages() {
      const count = Math.max(1, Math.floor(Number(this.itemsToShow) || 10));
      const start = Math.max(1, Math.min(this.activePage - Math.floor(count / 2), this.pagesCount - count + 1));
      return Array.from({ length: Math.min(count, this.pagesCount - start + 1) }, (_, index) => start + index);
    },
  },
  watch: {
    pagesCount(value) { if (this.activePage > value) this.onPaginationClicked(value); },
    itemsPerPage() { if (this.activePage !== 1) this.onPaginationClicked(1); },
    customItemsPerPage() { if (this.activePage !== 1) this.onPaginationClicked(1); },
  },
  methods: {
    onPaginationClicked(page) {
      if (!Number.isInteger(page) || page < 1 || page > this.pagesCount || page === this.activePage) return;
      this.activePage = page;
      this.$emit('onPageClicked', page);
    },
  },
};
</script>
<style scoped>
.pagination { display: flex; flex-wrap: wrap; gap: 6px; padding: 12px 0; margin: 0; }
.page-link { min-width: 40px; min-height: 40px; padding: 8px 12px; border: 1px solid var(--admin-border); border-radius: 8px; background: #fff; color: #475569; font-size: 12px; }
.active .page-link { background: var(--admin-primary); border-color: var(--admin-primary); color: #fff; }
.page-link:disabled { color: #94a3b8; background: #f8fafc; }
</style>
