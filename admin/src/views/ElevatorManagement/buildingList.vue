<template>
  <div class="follow-order">
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
          <template #controls
            ><label class="ordering-title">ترتیب ثبت</label
            ><b-form-select
              aria-label="ترتیب ثبت"
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
              <th>شهر</th>
              <th>آدرس</th>

              <th>نوع ساختمان</th>
              <th>عملیات</th>
            </tr>
          </template>

          <template #TableBody>
            <tr v-for="(item, index) in dataPackage" :key="item.id">
              <td class="persian-number">
                {{ 20 * (page - 1) + 1 + index }}
              </td>
              <td>{{ item.verbose_name }}</td>
              <td>{{ (item.city && item.city.name) || '—' }}</td>
              <td>
                <span class="cell-text" :title="item.address">{{ item.address || '—' }}</span>
              </td>
              <td>
                {{ { Complex: 'مجتمع', Apartment: 'آپارتمان' }[item.type] || item.type || '—' }}
              </td>

              <td>
                <button
                  type="button"
                  class="icon-action"
                  @click="elevatorItemFunc(item.id)"
                  aria-label="آسانسور"
                  title="آسانسور"
                >
                  <ActionIcon name="elevator" />
                </button>

                <button
                  type="button"
                  class="icon-action"
                  @click="$router.push('/elevatormanagement/buildingdetail/' + item.id)"
                  aria-label="جزئیات ساختمان"
                  title="جزئیات ساختمان"
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
import Tableview from '../../components/Tableview/index.vue';
import Pagination from '@/components/ListPagination/index.vue';

export default {
  components: {
    Tableview,
    Pagination,
  },
  data() {
    return {
      loadingList: true,
      listError: '',
      dataPackage: [],
      page: 1,
      totalDataCount: 0,
      selected: '-id',
      buildingId: '',
      options: [
        { item: 'id', name: 'صعودی' },
        { item: '-id', name: 'نزولی' },
      ],
    };
  },
  mounted() {
    this.getDataPackage();
  },
  methods: {
    applyFilters() {
      this.page = 1;
      return this.getDataPackage();
    },
    removeFilter() {
      this.page = 1;
    },
    async myCallback() {
      await this.getDataPackage(20, 20 * (this.page - 1));
    },
    async getDataPackage(limit = 20, offset = 0) {
      this.loadingList = true;
      this.listError = '';
      try {
        const res = await this.$ApiServiceLayer.get(
          this.$PATH.RELATIVE_PATH.MULTI.VISIT_BUILDING_LIST_CREATE +
            '?limit=' +
            limit +
            '&offset=' +
            offset +
            '&p=' +
            this.$STORE.state.userConfig.setProjectId +
            '&is_active=true' +
            '&parent__isnull=false&ordering=' +
            this.selected,
          ''
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
    elevatorItemFunc(buildingId) {
      const routeData = this.$router.resolve({
        name: 'createElevator',
        params: { id: buildingId },
      });
      window.open(routeData.href, '_blank');
    },
  },
};
</script>
