<template>
  <div class="list-warehouse">
    <FilterPanel @apply="applyFilters">
      <div class="filter-field">
        <label for="ware-type">نوع کالا</label
        ><select id="ware-type" v-model="pickTypes" class="form-select">
          <option value="">همه کالاها</option>
          <option v-for="types in wareType" :value="types.id" :key="types.id">
            {{ types.verbose_name }}
          </option>
        </select>
      </div>
      <template #actions
        ><button type="submit" class="accept" :disabled="loadingList">اعمال فیلتر</button
        ><button type="button" class="remove-filtes" @click="removeFilter">
          پاک کردن فیلترها
        </button></template
      >
    </FilterPanel>
    <div class="box list-box">
      <Tableview
        :recordCount="totalDataCount"
        :page="page"
        :hover="true"
        :bordered="true"
        :showNoContent="loadingList"
        :showNoData="!loadingList && getDataLists.length === 0"
        :errorMessage="listError"
        @retry="getData(20, 20 * (page - 1))"
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
            <th>نام انگلیسی</th>
            <th>نام فارسی</th>
            <th>کد کالا</th>
            <th>نوع کالا</th>
            <th>مصرفی</th>
            <th>موجودی</th>
            <th>توضیحات</th>
            <th>فعال/غیرفعال</th>
            <th>عملیات</th>
          </tr>
        </template>

        <template #TableBody>
          <tr v-for="(item, index) in getDataLists" :key="item.id">
            <td class="persian-number">
              {{ index + 1 }}
            </td>
            <td>{{ item.name_en }}</td>
            <td>{{ item.name_fa }}</td>
            <td>{{ item.identifier }}</td>
            <td>{{ item.type.verbose_name }}</td>
            <td v-if="item.is_for_use === true">بله</td>
            <td v-else>خیر</td>
            <td class="persian-number">{{ item.stock_count }} {{ item.unit_fa }}</td>
            <td>{{ item.description }}</td>
            <td>
              <select
                style="border-radius: 4px; padding: 2px"
                v-model="item.active"
                @change="changeActiveWare(item)"
              >
                <option :value="true">فعال</option>
                <option :value="false">غیرفعال</option>
              </select>
            </td>
            <td>
                <RowActions :items="[{ label: 'جزئیات', icon: 'view', action: () => action(item.id) }, { label: 'ویرایش', icon: 'edit', action: () => editData(item) }, { label: 'تاریخچه انتقال', icon: 'history', action: () => transAction(item.id) }]" />
              </td>
          </tr>
        </template>
      </Tableview>
      <b-modal size="lg" v-model="editModal" hide-footer>
        <div class="d-flex mb-4">
          <div class="d-flex flex-column ml-3">
            <label for="html">نام فارسی</label>
            <input class="form-select" type="text" v-model="modalUserData.name_fa" />
          </div>
          <div class="d-flex flex-column ml-3">
            <label for="html">نام انگلیسی</label>
            <input class="form-select" type="text" v-model="modalUserData.name_en" />
          </div>
        </div>
        <div class="mb-3">
          <label for="html">توضیحات</label>
          <textarea v-model="modalUserData.description" class="textarea"></textarea>
        </div>
        <div class="d-flex justify-content-end align-items-end">
          <button @click="editBtn" class="accept">تایید</button>
          <button class="remove-filtes" @click="editModal = false">بستن</button>
        </div>
      </b-modal>
    </div>
  </div>
</template>
<script>
import FilterPanel from '@/components/FilterPanel/index.vue';
import Tableview from '../../components/Tableview/index.vue';
import Pagination from '@/components/ListPagination/index.vue';

import RowActions from '@/components/RowActions/index.vue';
export default {
  components: { RowActions,
    FilterPanel,
    Tableview,
    Pagination,
  },
  data() {
    return {
      loadingList: true,
      listError: '',
      getDataLists: [],
      wareType: [],
      pickTypes: '',
      totalDataCount: 0,
      page: 1,
      editModal: false,
      modalUserData: {},
    };
  },
  mounted() {
    this.getData();
    this.getWareType();
  },
  computed: {
    showContnetFunc() {
      return this.getDataLists === 0;
    },
    showDataFunc() {
      if (this.getDataLists.length !== undefined) {
        return this.getDataLists.length === 0;
      }
      return false;
    },
  },
  methods: {
    applyFilters() {
      this.page = 1;
      return this.getData();
    },
    removeFilter() {
      this.page = 1;
      this.pickTypes = '';
      this.getData();
    },
    async getWareType() {
      const res = await this.$ApiServiceLayer.get(
        this.$PATH.RELATIVE_PATH.MULTI.WAREHOUSE_TYPE +
          '?p=' +
          this.$STORE.state.userConfig.setProjectId,
        this.$PATH.SERVICE_NAME.EMPTY
      );
      if (res.status === 200) {
        this.wareType = res.data;
      }
    },
    async getData(limit = 20, offset = 0) {
      this.loadingList = true;
      this.listError = '';
      try {
        const res = await this.$ApiServiceLayer.get(
          this.$PATH.RELATIVE_PATH.MULTI.WAREHOUSE_LIST +
            '?p=' +
            this.$STORE.state.userConfig.setProjectId +
            '&limit=' +
            limit +
            '&offset=' +
            offset +
            '&type=' +
            this.pickTypes,
          this.$PATH.SERVICE_NAME.EMPTY
        );
        if (res.status !== 200) {
          this.listError = this.$ApiServiceLayer.getErrorMessage(res);
          return;
        }
        if (res.status === 200) {
          this.getDataLists = res.data.results;
          this.totalDataCount = res.data.count;
        }
      } finally {
        this.loadingList = false;
      }
    },
    async myCallback() {
      await this.getData(20, 20 * (this.page - 1));
    },
    transAction(id) {
      this.$router.push({ name: 'transactionList', params: { id: id } });
    },
    action(id) {
      this.$router.push({ name: 'wareDetail', params: { id: id } });
    },
    editData(item) {
      this.editModal = true;
      this.modalUserData = { ...item };
    },
    async editBtn() {
      const data = {
        name_fa: this.modalUserData.name_fa,
        name_en: this.modalUserData.name_en,
        description: this.modalUserData.description,
      };
      console.log(this.modalUserData.name_en);
      const res = await this.$ApiServiceLayer.patch(
        this.$PATH.RELATIVE_PATH.MULTI.WAREHOUSE_EDIT +
          this.modalUserData.id +
          '/' +
          '?p=' +
          this.$STORE.state.userConfig.setProjectId,
        this.$PATH.SERVICE_NAME.EMPTY,
        data
      );
      if (res.status === 200) {
        this.$notify({
          group: 'tc',
          type: 'success',
          text: 'تغییرات با موفقیت اعمال شد!',
        });
        this.getData();
        this.editModal = false;
      }
    },
    async changeActiveWare(item) {
      const res = await this.$ApiServiceLayer.patch(
        this.$PATH.RELATIVE_PATH.MULTI.WAREHOUSE_EDIT +
          item.id +
          '/' +
          '?p=' +
          this.$STORE.state.userConfig.setProjectId,
        this.$PATH.SERVICE_NAME.EMPTY,
        { active: item.active }
      );
      console.log(res);
      if (res.status === 200) {
        this.$notify({
          group: 'tc',
          type: 'success',
          text: 'وضعیت با موفقیت تغییر پیدا کرد!',
        });
      }
    },
  },
};
</script>
<style lang="scss" scoped>
.textarea {
  border: 1px solid #c4c4c4;
  width: 100%;
  border-radius: 4px;
  min-height: 100px;
  padding: 10px;
}
</style>
