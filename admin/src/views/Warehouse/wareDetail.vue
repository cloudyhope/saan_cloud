<template>
  <div class="warehouse-detail record-detail">
    <section class="detail-hero">
      <div class="detail-hero-top">
        <div>
          <span class="detail-eyebrow">مشخصات کالا</span>
          <h2>{{ detailData.name_fa || 'جزئیات کالا' }}</h2>
        </div>
        <router-link class="detail-back" to="/warehouse/warelist">بازگشت به فهرست ←</router-link>
      </div>
      <div class="detail-summary">
        <span class="detail-badge">{{
          (detailData.type || {}).verbose_name || 'نوع کالا ثبت نشده'
        }}</span
        ><span>{{ detailData.identifier || 'کد ثبت نشده' }}</span>
      </div>
      <InfoGrid
        :fields="[
          {
            label: 'موجودی پروژه',
            value:
              Number(detailData.locations_stock_count || 0) +
              Number(detailData.users_stock_count || 0),
          },
          { label: 'موجودی انبارها', value: detailData.locations_stock_count },
          { label: 'موجودی نزد افراد', value: detailData.users_stock_count },
        ]"
      />
      <div class="detail-form-actions">
        <button class="reject" :disabled="loadingList" @click="toggleBackgroundColor">
          {{ buttonText }}
        </button>
      </div>
    </section>
    <div class="detail-section">
      <Tableview
        :hover="true"
        :bordered="true"
        :showNoContent="loadingList"
        :errorMessage="listError"
        @retry="makeApiCall(condition === 'USER' ? 'user' : 'location')"
        :showNoData="showDataFunc"
      >
        <template #TableTitle>
          <tr>
            <th>ردیف</th>
            <th>نام انبار/فرد</th>
            <th>مقدار موجودی</th>
            <th>عملیات</th>
          </tr>
        </template>

        <template v-if="buttonBackgroundColor === '#357AE1'" #TableBody>
          <tr v-for="(item, index) in getLocationDataLists" :key="item.id">
            <td class="persian-number">
              {{ index + 1 }}
            </td>
            <td>{{ item.location.name_fa }}</td>
            <td class="persian-number">{{ item.stock_count }}</td>
            <td>
                <RowActions :items="[{ label: 'افزایش موجودی', icon: 'plus', action: () => openstockModal(item) }, { label: 'مصرف', icon: 'minus', action: () => openUseModal(item) }, { label: 'انتقال به انبار', icon: 'transfer', action: () => openRelocateModal(item) }, { label: 'انتقال به کاربر', icon: 'user', action: () => openDeliverModal(item) }, { label: 'ثبت ضایعات', icon: 'trash', action: () => openUseModal(item, 'SCRAP'), danger: true }]" />
              </td>
          </tr>
        </template>
        <template v-else #TableBody>
          <tr v-for="(item, index) in getUserDataLists" :key="item.id">
            <td class="persian-number">
              {{ index + 1 }}
            </td>
            <td>{{ item.user.first_name }} {{ item.user.last_name }}</td>
            <td class="persian-number">{{ item.stock_count }}</td>
            <td>
                <RowActions :items="[{ label: 'انتقال به مصرف', icon: 'minus', action: () => openUseModal(item) }, { label: 'انتقال به انبار', icon: 'transfer', action: () => openRelocateModal(item) }, { label: 'انتقال به کاربر', icon: 'user', action: () => openDeliverModal(item) }, { label: 'ثبت ضایعات', icon: 'trash', action: () => openUseModal(item, 'SCRAP'), danger: true }]" />
              </td>
          </tr>
        </template>
      </Tableview>
      <b-modal
        size="lg"
        v-model="useModal"
        :title="useKind === 'SCRAP' ? 'ثبت ضایعات' : 'مصرف کالا'"
        header-close-label="بستن"
        hide-footer
        centered
      >
        <div class="my-4">
          <div>{{ useKind === 'SCRAP' ? 'مقدار ضایعات و دلیل آن را ثبت کنید.' : 'مقدار مصرفی مورد نظر خود را وارد کنید.' }}</div>
          <label>مقدار: </label>
          <input
            aria-label="مقدار کالا"
            type="number"
            min="1"
            step="1"
            v-model="useInputValue"
            class="inputs mb-3"
          />
          <b-form-textarea
            id="textarea"
            v-model="textarea"
            :placeholder="useKind === 'SCRAP' ? 'دلیل ضایعات (حداقل ۱۰ نویسه)' : 'توضیحات'"
            rows="3"
            max-rows="6"
            class="mb-3"
          ></b-form-textarea>
          <div class="d-flex justify-content-end">
            <button :disabled="disabledUseBtn" @click="submitUseModal" class="confirm-item">
              ثبت
            </button>
          </div>
        </div>
      </b-modal>
      <b-modal
        size="lg"
        v-model="relocateModal"
        :title="condition === 'USER' ? 'برگشت کالا به انبار' : 'انتقال به انبار'"
        header-close-label="بستن"
        hide-footer
        centered
      >
        <div class="my-4">
          <div>{{ condition === 'USER' ? 'مقدار برگشتی و دلیل برگشت را ثبت کنید.' : 'مقدار انتقالی را وارد کنید.' }}</div>
          <div class="d-flex justify-content-between align-items-center mb-3">
            <div class="w-100">
              <label>مقدار: </label>
              <input
                aria-label="مقدار کالا"
                type="number"
                min="1"
                step="1"
                v-model="useInputValue"
                class="inputs w-75"
              />
            </div>
            <div class="d-flex justify-content-end align-items-end w-100">
              <label for="warehouse-destination">انبار:</label>
              <select id="warehouse-destination" v-model="pickLocation" class="inputs w-75">
                <option v-for="location in locationLists" :value="location.id" :key="location.id">
                  {{ location.name_fa }}
                </option>
              </select>
            </div>
          </div>
          <b-form-textarea
            id="textarea"
            v-model="textarea"
            :placeholder="condition === 'USER' ? 'دلیل برگشت (حداقل ۱۰ نویسه)' : 'توضیحات'"
            rows="3"
            max-rows="6"
            class="mb-3"
          ></b-form-textarea>
          <div class="d-flex justify-content-end">
            <button :disabled="disabledUseBtn" @click="submitUseModal" class="confirm-item">
              ثبت
            </button>
          </div>
        </div>
      </b-modal>
      <b-modal
        size="lg"
        v-model="deliverModal"
        title="تحویل به نیروی اجرایی"
        header-close-label="بستن"
        hide-footer
        centered
      >
        <div class="my-4">
          <div>مقدار مصرفی مورد نظر خود را وارد کنید.</div>
          <div class="d-flex justify-content-between align-items-center mb-3">
            <div class="w-100">
              <label>مقدار: </label>
              <input
                aria-label="مقدار کالا"
                type="number"
                min="1"
                step="1"
                v-model="useInputValue"
                class="inputs w-75"
              />
            </div>
            <div class="d-flex justify-content-end align-items-end w-100">
              <label for="warehouse-person">نیروی اجرایی:</label>
              <select id="warehouse-person" v-model="pickPromoter" class="inputs w-75">
                <option
                  v-for="promoter in promoterLists"
                  :value="promoter.user.id"
                  :key="promoter.id"
                >
                  {{ promoter.user.first_name }} {{ promoter.user.last_name }}
                </option>
              </select>
            </div>
          </div>
          <b-form-textarea
            id="textarea"
            v-model="textarea"
            placeholder="توضیحات"
            rows="3"
            max-rows="6"
            class="mb-3"
          ></b-form-textarea>
          <div class="d-flex justify-content-end">
            <button :disabled="disabledUseBtn" @click="submitUseModal" class="confirm-item">
              ثبت
            </button>
          </div>
        </div>
      </b-modal>
      <b-modal
        size="lg"
        v-model="stockModal"
        title="افزایش موجودی"
        header-close-label="بستن"
        hide-footer
        centered
      >
        <div class="my-4">
          <div>مقدار ورودی مورد نظر خود را وارد کنید.</div>
          <div class="d-flex justify-content-between align-items-center mb-3">
            <div class="w-100">
              <label>مقدار: </label>
              <input
                aria-label="مقدار کالا"
                type="number"
                min="1"
                step="1"
                v-model="useInputValue"
                class="inputs w-25"
              />
            </div>
          </div>

          <div class="d-flex justify-content-end">
            <button :disabled="disabledUseBtn" @click="submitUseModal" class="confirm-item">
              ثبت
            </button>
          </div>
        </div>
      </b-modal>
    </div>
  </div>
</template>
<script>
import { persistentRequestKey, clearRequestKey } from '@/utils/idempotency';
import InfoGrid from '@/components/RecordDetails/InfoGrid.vue';
import Tableview from '../../components/Tableview/index.vue';
import RowActions from '@/components/RowActions/index.vue';
export default {
  components: { RowActions,
    InfoGrid,
    Tableview,
  },
  data() {
    return {
      apiData: null,
      busy: false,
      buttonBackgroundColor: '#357AE1',
      buttonTextColor: '#fff',
      buttonText: 'نمایش موجودی نزد افراد',
      getLocationDataLists: [],
      loadingList: true,
      requestKey: 0,
      listError: '',
      getUserDataLists: [],
      promoterLists: [],
      locationLists: [],
      totalDataCount: 0,
      page: 1,
      detailData: {},
      useModal: false,
      useKind: 'CONSUME',
      relocateModal: false,
      deliverModal: false,
      useInputValue: null,
      stockModal: false,
      pickPromoter: '',
      pickLocation: '',
      columnData: {},
      condition: 'LOCATION',
      textarea: null,
      wareId: null,
      toState: null,
    };
  },
  watch: {
    '$route.params.id': {
      immediate: true,
      handler() {
        this.makeApiCall('location');
      },
    },
  },
  computed: {
    disabledUseBtn() {
      const quantity = Number(this.useInputValue);
      return (
        this.busy ||
        !Number.isSafeInteger(quantity) ||
        quantity <= 0 ||
        (!this.stockModal && quantity > Number(this.columnData.stock_count)) ||
        (this.relocateModal && !this.pickLocation) ||
        (((this.useModal && this.useKind === 'SCRAP') ||
          (this.relocateModal && this.condition === 'USER')) &&
          (!this.textarea || this.textarea.trim().length < 10)) ||
        (this.deliverModal && !this.pickPromoter)
      );
    },
    showDataFunc() {
      return (
        !this.loadingList &&
        (this.condition === 'USER' ? this.getUserDataLists : this.getLocationDataLists).length === 0
      );
    },
  },
  methods: {
    toggleBackgroundColor() {
      if (this.buttonBackgroundColor === '#357AE1') {
        this.makeApiCall('user');
        this.buttonBackgroundColor = '#fff';
        this.buttonTextColor = '#357AE1';
        this.buttonText = 'نمایش موجودی انبار';
        this.condition = 'USER';
      } else {
        this.makeApiCall('location');
        this.buttonBackgroundColor = '#357AE1';
        this.buttonTextColor = '#fff';
        this.buttonText = 'نمایش موجودی نزد افراد';
        this.condition = 'LOCATION';
      }
    },
    openUseModal(data, kind = 'CONSUME') {
      this.useInputValue = null;
      this.pickLocation = '';
      this.pickPromoter = '';
      this.textarea = null;
      this.useModal = !this.useModal;
      this.useKind = kind;
      this.columnData = data;
      this.toState = null;
    },
    openRelocateModal(data) {
      this.useInputValue = null;
      this.pickLocation = '';
      this.pickPromoter = '';
      this.textarea = null;
      this.relocateModal = !this.relocateModal;
      this.toState = 'LOCATION';
      this.columnData = data;
      this.getLocationLists();
    },
    openDeliverModal(data) {
      this.useInputValue = null;
      this.pickLocation = '';
      this.pickPromoter = '';
      this.textarea = null;
      this.deliverModal = !this.deliverModal;
      this.columnData = data;
      this.toState = 'USER';
      this.getPromoterLists();
    },
    openstockModal(data) {
      this.useInputValue = null;
      this.pickLocation = '';
      this.pickPromoter = '';
      this.textarea = null;
      this.stockModal = !this.stockModal;
      this.columnData = data;
      this.toState = 'LOCATION';
    },
    async makeApiCall(apiParam, limit = 20, offset = 0) {
      const requestKey = ++this.requestKey;
      this.wareId = this.$route.params.id;
      this.loadingList = true;
      this.listError = '';
      this.condition = apiParam === 'user' ? 'USER' : 'LOCATION';
      this.buttonBackgroundColor = apiParam === 'user' ? '#fff' : '#357AE1';
      this.buttonText = apiParam === 'user' ? 'نمایش موجودی انبار' : 'نمایش موجودی نزد افراد';
      try {
        const res = await this.$ApiServiceLayer.get(
          this.$PATH.RELATIVE_PATH.MULTI.WAREHOUSE_USER_LOCATION_RETRIEVE +
            this.wareId +
            '/?p=' +
            this.$STORE.state.userConfig.setProjectId +
            '&limit=' +
            limit +
            '&offset=' +
            offset +
            '&based_on=' +
            apiParam,
          ''
        );
        if (requestKey !== this.requestKey) return;
        if (res.status !== 200) {
          this.listError = this.$ApiServiceLayer.getErrorMessage(res);
          return;
        }
        this.detailData = res.data;
        if (apiParam === 'user') this.getUserDataLists = res.data.users || [];
        else this.getLocationDataLists = res.data.locations || [];
      } finally {
        if (requestKey === this.requestKey) this.loadingList = false;
      }
    },
    async submitUseModal() {
      if (this.disabledUseBtn) return;
      this.busy = true;
      try {
        const data = {
          lines: [
            {
              ware: this.wareId,
              amount: parseInt(this.useInputValue * -1),
              location: this.stockModal
                ? null
                : this.condition === 'LOCATION'
                ? this.columnData.location.id
                : null,
              user: this.stockModal
                ? null
                : this.condition === 'USER'
                ? this.columnData.user.id
                : null,
              side: 'FROM',
              involved: this.stockModal ? null : this.condition,
            },
            {
              ware: this.wareId,
              amount: parseInt(this.useInputValue),
              location: this.stockModal
                ? this.columnData.location.id
                : this.toState === 'LOCATION'
                ? this.pickLocation
                : null,
              user: this.toState === 'USER' ? this.pickPromoter : null,
              side: 'TO',
              involved: this.toState,
            },
          ],
          description: this.textarea || '',
          kind: this.stockModal ? 'RECEIPT' : this.useModal ? this.useKind :
            this.relocateModal && this.condition === 'USER' ? 'RETURN' : 'TRANSFER',
        };
        const keyScope = 'transfer.' + this.$STORE.state.userConfig.setProjectId + '.' + this.wareId;
        data.request_key = persistentRequestKey(keyScope, data);
        const res = await this.$ApiServiceLayer.post(
          this.$PATH.RELATIVE_PATH.POST.WARE_TRANSACTION +
            '?p=' +
            this.$STORE.state.userConfig.setProjectId,
          this.$PATH.SERVICE_NAME.EMPTY,
          data
        );
        if (res.status === 200) {
          clearRequestKey(keyScope, data.request_key);
          this.useModal = false;
          this.relocateModal = false;
          this.deliverModal = false;
          this.stockModal = false;
          this.useInputValue = null;
          this.pickPromoter = '';
          this.textarea = null;
          this.$notify({
            group: 'tc',
            type: 'success',
            text: data.kind === 'SCRAP' ? 'ضایعات ثبت شد.' : data.kind === 'RETURN' ? 'برگشت به انبار ثبت شد.' : 'گردش موجودی ثبت شد.',
          });
          this.makeApiCall('location');
          this.buttonTextColor = '#fff';
        } else {
          this.$notify({
            group: 'tc',
            type: 'error',
            text: this.$ApiServiceLayer.getErrorMessage(res),
          });
        }
      } finally {
        this.busy = false;
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
    async getLocationLists() {
      const res = await this.$ApiServiceLayer.get(
        this.$PATH.RELATIVE_PATH.MULTI.LOCATION_LIST_CREATE +
          '?p=' +
          this.$STORE.state.userConfig.setProjectId,
        this.$PATH.SERVICE_NAME.EMPTY
      );
      if (res.status === 200) {
        this.locationLists = res.data;
      }
    },
  },
};
</script>
<style scoped>
.warehouse-detail {
  padding: 0;
}
.opt-btn {
  display: inline-grid;
  place-items: center;
  width: 36px;
  height: 36px;
  border: 1px solid #e0e7f2;
  background: #f7f9fc;
  border-radius: 8px;
  margin: 2px;
}
.opt-btn img {
  width: 20px;
  height: 20px;
}
.inputs {
  margin-top: 16px;
  width: 100%;
  min-height: 44px;
  border: 1px solid #ced7e5;
  padding: 10px 12px;
  border-radius: 9px;
}
.confirm-item,
.reject-item {
  min-height: 44px;
  padding: 10px 18px;
  border-radius: 9px;
  margin-left: 8px;
}
.confirm-item {
  background: #345de0;
  color: #fff;
  border: 1px solid #345de0;
}
.confirm-item:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}
.reject-item {
  background: #fff;
  color: #536680;
  border: 1px solid #dce3ef;
}
@media (max-width: 640px) {
  .opt-btn {
    width: 44px;
    height: 44px;
  }
}
</style>
