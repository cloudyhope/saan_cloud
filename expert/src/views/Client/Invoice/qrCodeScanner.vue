<template>
  <div>
    <BaseTopBar title="اسکن بارکد" />
    <StreamBarcodeReader class="barcode_class" @decode="onDecode"></StreamBarcodeReader>
    <p v-if="error" class="scan-error" role="alert">{{ error }}</p>
  </div>
</template>
<script>
import BaseTopBar from "@/components/Topbar/BaseTopbar.vue";
import { StreamBarcodeReader } from "vue-barcode-reader";

export default {
  name: "createInvoice",
  components: {
    BaseTopBar,
    StreamBarcodeReader,
  },
  data() {
    return {
      text: "",
      id: null,
      error: '',
      navigating: false,
    };
  },
  computed: {},
  created() {
  },
  methods: {
    onDecode(a) {
      if (this.navigating) return;
      const match = String(a || '').match(/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})(?:\/?(?:\?.*)?)?$/i);
      if (!match) {
        this.error = 'کد اسکن‌شده شناسه معتبر فاکتور ندارد.';
        return;
      }
      this.error = '';
      this.navigating = true;
      this.$router.push({ name: 'userCreateInvoice', params: { id: match[1], layer: this.$route.params.layer } })
        .catch(() => { this.navigating = false; });
    },
  },
};
</script>

<style scoped>
.barcode_class {
  margin-top: 72px;
  direction: ltr !important;
}
.scan-error { margin: 16px 20px; color: #b42318; line-height: 1.8; }
</style>
