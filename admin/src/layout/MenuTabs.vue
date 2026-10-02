<template>
  <nav v-if="info" class="menu-tabs" :aria-label="info.group.verbose_name">
    <router-link v-for="tab in info.tabs" :key="tab.id" :to="destination(tab)" class="tab" :class="{ current: isCurrent(tab) }"
                 :aria-current="isCurrent(tab) ? 'page' : null">
      <NavigationIcon :route="tab.frontend_route_url" />
      <span>{{ tab.verbose_name }}</span>
    </router-link>
  </nav>
</template>
<script>
import NavigationIcon from '../components/NavigationIcon/index.vue';
import { menuContainsRoute, menuDestination, tabsForRoute } from '../utils/adminNavigation';

// Children of a menu group marked display=tabs: the sidebar shows one link, the page shows these.
export default {
  name: 'MenuTabs',
  components: { NavigationIcon },
  computed: {
    info() { return tabsForRoute(this.$STORE.state.appConfig.menu, this.$route.path); },
  },
  methods: {
    destination: menuDestination,
    isCurrent(tab) { return menuContainsRoute(tab, this.$route.path); },
  },
};
</script>
<style scoped>
.menu-tabs { display: flex; gap: 4px; padding: 4px; margin: -4px 0 18px; border-radius: 14px; background: #e9edf5; overflow-x: auto; scrollbar-width: none; width: max-content; max-width: 100%; }
.menu-tabs::-webkit-scrollbar { display: none; }
.tab { display: inline-flex; align-items: center; gap: 8px; min-height: 40px; padding: 6px 16px; border-radius: 11px; color: #4a5a78; font-size: 13px; font-weight: 700; white-space: nowrap; text-decoration: none; transition: background .15s, color .15s; }
.tab:hover { background: #f4f6fb; color: #25324b; }
.tab.current { background: #fff; color: #345de0; box-shadow: 0 2px 8px #1b2a4a1a; }
.tab:focus-visible { outline: 3px solid #3a94b4; outline-offset: 1px; }
.tab .navigation-icon { width: 18px; height: 18px; flex-basis: 18px; }
</style>
