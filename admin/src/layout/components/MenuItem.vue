<template>
  <li class="menu-entry" :class="{ 'is-group': isGroup, 'is-open': open && !collapsed, 'is-child': depth > 0 }">
    <button v-if="isGroup" type="button" class="menu-link group-toggle" :class="{ 'is-current': active }" :title="menu.verbose_name" :aria-expanded="open && !collapsed" :aria-controls="submenuId" @click="toggle">
      <NavigationIcon :source="iconSource" :route="menu.frontend_route_url" :name="menu.verbose_name" group inverse />
      <span v-if="!collapsed" class="menu-label">{{ menu.verbose_name }}</span>
      <svg v-if="!collapsed" class="chevron" :class="{ rotated: open }" viewBox="0 0 20 20" aria-hidden="true"><path d="m6 8 4 4 4-4" /></svg>
    </button>
    <router-link v-else :to="destination" class="menu-link" :class="{ 'is-current': active }" :title="menu.verbose_name" :aria-label="menu.verbose_name">
      <NavigationIcon :source="iconSource" :route="menu.frontend_route_url" :name="menu.verbose_name" inverse />
      <span v-if="!collapsed" class="menu-label">{{ menu.verbose_name }}</span>
      <span v-if="active && !collapsed" class="current-marker" aria-hidden="true"></span>
    </router-link>
    <transition name="submenu">
      <ul v-if="isGroup && open && !collapsed" :id="submenuId" class="submenu-list">
        <MenuItem v-for="child in menu.children" :key="child.id" :menu="child" :depth="depth + 1" @expand="$emit('expand')" />
        <li v-if="!menu.children.length" class="empty-group">زیرمنویی برای این گروه تعریف نشده است.</li>
      </ul>
    </transition>
  </li>
</template>
<script>
import NavigationIcon from '../../components/NavigationIcon/index.vue';
import { menuContainsRoute, menuDestination, menuIconSource } from '../../utils/adminNavigation';
export default {
  name: 'MenuItem',
  components: { NavigationIcon },
  props: { menu: { type: Object, required: true }, collapsed: Boolean, depth: { type: Number, default: 0 } },
  data() { return { open: false }; },
  computed: {
    isGroup() { return this.menu.has_submenu || this.menu.children.length > 0; },
    active() { return menuContainsRoute(this.menu, this.$route.path); },
    destination() { return menuDestination(this.menu); },
    iconSource() { return menuIconSource(this.menu, this.active); },
    submenuId() { return 'navigation-group-' + this._uid; },
  },
  watch: { active: { immediate: true, handler(value) { if (value) this.open = true; } } },
  methods: {
    toggle() {
      if (this.collapsed) { this.$emit('expand'); this.open = true; }
      else this.open = !this.open;
    },
  },
};
</script>
<style scoped>
.menu-entry { margin: 5px 0; list-style: none; }
.menu-link { display: flex; align-items: center; gap: 12px; width: 100%; min-height: 48px; padding: 11px 13px; border: 1px solid transparent; border-radius: 11px; background: transparent; color: #c3cee0; font-size: 13px; line-height: 1.7; text-align: right; transition: background-color .18s, color .18s, border-color .18s; }
.menu-link:hover { color: #fff; background: #243451; }
.menu-link.is-current { color: #fff; background: #345de0; border-color: #5177ec; box-shadow: 0 4px 14px #060f282b; }
.group-toggle.is-current { background: #263957; border-color: #3c5273; box-shadow: none; color: #dce6ff; }
.menu-label { flex: 1; min-width: 0; }
.menu-link .navigation-icon { width: 28px; height: 28px; flex-basis: 28px; padding: 4px; background: #e9f0ff; border-radius: 7px; }
.chevron { width: 18px; height: 18px; flex-shrink: 0; fill: none; stroke: currentColor; stroke-width: 1.7; transition: transform .2s; }
.chevron.rotated { transform: rotate(180deg); }
.submenu-list { padding: 0 13px 0 0; margin: 8px 20px 12px 0; border-right: 1px solid #3c4c69; }
.is-child .menu-link { font-size: 12px; min-height: 44px; gap: 10px; padding: 9px 10px; }
.is-child .navigation-icon { width: 24px; height: 24px; flex-basis: 24px; padding: 3px; }
.current-marker { width: 6px; height: 6px; background: #dbe5ff; border-radius: 50%; flex-shrink: 0; }
.empty-group { color: #aebbd0; padding: 12px; font-size: 11px; }
.submenu-enter-active, .submenu-leave-active { transition: opacity .18s, transform .18s; }
.submenu-enter, .submenu-leave-to { opacity: 0; transform: translateY(-5px); }
</style>
