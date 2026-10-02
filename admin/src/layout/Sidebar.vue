<template>
  <aside class="sidebar-component-container" aria-label="منوی اصلی">
    <SideWeb class="desktop-sidebar" />
    <div v-if="showMenu" class="side-bar-mobile" @keydown="onDrawerKeydown" role="dialog" aria-modal="true" aria-label="منوی مدیریت">
      <button class="mobile-overlay" type="button" aria-label="بستن منو" @click="closeMobileMenu"></button>
      <div class="mobile-panel" ref="mobilePanel"><button class="close-menu" ref="closeButton" type="button" @click="closeMobileMenu">بستن منو ×</button><SideWeb mobile /></div>
    </div>
  </aside>
</template>
<script>
import SideWeb from './components/sidebarWeb.vue';
export default {
  components: { SideWeb },
  computed: { showMenu() { return this.$STORE.state.appConfig.mobileMobile; } },
  watch: {
    $route() { this.closeMobileMenu(); },
    showMenu(value) {
      if (value) {
        this.previousFocus = document.activeElement;
        this.$nextTick(() => this.$refs.closeButton.focus());
      } else if (this.previousFocus && document.contains(this.previousFocus)) this.previousFocus.focus();
    },
  },
  methods: {
    closeMobileMenu() { this.$STORE.commit('appConfig/openMenuMobile', false); },
    onDrawerKeydown(event) {
      if (event.key === 'Escape') { event.preventDefault(); this.closeMobileMenu(); }
      if (event.key !== 'Tab') return;
      const elements = Array.from(this.$refs.mobilePanel.querySelectorAll('button, a[href]')).filter(element => !element.disabled && element.getClientRects().length);
      const first = elements[0], last = elements[elements.length - 1];
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
      if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
    },
  },
};
</script>
<style scoped>
.sidebar-component-container { flex-shrink: 0; }
.side-bar-mobile { position: fixed; inset: 0; z-index: 1000; }
.mobile-overlay { position: absolute; inset: 0; width: 100%; height: 100%; background: rgba(15, 23, 42, .5); border: 0; }
.mobile-panel { position: relative; width: min(300px, 86vw); height: 100%; background: #17243d; overflow-y: auto; }
.close-menu { width: 100%; min-height: 48px; border: 0; border-bottom: 1px solid #33435d; background: #17243d; text-align: left; padding: 12px 20px; color: #dce6ff; }
@media (max-width: 767px) { .desktop-sidebar { display: none; } }
@media (min-width: 768px) { .side-bar-mobile { display: none; } }
</style>
