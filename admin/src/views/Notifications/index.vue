<template>
  <main class="admin-inbox" dir="rtl">
    <header class="inbox-header"><div><span class="inbox-eyebrow">صندوق شخصی پروژه</span><h1>اعلان‌ها</h1><p>گفتگوهای تازه و رویدادهای مرتبط با کار شما در این پروژه</p></div><div class="unread-summary"><span>{{ number(unreadCount) }}</span> خوانده‌نشده</div></header>
    <div class="inbox-toolbar"><div><h2>تازه‌ترین رویدادها</h2><small>{{ number(total) }} اعلان ثبت‌شده</small></div><div><button type="button" :disabled="busy" @click="load(true)">به‌روزرسانی</button><button v-if="unreadCount && loaded" type="button" :disabled="busy" @click="markAllRead">خواندن همه</button></div></div>
    <div v-if="error" class="inbox-error" role="alert">{{ error }} <button type="button" :disabled="busy" @click="load(true)">تلاش دوباره</button></div>
    <div v-if="loading && !loaded" class="inbox-loading" role="status">در حال دریافت اعلان‌ها…</div>
    <EmptyState v-else-if="loaded && !items.length" kind="notifications" title="هنوز اعلانی ندارید" description="پیام‌های مربوط به شما پس از ثبت، همین‌جا نمایش داده می‌شوند." />
    <div v-else class="inbox-list"><button v-for="item in items" :key="item.id" type="button" class="inbox-item" :class="{ unread: !item.read_at }" :disabled="busy" @click="openItem(item)"><span class="item-icon" aria-hidden="true">{{ ({ support_incoming: '✉', visit_review: '✓', visit_declined: '↩', visit_overdue: '!', part_request: '▣' })[item.kind] || '◌' }}</span><span class="item-copy"><strong>{{ item.title }}<i v-if="!item.read_at" aria-label="خوانده‌نشده"></i></strong><span>{{ item.body }}</span><small>{{ date(item.created_at) }}</small></span><span class="item-arrow" aria-hidden="true">‹</span></button></div>
    <button v-if="loaded && nextOffset !== null" type="button" class="inbox-more" :disabled="busy" @click="load(false)">نمایش اعلان‌های بیشتر</button>
  </main>
</template>

<script>
import EmptyState from '@/components/EmptyState/index.vue';
export default {
  components: { EmptyState },
  name: 'AdminNotifications',
  data() { return { items: [], total: 0, unreadCount: 0, nextOffset: null,
    loading: false, loaded: false, saving: false, error: '', sequence: 0 }; },
  computed: {
    project() { return this.$STORE.state.userConfig.setProjectId; },
    busy() { return this.loading || this.saving; },
  },
  created() { this.load(true); },
  beforeDestroy() { this.sequence += 1; },
  watch: {
    project() {
      this.sequence += 1; this.items = []; this.total = 0; this.unreadCount = 0;
      this.nextOffset = null; this.loading = false; this.loaded = false; this.saving = false;
      this.error = ''; this.load(true);
    },
  },
  methods: {
    number(value) { return Number(value || 0).toLocaleString('fa-IR'); },
    date(value) { if (!value) return 'زمان نامشخص'; const parsed = new Date(value); return Number.isNaN(parsed.getTime()) ? 'زمان نامشخص' : parsed.toLocaleString('fa-IR', { year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit' }); },
    apiError(response) { return (response.data && (response.data.detail || response.data.message)) || 'دریافت اطلاعات ممکن نشد.'; },
    async load(reset) {
      if (!this.project || this.busy) return;
      const project = this.project;
      const sequence = ++this.sequence;
      const offset = reset ? 0 : this.nextOffset;
      if (offset === null) return;
      this.loading = true; this.error = '';
      try {
        const response = await this.$ApiServiceLayer.get(`/core/api/notifications/?p=${project}&limit=20&offset=${offset}`);
        if (sequence !== this.sequence || project !== this.project) return;
        if (response.status !== 200) { this.error = this.apiError(response); return; }
        const data = response.data || {};
        this.items = reset ? (data.results || []) : [...this.items, ...(data.results || [])];
        this.total = Number(data.count || 0); this.unreadCount = Number(data.unread_count || 0);
        this.$root.$emit('notifications-updated', { project, unreadCount: this.unreadCount });
        this.nextOffset = data.next_offset == null ? null : Number(data.next_offset);
        this.loaded = true;
      } catch (_) { if (sequence === this.sequence && project === this.project) this.error = 'دریافت اعلان‌ها ممکن نشد. دوباره تلاش کنید.'; }
      finally { if (sequence === this.sequence && project === this.project) this.loading = false; }
    },
    async openItem(item) {
      if (this.busy) return;
      const project = this.project;
      const sequence = this.sequence;
      this.saving = true; this.error = '';
      try {
        if (!item.read_at) {
          const response = await this.$ApiServiceLayer.post(`/core/api/notifications/${item.id}/read/?p=${project}`, '', {});
          if (sequence !== this.sequence || project !== this.project) return;
          if (response.status === 200) { item.read_at = response.data.read_at; this.unreadCount = Math.max(0, this.unreadCount - 1); this.$root.$emit('notifications-updated', { project, unreadCount: this.unreadCount }); }
          else this.error = this.apiError(response);
        }
      } catch (_) { if (sequence === this.sequence && project === this.project) this.error = 'ثبت وضعیت اعلان ممکن نشد.'; }
      finally { if (sequence === this.sequence && project === this.project) this.saving = false; }
      if (sequence === this.sequence && project === this.project && item.kind === 'support_incoming' && item.object_id) {
        this.$router.push({ name: 'ticketDetail', params: { id: item.object_id } }, () => {}, () => {});
      }
      if (sequence === this.sequence && project === this.project && item.kind === 'part_request') {
        this.$router.push('/warehouse/part-requests', () => {}, () => {});
      }
      if (sequence === this.sequence && project === this.project && ['visit_review', 'visit_declined', 'visit_overdue'].includes(item.kind) && item.object_id) {
        this.$router.push('/visitmanagment/answerlist/' + item.object_id, () => {}, () => {});
      }
    },
    async markAllRead() {
      if (!this.project || this.busy) return;
      const project = this.project;
      const sequence = this.sequence;
      this.saving = true; this.error = '';
      try {
        const response = await this.$ApiServiceLayer.post(`/core/api/notifications/read-all/?p=${project}`, '', {});
        if (sequence !== this.sequence || project !== this.project) return;
        if (response.status !== 200) { this.error = this.apiError(response); return; }
        const now = new Date().toISOString();
        this.items.forEach(item => { if (!item.read_at) item.read_at = now; });
        this.unreadCount = Number(response.data.unread_count || 0);
        this.$root.$emit('notifications-updated', { project, unreadCount: this.unreadCount });
      } catch (_) { if (sequence === this.sequence && project === this.project) this.error = 'ثبت وضعیت اعلان‌ها ممکن نشد.'; }
      finally { if (sequence === this.sequence && project === this.project) this.saving = false; }
    },
  },
};
</script>

<style scoped>
.admin-inbox{padding:24px;min-height:calc(100vh - 72px);color:var(--admin-text);background:#f5f8fb}.inbox-header{display:flex;justify-content:space-between;align-items:flex-end;gap:16px;padding:27px 30px;border-radius:22px;background:linear-gradient(135deg,#143b56,#1f6e86);color:#fff;box-shadow:0 12px 30px #153d541f}.inbox-eyebrow{font-size:12px;color:#bee7ef}.inbox-header h1{font-size:27px;color:#fff;margin:5px 0}.inbox-header p{font-size:13px;color:#e2f1f5;margin:0;line-height:1.8}.unread-summary{padding:10px 15px;border:1px solid #ffffff50;border-radius:13px;background:#ffffff1b;font-size:13px;white-space:nowrap}.unread-summary span{font-size:20px;font-weight:800}.inbox-toolbar{display:flex;justify-content:space-between;align-items:center;gap:14px;margin:25px 0 16px}.inbox-toolbar h2{font-size:19px;margin:0}.inbox-toolbar small{color:#638092}.inbox-toolbar>div:last-child{display:flex;gap:8px}.inbox-toolbar button,.inbox-more{min-height:42px;padding:8px 13px;border:1px solid #bbd4df;border-radius:10px;background:#fff;color:#216a84;font-size:13px;font-weight:700}.inbox-error{padding:14px;border:1px solid #f0c9c4;border-radius:12px;background:#fff1ef;color:#993f37;margin-bottom:14px}.inbox-error button{border:0;background:none;color:#236b8b;text-decoration:underline}.inbox-loading,.inbox-empty{padding:45px 20px;border:1px dashed #ccdde5;border-radius:16px;background:#fff;text-align:center;color:#60798b}.inbox-empty span{font-size:35px;color:#80a5b6}.inbox-empty h2{font-size:17px;margin:5px 0}.inbox-empty p{font-size:13px;margin:0}.inbox-list{display:grid;gap:10px}.inbox-item{display:flex;align-items:center;gap:14px;width:100%;padding:16px;border:1px solid #dce8ef;border-radius:15px;background:#fff;text-align:right;color:#23495e;box-shadow:0 3px 13px #173e5409}.inbox-item.unread{background:#f2faf8;border-color:#b5d7d2}.item-icon{width:42px;height:42px;flex:none;display:grid;place-items:center;border-radius:12px;background:#e4f2f2;color:#236a83;font-size:22px}.item-copy{display:grid;gap:5px;flex:1;min-width:0}.item-copy strong{font-size:14px;overflow-wrap:anywhere}.item-copy strong i{display:inline-block;width:7px;height:7px;margin:0 7px;border-radius:50%;background:#12927a}.item-copy>span{font-size:12px;color:#526f80;overflow-wrap:anywhere}.item-copy small{font-size:11px;color:#718b9a}.item-arrow{color:#7a9ba8;font-size:27px}.inbox-more{width:100%;margin-top:13px}.admin-inbox button:focus-visible{outline:3px solid #3898bd;outline-offset:3px}.admin-inbox button:disabled{opacity:.55;cursor:default}@media(max-width:767px){.admin-inbox{padding:16px}.inbox-header{align-items:flex-start;flex-direction:column;padding:23px}.inbox-toolbar{align-items:flex-start;flex-direction:column}.inbox-toolbar>div:last-child{width:100%}.inbox-toolbar button{flex:1}.inbox-item{padding:13px}}
</style>
