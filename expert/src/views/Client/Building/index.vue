<template>
  <main class="field-page field-detail">
    <header class="field-row field-detail-header"><v-btn icon :to="{ name: 'home' }" aria-label="بازگشت به ساختمان‌ها"><v-icon>mdi-arrow-right</v-icon></v-btn><h1>جزئیات ساختمان</h1></header>
    <v-skeleton-loader v-if="loading" type="article, list-item-three-line" />
    <v-alert v-else-if="error" type="error" outlined role="alert">{{ error }}<v-btn text @click="load">تلاش دوباره</v-btn></v-alert>
    <template v-else>
      <section class="field-card"><span class="field-eyebrow">کد {{ building.code || building.id }}</span><h2>{{ building.verbose_name || building.name }}</h2><p class="field-address">{{ building.address || 'آدرس ثبت نشده' }}</p><span class="field-badge">{{ totalElevators }} آسانسور در دسترس</span></section>
      <v-alert v-if="submitted" type="success" outlined role="status">درخواست ثبت شد و در انتظار بررسی و برنامه‌ریزی شرکت است.<v-btn text :to="{ name: 'clientVisits' }">مشاهده درخواست‌ها</v-btn></v-alert>
      <header class="field-heading"><h2>انتخاب آسانسورها</h2><p>آسانسورهایی که به خدمت نیاز دارند را انتخاب کنید.</p></header>
      <section v-for="group in groups" :key="group.id" class="field-card field-elevator-group">
        <h3>{{ group.verbose_name || group.name }}</h3>
        <label v-for="link in group.elevators || []" :key="link.elevator.id" class="field-elevator" :class="{ 'is-selected': selected.includes(link.elevator.id) }">
          <input type="checkbox" :value="link.elevator.id" v-model="selected" :disabled="sending" />
          <span class="field-grow"><strong>{{ link.elevator.title || 'آسانسور ' + link.elevator.id }}</strong><span class="field-muted">{{ link.elevator.number_of_floors || '—' }} طبقه · ظرفیت {{ link.elevator.capacity || '—' }}</span></span>
          <v-icon color="primary">mdi-elevator</v-icon>
        </label>
        <p v-if="!(group.elevators || []).length" class="field-muted">آسانسوری ثبت نشده است.</p>
      </section>
      <div class="field-sticky-action"><span>{{ selected.length ? selected.length + ' آسانسور انتخاب شد' : 'یک یا چند آسانسور را انتخاب کنید' }}</span><v-btn block large color="primary" elevation="0" :disabled="!selected.length || sending" @click="openSheet">ادامه و انتخاب خدمت<v-icon left>mdi-chevron-left</v-icon></v-btn></div>
    </template>
    <v-bottom-sheet v-model="sheet" max-width="576" :persistent="sending">
      <v-sheet class="field-request-sheet">
        <div class="field-row"><h2 class="field-grow">درخواست خدمت</h2><v-btn icon aria-label="بستن انتخاب خدمت" :disabled="sending" @click="sheet = false"><v-icon>mdi-close</v-icon></v-btn></div>
        <p class="field-muted">برای {{ selected.length }} آسانسور، نوع خدمت را مشخص کنید.</p>
        <v-progress-linear v-if="typesLoading" indeterminate color="primary" />
        <v-alert v-if="requestError" type="error" outlined role="alert">{{ requestError }}</v-alert>
        <v-radio-group v-model="type" :disabled="sending" class="field-type-list"><v-radio v-for="item in types" :key="item.id" :value="item.id" :label="item.verbose_name || item.name" /></v-radio-group>
        <p v-if="!typesLoading && !types.length" class="field-muted">خدمتی برای این پروژه در دسترس نیست.</p>
        <v-btn v-if="!types.length && !typesLoading" text color="primary" @click="openSheet">دریافت دوباره خدمات</v-btn>
        <v-btn block large color="primary" elevation="0" :loading="sending" :disabled="!type || !selected.length || typesLoading" @click="submit">ثبت درخواست</v-btn>
        <p class="field-caption">پس از بررسی درخواست، زمان مراجعه کارشناس تعیین می‌شود.</p>
      </v-sheet>
    </v-bottom-sheet>
  </main>
</template>
<script>
import { pageRows, errorMessage, persistentRequestKey, clearRequestKey } from '@/utils/clientRequests';
export default {
  data: () => ({ building: {}, children: [], selected: [], types: [], type: null, sheet: false, loading: false, sending: false, typesLoading: false, error: '', requestError: '', submitted: false, key: '', fingerprint: '' }),
  computed: {
    project() { return this.$STORE.state.userConfig.selectedProject; },
    requestScope() { return [this.$STORE.state.userConfig.userInfo.user.id, this.project, this.$route.params.id].join('.'); },
    groups() { return [this.building, ...this.children].filter(group => group.id); },
    totalElevators() { return this.groups.reduce((count, group) => count + (group.elevators || []).length, 0); },
    selections() {
      return this.groups.map(group => ({ building: group.id, elevators: (group.elevators || []).map(link => link.elevator.id).filter(id => this.selected.includes(id)).sort((a, b) => a - b) })).filter(group => group.elevators.length).sort((a, b) => a.building - b.building);
    }
  },
  mounted() { this.load(); },
  watch: { '$route.params.id'() { this.selected = []; this.load(); } },
  methods: {
    async load() {
      this.loading = true; this.error = ''; this.submitted = false;
      try {
        const root = await this.$ApiServiceLayer.get(this.$PATH.RELATIVE_PATH.MULTI.BUILDING_EDITS + this.$route.params.id + '/?p=' + this.project);
        if (root.status !== 200) { this.error = errorMessage(root); return; }
        this.building = root.data;
        const children = await this.$ApiServiceLayer.get(this.$PATH.RELATIVE_PATH.MULTI.BUILDING_LIST_CREATE_CLIENT + '?p=' + this.project + '&parent=' + this.building.id);
        if (children.status !== 200) { this.error = errorMessage(children); return; }
        this.children = pageRows(children.data);
      } finally { this.loading = false; }
    },
    async openSheet() {
      this.sheet = true; this.requestError = ''; this.typesLoading = true;
      try {
        const response = await this.$ApiServiceLayer.get(this.$PATH.RELATIVE_PATH.GET.VISIT_TYPE + '?p=' + this.project + '&is_active=true', 'core');
        if (response.status !== 200) { this.requestError = errorMessage(response); return; }
        this.types = pageRows(response.data);
        if (!this.types.some(item => item.id === this.type)) this.type = null;
      } finally { this.typesLoading = false; }
    },
    async submit() {
      if (this.sending || !this.type || !this.selections.length) return;
      this.sending = true; this.requestError = '';
      try {
        const payload = { buildings: this.selections, type: this.type };
        const fingerprint = JSON.stringify(payload);
        if (fingerprint !== this.fingerprint) { this.key = persistentRequestKey(this.requestScope, payload); this.fingerprint = fingerprint; }
        const response = await this.$ApiServiceLayer.post(this.$PATH.RELATIVE_PATH.POST.SERVICE_REQUEST_CREATE + '?p=' + this.project, '', { ...payload, request_key: this.key });
        if (![200, 201].includes(response.status) || !(response.data.successfuls || []).length || (response.data.errors || []).length) { this.requestError = errorMessage(response); return; }
        clearRequestKey(this.requestScope, this.key);
        this.sheet = false; this.submitted = true; this.selected = []; this.type = null; this.key = ''; this.fingerprint = '';
      } finally { this.sending = false; }
    }
  }
};
</script>
