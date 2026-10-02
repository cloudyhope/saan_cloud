<template>
  <div class="containers ticket-list">
    <div class="warning" v-if="openTicketsCount > 0">
      <div class="d-flex">
        <img src="../../assets/images/iconPack/carbon_warning-square.svg" />
        <span class="text">توجه</span>
      </div>
      <div>
        <ul>
          <li class="persian-number">
            شما {{ openTicketsCount }} تیکت باز دارید. در صورتی که مشکل حل شده است لطفا تیکت را
            ببندید.
          </li>
        </ul>
      </div>
    </div>
    <button @click="newTicket" class="new-ticket">
      <img class="icon" src="../../assets/images/iconPack/plus-white.svg" />
      تیکت جدید
    </button>
    <div class="table-box">
      <Tableview
        :recordCount="totalDataCount"
        :page="page"
        class="table pb-4"
        :hover="true"
        :bordered="true"
        :showNoContent="loadingList"
        :showNoData="!loadingList && ticketList.length === 0"
        :errorMessage="listError"
        @retry="getTicketList(20, 20 * (page - 1))"
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
            <th>شماره</th>
            <th>عنوان</th>
            <th>موضوع</th>
            <th>وضعیت</th>
            <th>تاریخ آخرین به‌روزرسانی</th>
            <th>عملیات</th>
          </tr>
        </template>

        <template #TableBody>
          <tr
            @click="ticketDetailPage(item.id)"
            v-for="(item, index) in ticketList"
            :key="item.id"
            class="ticket-detail"
          >
            <td class="persian-number">{{ 1 + index }}</td>
            <td>{{ item.title }}</td>
            <td>{{ item.subject }}</td>
            <td v-if="item.status === 'A'">پاسخ داده شده</td>
            <td v-if="item.status === 'W'">در انتظار پاسخ</td>
            <td v-if="item.status === 'C'">بسته شده</td>
            <td>
              <DisplayDate :value="item.datetime_last_change" />
            </td>
            <td v-if="item.status === 'W'"></td>
            <td v-if="item.status === 'C'">
              <input
                style="width: 20px; height: 20px"
                type="checkbox"
                checked="checked"
                :disabled="true"
              />
            </td>
            <td @click.stop="closeTicket(item.id)" v-if="item.status === 'A'">
              <button class="close-ticket">
                <img class="icon ml-2" src="../../assets/images/iconPack/charm_tick.svg" />
                بستن
              </button>
            </td>
          </tr>
        </template>
      </Tableview>
    </div>
  </div>
</template>
<script>
import DisplayDate from '@/components/DisplayDate/index.vue';
import Tableview from '../../components/Tableview/index.vue';
import Pagination from '@/components/ListPagination/index.vue';

export default {
  components: {
    DisplayDate,
    Tableview,
    Pagination,
  },
  data() {
    return {
      loadingList: true,
      listError: '',
      ticketList: [],
      page: 1,
      totalDataCount: 0,
    };
  },
  computed: {
    openTicketsCount() {
      return this.ticketList.filter((ticket) => ticket.status !== 'C').length;
    },
    showContnetFunc() {
      return !Array.isArray(this.ticketList);
    },
    showDataFunc() {
      return Array.isArray(this.ticketList) && this.ticketList.length === 0;
    },
  },
  mounted() {
    this.getTicketList();
  },
  methods: {
    async getTicketList(limit = 20, offset = 0) {
      this.loadingList = true;
      this.listError = '';
      try {
        const res = await this.$ApiServiceLayer.get(
          this.$PATH.RELATIVE_PATH.MULTI.TICKET_LIST +
            '?limit=' +
            limit +
            '&offset=' +
            offset +
            '&ordering=-datetime_last_change' +
            '&p=' +
            this.$STORE.state.userConfig.setProjectId,
          this.$PATH.SERVICE_NAME.AUTH
        );
        if (res.status !== 200) {
          this.listError = this.$ApiServiceLayer.getErrorMessage(res);
          return;
        }
        if (res.status === 200) {
          this.ticketList = res.data.results;
          this.totalDataCount = res.data.count;
        }
      } finally {
        this.loadingList = false;
      }
    },
    async myCallback() {
      await this.getTicketList(20, 20 * (this.page - 1));
    },
    async closeTicket(id) {
      const res = await this.$ApiServiceLayer.patch(
        this.$PATH.RELATIVE_PATH.MULTI.TICKET_EDIT +
          id +
          '/' +
          '?p=' +
          this.$STORE.state.userConfig.setProjectId,
        this.$PATH.SERVICE_NAME.AUTH,
        { status: 'C' }
      );
      if (res.status === 200) {
        this.$notify({
          group: 'tc',
          type: 'success',
          text: 'تیکت با موفقیت بسته شد!',
        });
        this.getTicketList();
      }
    },
    newTicket() {
      this.$router.push({ name: 'newTicket' });
    },
    ticketDetailPage(id) {
      this.$router.push({ name: 'ticketDetail', params: { id: id } });
    },
  },
};
</script>
<style lang="scss" scoped>
.containers {
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
      list-style: none;
    }
    .text {
      color: #664d03;
      font-size: 16px;
      margin-right: 15px;
    }
  }
  // .table {
  // 	border: 1px solid #c4c4c4;
  // }
  .new-ticket {
    background: #285595;
    color: #fff;
    border-radius: 4px;
    padding: 4px 10px;
    border: none;
    margin-bottom: 24px;
    .icon {
      width: 14px;
    }
  }

  .table-box {
    background: #fff;
    border-radius: 8px;
  }
  .close-ticket {
    border: 1px solid #16c98d;
    color: #16c98d;
    background: #fff;
    padding: 6px;
    border-radius: 4px;
    font-size: 14px;
  }
  .ticket-detail {
    cursor: pointer;
  }
}
</style>
<style>
.ticket-list .vpd-icon-btn {
  display: none !important;
}
.ticket-list .vpd-input-group input:disabled {
  background: #fff;
  text-align: center;
  min-width: 130px;
  border: none;
  font-family: 'IRANYekanfa' !important;
  font-size: 16px;
}
</style>
