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
              <th>نام مشتری-شرکت</th>
              <th>نام و نام خانوادگی</th>
              <th>شماره تماس</th>
              <th>توضیحات</th>
              <th>عملیات</th>
            </tr>
          </template>

          <template #TableBody>
            <tr v-for="(item, index) in dataPackage" :key="item.id">
              <td class="persian-number">
                {{ 20 * (page - 1) + 1 + index }}
              </td>
              <td>{{ item.client.name_fa }}</td>
              <td>{{ item.user.first_name }} {{ item.user.last_name }}</td>
              <td>{{ item.user.username }}</td>
              <td>{{ item.client.description }}</td>
              <td>
                <RowActions :items="[{ label: 'جزئیات مشتری', icon: 'view', to: '/customermanagement/detail/' + item.client.id }]" />
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

import RowActions from '@/components/RowActions/index.vue';
export default {
  components: { RowActions,
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
      selected: 'datetime_created',
    };
  },
  mounted() {
    this.getDataPackage();
  },
  computed: {
    options() {
      return [
        { item: 'datetime_created', name: 'صعودی' },
        { item: '-datetime_created', name: 'نزولی' },
      ];
    },
  },
  methods: {
    applyFilters() {
      this.page = 1;
      return this.getDataPackage();
    },
    removeFilter() {
      this.page = 1;
    },
    myCallback() {
      return this.getDataPackage(20, 20 * (this.page - 1));
    },

    async getDataPackage(limit = 20, offset = 0) {
      this.loadingList = true;
      this.listError = '';
      try {
        const res = await this.$ApiServiceLayer.get(
          this.$PATH.RELATIVE_PATH.MULTI.USER_CLIENT_LIST_CREATE +
            '?limit=' +
            limit +
            '&offset=' +
            offset +
            '&p=' +
            this.$STORE.state.userConfig.setProjectId +
            '&is_active=true&ordering=' +
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
  },
};
</script>
