<template>
  <main class="field-page inbox-page" dir="rtl">
    <header class="inbox-hero">
      <router-link :to="{ name: hasClient ? 'home' : 'tasks' }" class="inbox-back"><v-icon color="white" size="18">mdi-arrow-right</v-icon>بازگشت به خانه</router-link>
      <span class="inbox-eyebrow">رویدادهای مربوط به شما</span>
      <h1>اعلان‌ها</h1>
      <p>مأموریت‌ها، پاسخ پشتیبانی و وضعیت گارانتی و تعمیر پروژه فعال را اینجا دنبال کنید.</p>
      <div class="inbox-summary"><span class="inbox-summary-icon"><v-icon color="#194d67" size="22">mdi-bell-outline</v-icon></span><span><strong>{{ number(unreadCount) }}</strong> اعلان خوانده‌نشده</span></div>
    </header>
    <div class="inbox-body">
      <div class="inbox-toolbar"><div><span>صندوق شما</span><h2>تازه‌ترین رویدادها</h2></div><button type="button" class="inbox-refresh" :disabled="loading || markAllBusy || !!readingId" aria-label="به‌روزرسانی اعلان‌ها" @click="load(true)"><v-icon size="20">mdi-refresh</v-icon></button></div>
      <div v-if="unreadCount && loaded" class="inbox-actions"><button type="button" :disabled="loading || markAllBusy || !!readingId" @click="markAllRead">{{ markAllBusy ? 'در حال ثبت…' : 'خواندن همه اعلان‌ها' }}</button></div>
      <v-alert v-if="error" type="error" outlined role="alert">{{ error }} <v-btn text color="error" @click="load(true)">تلاش دوباره</v-btn></v-alert>
      <v-skeleton-loader v-if="loading && !loaded" type="list-item-three-line, list-item-three-line, list-item-three-line" />
      <div v-else-if="loaded && !items.length" class="inbox-empty"><v-icon color="#6b97a6" size="34">mdi-bell-check-outline</v-icon><h2>هنوز اعلانی ندارید</h2><p>وقتی رویدادی مربوط به شما ثبت شود، همین‌جا دیده می‌شود.</p></div>
      <div v-else class="inbox-list"><button v-for="item in items" :key="item.id" type="button" class="inbox-card" :class="{ unread: !item.read_at }" :disabled="loading || markAllBusy || !!readingId" @click="openItem(item)"><span class="inbox-card-icon"><v-icon color="#246b84" size="21">{{ icon(item.kind) }}</v-icon></span><span class="inbox-card-copy"><span class="inbox-card-title"><strong>{{ item.title }}</strong><i v-if="!item.read_at" aria-label="خوانده‌نشده"></i></span><span>{{ item.body }}</span><small>{{ date(item.created_at) }}</small></span><v-icon color="#7c9aa9" size="19">mdi-chevron-left</v-icon></button></div>
      <button v-if="nextOffset !== null && loaded" type="button" class="inbox-more" :disabled="loading || markAllBusy || !!readingId" @click="load(false)">{{ loading ? 'در حال دریافت…' : 'اعلان‌های بیشتر' }}<v-icon size="18">mdi-chevron-down</v-icon></button>
    </div>
  </main>
</template>

<script>
import { errorMessage } from '@/utils/clientRequests';

export default {
  name: 'PersonalNotifications',
  data: () => ({ items: [], unreadCount: 0, nextOffset: null, loading: false, loaded: false,
    error: '', sequence: 0, readingId: null, markAllBusy: false }),
  computed: {
    project() { return this.$STORE.state.userConfig.selectedProject; },
    hasClient() { return (this.$STORE.state.userConfig.navigation || []).some(item => item.route === 'home'); },
    hasExpert() { return (this.$STORE.state.userConfig.navigation || []).some(item => item.route === 'tasks'); },
  },
  mounted() { this.load(true); },
  beforeDestroy() { this.sequence += 1; },
  watch: {
    project() {
      this.sequence += 1; this.items = []; this.unreadCount = 0; this.nextOffset = null;
      this.loading = false; this.loaded = false; this.error = ''; this.readingId = null;
      this.markAllBusy = false; this.load(true);
    },
  },
  methods: {
    icon(kind) { return ({ support_reply: 'mdi-message-text-outline', warranty_decision: 'mdi-shield-check-outline', repair_status: 'mdi-tools', visit_assignment: 'mdi-clipboard-check-outline' })[kind] || 'mdi-bell-outline'; },
    number(value) { return Number(value || 0).toLocaleString('fa-IR'); },
    date(value) { if (!value) return 'زمان نامشخص'; const parsed = new Date(value); return Number.isNaN(parsed.getTime()) ? 'زمان نامشخص' : parsed.toLocaleString('fa-IR', { year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit' }); },
    async load(reset) {
      if (!this.project || this.loading || this.markAllBusy || this.readingId) return;
      const project = this.project;
      const sequence = ++this.sequence;
      const offset = reset ? 0 : this.nextOffset;
      if (offset === null) return;
      this.loading = true; this.error = '';
      try {
        const response = await this.$ApiServiceLayer.get(`core/api/notifications/?p=${project}&limit=20&offset=${offset}`);
        if (sequence !== this.sequence || project !== this.project) return;
        if (response.status !== 200) { this.error = errorMessage(response); return; }
        const data = response.data || {};
        this.items = reset ? (data.results || []) : [...this.items, ...(data.results || [])];
        this.unreadCount = Number(data.unread_count || 0);
        this.nextOffset = data.next_offset == null ? null : Number(data.next_offset);
        this.loaded = true;
      } catch (_) { if (sequence === this.sequence && project === this.project) this.error = 'دریافت اعلان‌ها ممکن نشد. دوباره تلاش کنید.'; }
      finally { if (sequence === this.sequence && project === this.project) this.loading = false; }
    },
    async openItem(item) {
      if (this.readingId || this.markAllBusy) return;
      const project = this.project;
      const sequence = this.sequence;
      this.readingId = item.id;
      if (!item.read_at) {
        try {
          const response = await this.$ApiServiceLayer.post(`core/api/notifications/${item.id}/read/?p=${project}`, '', {});
          if (sequence !== this.sequence || project !== this.project) return;
          if (response.status === 200) { item.read_at = response.data.read_at; this.unreadCount = Math.max(0, this.unreadCount - 1); }
          else this.error = errorMessage(response);
        } catch (_) { if (sequence === this.sequence && project === this.project) this.error = 'ثبت وضعیت اعلان ممکن نشد.'; }
      }
      if (sequence === this.sequence && project === this.project) {
        this.readingId = null;
        if (item.kind === 'support_reply' && item.object_id) this.$router.push({ name: this.hasClient ? 'clientSupport' : 'chatHistory', query: { ticket: item.object_id } }).catch(() => {});
        if (item.kind === 'warranty_decision') this.$router.push({ name: 'clientWarranty', query: { tab: 'claims' } }).catch(() => {});
        if (item.kind === 'repair_status') this.$router.push({ name: 'clientWarranty', query: { tab: 'repairs' } }).catch(() => {});
        if (item.kind === 'visit_assignment') this.$router.push(this.hasExpert && item.object_id ? { name: 'storeDetail', params: { id: item.object_id } } : { name: 'projects' }).catch(() => {});
      }
    },
    async markAllRead() {
      if (!this.project || this.loading || this.markAllBusy || this.readingId) return;
      const project = this.project;
      const sequence = this.sequence;
      this.markAllBusy = true; this.error = '';
      try {
        const response = await this.$ApiServiceLayer.post(`core/api/notifications/read-all/?p=${project}`, '', {});
        if (sequence !== this.sequence || project !== this.project) return;
        if (response.status !== 200) { this.error = errorMessage(response); return; }
        const now = new Date().toISOString();
        this.items.forEach(item => { if (!item.read_at) item.read_at = now; });
        this.unreadCount = Number(response.data.unread_count || 0);
      } catch (_) { if (sequence === this.sequence && project === this.project) this.error = 'ثبت وضعیت اعلان‌ها ممکن نشد.'; }
      finally { if (sequence === this.sequence && project === this.project) this.markAllBusy = false; }
    },
  },
};
</script>

<style scoped>
.inbox-page{padding:0 0 calc(112px + env(safe-area-inset-bottom));background:#f4f8fb;color:#17394e}.inbox-hero{padding:calc(20px + env(safe-area-inset-top)) 20px 29px;border-radius:0 0 29px 29px;background:linear-gradient(145deg,#10324e,#1c6682);color:#fff;box-shadow:0 13px 30px #143a5424}.inbox-back{display:inline-flex;align-items:center;gap:7px;min-height:44px;color:#e6f5fa;text-decoration:none;font-size:13px}.inbox-eyebrow{display:block;margin-top:17px;color:#bce4ed;font-size:12px;font-weight:700}.inbox-hero h1{color:#fff;font-size:28px;margin:5px 0}.inbox-hero p{color:#e0eff4;font-size:13px;line-height:1.8;max-width:360px;margin:0 0 21px}.inbox-summary{display:flex;align-items:center;gap:10px;max-width:230px;padding:10px 13px;border:1px solid #ffffff40;border-radius:15px;background:#ffffff20;font-size:12px}.inbox-summary-icon{width:38px;height:38px;display:grid;place-items:center;flex:none;border-radius:11px;background:#d8f2de}.inbox-summary strong{font-size:20px}.inbox-body{padding:24px 20px}.inbox-toolbar{display:flex;align-items:center;justify-content:space-between;gap:10px}.inbox-toolbar span{color:#3e8095;font-size:11px;font-weight:700}.inbox-toolbar h2{font-size:18px;margin:4px 0}.inbox-refresh{width:44px;height:44px;display:grid;place-items:center;border:1px solid #d5e4ea;border-radius:12px;background:#fff;color:#29667d}.inbox-actions{display:flex;justify-content:flex-end;margin:5px 0 14px}.inbox-actions button{min-height:40px;color:#226a84;font-size:12px;font-weight:700}.inbox-list{display:grid;gap:10px;margin-top:14px}.inbox-card{display:flex;align-items:center;gap:11px;width:100%;padding:15px;border:1px solid #dce8ee;border-radius:16px;background:#fff;color:#17394e;text-align:right;box-shadow:0 4px 15px #143d550a}.inbox-card.unread{border-color:#b3d9dc;background:#f5fbf9}.inbox-card-icon{width:42px;height:42px;display:grid;place-items:center;flex:none;border-radius:12px;background:#e5f2f4}.inbox-card-copy{display:grid;gap:5px;min-width:0;flex:1}.inbox-card-title{display:flex;align-items:center;gap:6px}.inbox-card-title strong{font-size:13px;overflow-wrap:anywhere}.inbox-card-title i{width:7px;height:7px;flex:none;border-radius:50%;background:#1a917a}.inbox-card-copy>span:nth-child(2){color:#527082;font-size:12px;line-height:1.7;overflow-wrap:anywhere}.inbox-card-copy small{color:#718d9c;font-size:11px}.inbox-empty{display:grid;justify-items:center;gap:8px;margin-top:19px;padding:36px 20px;border:1px dashed #c5d9e2;border-radius:18px;background:#fff;text-align:center}.inbox-empty h2{font-size:16px;margin:4px 0 0}.inbox-empty p{margin:0;color:#607b8c;font-size:12px;line-height:1.8}.inbox-more{display:flex;align-items:center;justify-content:center;gap:6px;width:100%;min-height:47px;margin-top:14px;border:1px solid #bad4dd;border-radius:12px;background:#fff;color:#246b82;font-size:13px;font-weight:700}.inbox-page button:focus-visible,.inbox-page a:focus-visible{outline:3px solid #3b9fc2;outline-offset:3px}@media(max-width:350px){.inbox-body{padding-left:14px;padding-right:14px}.inbox-hero{padding-left:16px;padding-right:16px}.inbox-card{padding:12px}}
</style>
