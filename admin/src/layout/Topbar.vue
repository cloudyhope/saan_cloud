<template>
  <header class="topbar-container">
    <div class="topbar-start">
      <button class="menu-button web" type="button" @click="changeMenuStatus" :aria-expanded="!$STORE.state.appConfig.closeMenu" aria-label="باز و بسته کردن منو"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 6h16M4 12h16M4 18h16" /></svg></button>
      <button class="menu-button mobile" type="button" @click="openMobileMenu" :aria-expanded="$STORE.state.appConfig.mobileMobile" aria-label="باز کردن منو"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 6h16M4 12h16M4 18h16" /></svg></button>
      <span class="project-name">{{ projectTitle }}</span>
    </div>
    <div class="topbar-end">
      <router-link v-if="projectId" :to="{ name: 'notifications' }" class="notifications-link" aria-label="اعلان‌ها"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4" /></svg><span v-if="unreadCount" class="notifications-count">{{ unreadCount > 99 ? '۹۹+' : unreadCount.toLocaleString('fa-IR') }}</span></router-link>
      <div class="profile" ref="profile" @keydown.esc="showProfile = false">
        <button type="button" class="profile-button" :aria-expanded="showProfile" aria-controls="profile-menu" @click="showProfile = !showProfile">
          <span class="avatar" aria-hidden="true">{{ userTitle.charAt(0) }}</span><span class="profile-name">{{ userTitle }}</span><span aria-hidden="true">⌄</span>
        </button>
        <div id="profile-menu" class="profile-menu" v-if="showProfile"><button type="button" @click="switchProject">تغییر پروژه</button><button type="button" @click="logout">خروج از حساب کاربری</button></div>
      </div>
    </div>
  </header>
</template>
<script>
import { logoutSession } from '@/api/apiServiceLayer';
export default {
  data() { return { projectName: {}, showProfile: false, unreadCount: 0, unreadSequence: 0, nameSequence: 0 }; },
  computed: {
    projectId() { return this.$STORE.state.userConfig.setProjectId; },
    userTitle() { const user = this.projectName.user || {}; return [user.first_name, user.last_name].filter(Boolean).join(' ') || 'حساب کاربری'; },
    projectTitle() { const project = this.projectName.project || {}; return project.name_fa || 'سامانه مدیریت سان'; },
  },
  watch: {
    $route() { this.showProfile = false; this.getUnread(); },
    projectId() { this.projectName = {}; this.unreadCount = 0; this.unreadSequence += 1; this.nameSequence += 1; this.getProjectName(); this.getUnread(); },
  },
  created() { this.$root.$on('notifications-updated', this.onNotificationsUpdated); this.getProjectName(); this.getUnread(); },
  mounted() { document.addEventListener('click', this.closeOutside); },
  beforeDestroy() { this.unreadSequence += 1; this.nameSequence += 1; this.$root.$off('notifications-updated', this.onNotificationsUpdated); document.removeEventListener('click', this.closeOutside); },
  methods: {
    onNotificationsUpdated({ project, unreadCount }) { if (project === this.projectId) { this.unreadSequence += 1; this.unreadCount = unreadCount; } },
    closeOutside(event) { if (this.$refs.profile && !this.$refs.profile.contains(event.target)) this.showProfile = false; },
    changeMenuStatus() { this.$STORE.commit('appConfig/changeMenuStatus', !this.$STORE.state.appConfig.closeMenu); },
    openMobileMenu() { this.$STORE.commit('appConfig/openMenuMobile', true); },
    async getUnread() {
      if (!this.projectId) return;
      const project = this.projectId;
      const sequence = ++this.unreadSequence;
      try {
        const response = await this.$ApiServiceLayer.get(`/core/api/notifications/?p=${project}&limit=1`);
        if (sequence === this.unreadSequence && project === this.projectId)
          this.unreadCount = response.status === 200 ? Number(response.data.unread_count || 0) : 0;
      } catch (_) { if (sequence === this.unreadSequence) this.unreadCount = 0; }
    },
    async getProjectName() {
      const projectId = this.$STORE.state.userConfig.setProjectId;
      if (!projectId) return;
      const sequence = ++this.nameSequence;
      const res = await this.$ApiServiceLayer.get(this.$PATH.RELATIVE_PATH.GET.AUTH_ROLE, this.$PATH.SERVICE_NAME.AUTH);
      if (sequence !== this.nameSequence || projectId !== this.projectId) return;
      if (res.status === 200) {
        const assignments = Array.isArray(res.data) ? res.data : (res.data.results || []);
        const active = assignments.find(item => item.project && item.project.id === projectId);
        if (!active) {
          this.$STORE.commit('userConfig/setProjectInfo', null);
          this.$router.push({ name: 'projects' });
          return;
        }
        this.projectName = active;
      }
    },
    switchProject() {
      this.$STORE.commit('userConfig/setProjectInfo', null);
      this.$router.push({ name: 'projects' });
    },
    async logout() {
      await logoutSession();
      this.$STORE.commit('appConfig/openMenuMobile', false);
      this.$router.push({ name: 'login' });
    },
  },
};
</script>
<style scoped>
.topbar-container { position: sticky; top: 0; z-index: 30; min-height: 72px; background: #fff; border-bottom: 1px solid var(--admin-border); padding: 12px 24px; display: flex; justify-content: space-between; align-items: center; gap: 16px; }
.topbar-start, .topbar-end, .profile-button { display: flex; align-items: center; gap: 12px; }
.notifications-link { position: relative; display: grid; place-items: center; width: 44px; height: 44px; flex: none; border: 1px solid var(--admin-border); border-radius: 12px; color: var(--admin-primary); text-decoration: none; }
.notifications-link svg { width: 21px; height: 21px; fill: none; stroke: currentColor; stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round; }
.notifications-count { position: absolute; top: -5px; left: -5px; min-width: 19px; height: 19px; padding: 0 3px; display: grid; place-items: center; border-radius: 10px; background: #bd4d45; color: #fff; font-size: 10px; font-weight: 800; }
.notifications-link:focus-visible { outline: 3px solid #3a94b4; outline-offset: 2px; }
.menu-button { width: 44px; height: 44px; border: 1px solid var(--admin-border); border-radius: 10px; background: #fff; color: var(--admin-text); }
.menu-button svg { width: 22px; height: 22px; fill: none; stroke: currentColor; stroke-width: 1.7; }
.mobile { display: none; }
.project-name { font-size: 13px; color: var(--admin-muted); }
.profile { position: relative; }
.profile-button { border: 0; background: transparent; color: var(--admin-text); font-size: 13px; min-height: 44px; }
.avatar { width: 36px; height: 36px; display: grid; place-items: center; background: var(--admin-primary-soft); color: var(--admin-primary); border-radius: 50%; font-weight: 700; }
.profile-menu { position: absolute; top: calc(100% + 12px); left: 0; min-width: 220px; padding: 8px; background: #fff; border: 1px solid var(--admin-border); border-radius: 12px; box-shadow: var(--admin-shadow); z-index: 50; }
.profile-menu button { width: 100%; background: #fff; color: var(--admin-danger); border: 0; text-align: right; padding: 12px; border-radius: 8px; }
.profile-menu button:hover { background: #fff1f2; }
@media (max-width: 767px) { .topbar-container { padding: 12px 16px; } .web { display: none; } .mobile { display: block; } .project-name { display: block; max-width: 110px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; } .profile-name { display: none; } }
@media (max-width: 360px) { .project-name { max-width: 76px; } }
</style>
