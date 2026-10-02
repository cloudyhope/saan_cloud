<template>
  <div class="table-view">
    <div v-if="recordCount !== undefined" class="table-caption">
      <div class="table-caption-title">
        <NavigationIcon :route="$route.path" />
        <h2>{{ tableTitle || $route.meta.title || 'نتایج' }}</h2>
        <span v-if="!showNoContent && !errorMessage" class="record-count"
          >{{ recordCount.toLocaleString('fa-IR') }} مورد</span
        >
      </div>
      <div class="table-controls"><slot name="controls" /></div>
    </div>
    <div v-if="scrollWidth > containerWidth" class="table-scroll-hint">
      برای مشاهده همه ستون‌ها، جدول را افقی حرکت دهید.<svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M4 12h16M7 9l-3 3 3 3m10-6 3 3-3 3" />
      </svg>
    </div>
    <div
      ref="topScroll"
      class="scroll-top-container"
      @scroll="syncScroll('top')"
      v-show="scrollWidth > containerWidth"
    >
      <div class="scroll-handler" :style="{ width: scrollWidth + 'px' }"></div>
    </div>
    <div
      ref="tableScroll"
      class="table-responsive"
      @scroll="syncScroll('table')"
      :aria-busy="showNoContent"
      tabindex="0"
      :aria-label="'جدول ' + (tableTitle || $route.meta.title || 'اطلاعات')"
    >
      <table
        ref="table"
        class="table content-table-view"
        :id="resolvedTableId"
        :class="{
          'table-dark': dark,
          'table-bordered': bordered,
          'table-striped': striped,
          'table-hover': hover || hoverAnimation,
        }"
      >
        <thead>
          <slot name="TableTitle" />
        </thead>
        <thead v-if="$slots.TableSearch">
          <slot name="TableSearch" />
        </thead>
        <tbody>
          <tr v-if="showNoContent">
            <td :colspan="columnCount" class="table-state">
              <span class="spinner-border spinner-border-sm" aria-hidden="true"></span
              ><span role="status">در حال دریافت اطلاعات…</span>
            </td>
          </tr>
          <tr v-else-if="errorMessage">
            <td :colspan="columnCount" class="table-state">
              <p role="alert">{{ errorMessage }}</p>
              <button class="btn btn-outline-primary" type="button" @click="$emit('retry')">
                تلاش مجدد
              </button>
            </td>
          </tr>
          <tr v-else-if="showNoData">
            <td :colspan="columnCount" class="table-state">
              <span class="empty-symbol" aria-hidden="true"
                ><svg viewBox="0 0 24 24">
                  <path d="M10 3a7 7 0 1 0 0 14 7 7 0 0 0 0-14M15 15l6 6M7 10h6" /></svg
              ></span>
              <strong>موردی یافت نشد</strong
              ><small class="empty-description">اطلاعاتی برای نمایش در این فهرست وجود ندارد.</small>
            </td>
          </tr>
          <slot v-else name="TableBody" />
        </tbody>
      </table>
    </div>
    <div v-if="$slots.footer" class="table-footer">
      <span class="table-range" role="status">{{
        showNoContent
          ? 'در حال دریافت اطلاعات…'
          : errorMessage
          ? 'دریافت اطلاعات ناموفق بود'
          : recordCount
          ? 'نمایش ' +
            rangeStart.toLocaleString('fa-IR') +
            ' تا ' +
            rangeEnd.toLocaleString('fa-IR') +
            ' از ' +
            recordCount.toLocaleString('fa-IR') +
            ' مورد'
          : 'بدون نتیجه'
      }}</span>
      <slot name="footer" />
    </div>
  </div>
</template>
<script>
import NavigationIcon from '../NavigationIcon/index.vue';
export default {
  components: { NavigationIcon },
  props: {
    dark: Boolean,
    hover: Boolean,
    hoverAnimation: Boolean,
    bordered: Boolean,
    striped: Boolean,
    showFooterColumn: { type: Boolean, default: true },
    showNoContent: Boolean,
    showNoData: Boolean,
    tableId: String,
    errorMessage: String,
    recordCount: Number,
    tableTitle: String,
    page: { type: Number, default: 1 },
    perPage: { type: Number, default: 20 },
  },
  computed: {
    resolvedTableId() {
      return this.tableId || 'admin-table-' + this._uid;
    },
    rangeStart() {
      return Math.min((this.page - 1) * this.perPage + 1, this.recordCount || 0);
    },
    rangeEnd() {
      return Math.min(this.page * this.perPage, this.recordCount || 0);
    },
  },
  data() {
    return { scrollWidth: 0, containerWidth: 0, columnCount: 1 };
  },
  methods: {
    measure() {
      const table = this.$refs.table;
      if (!table) return;
      this.scrollWidth = table.scrollWidth;
      this.containerWidth = this.$refs.tableScroll.clientWidth;
      const row = table.querySelector('thead tr');
      const count = row
        ? Array.from(row.cells).reduce((sum, cell) => sum + (cell.colSpan || 1), 0)
        : 1;
      if (this.columnCount !== count) this.columnCount = count;
    },
    syncScroll(source) {
      const from = source === 'top' ? this.$refs.topScroll : this.$refs.tableScroll;
      const to = source === 'top' ? this.$refs.tableScroll : this.$refs.topScroll;
      if (from && to && to.scrollLeft !== from.scrollLeft) to.scrollLeft = from.scrollLeft;
    },
  },
  mounted() {
    this.measure();
    window.addEventListener('resize', this.measure);
    if (typeof ResizeObserver !== 'undefined') {
      this.tableObserver = new ResizeObserver(this.measure);
      this.tableObserver.observe(this.$refs.table);
      this.tableObserver.observe(this.$refs.tableScroll);
    }
  },
  updated() {
    this.$nextTick(this.measure);
  },
  beforeDestroy() {
    window.removeEventListener('resize', this.measure);
    if (this.tableObserver) this.tableObserver.disconnect();
  },
};
</script>
<style scoped>
.table-view {
  border: 1px solid var(--admin-border);
  border-radius: 12px;
  overflow: hidden;
  margin-top: 12px;
}
.table-caption {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
  padding: 18px 20px;
  background: #fff;
  border-bottom: 1px solid var(--admin-border);
}
.table-caption-title {
  display: flex;
  align-items: center;
  gap: 10px;
  color: var(--admin-primary);
}
.table-caption h2 {
  font-size: 14px;
  font-weight: 700;
  margin: 0;
  color: var(--admin-text);
}
.record-count {
  background: var(--admin-primary-soft);
  color: var(--admin-primary);
  font-size: 12px;
  padding: 3px 10px;
  border-radius: 20px;
  white-space: nowrap;
}
.table-controls {
  display: flex;
  align-items: center;
  gap: 10px;
}
.table-scroll-hint {
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: var(--admin-muted);
  background: #fafbfe;
  padding: 8px 20px;
  font-size: 12px;
}
.table-scroll-hint svg {
  width: 20px;
  height: 20px;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.5;
  flex-shrink: 0;
}
.scroll-top-container {
  overflow-x: auto;
  overflow-y: hidden;
}
.scroll-handler {
  height: 2px;
}
.table-responsive {
  overflow-x: auto;
}
.table {
  margin: 0;
  font-size: 12px;
}
.table th {
  background: #f1f5f9;
  color: #475569;
  font-weight: 700;
  white-space: nowrap;
}
.table td,
.table th {
  text-align: right;
  padding: 14px 16px;
  vertical-align: middle;
  border: 0;
  border-bottom: 1px solid var(--admin-border);
}
.table td:first-child,
.table th:first-child {
  text-align: center;
  color: var(--admin-muted);
  width: 52px;
}
.table .table-state {
  text-align: center;
}
.table tbody {
  background: #fff;
}
.table tbody tr:last-child td {
  border-bottom: 0;
}
.table-state {
  height: 148px;
  color: var(--admin-muted);
}
.table-state .spinner-border {
  margin-left: 10px;
  color: var(--admin-primary);
}
.empty-symbol {
  display: grid;
  place-items: center;
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: #f0f4fb;
  color: #8a9bb7;
  margin: 0 auto 12px;
}
.empty-symbol svg {
  width: 25px;
  height: 25px;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.6;
  stroke-linecap: round;
}
.empty-description {
  display: block;
  font-size: 12px;
  font-weight: 400;
  margin-top: 6px;
}
.table-dark th,
.table-dark tbody {
  background: #1e293b;
  color: #fff;
}
.table-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
  padding: 16px 20px;
  border-top: 1px solid var(--admin-border);
}
.table-range {
  font-size: 12px;
  color: var(--admin-muted);
}
@media (max-width: 575px) {
  .table-caption,
  .table-footer {
    padding: 16px;
  }
  .table-controls {
    width: 100%;
    justify-content: space-between;
  }
  .table-footer {
    justify-content: center;
  }
  .table-range {
    width: 100%;
    text-align: center;
  }
}
</style>
