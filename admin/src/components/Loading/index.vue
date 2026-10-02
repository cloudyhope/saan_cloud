<template>
  <div v-if="show" class="loading-container" role="status" aria-label="در حال انجام عملیات">
    <div class="loading-card"><span class="spinner-border" aria-hidden="true"></span><span>در حال انجام عملیات…</span></div>
  </div>
</template>
<script>
export default {
  data() { return { show: true }; },
  mounted() { this.lockPage(); },
  beforeDestroy() { this.restorePage(); },
  methods: {
    lockPage() { if (this.locked) return; this.previousOverflow = document.body.style.overflow; document.body.style.overflow = 'hidden'; this.locked = true; },
    restorePage() { if (this.locked) document.body.style.overflow = this.previousOverflow || ''; this.locked = false; },
    open() { this.show = true; this.lockPage(); this.$emit('onOpened'); },
    close() { this.show = false; this.restorePage(); this.$emit('onClosed'); },
  },
};
</script>
<style scoped>
.loading-container { position: fixed; inset: 0; z-index: 99999; background: rgba(244,246,250,.8); display: flex; align-items: center; justify-content: center; }
.loading-card { display: flex; align-items: center; gap: 16px; padding: 24px; border: 1px solid var(--admin-border); border-radius: 12px; background: #fff; color: var(--admin-muted); box-shadow: var(--admin-shadow); font-size: 13px; }
.spinner-border { width: 24px; height: 24px; border-width: 2px; color: var(--admin-primary); }
</style>
