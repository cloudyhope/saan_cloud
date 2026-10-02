<template>
  <header class="topbar-container">
    <div class="topbar-start">
      <button class="icon-button web" type="button" @click="changeMenuStatus" :aria-expanded="!$STORE.state.appConfig.closeMenu" aria-label="باز و بسته کردن منو"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 7h16M4 12h10M4 17h16" /></svg></button>
      <button class="icon-button mobile" type="button" @click="openMobileMenu" :aria-expanded="$STORE.state.appConfig.mobileMobile" aria-label="باز کردن منو"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 7h16M4 12h10M4 17h16" /></svg></button>
      <span class="divider" aria-hidden="true"></span>
      <div class="project-chip" :title="projectTitle">
        <span class="project-mark" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M6 21V4h9v17M15 9h4v12M3 21h18M9 8h3M9 12h3M9 16h3" /></svg></span>
        <span class="project-copy"><small>پروژه فعال</small><strong>{{ projectTitle }}</strong></span>
      </div>
    </div>
    <QuickSearch />
    <div class="topbar-end">
      <router-link v-if="projectId" :to="{ name: 'notifications' }" class="icon-button notifications-link" aria-label="اعلان‌ها"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4" /></svg><span v-if="unreadCount" class="notifications-count">{{ unreadCount > 99 ? '۹۹+' : unreadCount.toLocaleString('fa-IR') }}</span></router-link>
      <span class="divider" aria-hidden="true"></span>
      <div class="profile" ref="profile" @keydown.esc="showProfile = false">
        <button type="button" class="profile-button" :aria-expanded="showProfile" aria-haspopup="menu" aria-controls="profile-menu" @click="showProfile = !showProfile">
          <span class="avatar" aria-hidden="true">{{ userTitle.charAt(0) }}</span>
          <span class="profile-copy"><strong>{{ userTitle }}</strong><small>{{ roleTitle }}</small></span>
          <svg class="chevron" :class="{ open: showProfile }" viewBox="0 0 24 24" aria-hidden="true"><path d="m6 9 6 6 6-6" /></svg>
        </button>
        <div id="profile-menu" class="profile-menu" role="menu" v-if="showProfile">
          <div class="menu-head"><strong>{{ userTitle }}</strong><small>{{ roleTitle }} · {{ projectTitle }}</small></div>
          <button type="button" role="menuitem" @click="switchProject"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 7h12l-3-3M17 17H5l3 3" /></svg>تغییر پروژه</button>
          <button type="button" role="menuitem" class="danger" @click="logout"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M10 5H5v14h5M15 8l4 4-4 4M19 12H9" /></svg>خروج از حساب کاربری</button>
        </div>
      </div>
    </div>
  </header>
</template>
<script>
import { logoutSession } from '@/api/apiServiceLayer';
import QuickSearch from './QuickSearch.vue';
export default {
  components: { QuickSearch },
  data() { return { projectName: {}, showProfile: false, unreadCount: 0, unreadSequence: 0, nameSequence: 0 }; },
  computed: {
    projectId() { return this.$STORE.state.userConfig.setProjectId; },
    userTitle() { const user = this.projectName.user || {}; return [user.first_name, user.last_name].filter(Boolean).join(' ') || 'حساب کاربری'; },
    projectTitle() { const project = this.projectName.project || {}; return project.name_fa || 'سامانه مدیریت سان'; },
    roleTitle() { const role = this.projectName.role || {}; return role.verbose_name || role.title || 'کاربر پنل'; },
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
.topbar-container { position: sticky; top: 0; z-index: 30; min-height: 64px; background: #fff; border-bottom: 1px solid var(--admin-border); padding: 8px 24px; display: flex; justify-content: space-between; align-items: center; gap: 16px; }
.topbar-start, .topbar-end, .profile-button, .project-chip { display: flex; align-items: center; gap: 12px; min-width: 0; }
.divider { width: 1px; height: 28px; background: var(--admin-border); flex: none; }
.icon-button { position: relative; display: grid; place-items: center; width: 40px; height: 40px; flex: none; border: 0; border-radius: 12px; background: transparent; color: #4a5a78; text-decoration: none; transition: background .15s, color .15s; }
.icon-button:hover { background: var(--admin-primary-soft); color: var(--admin-primary); }
.icon-button:focus-visible, .profile-button:focus-visible { outline: 3px solid #3a94b4; outline-offset: 2px; }
.icon-button svg, .profile-menu button svg { width: 21px; height: 21px; fill: none; stroke: currentColor; stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round; }
.notifications-count { position: absolute; top: 1px; left: 1px; min-width: 18px; height: 18px; padding: 0 4px; display: grid; place-items: center; border-radius: 9px; background: #d03b3b; color: #fff; font-size: 10px; font-weight: 800; box-shadow: 0 0 0 2px #fff; }
.mobile { display: none; }
.project-mark { display: grid; place-items: center; width: 36px; height: 36px; flex: none; border-radius: 11px; background: var(--admin-primary-soft); color: var(--admin-primary); }
.project-mark svg { width: 20px; height: 20px; fill: none; stroke: currentColor; stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round; }
.project-copy, .profile-copy { display: grid; line-height: 1.45; min-width: 0; }
.project-copy small, .profile-copy small { font-size: 10.5px; color: var(--admin-muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.project-copy strong, .profile-copy strong { font-size: 13px; color: var(--admin-text); font-weight: 700; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.profile { position: relative; }
.profile-button { border: 0; background: transparent; padding: 4px 6px 4px 8px; border-radius: 14px; min-height: 48px; cursor: pointer; transition: background .15s; }
.profile-button:hover { background: #f3f5fb; }
.avatar { width: 36px; height: 36px; flex: none; display: grid; place-items: center; background: linear-gradient(140deg, #2a4f9a, #345de0); color: #fff; border-radius: 12px; font-weight: 800; font-size: 14px; }
.profile-copy { text-align: right; max-width: 150px; }
.chevron { width: 16px; height: 16px; fill: none; stroke: #7a8aa6; stroke-width: 2; stroke-linecap: round; stroke-linejoin: round; transition: transform .15s; }
.chevron.open { transform: rotate(180deg); }
.profile-menu { position: absolute; top: calc(100% + 10px); left: 0; min-width: 250px; padding: 6px; background: #fff; border: 1px solid var(--admin-border); border-radius: 14px; box-shadow: var(--admin-shadow); z-index: 50; }
.menu-head { display: grid; padding: 10px 12px 12px; margin-bottom: 4px; border-bottom: 1px solid var(--admin-border); }
.menu-head strong { font-size: 13px; color: var(--admin-text); }
.menu-head small { font-size: 11px; color: var(--admin-muted); }
.profile-menu button { display: flex; align-items: center; gap: 10px; width: 100%; background: #fff; color: var(--admin-text); border: 0; text-align: right; padding: 10px 12px; border-radius: 10px; font-size: 13px; cursor: pointer; }
.profile-menu button svg { width: 18px; height: 18px; color: #6b7890; }
.profile-menu button:hover { background: #f3f5fb; }
.profile-menu button.danger { color: #b42d2d; }
.profile-menu button.danger svg { color: inherit; }
.profile-menu button.danger:hover { background: #fff1f2; }
@media (max-width: 767px) { .topbar-container { padding: 8px 12px; } .web { display: none; } .mobile { display: grid; } .project-copy small, .profile-copy, .chevron { display: none; } .project-copy strong { max-width: 120px; } .profile-button { padding: 4px; } }
@media (max-width: 360px) { .project-copy strong { max-width: 80px; } .topbar-start .divider { display: none; } }
</style>
