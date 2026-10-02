<template>
  <div>
    <notifications v-for="notification in groups" :key="notification.group" :group="notification.group" :position="notification.position" width="360px" class="admin-notifications">
      <template #body="props">
        <div class="notify-container" :class="'notify-' + props.item.type" role="status">
          <div class="notify-body"><div class="notify-title" v-if="props.item.title">{{ props.item.title }}</div><div class="notify-text">{{ props.item.text }}</div></div>
          <button type="button" class="close-notification" aria-label="بستن پیام" @click="props.close">×</button>
        </div>
      </template>
    </notifications>
  </div>
</template>
<script>
export default {
  data() {
    return { groups: [
      { group: 'tc', position: 'top center' }, { group: 'tr', position: 'top right' }, { group: 'tl', position: 'top left' },
      { group: 'bc', position: 'bottom center' }, { group: 'br', position: 'bottom right' }, { group: 'bl', position: 'bottom left' },
    ] };
  },
};
</script>
<style scoped>
.admin-notifications { max-width: calc(100vw - 24px); }
.notify-container { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; margin: 12px; padding: 16px; border: 1px solid var(--admin-border); border-right: 4px solid var(--admin-primary); border-radius: 10px; background: #fff; color: var(--admin-text); box-shadow: var(--admin-shadow); }
.notify-success { border-right-color: #157f59; } .notify-danger, .notify-error { border-right-color: var(--admin-danger); } .notify-warning { border-right-color: #b7791f; }
.notify-body { min-width: 0; } .notify-title { font-size: 13px; font-weight: 700; margin-bottom: 4px; }
.notify-text { font-size: 12px; line-height: 1.8; white-space: pre-line; overflow-wrap: anywhere; }
.close-notification { flex-shrink: 0; width: 32px; height: 32px; border: 0; background: #f1f5f9; border-radius: 6px; color: var(--admin-muted); font-size: 22px; }
</style>
