<template>
  <span class="navigation-icon" aria-hidden="true">
    <!-- Icons come from the menu record (active_icon / deactive_icon), like every other menu attribute. -->
    <span v-if="maskable" class="mask" :style="maskStyle" />
    <img v-else-if="resolved && !failed" :src="resolved" alt="" @error="failed = true" />
    <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
      <path :d="group ? 'M3 6h6l2 2h10v11H3z' : 'M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6'" />
    </svg>
  </span>
</template>
<script>
import { menuForRoute, menuIconSource } from '../../utils/adminNavigation';

export default {
  name: 'NavigationIcon',
  // `source`: the sidebar passes the state-specific icon. Without it, the icon of the page's
  // menu entry is used and drawn as a mask so it follows the surrounding text colour.
  props: { source: String, route: String, name: String, group: Boolean, inverse: Boolean },
  data() { return { failed: false }; },
  computed: {
    resolved() {
      if (this.source) return this.source;
      const menu = this.route ? menuForRoute(this.$STORE.state.appConfig.menu, this.route) : null;
      return menu ? menuIconSource(menu, false) : '';
    },
    maskable() { return !this.source && /^data:image\/svg\+xml/.test(this.resolved || ''); },
    maskStyle() { const url = `url("${this.resolved}")`; return { WebkitMaskImage: url, maskImage: url }; },
  },
  watch: { resolved() { this.failed = false; } },
};
</script>
<style scoped>
.navigation-icon { width: 22px; height: 22px; flex: 0 0 22px; display: inline-flex; align-items: center; justify-content: center; }
img, svg, .mask { width: 100%; height: 100%; object-fit: contain; }
.mask { display: block; background: currentColor; -webkit-mask: no-repeat center / contain; mask: no-repeat center / contain; }
</style>
