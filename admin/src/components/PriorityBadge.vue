<template>
  <span v-if="level" class="priority-badge" :style="{ background: level.soft, color: level.ink }" :title="'امتیاز اولویت ' + faScore(score)">
    <i :style="{ background: level.color }" aria-hidden="true" />{{ level.label }}<b v-if="showScore">{{ faScore(score) }}</b>
  </span>
  <span v-else class="priority-badge empty">بدون اولویت</span>
</template>

<script>
import { faScore, levelOf } from '@/utils/priority';

export default {
  name: 'PriorityBadge',
  props: { score: { type: Number, default: null }, showScore: { type: Boolean, default: true } },
  computed: { level() { return levelOf(this.score); } },
  methods: { faScore },
};
</script>

<style scoped>
.priority-badge { display: inline-flex; align-items: center; gap: 5px; padding: 2px 9px; border-radius: 8px; font-size: 11.5px; font-weight: 700; white-space: nowrap; }
.priority-badge i { width: 7px; height: 7px; border-radius: 50%; }
.priority-badge b { font-weight: 800; margin-right: 2px; font-variant-numeric: tabular-nums; }
.priority-badge.empty { background: #f3f5f9; color: #8a93a5; }
</style>
