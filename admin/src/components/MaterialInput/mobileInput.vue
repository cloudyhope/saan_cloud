<template><MaterialInput ref="input" v-bind="$props" v-on="inputListeners" /></template>
<script>
import MaterialInput from './indx.vue';
export default {
  inheritAttrs: false,
  components: { MaterialInput },
  props: { ...MaterialInput.props, vModel: String, inputType: { type: String, default: 'tel' } },
  computed: {
    inputListeners() {
      return { ...this.$listeners, input: value => this.$emit('input', String(value).replace(/[۰-۹]/g, d => '۰۱۲۳۴۵۶۷۸۹'.indexOf(d)).replace(/[٠-٩]/g, d => '٠١٢٣٤٥٦٧٨٩'.indexOf(d)).replace(/\D/g, '')) };
    },
  },
  methods: { setInputFocus() { this.$refs.input.setInputFocus(); } },
};
</script>
