<template>
  <div class="gantt" @mouseleave="tip = null">
    <div class="legend" aria-hidden="true">
      <span v-for="bucket in legend" :key="bucket.key"><i :style="{ background: bucket.color }" />{{ bucket.label }}</span>
      <span><i class="plan-key" />بازه برنامه (ثبت تا موعد)</span>
      <span><i class="late-key" />دیرکرد</span>
    </div>
    <EmptyState v-if="!rows.length" kind="visits" size="sm" inline title="در این بازه مأموریت زمان‌بندی‌شده‌ای نیست" description="بازه یا فیلترها را تغییر دهید." />
    <div v-else class="frame">
      <div class="labels" :style="{ width: labelWidth + 'px' }">
        <div class="axis-spacer" />
        <button v-for="row in shown" :key="row.key" type="button" class="row-label" :class="{ selected: row.key === selected, dim: selected && row.key !== selected }"
                :style="{ height: rowHeight(row) + 'px' }" :aria-pressed="row.key === selected ? 'true' : 'false'"
                @click="$emit('select', row.key === selected ? '' : row.key)">
          <span>{{ row.label }}</span><small>{{ fa(row.items.length) }} مأموریت</small>
        </button>
      </div>
      <div ref="scroller" class="timeline-scroll">
        <div class="timeline" :style="{ width: inner + 'px' }">
          <div class="axis">
            <span v-for="tick in ticks" :key="tick" class="tick" :style="{ right: offset(tick) + 'px' }">{{ jDate(tick) }}</span>
          </div>
          <div v-for="tick in ticks" :key="'g' + tick" class="gridline" :style="{ right: offset(tick) + 'px' }" />
          <div v-if="today >= range.from && today <= range.to" class="today" :style="{ right: (offset(today) + perDay / 2) + 'px' }"><span>امروز</span></div>
          <div v-for="row in shown" :key="'r' + row.key" class="lane-row" :class="{ dim: selected && row.key !== selected }" :style="{ height: rowHeight(row) + 'px' }">
            <template v-for="item in packed(row)">
              <span :key="'p' + item.id" class="plan" :style="span(item.plannedStart, item.plannedEnd, item.lane, 'plan')" />
              <button :key="'a' + item.id" type="button" class="bar" :class="{ late: item.late, unstarted: !item.actualStart }"
                      :style="barStyle(item)" :aria-label="describe(item)"
                      @mouseenter="show(item, $event)" @focus="show(item, $event)" @blur="tip = null" @click="$emit('open', item.id)" />
              <span v-if="item.due && item.due >= range.from && item.due <= range.to" :key="'d' + item.id" class="due" :class="{ late: item.late }"
                    :style="dueStyle(item)" />
            </template>
          </div>
        </div>
      </div>
    </div>
    <button v-if="rows.length > limit" type="button" class="more" @click="expanded = !expanded">{{ expanded ? 'نمایش کمتر' : `نمایش همه کارشناسان (${fa(rows.length)})` }}</button>
    <div v-if="tip" class="tip" :style="tip.style" role="status">
      <b>{{ tip.title }}</b><span>{{ tip.type }} · {{ tip.status }}</span>
      <span>برنامه: {{ tip.plan }}</span><span>اجرا: {{ tip.actual }}</span>
      <span v-if="tip.priority">اولویت: {{ tip.priority }}</span>
      <span v-if="tip.late" class="tip-late">دیرکرد نسبت به موعد</span>
      <span class="tip-hint">برای مشاهده گزارش کلیک کنید</span>
    </div>
  </div>
</template>

<script>
import widthMixin from './widthMixin';
import { fa, faId, jDate } from './format';
import { BUCKET, BUCKETS, daysBetween, lanes, addDays } from '@/utils/dashboardData';
import { levelOf } from '@/utils/priority';

import EmptyState from '@/components/EmptyState/index.vue';
const LANE = 18;

export default {
  components: { EmptyState },
  name: 'GanttChart',
  mixins: [widthMixin],
  props: {
    rows: { type: Array, required: true }, range: { type: Object, required: true }, today: { type: String, required: true },
    lookups: { type: Object, required: true }, selected: { type: [String, Number], default: '' },
  },
  data: () => ({ tip: null, expanded: false, limit: 10 }),
  computed: {
    labelWidth() { return this.width < 640 ? 112 : 168; },
    days() { return daysBetween(this.range.from, this.range.to) + 1; },
    available() { return Math.max(200, this.width - this.labelWidth - 2); },
    perDay() { return Math.max(this.available / this.days, 6); },
    inner() { return Math.max(this.available, this.days * this.perDay); },
    ticks() {
      const every = Math.max(1, Math.ceil(this.days / Math.max(2, Math.floor(this.inner / 80))));
      const list = [];
      for (let i = 0; i < this.days; i += every) list.push(addDays(this.range.from, i));
      return list;
    },
    shown() { return this.expanded ? this.rows : this.rows.slice(0, this.limit); },
    legend() { return BUCKETS.filter(b => b.key !== 'pending'); },
  },
  watch: {
    // Long ranges scroll; open on the most recent days (the left end in RTL).
    inner() { this.$nextTick(() => { const el = this.$refs.scroller; if (el) el.scrollLeft = -el.scrollWidth; }); },
  },
  methods: {
    fa, jDate,
    packed(row) { return lanes(row.items); },
    rowHeight(row) { return Math.max(1, Math.max(...this.packed(row).map(i => i.lane)) + 1) * LANE + 14; },
    // Right-to-left time axis: the first day of the range sits at the right edge.
    offset(date) { return daysBetween(this.range.from, date) * this.perDay; },
    clip(from, to) {
      const start = from < this.range.from ? this.range.from : from;
      const end = to > this.range.to ? this.range.to : to;
      return end < start ? null : { right: this.offset(start), width: (daysBetween(start, end) + 1) * this.perDay };
    },
    span(from, to, lane) {
      const box = this.clip(from, to);
      return box ? { right: box.right + 'px', width: box.width + 'px', top: (8 + lane * LANE + 11) + 'px' } : { display: 'none' };
    },
    barStyle(item) {
      const from = item.actualStart || item.plannedStart;
      const to = item.actualEnd || item.plannedEnd;
      const box = this.clip(from, to);
      if (!box) return { display: 'none' };
      const color = BUCKET[item.bucket].color;
      return { right: box.right + 'px', width: Math.max(box.width - 2, 6) + 'px', top: (8 + item.lane * LANE) + 'px',
        background: item.actualStart ? color : '#fff', borderColor: color };
    },
    dueStyle(item) { return { right: (this.offset(item.due) + this.perDay / 2 - 4) + 'px', top: (8 + item.lane * LANE + 1) + 'px' }; },
    describe(item) {
      return `مأموریت ${faId(item.id)}، ${this.lookups.buildings[item.building] || ''}، ${BUCKET[item.bucket].label}${item.late ? '، دیرکرد' : ''}`;
    },
    show(item, event) {
      const host = this.$el.getBoundingClientRect();
      const rect = event.target.getBoundingClientRect();
      const left = rect.left - host.left;
      const style = { top: (rect.bottom - host.top + 8) + 'px' };
      if (left > host.width / 2) style.right = Math.max(8, host.right - rect.right) + 'px'; else style.left = Math.max(8, left) + 'px';
      this.tip = {
        style, late: item.late, status: BUCKET[item.bucket].label,
        priority: item.priority === null || item.priority === undefined ? '' : `${levelOf(item.priority).label} (${fa(item.priority, 1)})`,
        title: `${this.lookups.buildings[item.building] || 'ساختمان'} · مأموریت ${faId(item.id)}`,
        type: this.lookups.types[item.type] || 'خدمت',
        plan: `${jDate(item.plannedStart)} تا ${item.due ? jDate(item.due) : 'بدون موعد'}`,
        actual: item.actualStart ? `${jDate(item.actualStart)} تا ${item.actualEnd === this.today && !['review', 'approved', 'rejected'].includes(item.bucket) ? 'اکنون' : jDate(item.actualEnd)}` : 'شروع نشده',
      };
    },
  },
};
</script>

<style scoped>
.gantt { position: relative; }
.legend { display: flex; flex-wrap: wrap; gap: 8px 14px; font-size: 11.5px; color: #4a566c; margin-bottom: 10px; }
.legend span { display: inline-flex; align-items: center; gap: 6px; }
.legend i { width: 12px; height: 10px; border-radius: 3px; }
.legend .plan-key { height: 4px; background: #c9d4e4; }
.legend .late-key { background: #fff; border: 2px solid #d03b3b; }
.frame { display: flex; border: 1px solid #e3e9f2; border-radius: 12px; overflow: hidden; background: #fff; }
.labels { flex: none; border-left: 1px solid #e3e9f2; background: #fafbfd; }
.axis-spacer, .axis { height: 30px; border-bottom: 1px solid #e3e9f2; }
.row-label { display: flex; flex-direction: column; justify-content: center; align-items: flex-start; width: 100%; padding: 0 12px; border: 0;
  border-bottom: 1px solid #eef1f6; background: transparent; font: inherit; font-size: 12px; color: #25324b; text-align: right; cursor: pointer; }
.row-label span { font-weight: 700; max-width: 100%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.row-label small { color: #7a8496; font-size: 10.5px; }
.row-label:hover { background: #f1f5fc; }
.row-label.selected { background: #eef3fd; box-shadow: inset -3px 0 0 #345de0; }
.row-label:focus-visible, .bar:focus-visible { outline: 3px solid #345de0; outline-offset: 1px; }
.dim { opacity: .4; }
.timeline-scroll { flex: 1; min-width: 0; overflow-x: auto; }
.timeline { position: relative; }
.axis { position: relative; }
.tick { position: absolute; top: 7px; transform: translateX(50%); font-size: 10.5px; color: #7a8496; white-space: nowrap; }
.gridline { position: absolute; top: 30px; bottom: 0; width: 1px; background: #f0f2f6; }
.today { position: absolute; top: 0; bottom: 0; width: 0; border-right: 1.5px dashed #345de0; z-index: 1; }
.today span { position: absolute; top: 7px; right: 4px; padding: 0 5px; border-radius: 6px; background: #345de0; color: #fff; font-size: 10px; white-space: nowrap; }
.lane-row { position: relative; border-bottom: 1px solid #eef1f6; }
.plan { position: absolute; height: 4px; border-radius: 4px; background: #c9d4e4; }
.bar { position: absolute; height: 10px; padding: 0; border: 1.5px solid; border-radius: 4px; cursor: pointer; z-index: 2; }
.bar.unstarted { border-style: dashed; }
.bar.late { box-shadow: 0 0 0 2px #fff, 0 0 0 4px #d03b3b; }
.bar:hover { filter: brightness(1.08); transform: scaleY(1.25); }
.due { position: absolute; width: 8px; height: 8px; transform: rotate(45deg); background: #52607a; border: 1px solid #fff; z-index: 2; pointer-events: none; }
.due.late { background: #d03b3b; }
.empty { padding: 26px; text-align: center; color: #7a8496; font-size: 12.5px; border: 1px dashed #d8e0ec; border-radius: 12px; }
.more { margin-top: 8px; border: 0; background: transparent; color: #345de0; font: inherit; font-size: 12px; font-weight: 700; cursor: pointer; }
.tip { position: absolute; z-index: 5; display: grid; gap: 2px; max-width: 280px; padding: 9px 11px; border-radius: 10px; background: #fff;
  border: 1px solid #dfe5ef; box-shadow: 0 10px 24px #1b2a4a24; font-size: 12px; color: #4a566c; pointer-events: none; }
.tip b { color: #17233b; font-size: 12.5px; }
.tip-late { color: #b42d2d; font-weight: 700; }
.tip-hint { color: #8a93a5; font-size: 10.5px; }
</style>
