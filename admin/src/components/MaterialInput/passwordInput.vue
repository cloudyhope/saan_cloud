<template><MaterialInput ref="input" v-bind="$props" v-on="$listeners" /></template>
<script>
import MaterialInput from './indx.vue';
export default {
  inheritAttrs: false,
  components: { MaterialInput },
  props: { ...MaterialInput.props, vModel: String, inputType: { type: String, default: 'password' } },
  methods: { setInputFocus() { this.$refs.input.setInputFocus(); } },
};
</script>
