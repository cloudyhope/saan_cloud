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
              <th>ادرس</th>
              <th>نوع ساختمان</th>
              <th>ظرفیت آسانسور</th>
              <th>شناسه آسانسور</th>
              <th>تعداد طبقات</th>
              <th>نام آسانسور</th>
              <th>نوع آسانسور</th>
              <th>عملیات</th>
            </tr>
          </template>

          <template #TableBody>
            <tr v-for="(item, index) in dataPackage" :key="item.id">
              <td class="persian-number">
                {{ 20 * (page - 1) + 1 + index }}
              </td>
              <td>{{ item.building.verbose_name }}</td>
              <td>{{ (item.building.city && item.building.city.name) || '—' }}</td>
              <td>{{ item.building.address }}</td>
              <td>{{ item.building.type }}</td>
              <td>{{ item.elevator.capacity }}</td>
              <td>{{ item.elevator.id }}</td>
              <td>{{ item.elevator.number_of_floors }}</td>
              <td>{{ item.elevator.title }}</td>
              <td>{{ item.elevator.type }}</td>
              <td>
                <button
                  type="button"
                  class="icon-action"
                  @click="visitDetail(item.building.id)"
                  aria-label="جزئیات ساختمان"
                  title="جزئیات ساختمان"
                >
                  <ActionIcon name="view" />
                </button>

                <button
                  type="button"
                  class="icon-action"
                  @click="elevatorItemDetailsFunc(item.elevator.id)"
                  aria-label="جزئیات آسانسور"
                  title="جزئیات آسانسور"
                >
                  <ActionIcon name="elevator" />
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
      options: [
        { item: 'id', name: 'ترتیب ثبت' },
        { item: '-id', name: 'جدیدترین' },
        { item: 'elevator__title', name: 'عنوان' },
        { item: '-elevator__title', name: 'عنوان (نزولی)' },
      ],
    };
  },
  mounted() {
    this.getDataPackage();
  },
  computed: {},
  methods: {
    applyFilters() {
      this.page = 1;
      return this.getDataPackage();
    },
    removeFilter() {
      this.page = 1;
    },

    async getDataPackage(limit = 20, offset = 0, order = null) {
      this.loadingList = true;
      this.listError = '';
      try {
        let url =
          this.$PATH.RELATIVE_PATH.MULTI.BUILDING_ELEVATOR_LIST_CREATE +
          '?limit=' +
          limit +
          '&offset=' +
          offset +
          '&p=' +
          this.$STORE.state.userConfig.setProjectId +
          '&ordering=' +
          this.selected;

        if (order) {
          url += '&ordering=' + order;
        }

        const res = await this.$ApiServiceLayer.get(url, '');
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
    elevatorItemDetailsFunc(id) {
      this.$router.push('/elevatormanagement/elevatordetail/' + id);
    },

    async myCallback(page) {
      const offset = (page - 1) * 20;
      await this.getDataPackage(20, offset);
    },

    visitDetail(id) {
      this.$router.push('/elevatormanagement/buildingdetail/' + id);
    },
  },
};
</script>
<style scoped>
.elevator-icon {
  width: 22px;
}
</style>
