<template>
  <section class="box filter-panel" :class="{ 'is-collapsed': !open }">
    <div class="filter-heading">
      <div>
        <span class="filter-symbol" aria-hidden="true"
          ><svg viewBox="0 0 24 24"><path d="M3 5h18l-7 8v6l-4 2v-8z" /></svg
        ></span>
        <h2>{{ title }}</h2>
      </div>
      <button
        type="button"
        class="filter-toggle"
        :aria-expanded="open"
        :aria-controls="panelId"
        @click="open = !open"
      >
        {{ open ? 'بستن فیلترها' : 'نمایش فیلترها'
        }}<svg viewBox="0 0 20 20" :class="{ rotated: open }" aria-hidden="true">
          <path d="m6 8 4 4 4-4" />
        </svg>
      </button>
    </div>
    <form v-show="open" :id="panelId" @submit.prevent="$emit('apply')">
      <div class="filter-grid"><slot /></div>
      <div v-if="$slots.actions" class="filter-footer"><slot name="actions" /></div>
    </form>
  </section>
</template>
<script>
export default {
  props: { title: { type: String, default: 'جست‌وجو و فیلتر' } },
  data() {
    return { open: true };
  },
  computed: {
    panelId() {
      return 'filters-' + this._uid;
    },
  },
};
</script>
<style scoped>
h2 {
  color: var(--admin-text);
  font-size: 14px;
  font-weight: 700;
  margin: 0;
}
.filter-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 18px 20px;
  padding-top: 20px;
}
.filter-footer {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid var(--admin-border);
}
@media (max-width: 575px) {
  .filter-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 16px 12px;
  }
  .filter-footer > button {
    flex: 1;
  }
}
@media (max-width: 359px) {
  .filter-grid {
    grid-template-columns: 1fr;
  }
}
</style>
