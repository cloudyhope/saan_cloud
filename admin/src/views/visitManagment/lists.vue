<template>
  <div class="follow-order">
    <FilterPanel @apply="applyFilters">
      <div class="filter-field">
        <label for="filter-pickProvince">استان</label>
        <select
          id="filter-pickProvince"
          @change="getCityOnChange"
          v-model="pickProvince"
          class="form-select"
        >
          <option value="">همه استان‌ها</option>
          <option v-for="province in provinceLists" :value="province.id" :key="province.id">
            {{ province.name }}
          </option>
        </select>
      </div>
      <div class="filter-field">
        <label for="filter-pickCity">شهر</label>

        <select id="filter-pickCity" v-model="pickCity" class="form-select">
          <option value="">همه شهرها</option>
          <option v-for="city in cityLists" :value="city.city.id" :key="city.city.id">
            {{ city.city.name }}
          </option>
        </select>
      </div>
      <div class="filter-field">
        <label for="filter-pickStore">نوع مشتری</label>
        <select id="filter-pickStore" v-model="pickStore" class="form-select">
          <option value="">همه مشتری‌ها</option>
          <option v-for="outlet in outletCat" :value="outlet.id" :key="outlet.id">
            {{ outlet.verbose_name }}
          </option>
        </select>
      </div>
      <div class="filter-field">
        <label for="filter-pickPromoter">نیروی اجرایی</label>
        <select id="filter-pickPromoter" v-model="pickPromoter" class="form-select">
          <option value="">همه نیروها</option>
          <option v-for="promoter in promoterLists" :value="promoter.user.id" :key="promoter.id">
            {{ promoter.user.first_name }} {{ promoter.user.last_name }}
          </option>
        </select>
      </div>
      <div class="filter-field">
        <label for="filter-visitTurn">نوبت</label>
        <input id="filter-visitTurn" class="inputs" v-model="visitTurn" placeholder="وارد کنید…" />
      </div>
      <div class="filter-field">
        <label for="filter-storeCode">کد مشتری</label>
        <input id="filter-storeCode" class="inputs" v-model="storeCode" placeholder="وارد کنید…" />
      </div>
      <div class="filter-field">
        <label for="start-time">انتخاب تاریخ</label>
        <input id="start-time" type="text" class="custom-input inputs" placeholder="انتخاب تاریخ" />
        <date-picker
          v-model="rangeDate"
          range
          clearable
          format="YYYY-MM-DDTHH:mm:00"
          display-format="jMMMM jD"
          custom-input="#start-time"
        />
      </div>
      <div class="filter-field">
        <label for="due-date">تاریخ اجرا</label>
        <input id="due-date" type="text" class="custom-input inputs" placeholder="انتخاب تاریخ" />
        <date-picker
          key="due-date"
          v-model="dueDate"
          clearable
          format="YYYY-MM-DD"
          display-format="jMMMM jD"
          custom-input="#due-date"
        />
      </div>
      <div class="filter-field">
        <label for="filter-pickSupervisor">نام سرپرست</label>
        <select id="filter-pickSupervisor" v-model="pickSupervisor" class="form-select">
          <option value="">همه سرپرست‌ها</option>
          <option
            v-for="superVisior in superVisiorLists"
            :value="superVisior.user.id"
            :key="superVisior.id"
          >
            {{ superVisior.user.first_name }} {{ superVisior.user.last_name }}
          </option>
        </select>
      </div>
      <template #actions>
        <button type="submit" class="accept" :disabled="loadingList">اعمال فیلتر</button>
        <button type="button" class="remove-filtes" @click="removeFilter">پاک کردن فیلترها</button>
      </template>
    </FilterPanel>
    <div class="box list-box">
      <div>
        <Tableview
          class="visit-table"
          :recordCount="totalDataCount"
          :page="page"
          :hover="true"
          :bordered="true"
          :showNoContent="loadingList"
          :showNoData="!loadingList && dataPackage.length === 0"
          :errorMessage="listError"
          @retry="getDataPackage(20, 20 * (page - 1))"
        >
          <template #controls
            ><label class="ordering-title">مرتب‌سازی</label
            ><b-form-select
              aria-label="مرتب‌سازی"
              v-model="selected"
              :options="options"
              class="ordering"
              value-field="item"
              text-field="name"
              @change="applyFilters"
            ></b-form-select
          ></template>
          <template #footer
            ><pagination
              :disabled="loadingList"
              v-model="page"
              :per-page="20"
              :records="totalDataCount"
              @paginate="myCallback"
          /></template>

          <template #TableTitle>
            <tr>
              <th>ردیف</th>
              <th>نام ساختمان</th>
              <th>آدرس</th>
              <th>تاریخ درخواست</th>

              <th>سرویس‌کار</th>
              <th>وضعیت</th>
              <th class="actions-column">عملیات</th>
            </tr>
          </template>

          <template #TableBody>
            <tr v-for="(item, index) in dataPackage" :key="item.id">
              <td class="persian-number">
                {{ 20 * (page - 1) + 1 + index }}
              </td>
              <td>
                <span
                  class="cell-text cell-primary"
                  :title="item.building && item.building.verbose_name"
                  >{{ (item.building && item.building.verbose_name) || '—' }}</span
                >
              </td>
              <td>
                <span class="cell-text" :title="item.building && item.building.address">{{
                  (item.building && item.building.address) || '—'
                }}</span>
              </td>
              <td>
                <DisplayDate :value="item.datetime_created" showTime />
              </td>

              <td>
                <div v-if="item.promoter">
                  <span class="cell-text cell-primary">{{
                    [item.promoter.first_name, item.promoter.last_name].filter(Boolean).join(' ') ||
                    '—'
                  }}</span
                  ><span class="cell-secondary" dir="ltr">{{ item.promoter.username || '—' }}</span>
                </div>
                <select
                  v-else
                  @change="assignPromoter(item)"
                  v-model="item.selectedPromoter"
                  aria-label="انتخاب سرویس‌کار"
                  class="form-select"
                >
                  <option
                    v-for="promoter in promoterLists"
                    :value="promoter.user.id"
                    :key="promoter.id"
                  >
                    {{ promoter.user.first_name }} {{ promoter.user.last_name }}
                  </option>
                </select>
              </td>
              <td>
                <select
                  :aria-label="'وضعیت ویزیت ' + item.id"
                  class="visit-status-select"
                  :class="'visit-status-' + item.status"
                  v-model="item.status"
                  @change="changeVisitStatus(item)"
                >
                  <option value="0">ویزیت نشده</option>
                  <option value="1">تکمیل نشده</option>
                  <option value="2">تکمیل شده</option>
                  <option value="3">تایید شده</option>
                  <option value="4">رد شده</option>
                  <option value="5">ویزیت مجدد</option>
                </select>
              </td>

              <td class="actions-cell">
                <div class="action-buttons">
                  <button
                    type="button"
                    class="icon-action"
                    @click="visitDetail(item.id)"
                    aria-label="جزئیات"
                    title="جزئیات"
                  >
                    <ActionIcon name="view" />
                  </button>

                  <button
                    type="button"
                    class="icon-action"
                    @click="elevatorItemFunc(item.elevator)"
                    aria-label="آسانسور"
                    title="آسانسور"
                  >
                    <ActionIcon name="elevator" />
                  </button>
                  <button
                    type="button"
                    class="icon-action"
                    @click="deleteItemFunc(item.id)"
                    aria-label="حذف"
                    title="حذف"
                  >
                    <ActionIcon name="delete" />
                  </button>
                </div>
              </td>
            </tr>
          </template>
        </Tableview>
        <b-modal v-model="deleteItemModal" hide-footer hide-header centered>
          <div class="p-3">
            <div>آیا از حذف خود اطمینان دارید؟</div>
            <div class="d-flex justify-content-end mt-4">
              <button @click="deleteItem" class="confirm-item">بله</button>
              <button @click="deleteItemModal = !deleteItemModal" class="reject-item">خیر</button>
            </div>
          </div>
        </b-modal>
        <b-modal v-model="elevatorItemModal" size="lg" hide-footer hide-header centered>
          <div class="p-3">
            <Tableview
              :hover="true"
              :bordered="true"
              :showNoContent="false"
              :showNoData="selectedElevator.length === 0"
            >
              <template #TableTitle>
                <tr>
                  <th>ردیف</th>
                  <th>عنوان آسانسور</th>
                  <th>تعداد طبقات</th>
                  <th>ظرفیت آسانسور</th>
                  <th>نوع آسانسور</th>
                </tr>
              </template>

              <template #TableBody>
                <tr v-for="(item, index) in selectedElevator" :key="item.id">
                  <td class="persian-number">
                    {{ 20 * (page - 1) + 1 + index }}
                  </td>
                  <td>{{ item.title }}</td>
                  <td>{{ item.number_of_floors }}</td>
                  <td>{{ item.capacity }}</td>
                  <td>{{ item.type }}</td>
                </tr>
              </template>
            </Tableview>
          </div>
        </b-modal>
        <b-modal v-model="editVisitModal" size="md" hide-footer hide-header centered>
          <div class="p-3">
            <div class="card-body">
              <div>
                <div class="mb-2">لطفا تاریخ اجرای این برنامه را انتخاب کنید.</div>
                <input
                  id="modal-date-input"
                  type="text"
                  :disabled="status"
                  class="custom-input inputs"
                />
                <date-picker
                  v-model="dataPicker"
                  clearable
                  format="YYYY-MM-DDTHH:mm:00"
                  display-format="jMMMM jD"
                  custom-input="#modal-date-input"
                  :disabled="status"
                />
                <div class="d-flex align-items-center my-3">
                  <input class="ml-3" type="checkbox" v-model="status" />
                  <span>این برنامه تاریخ مشخصی برای اجرا ندارد.</span>
                </div>
                <select
                  @change="updateSelectedPromoterUsername"
                  v-model="tableSelectedPromoter.id"
                  class="inputs"
                >
                  <option
                    v-for="promoter in promoterLists"
                    :value="promoter.user.id"
                    :key="promoter.id"
                  >
                    {{ promoter.user.first_name }} {{ promoter.user.last_name }}
                  </option>
                </select>
              </div>

              <div class="d-flex justify-content-end mt-3">
                <button @click="submitVisitRetry" class="accept ml-0">تایید</button>
              </div>
            </div>
          </div>
        </b-modal>
      </div>
    </div>
  </div>
</template>
<script>
import DisplayDate from '@/components/DisplayDate/index.vue';
import FilterPanel from '../../components/FilterPanel/index.vue';
import Tableview from '../../components/Tableview/index.vue';
import Pagination from '@/components/ListPagination/index.vue';

export default {
  components: {
    DisplayDate,
    FilterPanel,
    Tableview,
    Pagination,
  },
  data() {
    return {
      loadingList: true,
      listError: '',
      dataPackage: [],
      cityLists: [],
      promoterLists: [],
      provinceLists: [],
      pickCity: '',
      dueDate: '',
      pickProvince: '',
      pickPromoter: '',
      visitTurn: '',
      storeCode: '',
      pickStore: '',
      selectedkCity: '',
      pickSupervisor: '',
      outletCat: [],
      superVisiorLists: [],
      elevatorItemModal: false,
      page: 1,
      totalDataCount: 0,
      selected: '-id',
      options: [
        { item: '-id', name: 'نزولی' },
        { item: 'id', name: 'صعودی' },
      ],
      rangeDate: ['', ''],
      deleteItemModal: false,
      selectedElevator: [],
      editVisitModal: false,
      dataPicker: '',
      visitTypeList: [],
      visitTypeSelected: '',
      status: false,
      tableSelectedPromoter: {},
      username: '',
      buildingCode: '',
    };
  },
  mounted() {
    this.getDataPackage();
    this.getCity();
    this.getPromoterLists();
    this.getProvince();
    // this.getOutletCat();
    this.getSuperVisiorLists();
  },
  computed: {
    selectedPromoterId() {
      return this.pickPromoter.id;
    },
    selectedCityId() {
      return this.pickCity.id;
    },
    selectedProvinceId() {
      return this.pickProvince.id;
    },
    showContnetFunc() {
      return this.dataPackage === 0;
    },
    showDataFunc() {
      if (this.dataPackage.length !== undefined) {
        return this.dataPackage.length === 0;
      }
      return false;
    },
  },
  methods: {
    applyFilters() {
      this.page = 1;
      return this.getDataPackage();
    },
    getCityOnChange() {
      this.selectedkCity = this.pickProvince;
      this.getCity();
    },
    getPromoterListsOnChange() {
      this.getPromoterLists();
    },
    removeFilter() {
      this.page = 1;
      this.pickCity = '';
      this.pickPromoter = '';
      this.visitTurn = '';
      this.storeCode = '';
      this.pickProvince = '';
      this.pickStore = '';
      this.rangeDate = ['', ''];
      this.dueDate = '';
      this.selectedkCity = '';
      this.pickSupervisor = '';
      this.getDataPackage();
      this.getCity();
      this.getProvince();
      this.getPromoterLists();
    },
    // async getOutletCat() {
    // 	const res = await this.$ApiServiceLayer.get(
    // 		this.$PATH.RELATIVE_PATH.GET.OUTLET_CAT + '?p=' + this.$STORE.state.userConfig.setProjectId,
    // 		this.$PATH.SERVICE_NAME.AUTH,
    // 	);
    // 	if (res.status === 200) {
    // 		this.outletCat = res.data;
    // 	}
    // },
    async getSuperVisiorLists() {
      const res = await this.$ApiServiceLayer.get(
        this.$PATH.RELATIVE_PATH.GET.ROLE_ASSIGNMENT +
          '?p=' +
          this.$STORE.state.userConfig.setProjectId +
          '&role__title_abbreviation=V',
        this.$PATH.SERVICE_NAME.AUTH
      );
      if (res.status === 200) {
        this.superVisiorLists = res.data;
      }
    },
    async getDataPackage(limit = 20, offset = 0) {
      this.loadingList = true;
      this.listError = '';
      try {
        if (this.rangeDate[0] !== '' && this.rangeDate[1] == undefined) {
          this.rangeDate[1] = this.rangeDate[0].slice(0, 11) + '23:59:59';
        } else if (this.rangeDate[0] === null || this.rangeDate[0] === undefined) {
          this.rangeDate[0] = '';
        }
        const res = await this.$ApiServiceLayer.get(
          this.$PATH.RELATIVE_PATH.GET.GET_VISIT_LIST +
            '?outlet__city=' +
            this.pickCity +
            '&due_date=' +
            this.dueDate +
            '&outlet__city__province=' +
            this.pickProvince +
            '&promoter=' +
            this.pickPromoter +
            '&outlet__category=' +
            this.pickStore +
            '&outlet__code=' +
            this.storeCode +
            '&visit_turn=' +
            this.visitTurn +
            '&supervisor=' +
            this.pickSupervisor +
            '&limit=' +
            limit +
            '&offset=' +
            offset +
            '&ordering=' +
            this.selected +
            '&start_datetime__gte=' +
            this.rangeDate[0] +
            '&start_datetime__lte=' +
            this.rangeDate[1] +
            '&p=' +
            this.$STORE.state.userConfig.setProjectId +
            '&is_active=true',
          this.$PATH.SERVICE_NAME.AUTH
        );
        if (res.status !== 200) {
          this.listError = this.$ApiServiceLayer.getErrorMessage(res);
          return;
        }
        if (res.status === 200) {
          this.dataPackage = res.data.results;
          this.totalDataCount = res.data.count;
        }
      } finally {
        this.loadingList = false;
      }
    },
    async myCallback() {
      await this.getDataPackage(20, 20 * (this.page - 1));
    },
    visitDetail(id) {
      let routeData = this.$router.resolve({ name: 'answerList', params: { id: id } });
      window.open(routeData.href);
    },
    async getProvince() {
      const res = await this.$ApiServiceLayer.get(
        this.$PATH.RELATIVE_PATH.GET.GET_PROVINCE_LIST +
          '?p=' +
          this.$STORE.state.userConfig.setProjectId,
        this.$PATH.SERVICE_NAME.AUTH
      );
      if (res.status === 200) {
        this.provinceLists = res.data;
      }
    },
    async changeVisitStatus(item) {
      const res = await this.$ApiServiceLayer.patch(
        this.$PATH.RELATIVE_PATH.MULTI.VISITS_STATUS +
          item.id +
          '/' +
          '?p=' +
          this.$STORE.state.userConfig.setProjectId,
        this.$PATH.SERVICE_NAME.AUTH,
        { status: item.status, rejection_reason: item.status === '4' ? 'nadarad' : '' }
      );
      if (res.status === 200) {
        this.$notify({
          group: 'tc',
          type: 'success',
          text: 'وضعیت با موفقیت تغییر پیدا کرد!',
        });
        if (item.status === '5') {
          this.tableSelectedPromoter = item.promoter;
          this.visitTypeSelected = item.type.id;
          this.username = item.promoter.username || '';
          this.buildingCode = item.building.code;
          this.editVisitModal = true;
        }
      }
    },
    deleteItemFunc(ids) {
      this.deleteItemModal = !this.deleteItemModal;
      this.ids = ids;
    },
    elevatorItemFunc(elevator) {
      this.elevatorItemModal = !this.elevatorItemModal;
      this.selectedElevator = elevator;
    },

    async deleteItem() {
      const res = await this.$ApiServiceLayer.delete(
        this.$PATH.RELATIVE_PATH.MULTI.VISIT_DETAIL_EDIT +
          this.ids +
          '/' +
          '?p=' +
          this.$STORE.state.userConfig.setProjectId,
        this.$PATH.SERVICE_NAME.AUTH,
        {}
      );
      if (res.status === 204) {
        this.deleteItemModal = !this.deleteItemModal;
        this.$notify({
          group: 'tc',
          type: 'success',
          text: 'ویزیت با موفقیت حذف شد!',
        });
      }
    },
    async assignPromoter(item) {
      const res = await this.$ApiServiceLayer.patch(
        this.$PATH.RELATIVE_PATH.MULTI.VISIT_DETAIL_EDIT +
          item.id +
          '/' +
          '?p=' +
          this.$STORE.state.userConfig.setProjectId,
        this.$PATH.SERVICE_NAME.AUTH,
        { promoter: item.selectedPromoter }
      );
      if (res.status === 200) {
        this.$notify({
          group: 'tc',
          type: 'success',
          text: 'نیروی اجرایی با موفقیت انتخاب شد!',
        });
        this.getDataPackage();
      }
    },
    async getCity() {
      const res = await this.$ApiServiceLayer.get(
        this.$PATH.RELATIVE_PATH.GET.GET_CITY_LIST +
          '?city__province=' +
          this.selectedkCity +
          '&p=' +
          this.$STORE.state.userConfig.setProjectId,
        this.$PATH.SERVICE_NAME.AUTH
      );
      if (res.status === 200) {
        'city:', res.data;
        this.cityLists = res.data;
      }
    },
    async getPromoterLists() {
      const res = await this.$ApiServiceLayer.get(
        this.$PATH.RELATIVE_PATH.GET.GET_PROMOTER_LIST +
          '?p=' +
          this.$STORE.state.userConfig.setProjectId +
          '&city=' +
          this.pickCity,
        this.$PATH.SERVICE_NAME.AUTH
      );
      if (res.status === 200) {
        this.promoterLists = res.data;
      }
    },
    updateSelectedPromoterUsername() {
      const selectedPromoter = this.promoterLists.find(
        (promoter) => promoter.user.id === this.tableSelectedPromoter.id
      );
      if (selectedPromoter) {
        this.username = selectedPromoter.user.username || '';
      }
    },
    async submitVisitRetry() {
      const res = await this.$ApiServiceLayer.post(
        this.$PATH.RELATIVE_PATH.MULTI.CREATE_ACTION_PLAN +
          '?p=' +
          this.$STORE.state.userConfig.setProjectId,
        this.$PATH.SERVICE_NAME.AUTH,
        {
          project: this.$STORE.state.userConfig.setProjectId,
          actions: [
            {
              building_code: this.buildingCode,
              expert_phone_number: this.username,
              is_active: true,
            },
          ],
          has_due_date: !this.status,
          due_date: this.dataPicker,
          visit_type: this.visitTypeSelected,
        }
      );
      if (res.status === 200) {
        this.loading = false;
        this.editVisitModal = false;
        this.getDataPackage();
      }
    },
  },
};
</script>
