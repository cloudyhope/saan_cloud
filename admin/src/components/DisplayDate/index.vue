<template>
  <time v-if="date" :datetime="date.toISOString()" class="display-date"
    ><span>{{ dateLabel }}</span
    ><small v-if="showTime">{{ timeLabel }}</small></time
  >
  <span v-else class="text-muted">—</span>
</template>
<script>
const dateFormatter = new Intl.DateTimeFormat('fa-IR-u-ca-persian', {
  year: 'numeric',
  month: '2-digit',
  day: '2-digit',
});
const timeFormatter = new Intl.DateTimeFormat('fa-IR', {
  hour: '2-digit',
  minute: '2-digit',
  hour12: false,
});
export default {
  props: { value: [String, Number, Date], showTime: Boolean },
  computed: {
    date() {
      if (!this.value) return null;
      const value = typeof this.value === 'string' ? this.value.replace(' ', 'T') : this.value;
      const date = new Date(value);
      return Number.isNaN(date.getTime()) ? null : date;
    },
    dateLabel() {
      return this.date ? dateFormatter.format(this.date) : '';
    },
    timeLabel() {
      return this.date ? timeFormatter.format(this.date) : '';
    },
  },
};
</script>
<style scoped>
.display-date {
  display: inline-flex;
  flex-direction: column;
  align-items: flex-start;
  white-space: nowrap;
  font-family: 'IRANYekanfa', sans-serif;
  line-height: 1.8;
}
small {
  color: var(--admin-muted);
  font-size: 12px;
}
</style>
