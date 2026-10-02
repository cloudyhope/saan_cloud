<template>
  <component :is="clickable ? 'button' : 'div'" :type="clickable ? 'button' : null" class="kpi-tile"
             :class="['tone-' + tone, { selected, clickable }]" :aria-pressed="clickable ? (selected ? 'true' : 'false') : null"
             @click="clickable && $emit('select')">
    <span class="kpi-head"><span class="kpi-icon" aria-hidden="true"><svg viewBox="0 0 24 24"><path :d="icon" /></svg></span>{{ label }}</span>
    <strong class="kpi-value">{{ value }}</strong>
    <span v-if="hint" class="kpi-hint" :class="'hint-' + hintTone">{{ hint }}</span>
  </component>
</template>

<script>
export default {
  name: 'KpiTile',
  props: {
    label: { type: String, required: true },
    value: { type: String, required: true },
    hint: { type: String, default: '' },
    hintTone: { type: String, default: 'muted' }, // muted | good | bad
    tone: { type: String, default: 'neutral' }, // neutral | critical | warning | serious | good
    icon: { type: String, default: 'M4 12h16' },
    clickable: { type: Boolean, default: false },
    selected: { type: Boolean, default: false },
  },
};
</script>

<style scoped>
.kpi-tile { display: grid; gap: 6px; align-content: start; min-height: 116px; padding: 16px 16px 14px; text-align: right; color: #25324b;
  background: #fff; border: 1px solid #e3e9f2; border-radius: 14px; box-shadow: 0 4px 14px #1b2a4a0a; font: inherit; }
.kpi-tile.clickable { cursor: pointer; transition: border-color .18s, box-shadow .18s, transform .18s; }
.kpi-tile.clickable:hover { border-color: #b9c9e6; box-shadow: 0 8px 20px #1b2a4a14; }
.kpi-tile.selected { border-color: #345de0; box-shadow: 0 0 0 3px #345de02a; }
.kpi-tile:focus-visible { outline: 3px solid #345de0; outline-offset: 2px; }
.kpi-head { display: flex; align-items: center; gap: 8px; color: #5b6880; font-size: 12px; font-weight: 700; line-height: 1.6; }
.kpi-icon { flex: none; width: 30px; height: 30px; display: grid; place-items: center; border-radius: 9px; background: #eef3fd; color: #345de0; }
.kpi-icon svg { width: 17px; height: 17px; fill: none; stroke: currentColor; stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round; }
.tone-critical .kpi-icon { background: #fdeceb; color: #b42d2d; }
.tone-warning .kpi-icon { background: #fff4dc; color: #8f6200; }
.tone-serious .kpi-icon { background: #fdeee6; color: #a64b22; }
.tone-good .kpi-icon { background: #e6f5e6; color: #0a7a0a; }
.kpi-value { font-size: 27px; line-height: 1.25; font-weight: 800; color: #17233b; }
.kpi-hint { font-size: 11.5px; line-height: 1.6; color: #6b778d; }
.hint-good { color: #0f6e0f; }
.hint-bad { color: #b42d2d; }
</style>
