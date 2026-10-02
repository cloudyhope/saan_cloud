<template>
  <button type="button" class="custom-switch" role="switch" :aria-checked="checked" :aria-label="label || 'تغییر وضعیت'" :disabled="disabled" @click="toggleSwitch">
    <span class="switch-track" :class="{ active: checked }"><span class="switch-thumb" :class="{ active: checked }"></span></span>
  </button>
</template>
<script>
export default {
  name: 'CustomSwitch',
  props: { modelValue: { type: Boolean, default: undefined }, value: Boolean, disabled: Boolean, label: String },
  computed: { checked() { return this.modelValue === undefined ? this.value : this.modelValue; } },
  methods: { toggleSwitch() { const value = !this.checked; this.$emit('input', value); this.$emit('update:modelValue', value); this.$emit('change', value); } },
};
</script>
<style scoped>
.custom-switch { display: inline-flex; align-items: center; justify-content: center; min-width: 48px; min-height: 44px; padding: 0; background: transparent; border: 0; }
.custom-switch:disabled { opacity: .5; }
.switch-track { position: relative; display: block; width: 44px; height: 24px; border-radius: 12px; background: #cbd5e1; transition: background-color .2s; }
.switch-track.active { background: var(--admin-primary); }
.switch-thumb { position: absolute; left: 3px; top: 3px; width: 18px; height: 18px; border-radius: 50%; background: #fff; transition: transform .2s; }
.switch-thumb.active { transform: translateX(20px); }
</style>
