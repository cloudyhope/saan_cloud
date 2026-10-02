<template>
  <div>
    <Loading v-if="loading" />
    <div class="action-list">
      <div class="box list-box">
        <Tableview
          :recordCount="totalDataCount"
          :page="page"
          :hover="true"
          :bordered="true"
          :showNoContent="loadingList"
          :showNoData="!loadingList && walletTransactionType.length === 0"
          :errorMessage="listError"
          @retry="getwalletTransactionType(20, 20 * (page - 1))"
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
              <th>نوع تراکنش</th>
              <th>عنوان</th>
              <th>حداقل مقدار</th>
              <th>حداکثر مقدار</th>
              <th>حداکثر باقی مانده</th>
            </tr>
          </template>

          <template #TableBody>
            <tr v-for="(item, index) in walletTransactionType" :key="item.id">
              <td class="persian-number">
                {{ index + 1 }}
              </td>
              <td>{{ item.key }}</td>
              <td>
                {{ item.verbose_name }}
              </td>
              <td class="persian-number">
                {{ item.min_amount }}
              </td>

              <td class="persian-number">
                {{ item.max_amount }}
              </td>
              <td class="persian-number">
                {{ item.max_acceptable_rest_amount }}
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
import Loading from '../../components/Loading/index.vue';
export default {
  components: {
    Tableview,
    Pagination,
    Loading,
  },
  data() {
    return {
      loadingList: true,
      listError: '',
      walletTransactionType: [],
      totalDataCount: 0,
      page: 1,
      loading: true,
    };
  },
  mounted() {
    this.getwalletTransactionType();
  },
  methods: {
    async getwalletTransactionType(limit = 20, offset = 0) {
      this.loadingList = true;
      this.listError = '';
      try {
        const res = await this.$ApiServiceLayer.get(
          this.$PATH.RELATIVE_PATH.GET.WALLET_TRANSACTION_TYPES + '?p=' +
            this.$STORE.state.userConfig.setProjectId + '&limit=' + limit + '&offset=' + offset,
          this.$PATH.SERVICE_NAME.EMPTY,
          {}
        );
        if (res.status !== 200) {
          this.listError = this.$ApiServiceLayer.getErrorMessage(res);
          return;
        }
        if (res.status === 200) {
          this.walletTransactionType = res.data.results || [];
          this.totalDataCount = res.data.count || this.walletTransactionType.length;
          this.loading = false;
        }
      } finally {
        this.loadingList = false;
        this.loading = false;
      }
    },
    async myCallback() {
      await this.getwalletTransactionType(20, 20 * (this.page - 1));
    },
  },
};
</script>
<style lang="scss" scoped>
.empty-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 80vh;
}
.action-list {
  width: 100%;

  min-height: 80vh;

  .watch-items {
    cursor: pointer;
  }
}
</style>
