<template>
  <div class="quick-search">
    <button ref="trigger" type="button" class="search-trigger" aria-haspopup="dialog" :aria-expanded="open ? 'true' : 'false'" @click="show">
      <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="6.5" /><path d="m16 16 4.5 4.5" /></svg>
      <span class="trigger-text">جستجوی صفحه یا شماره مأموریت…</span>
      <kbd class="trigger-key" dir="ltr" aria-hidden="true">Ctrl K</kbd>
    </button>

    <div v-if="open" class="search-layer" @mousedown.self="hide">
      <div class="search-panel" role="dialog" aria-modal="true" aria-label="جستجوی سریع" @keydown.esc.prevent="hide">
        <div class="search-field">
          <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="6.5" /><path d="m16 16 4.5 4.5" /></svg>
          <input ref="input" v-model="query" type="search" role="combobox" autocomplete="off" spellcheck="false"
                 placeholder="نام صفحه، بخش یا شماره مأموریت را بنویسید" aria-label="جستجو" aria-controls="quick-search-list"
                 :aria-expanded="results.length ? 'true' : 'false'" :aria-activedescendant="results.length ? 'quick-option-' + active : null"
                 @keydown.down.prevent="move(1)" @keydown.up.prevent="move(-1)" @keydown.enter.prevent="go(results[active])">
          <kbd dir="ltr" aria-hidden="true">Esc</kbd>
        </div>
        <div class="search-body">
          <p v-if="results.length" class="group-label">{{ query.trim() ? 'نتایج' : recentShown ? 'اخیراً بازدیدشده' : 'پیشنهاد' }}</p>
          <ul v-if="results.length" id="quick-search-list" role="listbox" aria-label="نتایج جستجو">
            <li v-for="(item, index) in results" :id="'quick-option-' + index" :key="item.key" role="option" :aria-selected="index === active ? 'true' : 'false'"
                class="option" :class="{ active: index === active }" @mousemove="active = index" @click="go(item)">
              <span class="option-icon" :class="{ visit: item.visit }">
                <svg v-if="item.visit" viewBox="0 0 24 24" aria-hidden="true"><path d="M9 3.5h6v3H9zM9 5H6v15.5h12V5h-3M9.5 13l2 2 3.5-3.5" /></svg>
                <NavigationIcon v-else :route="item.path" />
              </span>
              <span class="option-copy"><strong>{{ item.title }}</strong><small v-if="item.trail.length">{{ item.trail.join(' ‹ ') }}</small></span>
              <span v-if="index === active" class="option-go" aria-hidden="true">↵</span>
            </li>
          </ul>
          <div v-else class="no-results" role="status">
            <EmptyState kind="search" size="sm" title="صفحه‌ای پیدا نشد" description="عبارت دیگری را امتحان کنید یا شماره مأموریت را وارد کنید." />
          </div>
        </div>
        <footer class="search-foot" aria-hidden="true"><span><kbd>↑</kbd><kbd>↓</kbd> پیمایش</span><span><kbd>↵</kbd> باز کردن</span><span><kbd>Esc</kbd> بستن</span></footer>
      </div>
    </div>
  </div>
</template>

<script>
import NavigationIcon from '../components/NavigationIcon/index.vue';
import EmptyState from '../components/EmptyState/index.vue';
import { searchableEntries } from '../utils/adminNavigation';
import { rankEntries, visitNumber } from '../utils/searchText';

const RECENT_KEY = 'saan-admin-recent-pages';
const MAX_RECENT = 5;

export default {
  name: 'QuickSearch',
  components: { NavigationIcon, EmptyState },
  data: () => ({ open: false, query: '', active: 0, recent: [] }),
  computed: {
    entries() {
      return searchableEntries(this.$STORE.state.appConfig.menu).map((entry) => ({
        key: entry.id, title: entry.title, trail: entry.trail, path: entry.path,
      }));
    },
    canOpenVisit() { return this.entries.some((entry) => entry.path.toLowerCase().startsWith('/visitmanagment')); },
    recentShown() { return !this.query.trim() && this.recentEntries.length > 0; },
    recentEntries() {
      return this.recent.map((path) => this.entries.find((entry) => entry.path === path)).filter(Boolean);
    },
    results() {
      if (!this.query.trim()) return (this.recentEntries.length ? this.recentEntries : this.entries).slice(0, 7);
      const ranked = rankEntries(this.entries, this.query, 8);
      const id = visitNumber(this.query);
      if (id !== null && this.canOpenVisit) {
        ranked.unshift({ key: 'visit-' + id, visit: true, title: `مأموریت شماره ${id.toLocaleString('fa-IR', { useGrouping: false })}`,
          trail: ['باز کردن گزارش مأموریت'], path: '/visitmanagment/answerlist/' + id });
      }
      return ranked;
    },
  },
  watch: { query() { this.active = 0; }, $route() { this.open = false; } },
  created() { this.loadRecent(); },
  mounted() { document.addEventListener('keydown', this.onKey); },
  beforeDestroy() { document.removeEventListener('keydown', this.onKey); },
  methods: {
    onKey(event) {
      const typing = /^(input|textarea|select)$/i.test((event.target || {}).tagName || '') || (event.target || {}).isContentEditable;
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') { event.preventDefault(); this.open ? this.hide() : this.show(); }
      else if (event.key === '/' && !typing && !this.open) { event.preventDefault(); this.show(); }
    },
    show() {
      this.open = true; this.query = ''; this.active = 0; this.loadRecent();
      this.$nextTick(() => this.$refs.input && this.$refs.input.focus());
    },
    hide() { this.open = false; this.$nextTick(() => this.$refs.trigger && this.$refs.trigger.focus()); },
    move(step) {
      const count = this.results.length;
      if (!count) return;
      this.active = (this.active + step + count) % count;
      this.$nextTick(() => { const el = document.getElementById('quick-option-' + this.active); if (el && el.scrollIntoView) el.scrollIntoView({ block: 'nearest' }); });
    },
    go(item) {
      if (!item) return;
      this.remember(item);
      this.open = false;
      this.$router.push(item.path, () => {}, () => {});
    },
    loadRecent() {
      try { this.recent = JSON.parse(localStorage.getItem(RECENT_KEY) || '[]').filter((path) => typeof path === 'string'); } catch (_) { this.recent = []; }
    },
    remember(item) {
      if (item.visit) return; // a visit number is not a page
      const next = [item.path, ...this.recent.filter((path) => path !== item.path)].slice(0, MAX_RECENT);
      this.recent = next;
      try { localStorage.setItem(RECENT_KEY, JSON.stringify(next)); } catch (_) { /* private mode: recents just do not persist */ }
    },
  },
};
</script>

<style scoped>
.quick-search { flex: 1 1 280px; min-width: 0; max-width: 420px; }
.search-trigger { display: flex; align-items: center; gap: 10px; width: 100%; min-height: 42px; padding: 0 12px; border: 1px solid var(--admin-border); border-radius: 13px;
  background: #f5f7fb; color: #7a889f; font: inherit; font-size: 13px; cursor: pointer; transition: border-color .15s, background .15s, box-shadow .15s; }
.search-trigger:hover { background: #fff; border-color: #c9d5f2; box-shadow: 0 2px 10px #1b2a4a0f; }
.search-trigger:focus-visible { outline: 3px solid #3a94b4; outline-offset: 2px; }
.search-trigger svg, .search-field svg { width: 19px; height: 19px; flex: none; fill: none; stroke: currentColor; stroke-width: 1.9; stroke-linecap: round; stroke-linejoin: round; }
.trigger-text { flex: 1; min-width: 0; text-align: right; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
kbd { display: inline-flex; align-items: center; justify-content: center; min-width: 22px; height: 22px; padding: 0 6px; border: 1px solid #d9e0ee; border-bottom-width: 2px; border-radius: 6px;
  background: #fff; color: #6b7890; font: 600 10.5px/1 inherit; font-family: inherit; }
.search-layer { position: fixed; inset: 0; z-index: 2000; display: flex; justify-content: center; align-items: flex-start; padding: 11vh 16px 16px; background: #0f1b33a6; }
.search-panel { width: min(640px, 100%); max-height: 78vh; display: flex; flex-direction: column; border-radius: 18px; background: #fff; box-shadow: 0 30px 80px #0a1430555; overflow: hidden; animation: pop .14s ease-out; }
@keyframes pop { from { opacity: 0; transform: translateY(-8px) scale(.985); } to { opacity: 1; transform: none; } }
.search-field { display: flex; align-items: center; gap: 12px; padding: 0 18px; min-height: 60px; border-bottom: 1px solid var(--admin-border); color: #345de0; }
.search-field input { flex: 1; min-width: 0; height: 58px; border: 0; background: transparent; color: var(--admin-text); font: inherit; font-size: 15px; outline: none; }
.search-panel .search-field input, .search-panel .search-field input:focus { border: 0; box-shadow: none; outline: none; background: transparent; border-radius: 0; }
.search-field input::placeholder { color: #98a4ba; }
.search-field input::-webkit-search-cancel-button { display: none; }
.search-body { overflow-y: auto; padding: 8px 10px 10px; min-height: 120px; }
.group-label { margin: 6px 10px 6px; color: #8794ab; font-size: 11px; font-weight: 700; }
ul { list-style: none; margin: 0; padding: 0; display: grid; gap: 2px; }
.option { display: flex; align-items: center; gap: 12px; padding: 9px 10px; border-radius: 12px; cursor: pointer; }
.option.active { background: #eef2ff; }
.option-icon { display: grid; place-items: center; width: 38px; height: 38px; flex: none; border-radius: 11px; background: #eef2ff; color: #345de0; }
.option.active .option-icon { background: #fff; box-shadow: 0 2px 8px #345de01f; }
.option-icon .navigation-icon { width: 20px; height: 20px; flex-basis: 20px; }
.option-icon.visit svg { width: 20px; height: 20px; fill: none; stroke: currentColor; stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round; }
.option-copy { display: grid; flex: 1; min-width: 0; line-height: 1.5; }
.option-copy strong { font-size: 13.5px; color: var(--admin-text); font-weight: 700; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.option-copy small { font-size: 11.5px; color: var(--admin-muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.option-go { color: #345de0; font-weight: 800; padding: 0 6px; }
.no-results { padding: 4px 0 8px; }
.search-foot { display: flex; flex-wrap: wrap; gap: 6px 18px; padding: 10px 18px; border-top: 1px solid var(--admin-border); background: #f8f9fc; color: #7a889f; font-size: 11.5px; }
.search-foot span { display: inline-flex; align-items: center; gap: 5px; }
@media (max-width: 860px) {
  .quick-search { flex: 0 0 auto; }
  .search-trigger { width: 42px; padding: 0; justify-content: center; }
  .trigger-text, .trigger-key { display: none; }
  .search-layer { padding-top: 6vh; }
  .search-foot { display: none; }
}
@media (prefers-reduced-motion: reduce) { .search-panel { animation: none; } }
</style>
