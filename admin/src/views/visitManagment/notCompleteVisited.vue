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
        <select
          id="filter-pickCity"
          @change="getPromoterListsOnChange"
          v-model="pickCity"
          class="form-select"
        >
          <option value="">همه شهرها</option>
          <option v-for="city in cityLists" :value="city.city.id" :key="city.city.id">
            {{ city.city.name }}
          </option>
        </select>
      </div>
      <div class="filter-field">
        <label for="start-date">انتخاب تاریخ</label>
        <input id="start-date" type="text" class="custom-input inputs" placeholder="انتخاب تاریخ" />
        <date-picker
          v-model="rangeDate"
          range
          clearable
          format="YYYY-MM-DDTHH:mm:00"
          display-format="jMMMM jD"
          custom-input="#start-date"
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
      <template #actions>
        <button type="submit" class="accept" :disabled="loadingList">اعمال فیلتر</button>
        <button type="button" class="remove-filtes" @click="removeFilter">پاک کردن فیلترها</button>
      </template>
    </FilterPanel>
    <div class="box list-box">
      <div>
        <Tableview
          :recordCount="totalDataCount"
          :page="page"
          :errorMessage="listError"
          @retry="getDataPackage(20, 20 * (page - 1))"
          :hover="true"
          :bordered="true"
          :showNoContent="showContnetFunc"
          :showNoData="showDataFunc"
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
              <th>شهر</th>
              <th>نام مشتری</th>
              <th>آدرس</th>
              <th>کد مشتری</th>
              <th>نام نیروی اجرایی</th>

              <th>تاریخ ویزیت</th>
              <th>نوبت</th>
              <th>امتیاز</th>
              <th>مشاهده</th>
            </tr>
          </template>

          <template #TableBody>
            <tr v-for="(item, index) in dataPackage" :key="item.id">
              <td class="persian-number">
                {{ 20 * (page - 1) + 1 + index }}
              </td>
              <td>{{ (item.building && item.building.city && item.building.city.name) || '—' }}</td>
              <td>{{ (item.building && item.building.verbose_name) || '—' }}</td>
              <td class="persian-number">{{ (item.building && item.building.address) || '—' }}</td>
              <td class="persian-number">{{ (item.building && item.building.code) || '—' }}</td>
              <td>
                {{
                  item.promoter
                    ? [item.promoter.first_name, item.promoter.last_name].filter(Boolean).join(' ')
                    : '—'
                }}
              </td>

              <td class="persian-number">
                <DisplayDate :value="item.start_datetime" showTime />
              </td>
              <td class="persian-number">{{ item.visit_turn }}</td>
              <td>
                <span class="persian-number" v-if="item.rate !== null">
                  <img
                    style="width: 20px"
                    src="@/assets/images/iconPack/Star_solid.svg"
                    alt="Solid Star"
                  />
                  {{ item.rate }}
                </span>
                <span v-else>-</span>
              </td>
              <td>
                <RowActions :items="[{ label: 'مشاهده جزئیات', icon: 'view', action: () => visitDetail(item.id) }]" />
              </td>
            </tr>
          </template>
        </Tableview>
      </div>
    </div>
  </div>
</template>
<script>
import DisplayDate from '@/components/DisplayDate/index.vue';
import FilterPanel from '@/components/FilterPanel/index.vue';
import Tableview from '../../components/Tableview/index.vue';
import Pagination from '@/components/ListPagination/index.vue';

import RowActions from '@/components/RowActions/index.vue';
export default {
  components: { RowActions,
    DisplayDate,
    FilterPanel,
    Tableview,
    Pagination,
  },
  data() {
    return {
      dataPackage: [],
      loadingList: true,
      listError: '',
      cityLists: [],
      promoterLists: [],
      provinceLists: [],
      superVisiorLists: [],
      dueDate: '',
      pickCity: '',
      pickProvince: '',
      pickPromoter: '',
      visitTurn: '',
      storeCode: '',
      pickStore: '',
      selectedkCity: '',
      outletCat: [],
      page: 1,
      totalDataCount: 0,
      pickSupervisor: '',
      selected: '-start_datetime',
      options: [
        { item: '-start_datetime', name: 'نزولی' },
        { item: 'start_datetime', name: 'صعودی' },
      ],
      rangeDate: ['', ''],
    };
  },
  mounted() {
    this.getDataPackage();
    this.getCity();
    // this.getPromoterLists();
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
      return this.loadingList;
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
      return this.getDataPackage(20, 0);
    },
    getCityOnChange() {
      this.selectedkCity = this.pickProvince;
      this.getCity();
    },
    getPromoterListsOnChange() {
      this.getPromoterLists();
    },
    removeFilter() {
      ('sd');
      this.pickCity = '';
      this.pickPromoter = '';
      this.visitTurn = '';
      this.storeCode = '';
      this.pickProvince = '';
      this.pickStore = '';
      this.dueDate = '';
      this.rangeDate = ['', ''];
      this.applyFilters();
      this.getCity();
      this.pickSupervisor = '';
      this.getPromoterLists();
    },
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
            '?status=1' +
            '&outlet__city=' +
            this.pickCity +
            '&due_date=' +
            this.dueDate +
            '&outlet__city__province=' +
            this.pickProvince +
            '&outlet__category=' +
            this.pickStore +
            '&promoter=' +
            this.pickPromoter +
            '&outlet__code=' +
            this.storeCode +
            '&visit_turn=' +
            this.visitTurn +
            '&limit=' +
            limit +
            '&offset=' +
            offset +
            '&supervisor=' +
            this.pickSupervisor +
            '&ordering=' +
            this.selected +
            '&start_datetime__gte=' +
            this.rangeDate[0] +
            '&start_datetime__lte=' +
            this.rangeDate[1] +
            '&p=' +
            this.$STORE.state.userConfig.setProjectId,
          this.$PATH.SERVICE_NAME.AUTH
        );
        if (res.status !== 200) throw new Error('Request failed');
        if (res.status === 200) {
          this.dataPackage = res.data.results;
          'data:', this.dataPackage;
          this.totalDataCount = res.data.count;
        }
      } catch (error) {
        this.dataPackage = [];
        this.totalDataCount = 0;
        this.listError = 'دریافت اطلاعات انجام نشد. دوباره تلاش کنید.';
      } finally {
        this.loadingList = false;
      }
    },
    async getOutletCat() {
      const res = await this.$ApiServiceLayer.get(
        this.$PATH.RELATIVE_PATH.GET.OUTLET_CAT + '?p=' + this.$STORE.state.userConfig.setProjectId,
        this.$PATH.SERVICE_NAME.AUTH
      );
      if (res.status === 200) {
        this.outletCat = res.data;
      }
    },
    async myCallback() {
      await this.getDataPackage(20, 20 * (this.page - 1));
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
        'promoter:', res.data;
        this.promoterLists = res.data;
      }
    },
    visitDetail(id) {
      let routeData = this.$router.resolve({ name: 'answerList', params: { id: id } });
      window.open(routeData.href);
    },
  },
};
</script>
