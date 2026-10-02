<template>
  <div class="sidebar-container" :class="{ closeMenu: collapsed, 'mobile-navigation': mobile }">
    <router-link to="/dashboard" class="logo-container" aria-label="داشبورد سان">
      <img :src="logo" alt="سان" />
    </router-link>
    <nav class="menu-item-container" aria-label="بخش‌های مدیریت">
      <div v-if="loading" class="menu-skeleton" role="status" aria-label="در حال دریافت منو"><span v-for="index in 5" :key="index"></span></div>
      <div v-else-if="failed" class="menu-message"><p v-if="!collapsed">دریافت منو انجام نشد.</p><button type="button" @click="getMenuList" aria-label="دریافت دوباره منو">تلاش مجدد</button></div>
      <ul v-else class="navigation" :class="{ 'collapsed-navigation': collapsed }">
        <MenuItem v-for="menu in menuList" :key="menu.id" :menu="menu" :collapsed="collapsed" :open-id="openId" @expand="expand" @open="openId = $event" />
      </ul>
    </nav>
    <div class="sidebar-footer">
      <span class="workspace-symbol" aria-hidden="true">S</span>
      <div v-if="!collapsed"><strong>سامانه سان</strong><span>مدیریت یکپارچه عملیات</span></div>
    </div>
  </div>
</template>
<script>
import MenuItem from './MenuItem.vue';
import { isTabGroup, menuContainsRoute, normalizeMenu } from '../../utils/adminNavigation';
export default {
  components: { MenuItem },
  props: { mobile: Boolean },
  data() { return { menuList: [], loading: true, failed: false, openId: null }; },
  computed: {
    collapsed() { return !this.mobile && this.$STORE.state.appConfig.closeMenu; },
    projectId() { return this.$STORE.state.userConfig.setProjectId; },
    logo() { return this.projectId === 10 ? 'https://s3.ir-thr-at1.arvanstorage.ir/public-maan/REPTOR.png' : this.$PATH.GET_IMAGE_PATH('logo.svg'); },
  },
  watch: { projectId() { this.getMenuList(); }, $route() { this.syncOpen(); } },
  created() { this.getMenuList(); },
  methods: {
    expand() { this.$STORE.commit('appConfig/changeMenuStatus', false); },
    // Opening a page opens only the group that contains it (tab groups are plain links).
    syncOpen() {
      const current = this.menuList.find((menu) => !isTabGroup(menu) && menu.children.length && menuContainsRoute(menu, this.$route.path));
      if (current) this.openId = current.id;
    },
    async getMenuList() {
      this.loading = true;
      this.failed = false;
      try {
        const res = await this.$ApiServiceLayer.get(this.$PATH.RELATIVE_PATH.GET.MENU_LIST + '?p=' + this.projectId + '&is_active=true', this.$PATH.SERVICE_NAME.AUTH);
        this.failed = res.status !== 200;
        this.menuList = this.failed ? [] : normalizeMenu(res.data);
        this.$STORE.commit('appConfig/setMenu', this.menuList);
        this.syncOpen();
      } finally { this.loading = false; }
    },
  },
};
</script>
<style scoped>
.sidebar-container { width: 272px; height: 100vh; height: 100dvh; background: #17243d; color: #fff; display: flex; flex-direction: column; transition: width .2s ease; border-left: 1px solid #23344e; }
.sidebar-container.closeMenu { width: 84px; }
.logo-container { height: 84px; flex-shrink: 0; display: flex; flex-direction: column; align-items: flex-start; justify-content: center; padding: 20px 28px; border-bottom: 1px solid #2b3a53; }
.logo-container img { max-width: 146px; max-height: 36px; object-fit: contain; }
.closeMenu .logo-container { padding: 18px; align-items: center; }
.closeMenu .logo-container img { width: 48px; }
.menu-item-container { flex: 1; overflow-y: auto; padding: 16px 14px; }
.navigation { padding: 0; margin: 0; }
.closeMenu .menu-item-container { padding: 16px 10px; }
.sidebar-footer { display: flex; gap: 12px; align-items: center; border-top: 1px solid #2b3a53; margin: 0 20px; padding: 20px 0; }
.sidebar-footer strong, .sidebar-footer span:not(.workspace-symbol) { display: block; }
.sidebar-footer strong { font-size: 12px; font-weight: 500; }
.sidebar-footer div > span { font-size: 10px; color: #aebbd0; margin-top: 3px; }
.workspace-symbol { display: grid; place-items: center; width: 36px; height: 36px; flex-shrink: 0; border: 1px solid #4b6085; border-radius: 11px; color: #d9e6ff; font-size: 18px; }
.closeMenu .sidebar-footer { margin: 0; justify-content: center; }
.menu-message { padding: 12px; color: #c3cee0; font-size: 12px; }
.menu-message button { border: 1px solid #4b6085; border-radius: 8px; background: #243451; color: #fff; min-height: 44px; }
.menu-skeleton span { display: block; height: 44px; border-radius: 10px; background: #293852; margin: 8px 0; }
.mobile-navigation { width: 100%; height: auto; min-height: calc(100% - 48px); border: 0; }
</style>
