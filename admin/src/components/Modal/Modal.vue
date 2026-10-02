<template>
  <div v-if="show" class="mnx-modal-wrapper show" @keydown="onKeydown">
    <div ref="dialog" class="mnx-modal" :class="[size]" role="dialog" aria-modal="true" :aria-label="title || 'پنجره عملیات'" tabindex="-1">
      <button class="close-btn" type="button" v-if="closeBtn" @click="close" aria-label="بستن پنجره">×</button>
      <div class="mnx-header-container"><slot name="mnx-header" /></div>
      <div class="mnx-body-container"><slot name="mnx-body" /></div>
      <div class="mnx-footer-container"><slot name="mnx-footer" /></div>
    </div>
    <div class="mnx-modal-mask"></div>
  </div>
</template>
<script>
export default {
  props: { size: { type: String, default: null }, closeBtn: { type: Boolean, default: false }, title: String },
  data() { return { show: false }; },
  beforeDestroy() { if (this.show) this.restorePage(); },
  methods: {
    open() {
      if (this.show) return;
      this.previousFocus = document.activeElement;
      this.previousOverflow = document.body.style.overflow;
      document.body.style.overflow = 'hidden';
      this.show = true;
      this.$nextTick(() => this.$refs.dialog.focus());
      this.$emit('onOpened');
    },
    restorePage() {
      document.body.style.overflow = this.previousOverflow || '';
      if (this.previousFocus && document.contains(this.previousFocus)) this.previousFocus.focus();
    },
    close() {
      if (!this.show) return;
      this.show = false;
      this.restorePage();
      this.$emit('onClosed');
    },
    onKeydown(event) {
      if (event.key === 'Escape' && this.closeBtn) { event.preventDefault(); this.close(); }
      if (event.key !== 'Tab') return;
      const nodes = Array.from(this.$refs.dialog.querySelectorAll('button, a[href], input, select, textarea, [tabindex]:not([tabindex="-1"])')).filter(node => !node.disabled && node.getClientRects().length);
      if (!nodes.length) { event.preventDefault(); this.$refs.dialog.focus(); return; }
      const first = nodes[0], last = nodes[nodes.length - 1];
      if (event.shiftKey && (document.activeElement === first || document.activeElement === this.$refs.dialog)) { event.preventDefault(); last.focus(); }
      else if (!event.shiftKey && (document.activeElement === last || document.activeElement === this.$refs.dialog)) { event.preventDefault(); first.focus(); }
    },
  },
};
</script>
<style scoped>
.mnx-modal-wrapper { position: fixed; inset: 0; z-index: 100000; display: flex; justify-content: center; align-items: center; padding: 16px; }
.mnx-modal { position: relative; width: 360px; max-width: 100%; max-height: calc(100vh - 32px); overflow-y: auto; background: #fff; padding: 24px; border-radius: 14px; z-index: 2; box-shadow: var(--admin-shadow); }
.mnx-modal.small { width: 400px; } .mnx-modal.medium { width: 640px; } .mnx-modal.large { width: 960px; } .mnx-modal.full { width: 100%; }
.close-btn { position: absolute; left: 16px; top: 16px; width: 36px; height: 36px; font-size: 24px; border: 0; border-radius: 8px; color: var(--admin-muted); background: #f1f5f9; }
.mnx-header-container { border-bottom: 1px solid var(--admin-border); padding-bottom: 16px; padding-left: 40px; }
.mnx-body-container { margin-top: 20px; } .mnx-footer-container { margin-top: 24px; }
.mnx-modal-mask { position: absolute; inset: 0; background: rgba(15,23,42,.5); }
</style>
