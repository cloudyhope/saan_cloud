<template>
  <dl class="record-info-grid">
    <div v-for="field in fields" :key="field.label" :class="{ 'info-wide': field.wide }">
      <dt>{{ field.label }}</dt>
      <dd :class="{ 'info-ltr': field.ltr }">
        <span>{{ value(field.value) }}</span>
      </dd>
    </div>
  </dl>
</template>
<script>
import { displayValue } from '@/utils/detailValues';
export default {
  props: { fields: { type: Array, default: () => [] } },
  methods: { value: displayValue },
};
</script>
