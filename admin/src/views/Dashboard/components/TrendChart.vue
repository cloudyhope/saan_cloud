<template>
  <div class="trend" @mouseleave="hover = -1">
    <div class="legend" aria-hidden="true">
      <span><i :style="{ background: colors.created }" />ثبت مأموریت</span>
      <span><i :style="{ background: colors.completed }" />پایان کار</span>
    </div>
    <svg :width="width" :height="height" :viewBox="`0 0 ${width} ${height}`" role="img"
         :aria-label="`روند ${unit} ثبت و پایان مأموریت‌ها`" @mousemove="move" @click="pick">
      <g class="grid">
        <g v-for="tick in yTicks" :key="'y' + tick">
          <line :x1="plot.left" :x2="plot.right" :y1="y(tick)" :y2="y(tick)" />
          <text :x="plot.right + 8" :y="y(tick) + 4" text-anchor="start">{{ fa(tick) }}</text>
        </g>
      </g>
      <line class="baseline" :x1="plot.left" :x2="plot.right" :y1="plot.bottom" :y2="plot.bottom" />
      <text v-for="index in xTicks" :key="'x' + index" class="x-label" :x="x(index)" :y="height - 6" text-anchor="middle">{{ jDate(points[index].from) }}</text>
      <rect v-if="selectedIndex >= 0" class="selected-band" :x="x(selectedIndex) - band / 2" :y="plot.top" :width="band" :height="plot.bottom - plot.top" />
      <path class="area" :d="area('created')" :fill="colors.created" />
      <path class="line" :d="line('created')" :stroke="colors.created" />
      <path class="line" :d="line('completed')" :stroke="colors.completed" />
      <g v-if="hover >= 0">
        <line class="crosshair" :x1="x(hover)" :x2="x(hover)" :y1="plot.top" :y2="plot.bottom" />
        <circle :cx="x(hover)" :cy="y(points[hover].created)" r="4.5" :fill="colors.created" class="dot" />
        <circle :cx="x(hover)" :cy="y(points[hover].completed)" r="4.5" :fill="colors.completed" class="dot" />
      </g>
    </svg>
    <div v-if="hover >= 0" class="tip" :style="tipStyle" role="status">
      <span class="tip-title">{{ label(points[hover]) }}</span>
      <span class="tip-row"><i :style="{ background: colors.created }" /><b>{{ fa(points[hover].created) }}</b> ثبت</span>
      <span class="tip-row"><i :style="{ background: colors.completed }" /><b>{{ fa(points[hover].completed) }}</b> پایان</span>
      <span class="tip-hint">برای فیلتر کلیک کنید</span>
    </div>
  </div>
</template>

<script>
import widthMixin from './widthMixin';
import { fa, jDate } from './format';
import { SERIES } from '@/utils/dashboardData';

export default {
  name: 'TrendChart',
  mixins: [widthMixin],
  props: { points: { type: Array, required: true }, step: { type: Number, default: 1 }, selected: { type: String, default: '' } },
  data: () => ({ height: 240, hover: -1, colors: SERIES }),
  computed: {
    unit() { return this.step === 1 ? 'روزانه' : 'هفتگی'; },
    // Time reads right-to-left, matching the page direction; the value axis sits on the right.
    plot() { return { left: 12, right: this.width - 40, top: 16, bottom: this.height - 30 }; },
    band() { return this.points.length > 1 ? (this.plot.right - this.plot.left) / (this.points.length - 1) : 40; },
    max() { return Math.max(4, ...this.points.map(p => Math.max(p.created, p.completed))); },
    yTicks() { const step = Math.max(1, Math.ceil(this.max / 4)); return [0, step, step * 2, step * 3, step * 4]; },
    xTicks() {
      const count = this.points.length;
      const every = Math.max(1, Math.ceil(count / Math.max(2, Math.floor(this.width / 90))));
      return Array.from({ length: count }, (_, i) => i).filter(i => (count - 1 - i) % every === 0);
    },
    selectedIndex() { return this.points.findIndex(p => this.selected && this.selected >= p.from && this.selected <= p.to); },
    tipStyle() {
      const left = this.x(this.hover);
      return left > this.width / 2 ? { right: (this.width - left + 14) + 'px' } : { left: (left + 14) + 'px' };
    },
  },
  methods: {
    fa, jDate,
    x(index) { return this.points.length > 1 ? this.plot.right - index * this.band : (this.plot.left + this.plot.right) / 2; },
    y(value) { return this.plot.bottom - (value / this.yTicks[4]) * (this.plot.bottom - this.plot.top); },
    line(key) { return this.points.map((p, i) => `${i ? 'L' : 'M'}${this.x(i).toFixed(1)},${this.y(p[key]).toFixed(1)}`).join(''); },
    area(key) {
      if (!this.points.length) return '';
      return `${this.line(key)}L${this.x(this.points.length - 1).toFixed(1)},${this.plot.bottom}L${this.x(0).toFixed(1)},${this.plot.bottom}Z`;
    },
    nearest(event) {
      const rect = event.currentTarget.getBoundingClientRect();
      const offset = event.clientX - rect.left;
      const index = Math.round((this.plot.right - offset) / this.band);
      return Math.min(this.points.length - 1, Math.max(0, index));
    },
    move(event) { if (this.points.length) this.hover = this.nearest(event); },
    pick(event) { if (this.points.length) this.$emit('select', this.points[this.nearest(event)]); },
    label(point) { return this.step === 1 ? jDate(point.from, { weekday: 'long', month: 'long', day: 'numeric' }) : `هفته ${jDate(point.from)} تا ${jDate(point.to)}`; },
  },
};
</script>

<style scoped>
.trend { position: relative; width: 100%; }
.legend { display: flex; gap: 16px; font-size: 12px; color: #4a566c; margin-bottom: 6px; }
.legend span { display: inline-flex; align-items: center; gap: 6px; }
.legend i, .tip-row i { display: inline-block; width: 14px; height: 2px; border-radius: 2px; }
svg { display: block; cursor: crosshair; overflow: visible; }
.grid line { stroke: #e6e9ef; stroke-width: 1; }
.grid text, .x-label { fill: #7a8496; font-size: 10.5px; font-family: inherit; }
.baseline { stroke: #c4cad6; stroke-width: 1; }
.line { fill: none; stroke-width: 2; stroke-linejoin: round; stroke-linecap: round; }
.area { opacity: .08; }
.crosshair { stroke: #9aa3b5; stroke-width: 1; stroke-dasharray: 3 3; }
.dot { stroke: #fff; stroke-width: 2; }
.selected-band { fill: #345de0; opacity: .08; }
.tip { position: absolute; top: 34px; z-index: 3; display: grid; gap: 3px; min-width: 150px; padding: 9px 11px; border-radius: 10px;
  background: #fff; border: 1px solid #dfe5ef; box-shadow: 0 10px 24px #1b2a4a24; font-size: 12px; color: #4a566c; pointer-events: none; }
.tip-title { font-weight: 700; color: #25324b; margin-bottom: 2px; }
.tip-row { display: flex; align-items: center; gap: 6px; }
.tip-row b { color: #17233b; font-size: 13px; }
.tip-hint { color: #8a93a5; font-size: 10.5px; margin-top: 2px; }
</style>
