<template>
  <nav class="field-navigation" aria-label="منوی اصلی">
    <div v-if="error" class="nav-error" role="alert">{{ error }}<v-btn small text @click="load">تلاش دوباره</v-btn></div>
    <template v-else>
      <router-link v-for="item in visibleItems" :key="item.route" :to="{ name: item.route }" class="field-nav-item" :class="{ selected: active(item) }" :aria-current="active(item) ? 'page' : null">
        <img v-if="icon(item)" :src="icon(item)" alt="" width="24" height="24" @error="failedIcons.push(item.route)" />
        <v-icon v-else :color="active(item) ? 'primary' : '#64748b'">{{ fallbackIcon(item.route) }}</v-icon><span>{{ item.title_fa || item.title }}</span>
      </router-link>
      <v-menu v-if="items.length > 5" top offset-y><template v-slot:activator="{ on, attrs }"><v-btn class="field-nav-more" text v-bind="attrs" v-on="on"><v-icon>mdi-dots-horizontal</v-icon><span>بیشتر</span></v-btn></template><v-list><v-list-item v-for="item in items.slice(4)" :key="item.route" :to="{ name: item.route }"><v-list-item-title>{{ item.title_fa || item.title }}</v-list-item-title></v-list-item></v-list></v-menu>
    </template>
  </nav>
</template>
<script>
import { navigation, requiredMenu } from '@/utils/fieldSession';
export default {
  data: () => ({ error: '', failedIcons: [] }),
  computed: {
    project() { return this.$STORE.state.userConfig.selectedProject; },
    items() { return (this.$STORE.state.userConfig.navigation || []).filter(item => this.$router.resolve({ name: item.route }).resolved.matched.length); },
    visibleItems() { return this.items.length > 5 ? this.items.slice(0, 4) : this.items; }
  },
  mounted() { this.load(); },
  watch: { project() { this.load(); } },
  methods: {
    active(item) { return this.$route.name !== 'clientSupport' && item.route === requiredMenu(this.$route.name); },
    icon(item) { return !this.failedIcons.includes(item.route) && (this.active(item) ? item.active_icon : item.deactive_icon); },
    fallbackIcon(route) { return ({ home: 'mdi-office-building', clientVisits: 'mdi-clipboard-text-clock', clientWarranty: 'mdi-shield-check-outline', tasks: 'mdi-clipboard-check-outline', setting: 'mdi-account-circle-outline', edu: 'mdi-school-outline', wares: 'mdi-toolbox-outline' })[route] || 'mdi-view-grid-outline'; },
    async load() { this.error = ''; try { await navigation(this.$ApiServiceLayer, this.project); } catch (error) { this.error = error.message; } }
  }
};
</script>
<style scoped>
.field-navigation { position: fixed; bottom: 0; left: 0; right: 0; max-width: 576px; margin: auto; display: flex; justify-content: space-around; background: #fff; border-top: 1px solid #e2e8f0; padding: 8px 6px calc(8px + env(safe-area-inset-bottom)); z-index: 5; box-shadow: 0 -4px 18px #0f172a06; }
.field-nav-item { flex: 1; min-width: 0; min-height: 54px; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 4px; color: #475569; font-size: 12px; text-decoration: none; border-radius: 12px; }
.field-nav-item.selected { background: #eff6ff; color: #1d4ed8; font-weight: 700; }
.field-nav-item:focus-visible { outline: 3px solid #2563eb; outline-offset: -3px; }
.field-nav-more { height: 54px !important; min-width: 48px !important; letter-spacing: 0; }
.field-nav-more ::v-deep .v-btn__content { flex-direction: column; }
.nav-error { font-size: 12px; color: #b91c1c; padding: 4px 12px; }
</style>
