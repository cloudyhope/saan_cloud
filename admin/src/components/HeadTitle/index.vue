<template>
  <div class="title-container"><h2>{{ title }}</h2><button type="button" v-if="isEdit" @click="$emit('onEdit')">ویرایش</button></div>
</template>
<script>
export default { props: { title: String, isEdit: { type: Boolean, default: false } } };
</script>
<style scoped>
.title-container { display: flex; align-items: center; justify-content: space-between; gap: 16px; border-bottom: 1px solid var(--admin-border); padding-bottom: 16px; margin-bottom: 24px; }
h2 { font-size: 16px; color: var(--admin-text); font-weight: 700; margin: 0; }
button { min-height: 40px; padding: 8px 16px; border: 1px solid var(--admin-border); border-radius: 8px; background: #fff; color: var(--admin-primary); font-size: 12px; }
</style>
