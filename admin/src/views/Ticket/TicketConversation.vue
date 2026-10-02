<template>
  <div class="record-detail">
    <div v-if="loading" class="detail-state" role="status">در حال دریافت تیکت…</div>
    <div v-else-if="error" class="detail-state" role="alert">
      <p>{{ error }}</p>
      <button class="accept" @click="load">تلاش دوباره</button>
    </div>
    <template v-else>
      <section class="detail-hero">
        <div class="detail-hero-top">
          <div>
            <span class="detail-eyebrow">تیکت پشتیبانی · {{ ticket.id }}</span>
            <h2>{{ ticket.title || 'تیکت پشتیبانی' }}</h2>
            <p>{{ ticket.subject }}</p>
          </div>
          <router-link class="detail-back" to="/ticket/ticketlist">بازگشت به فهرست ←</router-link>
        </div>
        <div class="detail-summary">
          <span class="detail-badge">{{
            { W: 'در انتظار پاسخ', A: 'پاسخ داده‌شده', C: 'بسته‌شده' }[ticket.status] || 'نامشخص'
          }}</span
          ><span>{{ messages.length }} پیام</span>
        </div>
        <InfoGrid
          :fields="[
            { label: 'ثبت‌کننده', value: person(ticket.creator) },
            {
              label: 'ساختمان',
              value: (
                (ticket.visit || {}).building ||
                (typeof ticket.building === 'object' ? ticket.building : {}) ||
                {}
              ).verbose_name,
            },
            {
              label: 'شناسه ویزیت',
              value: typeof ticket.visit === 'object' ? (ticket.visit || {}).id : ticket.visit,
            },
          ]"
        />
      </section>
      <section class="detail-section">
        <div class="detail-section-heading">
          <div>
            <h2>گفتگو و پیگیری</h2>
            <p>تاریخچه پیام‌های این درخواست</p>
          </div>
          <button
            v-if="ticket.status !== 'C'"
            class="reject"
            :disabled="busy"
            @click="closeOpen = true"
          >
            بستن تیکت
          </button>
        </div>
        <EmptyState v-if="!messages.length" kind="chat" size="sm" inline title="هنوز پیامی ثبت نشده" description="" />
        <div class="ticket-thread">
          <article
            v-for="message in messages"
            :key="message.id"
            class="ticket-message"
            :class="{
              'ticket-message-owner': (message.created_by || {}).id === (ticket.creator || {}).id,
            }"
          >
            <header>
              <strong>{{ person(message.created_by) || 'کاربر' }}</strong
              ><DisplayDate :value="message.datetime_created" showTime />
            </header>
            <p>{{ message.body }}</p>
          </article>
        </div>
        <form v-if="ticket.status !== 'C'" class="ticket-reply" @submit.prevent="send">
          <label for="ticket-reply-body">متن پاسخ</label
          ><textarea
            id="ticket-reply-body"
            v-model="body"
            rows="4"
            placeholder="پاسخ خود را بنویسید…"
          />
          <p v-if="actionError" class="detail-error" role="alert">{{ actionError }}</p>
          <div class="detail-form-actions">
            <button class="accept" :disabled="busy || !body.trim()">
              {{ busy ? 'در حال ارسال…' : 'ارسال پاسخ' }}
            </button>
          </div>
        </form>
        <p v-else class="detail-empty mt-4">این تیکت بسته شده است.</p>
      </section>
    </template>
    <b-modal v-model="closeOpen" title="بستن تیکت" header-close-label="بستن" centered hide-footer
      ><p>این گفتگو بسته شود؟ پس از بسته شدن امکان ارسال پاسخ وجود ندارد.</p>
      <p v-if="actionError" class="detail-error" role="alert">{{ actionError }}</p>
      <div class="detail-form-actions">
        <button class="reject" :disabled="busy" @click="closeOpen = false">انصراف</button
        ><button class="accept" :disabled="busy" @click="close">بستن تیکت</button>
      </div></b-modal
    >
  </div>
</template>
<script>
import InfoGrid from '@/components/RecordDetails/InfoGrid.vue';
import DisplayDate from '@/components/DisplayDate/index.vue';
import EmptyState from '@/components/EmptyState/index.vue';
export default {
  components: { EmptyState, InfoGrid, DisplayDate },
  data: () => ({
    loading: true,
    busy: false,
    error: '',
    actionError: '',
    ticket: {},
    messages: [],
    body: '',
    closeOpen: false,
  }),
  watch: {
    '$route.params.id': { immediate: true, handler: 'load' },
    closeOpen(value) {
      if (value) this.actionError = '';
    },
  },
  methods: {
    person(user) {
      return user
        ? [user.first_name, user.last_name].filter(Boolean).join(' ') || user.username
        : '';
    },
    path(value) {
      return (
        value + (value.includes('?') ? '&' : '?') + 'p=' + this.$STORE.state.userConfig.setProjectId
      );
    },
    async load() {
      const id = this.$route.params.id;
      this.loading = true;
      this.error = '';
      try {
        const results = await Promise.all([
          this.$ApiServiceLayer.get(this.path('/api/admin/ticket/edits/' + id + '/'), '/core'),
          this.$ApiServiceLayer.get(
            this.path(
              '/api/admin/ticket_message/list_create/?ticket=' + id + '&ordering=datetime_created'
            ),
            '/core'
          ),
        ]);
        const failed = results.find((r) => r.status !== 200);
        if (failed) throw new Error(this.$ApiServiceLayer.getErrorMessage(failed));
        if (id !== this.$route.params.id) return;
        this.ticket = results[0].data;
        this.messages = Array.isArray(results[1].data)
          ? results[1].data
          : results[1].data.results || [];
      } catch (e) {
        if (id === this.$route.params.id) this.error = e.message;
      } finally {
        if (id === this.$route.params.id) this.loading = false;
      }
    },
    async write(method, path, data) {
      this.busy = true;
      this.actionError = '';
      try {
        const res = await this.$ApiServiceLayer[method](this.path(path), '/core', data);
        if (res.status < 200 || res.status >= 300) {
          this.actionError = this.$ApiServiceLayer.getErrorMessage(res);
          return false;
        }
        return true;
      } finally {
        this.busy = false;
      }
    },
    async send() {
      if (
        await this.write('post', '/api/admin/ticket_message/list_create/', {
          ticket: Number(this.$route.params.id),
          body: this.body.trim(),
        })
      ) {
        this.body = '';
        await this.load();
        this.$notify({ group: 'tc', type: 'success', text: 'پاسخ ارسال شد.' });
      }
    },
    async close() {
      if (
        await this.write('patch', '/api/admin/ticket/edits/' + this.$route.params.id + '/', {
          status: 'C',
        })
      ) {
        this.closeOpen = false;
        await this.load();
        this.$notify({ group: 'tc', type: 'success', text: 'تیکت بسته شد.' });
      }
    },
  },
};
</script>
<style scoped>
.ticket-thread {
  display: grid;
  gap: 18px;
}
.ticket-message {
  padding: 20px;
  background: #f6f8fc;
  border: 1px solid #e6ebf3;
  border-radius: 12px;
  margin-right: 8%;
}
.ticket-message-owner {
  background: #f0f4ff;
  border-color: #dce5fc;
  margin-right: 0;
  margin-left: 8%;
}
.ticket-message header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding-bottom: 14px;
  border-bottom: 1px solid #dce3ef;
  font-size: 12px;
}
.ticket-message p {
  font-size: 14px;
  line-height: 2;
  margin: 16px 0 0;
  white-space: pre-line;
  overflow-wrap: anywhere;
}
.ticket-reply {
  margin-top: 30px;
  padding-top: 24px;
  border-top: 1px solid #edf0f6;
}
.ticket-reply label {
  font-size: 13px;
  margin-bottom: 10px;
}
@media (max-width: 640px) {
  .ticket-message {
    padding: 16px;
    margin-left: 0;
    margin-right: 0;
  }
  .ticket-message header {
    align-items: flex-start;
  }
}
</style>
