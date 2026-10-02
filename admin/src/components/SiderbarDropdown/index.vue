<template>
  <li class="nav-item">
    <button type="button" class="nav-toggle" :class="{ active: routeActive, collapsed: collapsed }" :aria-expanded="isActive && !collapsed" :aria-label="title" :title="title" @click="toggle">
      <img v-if="iconUrl" :src="iconUrl" alt="" /><span v-if="!collapsed" class="title">{{ title }}</span><span v-if="!collapsed" class="chevron" :class="{ rotated: isActive }" aria-hidden="true">⌄</span>
    </button>
    <ul v-if="isActive && !collapsed" class="submenu-list"><slot name="navItems" /></ul>
  </li>
</template>
<script>
export default {
  props: { title: String, iconUrl: String, iconActive: String, mainRoute: String, collapsed: Boolean, routes: { type: Array, default: () => [] } },
  data() { return { isActive: false }; },
  computed: { routeActive() { return this.routes.includes(this.$route.path) || this.mainRoute === this.$route.path; } },
  watch: { routeActive: { immediate: true, handler(value) { if (value) this.isActive = true; } } },
  methods: { toggle() { if (this.collapsed) { this.$emit('expand'); this.isActive = true; } else this.isActive = !this.isActive; } },
};
</script>
<style scoped>
.nav-item { margin-bottom: 4px; }
.nav-toggle { display: flex; align-items: center; gap: 12px; width: 100%; min-height: 46px; border: 0; border-radius: 10px; background: transparent; color: #475569; padding: 10px 12px; text-align: right; font-size: 13px; }
.nav-toggle:hover { background: #f1f5f9; } .nav-toggle.active { color: var(--admin-primary); background: var(--admin-primary-soft); }
.nav-toggle img { width: 22px; height: 22px; object-fit: contain; }
.title { flex: 1; } .chevron { transition: transform .2s; } .rotated { transform: rotate(180deg); }
.collapsed { justify-content: center; } .submenu-list { margin: 4px 8px 8px 0; padding: 0; border-right: 1px solid var(--admin-border); }
</style>
