<template>
  <main class="vf-page chat-page" dir="rtl">
    <VisitTopBar :title="data ? data.counterpart : 'گفتگوی مأموریت'" :eyebrow="`مأموریت ${faId(id)}`" :fallback="fallback"
                 subtitle="شماره تماس هیچ‌کدام از طرفین نمایش داده نمی‌شود؛ گفتگو تا پایان مأموریت باز است." compact />
    <div class="vf-body chat-body">
      <div v-if="error" class="vf-banner vf-banner-danger" role="alert">
        <v-icon color="#8a2f2a">mdi-alert-circle-outline</v-icon>
        <div><strong>گفتگو دریافت نشد</strong><p>{{ error }}</p>
          <button type="button" class="vf-banner-action" @click="load()"><v-icon size="16">mdi-refresh</v-icon>تلاش دوباره</button></div>
      </div>
      <v-skeleton-loader v-if="loading && !data" class="vf-skeleton" type="list-item-two-line, list-item-two-line" />
      <template v-else-if="data">
        <EmptyState v-if="!data.messages.length" kind="chat" size="sm"
                     :title="data.open ? 'هنوز پیامی رد و بدل نشده' : 'گفتگویی انجام نشده'"
                     :description="data.open ? 'هماهنگی زمان حضور یا دسترسی به موتورخانه را اینجا انجام دهید.' : 'در این مأموریت گفتگویی انجام نشده است.'" />
        <ol v-else class="chat-list" aria-live="polite">
          <li v-for="message in data.messages" :key="message.id" class="chat-row" :class="{ mine: message.mine }">
            <div class="chat-bubble">
              <span class="chat-who">{{ message.mine ? 'شما' : message.name }} · {{ message.side === 'expert' ? 'کارشناس' : 'مدیر ساختمان' }}</span>
              <p>{{ message.body }}</p>
              <time :datetime="message.at">{{ faDate(message.at, true) }}</time>
            </div>
          </li>
        </ol>
        <div v-if="!data.open" class="vf-banner vf-banner-info" role="note">
          <v-icon color="#1d4f6d">mdi-lock-outline</v-icon>
          <div><strong>گفتگو بسته است</strong><p>گفتگو فقط تا پایان مأموریت باز است. برای پیگیری بعدی از پشتیبانی استفاده کنید.</p></div>
        </div>
      </template>
    </div>
    <footer v-if="data && data.open" class="vf-actionbar chat-composer">
      <form class="chat-form" @submit.prevent="send">
        <label for="chat-input" class="chat-label">پیام شما</label>
        <textarea id="chat-input" v-model="draft" rows="1" maxlength="1000" placeholder="پیام خود را بنویسید…" :disabled="sending"
                  @keydown.enter.exact.prevent="send" />
        <button type="submit" class="vf-btn vf-btn-primary chat-send" :disabled="sending || !draft.trim()" aria-label="ارسال پیام">
          <v-progress-circular v-if="sending" indeterminate size="18" width="2" color="white" /><v-icon v-else color="white" size="20">mdi-send</v-icon>
        </button>
      </form>
      <p v-if="sendError" class="chat-error" role="alert">{{ sendError }}</p>
    </footer>
  </main>
</template>

<script>
import VisitTopBar from '@/components/Visit/VisitTopBar.vue';
import { errorMessage } from '@/utils/clientRequests';
import { faDate, faId, withProject } from '@/utils/visitFlow';

import EmptyState from '@/components/EmptyState/index.vue';
const POLL_MS = 15000;

export default {
  name: 'VisitChat',
  components: { EmptyState, VisitTopBar },
  data: () => ({ data: null, loading: false, error: '', draft: '', sending: false, sendError: '', timer: null, sequence: 0 }),
  computed: {
    id() { return this.$route.params.id; },
    isClient() { return this.$route.name === 'clientVisitChat'; },
    path() { return this.isClient ? `/api/client/visits/${this.id}/chat/` : `/api/promoter/visit/${this.id}/chat/`; },
    fallback() { return this.isClient ? { name: 'clientVisitDetail', params: { id: this.id } } : { name: 'storeDetail', params: { id: this.id } }; },
  },
  watch: { id() { this.data = null; this.load(); } },
  created() { this.load(); this.timer = setInterval(() => { if (!document.hidden) this.load(true); }, POLL_MS); },
  beforeDestroy() { clearInterval(this.timer); this.sequence++; },
  methods: {
    faId, faDate,
    async load(quiet = false) {
      const sequence = ++this.sequence;
      if (!quiet) { this.loading = true; this.error = ''; }
      try {
        const response = await this.$ApiServiceLayer.get(withProject(this.path), this.$PATH.SERVICE_NAME.AUTH);
        if (sequence !== this.sequence) return;
        if (response.status !== 200) { if (!quiet) this.error = errorMessage(response); return; }
        const grew = !this.data || response.data.messages.length !== this.data.messages.length;
        this.data = response.data;
        if (grew) this.$nextTick(this.scrollEnd);
      } catch (_) {
        if (sequence === this.sequence && !quiet) this.error = 'اتصال برقرار نشد. دوباره تلاش کنید.';
      } finally {
        if (sequence === this.sequence) this.loading = false;
      }
    },
    async send() {
      const body = this.draft.trim();
      if (!body || this.sending) return;
      this.sending = true; this.sendError = '';
      try {
        const response = await this.$ApiServiceLayer.post(withProject(this.path), this.$PATH.SERVICE_NAME.AUTH, { body });
        if (response.status === 201) { this.draft = ''; this.data = response.data; this.$nextTick(this.scrollEnd); return; }
        this.sendError = errorMessage(response);
        if (response.status === 400) this.load(true);
      } catch (_) {
        this.sendError = 'پیام ارسال نشد. اتصال را بررسی و دوباره تلاش کنید.';
      } finally { this.sending = false; }
    },
    scrollEnd() { window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' }); },
  },
};
</script>

<style scoped>
.chat-body { padding-bottom: 120px; }
.chat-list { list-style: none; margin: 0; padding: 0; display: grid; gap: 10px; }
.chat-row { display: flex; justify-content: flex-start; }
.chat-row.mine { justify-content: flex-end; }
.chat-bubble { max-width: 84%; padding: 10px 13px 8px; border-radius: 16px 16px 16px 6px; background: #fff; border: 1px solid var(--vf-line);
  box-shadow: 0 3px 10px #1436500a; }
.chat-row.mine .chat-bubble { border-radius: 16px 16px 6px 16px; background: #e6f3fb; border-color: #c6e0ee; }
.chat-who { display: block; font-size: 11px; font-weight: 800; color: var(--vf-brand); margin-bottom: 2px; }
.chat-bubble p { margin: 0; white-space: pre-line; overflow-wrap: anywhere; font-size: 13.5px; color: var(--vf-ink); }
.chat-bubble time { display: block; margin-top: 4px; font-size: 10.5px; color: var(--vf-soft); text-align: left; }
.chat-composer { padding-top: 10px; }
.chat-form { display: flex; gap: 8px; align-items: flex-end; }
.chat-label { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); }
.chat-form textarea { flex: 1; min-height: 48px; max-height: 120px; padding: 12px 14px; border: 1px solid #c9dbe5; border-radius: 14px;
  background: #fff; font: inherit; font-size: 14px; resize: none; color: var(--vf-ink); }
.chat-form textarea:focus { outline: 3px solid #9fd0ea; border-color: var(--vf-brand); }
.chat-send { flex: none; width: 48px; padding: 0; }
.chat-error { margin: 6px 2px 0; color: var(--vf-danger); font-size: 12px; }
</style>
