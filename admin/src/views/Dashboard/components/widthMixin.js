// Tracks the rendered width so SVG charts draw at real pixel size (crisp 2px lines, true hit areas).
export default {
  data: () => ({ width: 640 }),
  mounted() {
    if (typeof ResizeObserver === 'undefined') { this.width = this.$el.clientWidth || 640; return; }
    this.observer = new ResizeObserver(([entry]) => { this.width = Math.max(260, Math.floor(entry.contentRect.width)); });
    this.observer.observe(this.$el);
  },
  beforeDestroy() { if (this.observer) this.observer.disconnect(); },
};
