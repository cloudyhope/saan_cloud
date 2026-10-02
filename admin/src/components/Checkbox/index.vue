<template>
  <label class="admin-checkbox">
    <input type="checkbox" :checked="value" v-bind="$attrs" v-on="inputListeners" :aria-label="label || $attrs['aria-label'] || 'انتخاب مورد'" />
    <span v-if="label">{{ label }}</span>
  </label>
</template>
<script>
export default {
  inheritAttrs: false,
  props: { value: Boolean, label: String, checkboxColor: { type: String, default: 'primary' }, size: { type: String, default: 'md' }, checkboxKey: {} },
  computed: {
    inputListeners() {
      return { ...this.$listeners, input: event => { this.$emit('input', event.target.checked); this.$emit('onValueChanged', { value: event.target.checked, key: this.checkboxKey }); } };
    },
  },
};
</script>
<style scoped>
.admin-checkbox { display: inline-flex; align-items: center; gap: 8px; min-height: 44px; cursor: pointer; margin: 0; color: var(--admin-text); font-size: 13px; }
input { width: 18px; height: 18px; accent-color: var(--admin-primary); cursor: pointer; }
input:disabled { cursor: not-allowed; opacity: .5; }
</style>
