<template>
  <ul class="bar-list" :class="{ 'has-selection': !!selected }">
    <li v-for="item in items" :key="item.key">
      <button type="button" class="bar-row" :class="{ selected: item.key === selected, empty: !item.value }"
              :aria-pressed="item.key === selected ? 'true' : 'false'" :disabled="!item.value && item.key !== selected"
              :title="`${item.label}: ${fa(item.value)}`" @click="$emit('select', item.key === selected ? '' : item.key)">
        <span class="bar-label"><i v-if="item.color" class="swatch" :style="{ background: item.color }" />{{ item.label }}</span>
        <span class="bar-track"><span class="bar-fill" :style="{ width: share(item.value) + '%', background: item.color || color }" /></span>
        <span class="bar-value">{{ fa(item.value) }}</span>
      </button>
    </li>
    <li v-if="!items.length" class="bar-empty">{{ empty }}</li>
  </ul>
</template>

<script>
import { fa } from './format';

export default {
  name: 'BarList',
  props: {
    items: { type: Array, required: true }, // [{ key, label, value, color? }]
    selected: { type: [String, Number], default: '' },
    color: { type: String, default: '#2a78d6' },
    empty: { type: String, default: 'داده‌ای در این بازه نیست.' },
  },
  computed: { max() { return Math.max(1, ...this.items.map(item => item.value)); } },
  methods: { fa, share(value) { return value ? Math.max(3, (value / this.max) * 100) : 0; } },
};
</script>

<style scoped>
.bar-list { list-style: none; margin: 0; padding: 0; display: grid; gap: 4px; }
.bar-row { display: grid; grid-template-columns: minmax(110px, 38%) 1fr 44px; align-items: center; gap: 10px; width: 100%; min-height: 36px;
  padding: 4px 8px; border: 0; border-radius: 9px; background: transparent; color: #33405a; font: inherit; font-size: 12.5px; text-align: right; cursor: pointer; }
.bar-row:hover:not(:disabled) { background: #f3f6fb; }
.bar-row:disabled { cursor: default; }
.bar-row:focus-visible { outline: 3px solid #345de0; outline-offset: 1px; }
.has-selection .bar-row:not(.selected) { opacity: .45; }
.bar-row.selected { background: #eef3fd; }
.bar-label { display: flex; align-items: center; gap: 7px; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.swatch { flex: none; width: 10px; height: 10px; border-radius: 3px; }
.bar-track { height: 10px; border-radius: 4px; background: #eef1f6; overflow: hidden; display: flex; justify-content: flex-start; }
.bar-fill { height: 100%; border-radius: 4px; transition: width .3s ease; }
.bar-value { text-align: left; font-weight: 800; color: #17233b; font-variant-numeric: tabular-nums; }
.empty .bar-value, .empty .bar-label { color: #9aa3b5; }
.bar-empty { padding: 18px 8px; color: #7a8496; font-size: 12px; text-align: center; }
</style>
