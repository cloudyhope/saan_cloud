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
        <label for="filter-pickSurveyName">نام پرسش‌نامه</label>
        <select id="filter-pickSurveyName" v-model="pickSurveyName" class="form-select">
          <option value="">همه پرسش‌نامه‌ها</option>
          <option v-for="survey in surveyName" :value="survey.id" :key="survey.id">
            {{ survey.verbose_name }}
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
        <label for="filter-date">انتخاب تاریخ</label>
        <input
          id="filter-date"
          type="text"
          class="custom-input inputs"
          placeholder="انتخاب تاریخ"
        />
        <date-picker
          v-model="rangeDate"
          range
          clearable
          format="YYYY-MM-DDTHH:mm:00"
          display-format="jMMMM jD"
          custom-input="#filter-date"
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
              <th>نام پرسش‌نامه</th>
              <th>نام نیروی اجرایی</th>
              <th>شهر</th>
              <th>استان</th>
              <th>تاریخ</th>
              <th>احراز هویت</th>
              <th>موبایل پرسش‌شونده</th>

              <th>مشاهده</th>
            </tr>
          </template>

          <template #TableBody>
            <tr v-for="(item, index) in dataPackage" :key="item.id">
              <td class="persian-number">
                {{ 20 * (page - 1) + 1 + index }}
              </td>
              <td>{{ item.survey.verbose_name }}</td>
              <td>{{ item.user.first_name }} {{ item.user.last_name }}</td>
              <td v-if="item.city !== null" class="persian-number">{{ item.city.name }}</td>
              <td v-else></td>
              <td v-if="item.province !== null" class="persian-number">{{ item.province.name }}</td>
              <td v-else></td>

              <td class="custom-td">
                <DisplayDate :value="item.datetime_created" showTime />
              </td>
              <td v-if="item.phone_verified === 'false'">انجام نشده</td>
              <td v-else>انجام شده</td>
              <td class="persian-number">{{ item.phone_number }}</td>

              <td>
                <button
                  type="button"
                  class="icon-action"
                  @click="surveyDetail(item.id)"
                  aria-label="مشاهده جزئیات"
                  title="مشاهده جزئیات"
                >
                  <ActionIcon name="view" />
                </button>
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

export default {
  components: {
    DisplayDate,
    FilterPanel,
    Tableview,
    Pagination,
  },
  data() {
    return {
      dataPackage: [],
      cityLists: [],
      promoterLists: [],
      provinceLists: [],
      pickCity: '',
      pickProvince: '',
      pickPromoter: '',
      visitTurn: '',
      storeCode: '',
      pickSurveyName: '',
      selectedkCity: '',
      surveyName: [],
      page: 1,
      totalDataCount: 0,
      selected: '-datetime_last_change',
      options: [
        { item: '-datetime_last_change', name: 'نزولی' },
        { item: 'datetime_last_change', name: 'صعودی' },
      ],
      rangeDate: ['', ''],
    };
  },
  mounted() {
    this.getDataPackage();
    this.getCity();
    this.getPromoterLists();
    this.getProvince();
    this.getSurveyNameLists();
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
      this.pickCity = '';
      this.pickPromoter = '';
      this.visitTurn = '';
      this.storeCode = '';
      this.pickProvince = '';
      this.pickSurveyName = '';
      this.rangeDate = ['', ''];
      this.selectedkCity = '';
      this.applyFilters();
      this.getCity();
      this.getProvince();
      this.getPromoterLists();
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
        // ?survey=&user=&province=&city=&longitude=&latitude=&phone_verified=&phone_number=&is_closed=&is_deleted=&status=&datetime_created=&datetime_last_change=
        const res = await this.$ApiServiceLayer.get(
          this.$PATH.RELATIVE_PATH.MULTI.SURVEY_LISTS +
            '?city=' +
            this.pickCity +
            '&province=' +
            this.pickProvince +
            '&survey=' +
            this.pickSurveyName +
            '&user=' +
            this.pickPromoter +
            '&limit=' +
            limit +
            '&offset=' +
            offset +
            '&ordering=' +
            this.selected +
            '&datetime_created__gte=' +
            this.rangeDate[0] +
            '&datetime_created__lte=' +
            this.rangeDate[1] +
            '&status=2' +
            '&p=' +
            this.$STORE.state.userConfig.setProjectId,
          this.$PATH.SERVICE_NAME.AUTH
        );
        if (res.status !== 200) throw new Error('Request failed');
        if (res.status === 200) {
          this.dataPackage = res.data.results;
          'ds', this.dataPackage;
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
    async myCallback() {
      await this.getDataPackage(20, 20 * (this.page - 1));
    },
    surveyDetail(id) {
      let routeData = this.$router.resolve({ name: 'surveyAnswerList', params: { id: id } });
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
    async changeSurveyStatus(item) {
      const res = await this.$ApiServiceLayer.patch(
        this.$PATH.RELATIVE_PATH.MULTI.SURVEY_EDIT +
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
    async getSurveyNameLists() {
      const res = await this.$ApiServiceLayer.get(
        this.$PATH.RELATIVE_PATH.MULTI.SURVEY_NAME +
          '?p=' +
          this.$STORE.state.userConfig.setProjectId,
        this.$PATH.SERVICE_NAME.AUTH
      );
      if (res.status === 200) {
        'surve', res.data;
        this.surveyName = res.data;
      }
    },
  },
};
</script>

<!--  -->
