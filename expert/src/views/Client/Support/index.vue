<template>
  <main class="field-page client-support" dir="rtl">
    <header class="support-hero">
      <router-link :to="{ name: isExpert ? 'tasks' : 'home' }" class="support-back"><v-icon color="white" size="19">mdi-arrow-right</v-icon>{{ isExpert ? 'کارهای من' : 'داشبورد' }}</router-link>
      <span class="support-eyebrow">همراه شما در هر مرحله</span>
      <h1>پشتیبانی سان اپ</h1>
      <p>پرسش یا مشکلتان را بنویسید و پاسخ را همین‌جا پیگیری کنید.</p>
    </header>

    <div class="support-body">
      <v-alert v-if="error" type="error" outlined role="alert">{{ error }} <v-btn text color="error" @click="load">تلاش دوباره</v-btn></v-alert>
      <template v-if="activeTicketId">
        <button class="support-text-button" type="button" @click="openList"><v-icon size="18">mdi-arrow-right</v-icon>همه گفتگوها</button>
        <v-skeleton-loader v-if="detailLoading" type="article, article" />
        <template v-else-if="detail">
          <section class="support-panel" aria-labelledby="thread-title">
            <span class="support-kicker">گفتگوی شماره {{ number(detail.id) }}</span>
            <h2 id="thread-title">{{ detail.title }}</h2>
            <span class="support-status" :class="statusClass(detail.status)">{{ statusLabel(detail.status) }}</span>
            <router-link v-if="detail.visit_id" :to="{ name: isExpert ? 'storeDetail' : 'clientVisitDetail', params: { id: detail.visit_id } }" class="support-context">خدمت مرتبط را ببینید <v-icon size="18">mdi-arrow-left</v-icon></router-link>
          </section>
          <section class="support-panel" aria-label="پیام‌های گفتگو">
            <EmptyState v-if="!detail.messages.length" kind="chat" size="sm" inline title="هنوز پیامی ثبت نشده" description="" />
            <div v-for="message in detail.messages" :key="message.id" class="support-message" :class="{ mine: message.is_mine }">
              <span>{{ message.is_mine ? 'شما' : 'پشتیبانی' }} · {{ date(message.created_at) }}</span>
              <p>{{ message.body }}</p>
            </div>
          </section>
          <form v-if="detail.status !== 'C'" class="support-panel support-compose" @submit.prevent="sendReply">
            <v-textarea v-model="reply" outlined auto-grow rows="2" maxlength="5000" counter="5000" label="پاسخ شما" :disabled="sending" />
            <v-btn color="primary" block type="submit" :loading="sending" :disabled="sending || !reply.trim()">ارسال پاسخ</v-btn>
          </form>
          <v-alert v-else type="info" outlined>این گفتگو بسته شده است. برای موضوع تازه، گفتگوی جدید بسازید.</v-alert>
        </template>
      </template>
      <template v-else>
        <button v-if="!creating" class="support-new" type="button" @click="creating = true"><span><v-icon color="#1c5473" size="24">mdi-plus-circle-outline</v-icon></span><strong>گفتگوی جدید</strong><v-icon size="20">mdi-arrow-left</v-icon></button>
        <form v-if="creating" class="support-panel support-compose" @submit.prevent="createTicket">
          <div class="support-section-head"><div><span class="support-kicker">درخواست تازه</span><h2>چطور می‌توانیم کمک کنیم؟</h2></div><button type="button" class="support-close" aria-label="بستن فرم" @click="creating = false"><v-icon size="20">mdi-close</v-icon></button></div>
          <p v-if="contextVisit" class="support-context-note">این گفتگو به خدمت شماره {{ number(contextVisit) }} متصل می‌شود.</p>
          <v-text-field v-model="title" outlined maxlength="60" counter="60" label="موضوع" :disabled="sending" />
          <v-textarea v-model="body" outlined auto-grow rows="4" maxlength="5000" counter="5000" label="شرح درخواست" :disabled="sending" />
          <v-btn color="primary" block type="submit" :loading="sending" :disabled="sending || !title.trim() || !body.trim()">ثبت و ارسال گفتگو</v-btn>
        </form>
        <section class="support-list" aria-labelledby="support-list-heading">
          <div class="support-section-head"><div><span class="support-kicker">پیگیری ساده</span><h2 id="support-list-heading">گفتگوهای شما</h2></div><span class="support-count">{{ number(tickets.length) }}</span></div>
          <v-skeleton-loader v-if="loading" type="list-item-three-line, list-item-three-line" />
          <EmptyState v-else-if="!tickets.length && !error" kind="chat" size="sm" title="هنوز گفتگویی ندارید" description="از همین‌جا موضوعتان را مطرح کنید." />
          <button v-for="ticket in tickets" :key="ticket.id" class="support-ticket" type="button" @click="openTicket(ticket.id)"><span class="support-ticket-icon"><v-icon color="#266681" size="21">mdi-message-text-outline</v-icon></span><span class="support-ticket-copy"><strong>{{ ticket.title }}</strong><small>{{ date(ticket.updated_at) }}</small></span><span class="support-status" :class="statusClass(ticket.status)">{{ statusLabel(ticket.status) }}</span><v-icon color="#39718b" size="19">mdi-chevron-left</v-icon></button>
        </section>
      </template>
    </div>
  </main>
</template>

<script>
import { errorMessage } from '@/utils/clientRequests';

import EmptyState from '@/components/EmptyState/index.vue';
export default {
  components: { EmptyState },
  name: 'ClientSupport',
  data: () => ({ tickets: [], detail: null, loading: false, detailLoading: false, sending: false,
    error: '', creating: false, title: '', body: '', reply: '', sequence: 0 }),
  computed: {
    project() { return this.$STORE.state.userConfig.selectedProject; },
    isExpert() { return ['onlineChat', 'chatHistory'].includes(this.$route.name); },
    activeTicketId() { return this.$route.query.ticket || null; },
    contextVisit() { return this.$route.params.id || this.$route.query.visit || null; },
    contextTopic() { return this.$route.query.topic || null; },
  },
  mounted() {
    this.creating = !!(this.contextVisit || this.contextTopic);
    if (this.contextTopic === 'building') this.title = 'درخواست افزودن ساختمان';
    if (this.contextTopic === 'assignment') this.title = 'پیگیری واگذاری خدمت به کارشناس';
    this.load();
  },
  beforeDestroy() { this.sequence += 1; },
  watch: {
    project() {
      this.sequence += 1;
      this.tickets = []; this.detail = null; this.title = ''; this.body = ''; this.reply = '';
      this.loading = false; this.detailLoading = false; this.sending = false; this.error = '';
      this.creating = false;
      this.load();
    },
    activeTicketId() { this.detail = null; this.reply = ''; this.detailLoading = false; this.sending = false; this.error = ''; this.load(); },
    contextVisit(value) { if (value && !this.activeTicketId) this.creating = true; },
  },
  methods: {
    number(value) { return Number(value || 0).toLocaleString('fa-IR'); },
    date(value) { if (!value) return 'تاریخ نامشخص'; const parsed = new Date(value); return Number.isNaN(parsed.getTime()) ? 'تاریخ نامشخص' : parsed.toLocaleDateString('fa-IR', { year: 'numeric', month: 'long', day: 'numeric' }); },
    statusLabel(value) { return ({ W: 'در انتظار پاسخ', A: 'پاسخ داده‌شده', C: 'بسته‌شده' })[value] || 'در حال پیگیری'; },
    statusClass(value) { return ({ W: 'waiting', A: 'answered', C: 'closed' })[value] || 'waiting'; },
    listUrl() { return `core/api/${this.isExpert ? 'expert' : 'client'}/support/tickets/?p=${this.project}`; },
    detailUrl(id) { return `core/api/${this.isExpert ? 'expert' : 'client'}/support/tickets/${id}/?p=${this.project}`; },
    openList() { this.$router.push({ name: this.isExpert ? 'chatHistory' : 'clientSupport' }); },
    openTicket(id) { this.$router.push({ name: this.isExpert ? 'chatHistory' : 'clientSupport', query: { ticket: id } }); },
    async load() {
      const sequence = ++this.sequence;
      if (!this.project) return;
      const project = this.project;
      this.error = '';
      if (this.activeTicketId) {
        this.detailLoading = true;
        try {
          const response = await this.$ApiServiceLayer.get(this.detailUrl(this.activeTicketId));
          if (sequence !== this.sequence || project !== this.project) return;
          if (response.status !== 200) { this.error = errorMessage(response); return; }
          this.detail = response.data;
        } catch (_) { if (sequence === this.sequence && project === this.project) this.error = 'دریافت گفتگو ممکن نشد.'; }
        finally { if (sequence === this.sequence && project === this.project) this.detailLoading = false; }
      } else {
        this.loading = true;
        try {
          const response = await this.$ApiServiceLayer.get(this.listUrl());
          if (sequence !== this.sequence || project !== this.project) return;
          if (response.status !== 200) { this.error = errorMessage(response); return; }
          this.tickets = response.data;
        } catch (_) { if (sequence === this.sequence && project === this.project) this.error = 'دریافت گفتگوها ممکن نشد.'; }
        finally { if (sequence === this.sequence && project === this.project) this.loading = false; }
      }
    },
    async createTicket() {
      if (this.sending || !this.title.trim() || !this.body.trim()) return;
      const project = this.project;
      const sequence = this.sequence;
      this.sending = true; this.error = '';
      try {
        const payload = { title: this.title.trim(), body: this.body.trim() };
        if (this.contextVisit) payload.visit = Number(this.contextVisit);
        const response = await this.$ApiServiceLayer.post(this.listUrl(), '', payload);
        if (sequence !== this.sequence || project !== this.project) return;
        if (response.status !== 201) { this.error = errorMessage(response); return; }
        this.title = ''; this.body = ''; this.creating = false;
        this.openTicket(response.data.id);
      } catch (_) { if (sequence === this.sequence && project === this.project) this.error = 'ثبت گفتگو ممکن نشد. دوباره تلاش کنید.'; }
      finally { if (sequence === this.sequence && project === this.project) this.sending = false; }
    },
    async sendReply() {
      if (this.sending || !this.reply.trim() || !this.detail) return;
      const project = this.project;
      const sequence = this.sequence;
      const detailId = this.detail.id;
      this.sending = true; this.error = '';
      try {
        const response = await this.$ApiServiceLayer.post(this.detailUrl(detailId), '', { body: this.reply.trim() });
        if (sequence !== this.sequence || project !== this.project || !this.detail || this.detail.id !== detailId) return;
        if (response.status !== 201) { this.error = errorMessage(response); return; }
        this.detail.messages.push(response.data); this.detail.status = 'W'; this.reply = '';
      } catch (_) { if (sequence === this.sequence && project === this.project) this.error = 'ارسال پاسخ ممکن نشد. دوباره تلاش کنید.'; }
      finally { if (sequence === this.sequence && project === this.project) this.sending = false; }
    },
  },
};
</script>

<style scoped>
.client-support{padding:0 0 calc(112px + env(safe-area-inset-bottom));background:#f4f8fb;color:#17394e}.support-hero{padding:calc(20px + env(safe-area-inset-top)) 20px 27px;color:#fff;background:linear-gradient(145deg,#112f4a,#216d83);border-radius:0 0 29px 29px;box-shadow:0 12px 27px #123d5522}.support-back{display:inline-flex;align-items:center;gap:6px;min-height:44px;color:#e6f5fa;text-decoration:none;font-size:13px}.support-eyebrow{display:block;margin-top:23px;color:#bce7ed;font-size:12px;font-weight:700}.support-hero h1{color:#fff;font-size:27px;margin:5px 0}.support-hero p{margin:0;max-width:360px;color:#e3f2f5;font-size:13px;line-height:1.8}.support-body{display:grid;gap:15px;padding:22px 20px}.support-new{display:flex;align-items:center;gap:11px;min-height:69px;width:100%;padding:13px 15px;border:1px solid #c8e0e4;border-radius:17px;background:#e7f4f1;color:#16445a;text-align:right}.support-new span{width:38px;height:38px;display:grid;place-items:center;border-radius:11px;background:#fff}.support-new strong{flex:1;font-size:14px}.support-panel{padding:18px;border:1px solid #dce9ef;border-radius:17px;background:#fff;box-shadow:0 4px 17px #173f5809}.support-section-head{display:flex;align-items:flex-start;justify-content:space-between;gap:12px;margin-bottom:15px}.support-kicker{color:#2d758e;font-size:11px;font-weight:700}.support-section-head h2,.support-panel h2{color:#17394e;font-size:17px;margin:2px 0 0}.support-close{min-width:40px;min-height:40px;color:#536f80}.support-compose .v-input{margin-top:9px}.support-list{display:grid;gap:9px;margin-top:9px}.support-count{min-width:30px;padding:4px 8px;border-radius:8px;background:#e6f0f4;color:#235f79;text-align:center;font-size:12px}.support-ticket{display:flex;align-items:center;gap:10px;width:100%;min-height:76px;padding:12px;border:1px solid #dce9ef;border-radius:15px;background:#fff;color:#17394e;text-align:right}.support-ticket-icon{width:38px;height:38px;flex:none;display:grid;place-items:center;border-radius:11px;background:#eaf4f7}.support-ticket-copy{display:grid;gap:4px;flex:1;min-width:0}.support-ticket-copy strong{overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:13px}.support-ticket-copy small{color:#667f8d;font-size:11px}.support-status{display:inline-block;flex:none;border-radius:8px;padding:5px 7px;font-size:10px;font-weight:700}.support-status.waiting{color:#805414;background:#fff1d9}.support-status.answered{color:#17634f;background:#e2f3e9}.support-status.closed{color:#637384;background:#e9eef2}.support-empty{padding:25px 15px;border:1px dashed #bfd4df;border-radius:15px;background:#fff;text-align:center;color:#5d7887;font-size:13px}.support-empty p{margin:8px 0 0}.support-text-button{justify-self:start;display:inline-flex;align-items:center;gap:5px;min-height:42px;border:0;background:transparent;color:#216987;font-size:13px;font-weight:700}.support-context{display:flex;align-items:center;gap:4px;margin-top:14px;color:#256984;text-decoration:none;font-size:12px;font-weight:700}.support-context-note{padding:11px;border-radius:11px;background:#eef6f7;color:#386c7c;font-size:12px}.support-message{max-width:94%;margin:11px 0;padding:12px 14px;border-radius:15px 15px 4px 15px;background:#edf3f7;color:#24465b}.support-message.mine{margin-right:auto;border-radius:15px 15px 15px 4px;background:#e4f3ea}.support-message span{font-size:10px;color:#617f8f}.support-message p{margin:7px 0 0;white-space:pre-wrap;overflow-wrap:anywhere;font-size:13px;line-height:1.8}.client-support button:focus-visible,.client-support a:focus-visible{outline:3px solid #389bc2;outline-offset:3px}@media(max-width:350px){.support-body{padding-left:14px;padding-right:14px}.support-hero{padding-left:16px;padding-right:16px}.support-panel{padding:15px}.support-status{font-size:9px}}
</style>
