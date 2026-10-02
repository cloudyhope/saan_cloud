<template>
  <div class="workload" :class="{ 'has-selection': !!selected }">
    <div class="legend" aria-hidden="true">
      <span v-for="part in parts" :key="part.key"><i :style="{ background: part.color }" />{{ part.label }}</span>
    </div>
    <ul>
      <li v-for="row in shown" :key="row.key">
        <button type="button" class="row" :class="{ selected: row.key === selected }" :aria-pressed="row.key === selected ? 'true' : 'false'"
                :aria-label="`${row.label}: ${fa(row.overdue)} دیرکرد، ${fa(row.open)} باز، ${fa(row.completed)} پایان‌یافته`"
                @click="$emit('select', row.key === selected ? '' : row.key)">
          <span class="name">{{ row.label }}<small v-if="row.rating">★ {{ fa(row.rating, 1) }}</small></span>
          <span class="stack">
            <span v-for="part in parts" v-show="row[part.key]" :key="part.key" class="seg" :style="{ width: share(row[part.key]) + '%', background: part.color }"
                  @mouseenter="tip = { row, part }" @mouseleave="tip = null" />
          </span>
          <span class="total">{{ fa(row.total) }}</span>
        </button>
        <div v-if="tip && tip.row === row" class="tip" role="status"><b>{{ fa(row[tip.part.key]) }}</b> {{ tip.part.label }} · {{ row.label }}</div>
      </li>
      <li v-if="!rows.length" class="empty"><EmptyState kind="visits" size="sm" inline title="کاری برای کارشناسان ثبت نشده" description="" /></li>
    </ul>
    <button v-if="rows.length > limit" type="button" class="more" @click="expanded = !expanded">{{ expanded ? 'نمایش کمتر' : `نمایش همه (${fa(rows.length)})` }}</button>
  </div>
</template>

<script>
import { fa } from './format';

import EmptyState from '@/components/EmptyState/index.vue';
export default {
  components: { EmptyState },
  name: 'WorkloadBars',
  props: { rows: { type: Array, required: true }, selected: { type: [String, Number], default: '' } },
  data: () => ({
    tip: null, expanded: false, limit: 8,
    parts: [{ key: 'overdue', label: 'دیرکرد', color: '#d03b3b' }, { key: 'open', label: 'باز', color: '#2a78d6' },
      { key: 'completed', label: 'پایان‌یافته در بازه', color: '#0ca30c' }],
  }),
  computed: {
    max() { return Math.max(1, ...this.rows.map(row => row.total)); },
    shown() { return this.expanded ? this.rows : this.rows.slice(0, this.limit); },
  },
  methods: { fa, share(value) { return (value / this.max) * 100; } },
};
</script>

<style scoped>
.legend { display: flex; flex-wrap: wrap; gap: 14px; font-size: 12px; color: #4a566c; margin-bottom: 8px; }
.legend span { display: inline-flex; align-items: center; gap: 6px; }
.legend i { width: 10px; height: 10px; border-radius: 3px; }
ul { list-style: none; margin: 0; padding: 0; display: grid; gap: 2px; }
li { position: relative; }
.row { display: grid; grid-template-columns: minmax(110px, 34%) 1fr 36px; align-items: center; gap: 10px; width: 100%; min-height: 38px;
  padding: 4px 8px; border: 0; border-radius: 9px; background: transparent; font: inherit; font-size: 12.5px; color: #33405a; text-align: right; cursor: pointer; }
.row:hover { background: #f3f6fb; }
.row:focus-visible { outline: 3px solid #345de0; outline-offset: 1px; }
.has-selection .row:not(.selected) { opacity: .45; }
.row.selected { background: #eef3fd; }
.name { display: flex; align-items: baseline; gap: 6px; min-width: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.name small { color: #8f6200; font-size: 11px; font-weight: 700; }
.stack { display: flex; gap: 2px; height: 12px; }
.seg { height: 100%; border-radius: 4px; min-width: 4px; transition: width .3s ease; }
.total { text-align: left; font-weight: 800; color: #17233b; font-variant-numeric: tabular-nums; }
.tip { position: absolute; top: -30px; left: 50px; z-index: 3; padding: 6px 10px; border-radius: 9px; background: #fff; border: 1px solid #dfe5ef;
  box-shadow: 0 10px 24px #1b2a4a24; font-size: 12px; color: #4a566c; white-space: nowrap; pointer-events: none; }
.tip b { color: #17233b; }
.empty { padding: 18px 8px; color: #7a8496; font-size: 12px; text-align: center; }
.more { margin-top: 6px; border: 0; background: transparent; color: #345de0; font: inherit; font-size: 12px; font-weight: 700; cursor: pointer; }
</style>
