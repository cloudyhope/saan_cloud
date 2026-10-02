<template>
  <v-app>
    <div v-if="!online" class="pwa-notice" role="status">
      <v-icon small color="white">mdi-wifi-off</v-icon>
      <span>آفلاین هستید؛ اطلاعات تازه پس از اتصال بارگذاری می‌شود.</span>
    </div>
    <div v-if="updateAvailable" class="pwa-notice pwa-notice-update" role="status">
      <v-icon small color="white">mdi-update</v-icon>
      <span>نسخه تازهٔ سان اپ آماده است.</span>
      <button type="button" :disabled="updating" @click="reload">{{ updating ? 'در حال به‌روزرسانی…' : 'به‌روزرسانی' }}</button>
    </div>
    <router-view/>
  </v-app>
</template>

<script>
export default {
  name: 'App',
  data() { return { online: navigator.onLine, updateAvailable: false, updateRegistration: null, updating: false }; },
  mounted() {
    window.addEventListener('online', this.setOnline);
    window.addEventListener('offline', this.setOffline);
    window.addEventListener('saan:pwa-update', this.showUpdate);
  },
  beforeDestroy() {
    window.removeEventListener('online', this.setOnline);
    window.removeEventListener('offline', this.setOffline);
    window.removeEventListener('saan:pwa-update', this.showUpdate);
  },
  methods: {
    setOnline() { this.online = true; },
    setOffline() { this.online = false; },
    showUpdate(event) {
      this.updateRegistration = event.detail && event.detail.registration;
      this.updateAvailable = true;
    },
    reload() {
      if (this.updating) return;
      const waiting = this.updateRegistration && this.updateRegistration.waiting;
      if (!waiting || !navigator.serviceWorker) {
        window.location.reload();
        return;
      }
      this.updating = true;
      navigator.serviceWorker.addEventListener('controllerchange', () => window.location.reload(), { once: true });
      waiting.postMessage({ type: 'SKIP_WAITING' });
    },
  },
};
</script>
<style>
#app {
  background: #F5F9FB;
  min-height: 100%;
}
.pwa-notice { display: flex; align-items: center; gap: 8px; padding: 9px 16px; background: #974623; color: #fff; font-size: 12px; line-height: 1.55; }
.pwa-notice-update { background: #164A68; }
.pwa-notice span { flex: 1; }
.pwa-notice button { min-height: 36px; padding: 0 10px; border: 1px solid rgba(255,255,255,.65); border-radius: 8px; color: #fff; font-weight: 700; }
.pwa-notice button:disabled { opacity: .7; }
</style>
