<template>
  <span v-if="shown.length" class="row-actions">
    <!-- A single action stays one direct icon; two or more share one menu button. -->
    <template v-if="shown.length === 1">
      <router-link v-if="shown[0].to" :to="shown[0].to" class="icon-action" :aria-label="shown[0].label" :title="shown[0].label"><ActionIcon :name="shown[0].icon" /></router-link>
      <button v-else type="button" class="icon-action" :disabled="shown[0].disabled" :aria-label="shown[0].label" :title="shown[0].label" @click="run(shown[0])"><ActionIcon :name="shown[0].icon" :class="{ danger: shown[0].danger }" /></button>
    </template>
    <template v-else>
      <button ref="trigger" type="button" class="icon-action trigger" :class="{ open }" aria-haspopup="menu" :aria-expanded="open ? 'true' : 'false'"
              :aria-label="label" :title="label" @click.stop="toggle" @keydown.down.prevent="openMenu(true)">
        <ActionIcon name="more" inherit />
      </button>
      <div v-if="open" ref="menu" class="row-menu" role="menu" :aria-label="label" :style="position" @keydown="onMenuKey">
        <template v-for="(item, index) in shown">
          <span v-if="item.danger && index > 0 && !shown[index - 1].danger" :key="'sep' + index" class="sep" role="separator" />
          <router-link v-if="item.to" :key="'i' + index" :to="item.to" class="entry" role="menuitem" @click.native="close"><ActionIcon :name="item.icon" inherit />{{ item.label }}</router-link>
          <button v-else :key="'i' + index" type="button" class="entry" :class="{ danger: item.danger }" role="menuitem" :disabled="item.disabled" @click="run(item)"><ActionIcon :name="item.icon" inherit />{{ item.label }}</button>
        </template>
      </div>
    </template>
  </span>
</template>

<script>
import ActionIcon from '../ActionIcon/index.vue';

const MENU_WIDTH = 220;

// items: [{ label, icon, to | action, danger, disabled, hidden }]. `to` navigates, `action` runs a function.
export default {
  name: 'RowActions',
  components: { ActionIcon },
  props: { items: { type: Array, required: true }, label: { type: String, default: 'عملیات' } },
  data: () => ({ open: false, position: {} }),
  computed: { shown() { return this.items.filter((item) => item && !item.hidden); } },
  watch: { $route() { this.close(); } },
  beforeDestroy() { this.unbind(); },
  methods: {
    toggle() { this.open ? this.close() : this.openMenu(false); },
    openMenu(focusFirst) {
      // One menu at a time: any other open row menu closes when this one opens.
      window.dispatchEvent(new CustomEvent('row-actions-open', { detail: this._uid }));
      this.open = true;
      this.$nextTick(() => {
        this.place();
        if (focusFirst) this.focusEntry(0);
      });
      document.addEventListener('mousedown', this.onOutside, true);
      window.addEventListener('scroll', this.reposition, true);
      window.addEventListener('resize', this.reposition);
      window.addEventListener('row-actions-open', this.onOther);
    },
    close(restoreFocus) {
      if (!this.open) return;
      this.open = false;
      this.unbind();
      if (restoreFocus === true && this.$refs.trigger) this.$refs.trigger.focus();
    },
    unbind() {
      document.removeEventListener('mousedown', this.onOutside, true);
      window.removeEventListener('scroll', this.reposition, true);
      window.removeEventListener('resize', this.reposition);
      window.removeEventListener('row-actions-open', this.onOther);
    },
    // Following the button while the page or the table scrolls; it closes once the button leaves the window.
    reposition(event) {
      if (!this.open || (event && event.target && this.$refs.menu && this.$refs.menu.contains(event.target))) return;
      const trigger = this.$refs.trigger;
      if (!trigger) return;
      const box = trigger.getBoundingClientRect();
      if (box.bottom < 0 || box.top > window.innerHeight || box.right < 0 || box.left > window.innerWidth) this.close();
      else this.place();
    },
    onOther(event) { if (event.detail !== this._uid) this.close(); },
    onOutside(event) {
      if (this.$refs.menu && this.$refs.menu.contains(event.target)) return;
      if (this.$refs.trigger && this.$refs.trigger.contains(event.target)) return;
      this.close();
    },
    // The menu opens beside its button (towards free space) and stays inside the window.
    place() {
      const trigger = this.$refs.trigger;
      const menu = this.$refs.menu;
      if (!trigger || !menu) return;
      const box = trigger.getBoundingClientRect();
      const width = menu.offsetWidth || MENU_WIDTH;
      const height = menu.offsetHeight;
      let left = box.right + 8;
      if (left + width > window.innerWidth - 8) left = box.left - width - 8;
      left = Math.max(8, Math.min(left, window.innerWidth - width - 8));
      const top = Math.max(8, Math.min(box.top - 4, window.innerHeight - height - 8));
      this.position = { top: top + 'px', left: left + 'px' };
    },
    entries() { return this.$refs.menu ? [...this.$refs.menu.querySelectorAll('.entry:not([disabled])')] : []; },
    focusEntry(index) {
      const list = this.entries();
      if (list.length) list[(index + list.length) % list.length].focus();
    },
    onMenuKey(event) {
      const list = this.entries();
      const at = list.indexOf(document.activeElement);
      if (event.key === 'Escape') { event.preventDefault(); this.close(true); }
      else if (event.key === 'ArrowDown') { event.preventDefault(); this.focusEntry(at + 1); }
      else if (event.key === 'ArrowUp') { event.preventDefault(); this.focusEntry(at - 1); }
      else if (event.key === 'Home') { event.preventDefault(); this.focusEntry(0); }
      else if (event.key === 'End') { event.preventDefault(); this.focusEntry(list.length - 1); }
      else if (event.key === 'Tab') this.close();
    },
    run(item) {
      this.close();
      if (item.disabled || typeof item.action !== 'function') return;
      item.action();
    },
  },
};
</script>

<style scoped>
.row-actions { display: inline-flex; vertical-align: middle; }
/* #app .icon-action (theme) gives the 36px bordered square; the trigger only adds its open state. */
.trigger { color: #4a5a78; }
#app .row-actions .trigger.open, #app .row-actions .trigger:focus-visible { background: var(--admin-primary-soft); border-color: #9fb4e6; color: var(--admin-primary); }
.icon-action:focus-visible, .entry:focus-visible { outline: 3px solid #3a94b4; outline-offset: 2px; }
.row-menu { position: fixed; z-index: 1500; min-width: 190px; max-width: 260px; padding: 6px; border: 1px solid var(--admin-border); border-radius: 14px; background: #fff;
  box-shadow: 0 14px 40px #17243d2e; animation: pop .12s ease-out; }
@keyframes pop { from { opacity: 0; transform: scale(.97); } to { opacity: 1; transform: none; } }
.entry { display: flex; align-items: center; gap: 10px; width: 100%; min-height: 40px; padding: 8px 12px; border: 0; border-radius: 9px; background: transparent;
  color: #25324b; font: inherit; font-size: 13px; text-align: right; text-decoration: none; cursor: pointer; white-space: nowrap; }
.entry svg { width: 18px; height: 18px; flex: none; color: #5a6a88; }
.entry:hover, .entry:focus { background: #f1f4fb; color: #17233b; }
.entry:disabled { opacity: .45; cursor: default; }
.entry.danger, .entry.danger svg { color: #b42d2d; }
.entry.danger:hover { background: #fff1f2; }
.sep { display: block; height: 1px; margin: 5px 6px; background: var(--admin-border); }
@media (prefers-reduced-motion: reduce) { .row-menu { animation: none; } }
</style>
