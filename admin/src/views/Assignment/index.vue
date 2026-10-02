<template>
  <main class="assign-page" dir="rtl">
    <header class="assign-head">
      <div>
        <h1>تخصیص هوشمند کارشناس</h1>
        <p>بر اساس مهارت، گرید، کیفیت کار، ظرفیت و اولویت مأموریت؛ کار حساس‌تر زودتر و به بهترین کارشناس واجد شرایط پیشنهاد می‌شود. هیچ تخصیصی بدون تأیید شما انجام نمی‌شود.</p>
      </div>
      <div class="tabs" role="tablist">
        <button v-for="item in tabs" :key="item.key" type="button" role="tab" :aria-selected="tab === item.key ? 'true' : 'false'"
                :class="{ active: tab === item.key }" @click="tab = item.key">{{ item.label }}<b v-if="item.count">{{ fa(item.count) }}</b></button>
      </div>
    </header>

    <p v-if="error" class="notice error" role="alert">{{ error }} <button type="button" class="link" @click="load">تلاش دوباره</button></p>
    <div v-else-if="loading && !data" class="notice" role="status"><b-spinner small /> در حال دریافت…</div>
    <template v-else-if="data">
      <ProposalsTab v-if="tab === 'proposals'" :data="data" @changed="load" />
      <ExpertsTab v-else-if="tab === 'experts'" :data="data" @changed="load" />
      <SetupTab v-else :data="data" @changed="load" />
    </template>
  </main>
</template>

<script>
import ProposalsTab from './ProposalsTab.vue';
import ExpertsTab from './ExpertsTab.vue';
import SetupTab from './SetupTab.vue';
import { fa } from '@/utils/assignment';
import './assignment.css';

export default {
  name: 'SmartAssignment',
  components: { ProposalsTab, ExpertsTab, SetupTab },
  data: () => ({ data: null, loading: false, error: '', tab: 'proposals' }),
  computed: {
    project() { return this.$STORE.state.userConfig.setProjectId; },
    tabs() {
      return [{ key: 'proposals', label: 'پیشنهاد تخصیص', count: this.data ? this.data.unassigned : 0 },
        { key: 'experts', label: 'کارشناسان' }, { key: 'setup', label: 'مهارت‌ها و ضرایب' }];
    },
  },
  created() { this.load(); },
  methods: {
    fa,
    async load() {
      this.loading = true; this.error = '';
      const response = await this.$ApiServiceLayer.get(`/api/admin/assignment/overview/?p=${this.project}`, this.$PATH.SERVICE_NAME.AUTH);
      this.loading = false;
      if (response.status === 403) { this.error = 'تخصیص هوشمند نیازمند نقش مدیریتی پروژه است.'; return; }
      if (response.status !== 200) { this.error = this.$ApiServiceLayer.getErrorMessage(response); return; }
      this.data = response.data;
    },
  },
};
</script>
