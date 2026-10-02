<template>
  <header class="vf-topbar" :class="{ compact }">
    <div class="vf-topbar-row">
      <button type="button" class="vf-topbar-back" :aria-label="backLabel" @click="goBack">
        <v-icon color="white" size="22">mdi-arrow-right</v-icon>
      </button>
      <div class="vf-topbar-copy">
        <span v-if="eyebrow" class="vf-topbar-eyebrow">{{ eyebrow }}</span>
        <h1>{{ title }}</h1>
      </div>
      <slot name="action" />
    </div>
    <p v-if="subtitle" class="vf-topbar-sub">{{ subtitle }}</p>
    <slot />
  </header>
</template>

<script>
export default {
  name: 'VisitTopBar',
  props: {
    title: { type: String, default: '' },
    eyebrow: { type: String, default: '' },
    subtitle: { type: String, default: '' },
    // Where «back» goes when there is no in-app history (deep link, refresh).
    fallback: { type: Object, default: () => ({ name: 'tasks' }) },
    backLabel: { type: String, default: 'بازگشت' },
    compact: { type: Boolean, default: false },
  },
  methods: {
    goBack() {
      // After a deep link or refresh there is no in-app page to return to.
      if (window.__saanInAppNavigation) this.$router.back();
      else this.$router.push(this.fallback).catch(() => {});
    },
  },
};
</script>

<style scoped>
.vf-topbar { position: sticky; top: 0; z-index: 6; color: #fff; padding: calc(14px + env(safe-area-inset-top)) 16px 18px;
  background: linear-gradient(140deg, #102f4d, #1d608b); border-radius: 0 0 24px 24px; box-shadow: 0 10px 24px #10395722; }
.vf-topbar.compact { padding-bottom: 14px; }
.vf-topbar-row { display: flex; align-items: center; gap: 10px; }
.vf-topbar-back { flex: none; width: 44px; height: 44px; display: grid; place-items: center; border-radius: 14px;
  border: 1px solid #ffffff5c; background: #ffffff17; }
.vf-topbar-back:focus-visible { outline: 3px solid #9fd4f1; outline-offset: 2px; }
.vf-topbar-copy { flex: 1; min-width: 0; }
.vf-topbar-eyebrow { display: block; color: #bde1f1; font-size: 11.5px; font-weight: 700; line-height: 1.5; }
.vf-topbar h1 { color: #fff; font-size: 18px; font-weight: 800; line-height: 1.45; margin: 0; overflow: hidden;
  text-overflow: ellipsis; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; }
.vf-topbar-sub { margin: 10px 2px 0; color: #e1f1f7; font-size: 12.5px; line-height: 1.7; }
</style>
