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
        <select id="filter-pickStore" style="width: 100%" v-model="pickStore" class="search-input">
          <option value="">همه مشتری‌ها</option>
          <option v-for="outlet in outletCat" :value="outlet.id" :key="outlet.id">
            {{ outlet.verbose_name }}
          </option>
        </select>
      </div>
      <div class="filter-field">
        <label for="filter-visitCount">تعداد ویزیت</label>
        <input
          id="filter-visitCount"
          class="inputs"
          v-model="visitCount"
          placeholder="وارد کنید…"
        />
      </div>
      <div class="filter-field">
        <label for="filter-storeCode">کد مشتری</label>
        <input id="filter-storeCode" class="inputs" v-model="storeCode" placeholder="وارد کنید…" />
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
          :hover="true"
          :bordered="true"
          :showNoContent="loadingList"
          :showNoData="!loadingList && dataPackage.length === 0"
          :errorMessage="listError"
          @retry="getDataPackage(20, 20 * (page - 1))"
        >
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
              <th>منطقه</th>
              <th>محله</th>
              <th>نام مشتری</th>
              <th>ادرس مشتری</th>
              <th>نوع مشتری</th>
              <th>کد مشتری</th>
              <th>تعداد ویزیت</th>
              <th>عملیات</th>
            </tr>
          </template>

          <template #TableBody>
            <tr v-for="(item, index) in dataPackage" :key="item.id">
              <td class="persian-number">
                {{ 20 * (page - 1) + 1 + index }}
              </td>
              <td>{{ (item.city && item.city.name) || '—' }}</td>
              <td>
                <span v-if="item.district !== null">{{ item.district.verbose_name }}</span>
                <span v-else>-</span>
              </td>
              <td>
                <span v-if="item.region !== null">{{ item.region.verbose_name }}</span>
                <span v-else>-</span>
              </td>
              <td>{{ item.name }}</td>
              <td class="persian-number">{{ item.address }}</td>
              <td>{{ (item.category && item.category.verbose_name) || '—' }}</td>
              <td class="persian-number">{{ item.code }}</td>
              <td class="persian-number">{{ item.visit_count }}</td>

              <td>
                <button
                  type="button"
                  class="icon-action"
                  @click="detail(item.id)"
                  aria-label="مشاهده جزئیات"
                  title="مشاهده جزئیات"
                >
                  <ActionIcon name="view" />
                </button>
                <img
                  v-b-tooltip.hover
                  title="ویرایش"
                  @click="editStore(item)"
                  class="eye-icon icon-complement"
                  src="../../assets/images/iconPack/basil_edit-outline.svg"
                />
              </td>
            </tr>
          </template>
        </Tableview>
      </div>
    </div>
  </div>
</template>
<script>
import FilterPanel from '../../components/FilterPanel/index.vue';
import Tableview from '../../components/Tableview/index.vue';
import Pagination from '@/components/ListPagination/index.vue';

export default {
  components: {
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
      pickProvince: '',
      pickCity: '',
      visitCount: '',
      storeCode: '',
      selectedkCity: '',
      pickStore: '',
      outletCat: [],
      page: 1,
      showStoreSelector: false,
      totalDataCount: 0,
      queryStates: window.location.href.split('/').slice(-1)[0],
      selected: '-datetime_last_change',
      options: [
        { item: '-datetime_last_change', name: 'صعودی' },
        { item: 'datetime_last_change', name: 'نزولی' },
      ],
      rangeDate: [],
    };
  },
  async mounted() {
    this.getDataPackage();
    this.getCity();
    this.getPromoterLists();
    this.getProvince();
    this.getOutletCat();
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
    removeFilter() {
      this.page = 1;
      this.pickCity = '';
      this.storeCode = '';
      this.pickProvince = '';
      this.selectedkCity = '';
      this.visitCount = '';
      this.getDataPackage();
      this.getCity();
    },
    getCityOnChange() {
      this.selectedkCity = this.pickProvince;
      this.getCity();
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

    async getDataPackage(limit = 20, offset = 0) {
      this.loadingList = true;
      this.listError = '';
      try {
        const res = await this.$ApiServiceLayer.get(
          this.$PATH.RELATIVE_PATH.GET.GET_OUTLET_LIST +
            '?city=' +
            this.pickCity +
            '&city__province=' +
            this.pickProvince +
            '&visit_count=' +
            this.visitCount +
            '&code=' +
            this.storeCode +
            '&limit=' +
            limit +
            '&offset=' +
            offset +
            '&category=' +
            this.pickStore +
            '&ordering=' +
            this.selected +
            '&p=' +
            this.$STORE.state.userConfig.setProjectId,
          this.$PATH.SERVICE_NAME.AUTH
        );
        if (res.status !== 200) {
          this.listError = this.$ApiServiceLayer.getErrorMessage(res);
          return;
        }
        if (res.status === 200) {
          this.dataPackage = res.data.results;
          'sd:', this.dataPackage;
          this.totalDataCount = res.data.count;
        }
      } finally {
        this.loadingList = false;
      }
    },
    async myCallback() {
      await this.getDataPackage(20, 20 * (this.page - 1));
    },
    detail(id) {
      this.$router.push('/storemng/detail/' + id);
    },
    editStore(item) {
      this.$router.push({ name: 'editStore', params: { id: item.id } });
    },
  },
  watch: {
    queryStates: {
      handler(value) {
        value;
      },
    },
    immediate: true, // This ensures the watcher is triggered upon creation
  },
};
</script>
<style lang="scss" scoped>
.follow-order {
  .warning {
    display: flex;
    flex-direction: column;
    border: 1px solid #ffecb4;
    background: #fff3cd;
    padding: 16px;
    margin-bottom: 32px;
    border-radius: 8px;
    ul {
      margin-bottom: 0 !important;
      padding: 10px 35px;
    }
    li {
      list-style: disc;
    }
    .text {
      color: #664d03;
      font-size: 16px;
      margin-right: 15px;
    }
  }

  .warning-box {
    border-radius: 4px;
    padding: 4px 10px;
    font-family: 'IRANYekanfa' !important;
    color: #fff;
    cursor: pointer;
  }

  .icon-complement {
    width: 45px;
    padding: 0px 5px;
  }
}
</style>
