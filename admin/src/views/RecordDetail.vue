<template>
  <div class="record-detail">
    <div v-if="loading" class="detail-state" role="status">
      <b-spinner small /> در حال دریافت اطلاعات…
    </div>
    <div v-else-if="error" class="detail-state" role="alert">
      <p>{{ error }}</p>
      <button class="accept" @click="load">تلاش دوباره</button>
    </div>
    <template v-else>
      <section class="detail-hero">
        <div class="detail-hero-top">
          <div>
            <span class="detail-eyebrow">{{ kindLabel }} · {{ record.id }}</span>
            <h2>{{ title }}</h2>
            <p>{{ subtitle }}</p>
          </div>
          <router-link class="detail-back" :to="back">بازگشت به فهرست ←</router-link>
        </div>
        <div class="detail-summary">
          <span class="detail-badge">{{ kindLabel }}</span
          ><span v-if="record.code">کد: {{ record.code }}</span
          ><span v-if="record.type">{{ label(record.type) }}</span>
        </div>
        <InfoGrid :fields="summary" />
      </section>
      <section v-for="section in sections" :key="section.title" class="detail-section">
        <div class="detail-section-heading">
          <h2>{{ section.title }}</h2>
        </div>
        <InfoGrid
          :fields="
            section.fields.map((field) => ({
              label: field[1],
              value: fieldValue(field[0]),
              wide: field[2],
            }))
          "
        />
      </section>
      <PriorityPanel
        v-if="priorityTarget"
        :target="priorityTarget"
        :id="record.id"
      />
      <MaintenancePanel
        v-if="maintenanceElevators"
        :elevators="maintenanceElevators"
        :building="kind === 'building' ? record.id : null"
      />
      <section v-if="kind === 'building'" class="detail-section">
        <div class="detail-section-heading">
          <div>
            <h2>آسانسورهای ساختمان</h2>
            <p>{{ elevators.length }} آسانسور ثبت‌شده</p>
          </div>
          <router-link
            class="detail-text-link"
            :to="'/elevatormanagement/createelevator/' + record.id"
            >افزودن آسانسور</router-link
          >
        </div>
        <EmptyState v-if="!elevators.length" kind="building" size="sm" inline title="آسانسوری ثبت نشده" description="با «افزودن آسانسور» اولین آسانسور این ساختمان را تعریف کنید." />
        <div class="related-record-grid">
          <router-link
            v-for="item in elevators"
            :key="item.elevator.id"
            class="related-record"
            :to="'/elevatormanagement/elevatordetail/' + item.elevator.id"
            ><span class="section-symbol"><ActionIcon name="elevator" /></span>
            <div>
              <h3>{{ item.elevator.title || 'آسانسور' }}</h3>
              <p>
                {{ item.elevator.capacity || '—' }} نفر · {{ item.elevator.number_of_floors }} طبقه
              </p>
            </div>
            <ActionIcon name="view"
          /></router-link>
        </div>
      </section>
      <section v-if="kind === 'customer'" class="detail-section">
        <div class="detail-section-heading"><h2>افراد مرتبط با مشتری</h2></div>
        <EmptyState v-if="!contacts.length" kind="generic" size="sm" inline title="فردی ثبت نشده" description="" />
        <div v-for="item in contacts" :key="item.id" class="related-record">
          <InfoGrid
            :fields="[
              {
                label: 'نام و نام خانوادگی',
                value: [item.user.first_name, item.user.last_name].filter(Boolean).join(' '),
              },
              { label: 'شماره تماس', value: item.user.username, ltr: true },
              { label: 'ایمیل', value: item.user.email },
            ]"
          />
        </div>
      </section>
      <section v-if="kind === 'building'" class="detail-section management-section">
        <div class="detail-section-heading">
          <div>
            <h2>مدیریت ساختمان</h2>
            <p>مدیر فعلی و تاریخچه واگذاری این ساختمان</p>
          </div>
        </div>
        <div class="management-current">
          <span class="management-caption">مدیر فعلی</span>
          <strong>{{ currentManagement.map((item) => clientName(item.client)).join('، ') || 'ثبت نشده' }}</strong>
        </div>
        <div v-if="managements.length" class="management-history">
          <div v-for="item in managements" :key="item.id" class="management-history-row">
            <strong>{{ clientName(item.client) }}</strong>
            <span>{{ item.start_at ? formatDate(item.start_at) : 'شروع نامشخص' }} تا {{ item.end_at ? formatDate(item.end_at) : 'اکنون' }}</span>
            <small v-if="item.end_reason">{{ item.end_reason }}</small>
          </div>
        </div>
        <div class="management-form">
          <h3>واگذاری مدیریت</h3>
          <p>واگذاری، مدیر قبلی را با حفظ تاریخچه پایان می‌دهد.</p>
          <label for="management-client-search">جست‌وجوی کلاینت</label>
          <div class="management-search">
            <input id="management-client-search" v-model.trim="clientSearch" type="search" placeholder="نام کلاینت را وارد کنید" @keydown.enter.prevent="searchClients" />
            <button type="button" :disabled="searchingClients || clientSearch.length < 2" @click="searchClients">{{ searchingClients ? 'در حال جست‌وجو…' : 'جست‌وجو' }}</button>
          </div>
          <div v-if="clientResults.length" class="management-results" role="listbox" aria-label="نتیجه جست‌وجوی کلاینت">
            <button v-for="client in clientResults" :key="client.id" type="button" :class="{ selected: selectedClient && selectedClient.id === client.id }" @click="selectedClient = client">
              {{ clientName(client) }}
            </button>
          </div>
          <p v-if="selectedClient" class="management-selection">کلاینت انتخاب‌شده: <strong>{{ clientName(selectedClient) }}</strong></p>
          <label for="management-reason">دلیل واگذاری</label>
          <textarea id="management-reason" v-model.trim="transferReason" rows="2" maxlength="500" placeholder="دلیل انتقال مدیریت را ثبت کنید"></textarea>
          <button type="button" class="accept management-submit" :disabled="transferring || !selectedClient || transferReason.length < 3" @click="transferManagement">
            {{ transferring ? 'در حال ثبت…' : 'ثبت واگذاری' }}
          </button>
          <p v-if="managementMessage" :class="['management-message', { error: managementError }]" role="status">{{ managementMessage }}</p>
        </div>
      </section>
      <section v-if="buildings.length" class="detail-section">
        <div class="detail-section-heading">
          <h2>
            {{
              kind === 'building'
                ? record.parent
                  ? 'ساختمان مادر'
                  : 'ساختمان‌های زیرمجموعه'
                : 'ساختمان‌های مرتبط'
            }}
          </h2>
        </div>
        <div class="related-record-grid">
          <router-link
            v-for="b in buildings"
            :key="b.id"
            class="related-record"
            :to="'/elevatormanagement/buildingdetail/' + b.id"
            ><div>
              <h3>{{ b.verbose_name || b.name }}</h3>
              <p>{{ b.address || 'آدرس ثبت نشده' }}</p>
            </div>
            <ActionIcon name="view"
          /></router-link>
        </div>
      </section>
      <section v-if="kind === 'store'" class="detail-review-bar">
        <div>
          <h2>مدیریت اطلاعات فروشگاه</h2>
          <p>اطلاعات تماس، مالک و محل فروشگاه</p>
        </div>
        <router-link class="accept" :to="'/storemng/editstore/' + record.id"
          >ویرایش اطلاعات</router-link
        >
      </section>
      <p v-if="relatedError" class="detail-error" role="alert">
        {{ relatedError }} <button class="detail-text-link" @click="load">تلاش دوباره</button>
      </p>
    </template>
  </div>
</template>
<script>
import InfoGrid from '@/components/RecordDetails/InfoGrid.vue';
import PriorityPanel from '@/components/RecordDetails/PriorityPanel.vue';
import MaintenancePanel from '@/components/RecordDetails/MaintenancePanel.vue';
import { elevatorSections, entityLabels } from '@/utils/entityDetails';
import EmptyState from '@/components/EmptyState/index.vue';
const rows = (data) => (Array.isArray(data) ? data : data.results || []);
export default {
  components: { EmptyState, InfoGrid, PriorityPanel, MaintenancePanel },
  data: () => ({
    loading: true,
    error: '',
    relatedError: '',
    record: {},
    elevators: [],
    buildings: [],
    contacts: [],
    managements: [],
    clientSearch: '',
    clientResults: [],
    selectedClient: null,
    transferReason: '',
    searchingClients: false,
    transferring: false,
    managementMessage: '',
    managementError: false,
  }),
  computed: {
    maintenanceElevators() {
      if (!this.record.id) return null;
      if (this.kind === 'elevator') return [{ id: this.record.id, title: this.record.title }];
      if (this.kind === 'building') return this.elevators.map((item) => item.elevator).filter(Boolean);
      return null;
    },
    priorityTarget() {
      return { building: 'building', elevator: 'elevator', customer: 'client' }[this.kind] || '';
    },
    kind() {
      return this.$route.meta.recordKind;
    },
    kindLabel() {
      return { building: 'ساختمان', elevator: 'آسانسور', customer: 'مشتری', store: 'فروشگاه' }[
        this.kind
      ];
    },
    currentManagement() {
      const now = Date.now();
      return this.managements.filter((item) => !item.end_at && (!item.start_at || new Date(item.start_at).getTime() <= now));
    },
    back() {
      return {
        building: '/elevatormanagement/groupbuildinglist',
        elevator: '/elevatormanagement/elevatorlist',
        customer: '/customermanagement/list',
        store: '/storemng/listall',
      }[this.kind];
    },
    title() {
      return (
        this.record.verbose_name ||
        this.record.name_fa ||
        this.record.title ||
        this.record.name ||
        'جزئیات ' + this.kindLabel
      );
    },
    subtitle() {
      return this.record.address || this.record.description || '';
    },
    summary() {
      const r = this.record;
      return this.kind === 'building'
        ? [
            { label: 'نام ثبت‌شده', value: r.name },
            { label: 'شهر', value: (r.city || {}).name },
            { label: 'نوع ساختمان', value: this.label(r.type) },
            { label: 'وضعیت ویزیت', value: r.is_visiting ? 'در حال ویزیت' : 'آماده ویزیت' },
            { label: 'تعداد آسانسور', value: this.elevators.length },
            {
              label: 'ساختمان مادر',
              value: r.parent ? (this.buildings[0] || {}).verbose_name || 'ثبت نشده' : 'ندارد',
            },
          ]
        : this.kind === 'elevator'
        ? [
            { label: 'نوع آسانسور', value: this.label(r.elevator_type) },
            { label: 'ظرفیت نفر', value: r.capacity },
            { label: 'تعداد طبقات', value: r.number_of_floors },
          ]
        : this.kind === 'customer'
        ? [
            { label: 'نام لاتین', value: r.name },
            { label: 'نوع مشتری', value: this.label(r.type) },
            { label: 'افراد مرتبط', value: this.contacts.length },
          ]
        : [
            { label: 'نوع فروشگاه', value: (r.category || {}).verbose_name },
            { label: 'شماره تماس', value: r.phone, ltr: true },
            { label: 'شماره همراه', value: r.mobile_phone, ltr: true },
            { label: 'شهر', value: (r.city || {}).name },
            { label: 'وضعیت', value: r.is_active ? 'فعال' : 'غیرفعال' },
            { label: 'کد مشتری', value: r.customer_code },
          ];
    },
    sections() {
      return this.kind === 'elevator'
        ? elevatorSections
        : this.kind === 'building'
        ? [
            {
              title: 'نشانی و موقعیت',
              fields: [
                ['address', 'نشانی کامل', true],
                ['latitude', 'عرض جغرافیایی'],
                ['longitude', 'طول جغرافیایی'],
              ],
            },
          ]
        : this.kind === 'customer'
        ? [{ title: 'اطلاعات تکمیلی مشتری', fields: [['description', 'توضیحات', true]] }]
        : [
            {
              title: 'اطلاعات مالک',
              fields: [
                ['owner_name', 'نام مالک'],
                ['owner_national_code', 'کد ملی مالک'],
              ],
            },
            {
              title: 'نشانی و اطلاعات فعالیت',
              fields: [
                ['address', 'نشانی کامل', true],
                ['postal_code', 'کد پستی'],
                ['latitude', 'عرض جغرافیایی'],
                ['longitude', 'طول جغرافیایی'],
                ['period', 'دوره ویزیت'],
                ['visit_count', 'تعداد ویزیت'],
                ['is_visiting', 'در حال ویزیت'],
              ],
            },
          ];
    },
    recordKey() {
      return this.kind + ':' + this.$route.params.id;
    },
  },
  watch: { recordKey: { immediate: true, handler: 'load' } },
  methods: {
    clientName(client) {
      return (client && (client.name_fa || client.name)) || 'کلاینت بی‌نام';
    },
    formatDate(value) {
      const date = new Date(value);
      return Number.isNaN(date.getTime()) ? 'نامشخص' : new Intl.DateTimeFormat('fa-IR', { dateStyle: 'medium' }).format(date);
    },
    async searchClients() {
      if (this.searchingClients || this.clientSearch.length < 2) return;
      this.searchingClients = true;
      this.managementMessage = '';
      try {
        const data = await this.get('/api/visit/ClientListCreate/', '&limit=12&search=' + encodeURIComponent(this.clientSearch));
        this.clientResults = rows(data);
        if (!this.clientResults.length) this.managementMessage = 'کلاینتی با این نام پیدا نشد.';
      } catch (error) {
        this.managementError = true;
        this.managementMessage = error.message;
      } finally {
        this.searchingClients = false;
      }
    },
    async transferManagement() {
      if (this.transferring || !this.selectedClient || this.transferReason.length < 3) return;
      this.transferring = true;
      this.managementMessage = '';
      this.managementError = false;
      try {
        const response = await this.$ApiServiceLayer.post(
          '/core/api/admin/building_management/transfer/?p=' + this.$STORE.state.userConfig.setProjectId,
          '',
          { building: this.record.id, client: this.selectedClient.id, reason: this.transferReason }
        );
        if (![200, 201].includes(response.status)) throw new Error(this.$ApiServiceLayer.getErrorMessage(response));
        this.managements = rows(await this.get('/api/visit/BuildingClientListCreate/', '&building=' + this.record.id + '&ordering=-id'));
        this.managementMessage = response.data.changed ? 'واگذاری مدیریت ثبت شد.' : 'این کلاینت هم‌اکنون مدیر ساختمان است.';
        this.selectedClient = null;
        this.transferReason = '';
        this.clientResults = [];
      } catch (error) {
        this.managementError = true;
        this.managementMessage = error.message;
      } finally {
        this.transferring = false;
      }
    },
    label(value) {
      return entityLabels[value] || value;
    },
    fieldValue(key) {
      const value = this.record[key];
      if (['latitude', 'longitude'].includes(key) && value !== null && value !== undefined)
        return Number(value).toFixed(6);
      return this.label(value);
    },
    async get(path, query = '') {
      const res = await this.$ApiServiceLayer.get(
        path + '?p=' + this.$STORE.state.userConfig.setProjectId + query,
        ''
      );
      if (res.status !== 200) throw new Error(this.$ApiServiceLayer.getErrorMessage(res));
      return res.data;
    },
    async load() {
      const key = this.recordKey;
      const id = this.$route.params.id;
      this.loading = true;
      this.error = '';
      this.relatedError = '';
      this.elevators = [];
      this.buildings = [];
      this.contacts = [];
      this.managements = [];
      const path = {
        building: '/api/visit/BuildingEdits/',
        elevator: '/api/visit/ElevatorEdits/',
        customer: '/api/visit/ClientEdits/',
        store: '/core/api/admin/outlet_with_more_info/edits/',
      }[this.kind];
      try {
        const record = await this.get(path + id + '/');
        if (key !== this.recordKey) return;
        this.record = record;
        try {
          if (this.kind === 'building') {
            this.elevators = record.elevators || [];
            const data = record.parent
              ? [await this.get('/api/visit/BuildingEdits/' + record.parent + '/')]
              : rows(await this.get('/api/visit/BuildingListCreate/', '&parent=' + id));
            if (key !== this.recordKey) return;
            this.buildings = data;
            this.managements = rows(await this.get('/api/visit/BuildingClientListCreate/', '&building=' + id + '&ordering=-id'));
          } else if (this.kind === 'elevator') {
            const related = await this.get(
              '/api/visit/BuildingElevatorListCreate/',
              '&elevator=' + id
            );
            if (key !== this.recordKey) return;
            this.buildings = rows(related).map((item) => item.building);
          } else if (this.kind === 'customer') {
            const related = await Promise.all([
              this.get('/api/visit/UserClientListCreate/', '&client=' + id),
              this.get('/api/visit/BuildingClientListCreate/', '&client=' + id),
            ]);
            if (key !== this.recordKey) return;
            this.contacts = rows(related[0]);
            this.buildings = rows(related[1]).map((item) => item.building);
          }
        } catch (e) {
          this.relatedError = 'دریافت اطلاعات مرتبط انجام نشد: ' + e.message;
        }
      } catch (e) {
        if (key === this.recordKey) this.error = e.message;
      } finally {
        if (key === this.recordKey) this.loading = false;
      }
    },
  },
};
</script>
<style scoped>
.related-record-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}
.related-record {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  border: 1px solid #e4e9f2;
  border-radius: 12px;
  color: #344560;
  margin-bottom: 12px;
}
.related-record > div {
  flex: 1;
  min-width: 0;
}
.related-record h3 {
  font-size: 14px;
  margin: 0 0 8px;
}
.related-record p {
  font-size: 12px;
  color: #7a879b;
  line-height: 1.9;
  margin: 0;
}
.related-record:hover {
  border-color: #b6c7f3;
}
.management-section { display: grid; gap: 18px; }
.management-current { display: flex; flex-wrap: wrap; align-items: center; gap: 12px; padding: 17px 20px; border-radius: 14px; background: #eef7fb; color: #173d55; }
.management-caption { font-size: 12px; color: #45677c; }
.management-current strong { font-size: 16px; }
.management-history { display: grid; gap: 9px; }
.management-history-row { display: flex; flex-wrap: wrap; gap: 8px 18px; align-items: center; padding: 13px 16px; border: 1px solid #e4e9f2; border-radius: 11px; color: #344560; }
.management-history-row strong { min-width: 160px; }
.management-history-row span { color: #677789; font-size: 12px; }
.management-history-row small { width: 100%; color: #45677c; }
.management-form { display: grid; gap: 10px; max-width: 700px; padding: 21px; border: 1px solid #dce8ef; border-radius: 14px; background: #f8fbfc; }
.management-form h3 { margin: 0; font-size: 17px; color: #173d55; }
.management-form p { margin: 0; }
.management-form label { font-size: 13px; font-weight: 700; color: #344560; }
.management-form input, .management-form textarea { width: 100%; min-height: 44px; padding: 10px 12px; border: 1px solid #bacbd6; border-radius: 9px; background: #fff; color: #263d4d; }
.management-form :is(input, textarea, button):focus-visible { outline: 3px solid #79b5d8; outline-offset: 2px; }
.management-search { display: flex; gap: 9px; }
.management-search button, .management-results button { min-height: 44px; padding: 8px 16px; border-radius: 9px; border: 1px solid #bad0dd; background: #fff; color: #195c80; font-weight: 700; }
.management-search button:disabled, .management-submit:disabled { opacity: .55; cursor: not-allowed; }
.management-results { display: flex; flex-wrap: wrap; gap: 7px; }
.management-results button.selected { background: #1d5e86; color: #fff; }
.management-selection { color: #195c80; }
.management-submit { justify-self: start; min-height: 44px; }
.management-message { color: #217357; font-weight: 700; }
.management-message.error { color: #ae4545; }
@media (max-width: 640px) {
  .related-record-grid {
    grid-template-columns: 1fr;
  }
  .related-record {
    padding: 16px;
  }
  .related-record .record-info-grid {
    grid-template-columns: 1fr;
  }
  .management-search { flex-direction: column; }
  .management-submit { width: 100%; }
}
</style>
