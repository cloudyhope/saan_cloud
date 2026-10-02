<template>
  <div class="follow-order">
    <div class="box">
      <span class="title">فیلترها</span>

      <div class="row mt-3">
        <div class="col d-flex flex-column">
          <label for="html">استان:</label>
          <select @change="getCityOnChange" v-model="pickProvince" class="form-select">
            <option v-for="province in provinceLists" :value="province.id" :key="province.id">
              {{ province.name }}
            </option>
          </select>
        </div>
        <div class="col d-flex flex-column">
          <label for="html">شهر:</label>
          <select v-model="pickCity" class="form-select">
            <option v-for="city in cityLists" :value="city.city.id" :key="city.city.id">
              {{ city.city.name }}
            </option>
          </select>
        </div>

        <div class="col d-flex flex-column">
          <label for="html">تعداد ویزیت:</label>
          <input class="inputs" v-model="visitCount" />
        </div>
        <div class="col d-flex flex-column">
          <label for="html">کد مشتری:</label>
          <input class="inputs" v-model="storeCode" />
        </div>
      </div>
      <div class="d-flex justify-content-end mt-3">
        <button @click="getDataPackage((limit = 20), (offset = 0))" class="accept">تایید</button>
        <button class="remove-filtes" @click="removeFilter">حذف فیلتر</button>
        <!-- <img class="trash-icon" @click="removeFilter" src="../../assets/images/iconPack/trash-icon.png"> -->
      </div>
    </div>
    <div class="box">
      <div class="d-flex justify-content-between">
        <pagination
          v-model="page"
          :per-page="20"
          :records="totalDataCount"
          @paginate="myCallback"
        />
        <!-- <div class="d-flex flex-row align-items-center">
					<span class="ordering-title">مرتب سازی بر اساس :</span>
					<b-form-select
						v-model="selected"
						:options="options"
						class="ordering"
						value-field="item"
						text-field="name"
						@change="getDataPackage((limit = 10), (offset = 0), (order = selected))"
					></b-form-select>
				</div> -->
      </div>
      <div>
        <Tableview
          :hover="true"
          :bordered="true"
          :showNoContent="showContnetFunc"
          :showNoData="showDataFunc"
        >
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
              <th>جزئیات فروشگاه</th>
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
                <img
                  @click="detail(item.id)"
                  class="eye-icon"
                  src="../../assets/images/iconPack/eye.svg"
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
import Tableview from '../../components/Tableview/index.vue';
import Pagination from 'vue-pagination-2';

export default {
  components: {
    Tableview,
    Pagination,
  },
  data() {
    return {
      dataPackage: 0,
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
    await this.getType();
    this.getDataPackage();
    this.getCity();
    this.getPromoterLists();
    this.getProvince();
    this.getOutletCat();
    this.$router.afterEach(this.handleUrlChange);
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
    async handleUrlChange(to, from) {
      'sss', to.params.id, from.params.id;
      this.queryStates = to.params.id;

      await this.getType();
      this.getDataPackage();
      this.getCity();
      this.getPromoterLists();
      this.getProvince();
      this.getOutletCat();
    },
    removeFilter() {
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
    async getType() {
      const res = await this.$ApiServiceLayer.get(
        this.$PATH.RELATIVE_PATH.GET.MENU_EDIT +
          '/' +
          this.queryStates +
          '/' +
          '?p=' +
          this.$STORE.state.userConfig.setProjectId,
        this.$PATH.SERVICE_NAME.AUTH
      );
      if (res.status === 200) {
        this.type = res.data;
      }
    },
    async getDataPackage(limit = 20, offset = 0) {
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
          this.type.frontend_api_queryparams +
          '&ordering=' +
          this.selected +
          '&p=' +
          this.$STORE.state.userConfig.setProjectId,
        this.$PATH.SERVICE_NAME.AUTH
      );
      if (res.status === 200) {
        this.dataPackage = res.data.results;
        'sd:', this.dataPackage;
        this.totalDataCount = res.data.count;
      }
    },
    async myCallback() {
      await this.getDataPackage(20, 20 * (this.page - 1));
    },
    detail(id) {
      this.$router.push('/storemng/detail/' + id);
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
          this.$STORE.state.userConfig.setProjectId,
        this.$PATH.SERVICE_NAME.AUTH
      );
      if (res.status === 200) {
        'promoter:', res.data;
        this.promoterLists = res.data;
      }
    },
    warningPage(id) {
      this.$router.push({ name: 'warningPage', params: { id: id } });
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
  padding: 32px 50px;
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
  .box {
    // border: 1px solid #c4c4c4;
    padding: 24px;
    border-radius: 2px;
    margin-bottom: 16px;
    background: #fff;
    border-radius: 8px;
    box-shadow: 0px 4px 4px rgba(214, 214, 214, 0.6);
    .title {
      font-weight: 700;
      font-size: 18px;
    }
    .package-number {
      height: 38px;
      text-indent: 10px;
    }
    .inputs {
      width: 100%;
      height: 38px;
      border: 1px solid #c4c4c4;
      padding: 0 9px;
      border-radius: 2px;
      font-family: 'IRANYekanfa' !important;
      border-radius: 4px;
    }
  }
  .persian-number {
    font-family: 'IRANYekanfa' !important;
  }
  .warning-box {
    border-radius: 4px;
    padding: 4px 10px;
    font-family: 'IRANYekanfa' !important;
    color: #fff;
    cursor: pointer;
  }
  .form-select {
    width: 100%;
    border: 1px solid #c4c4c4;
    height: 38px;
    padding: 0 9px;
    border-radius: 2px;
    color: #828282;
    border-radius: 4px;
  }
  .accept {
    padding: 0 20px;
    height: 38px;
    background: #357ae1;
    border-radius: 2px;
    color: #fff;
    border: none !important;
    margin-left: 10px;
    border-radius: 4px;
  }
  .remove-filtes {
    padding: 0 20px;
    border: 1px solid #357ae1;
    border-radius: 2px;
    color: #357ae1;
    height: 38px;
    background: #fff;
    border-radius: 4px;
  }
  .ordering-title {
    min-width: 180px;
  }
  .ordering {
    max-width: 100px;
  }
  .show-date {
    border: none;
    text-indent: 55px;
    background: #fff;
  }
  .search-input {
    text-indent: 10px;
    height: 40px;
    border: 1px solid #c4c4c4;
    border-radius: 2px;
    font-family: 'IRANYekanfa' !important;
    border-radius: 4px;
  }
  .eye-icon {
    width: 32px;
    cursor: pointer;
  }
}
</style>
