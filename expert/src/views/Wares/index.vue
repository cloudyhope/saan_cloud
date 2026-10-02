<template>
  <div>
    <BaseTopBar :arrow="true" title="تجهیزات" />
    <!-- <EmptyContainer /> -->
    <div class="mx-6 my-3">
      <Skeleton
        v-if="initialLoading"
        type="list"
        :count="4"
        two-line
        :loading="true"
      />
      <div v-else-if="stockError" class="stock-state" role="alert">{{ stockError }} <button type="button" @click="getgiftData">تلاش دوباره</button></div>
      <div v-else-if="!availableStock.length" class="stock-state">موجودی قابل مصرفی برای شما ثبت نشده است.</div>
      <div v-else v-for="gift in availableStock" :key="gift.id">
        <v-card
          @click="openGiftModal(gift)"
          @keydown.enter.prevent="openGiftModal(gift)"
          @keydown.space.prevent="openGiftModal(gift)"
          role="button" tabindex="0"
          :aria-label="'ثبت مصرف ' + gift.ware.name_fa"
          class="cards-shadow"
        >
          <div class="d-flex justify-space-between align-center">
            <div class="d-flex align-center">
              <div class="img-container-gift">
                <v-img max-width="36" :src="gift.ware.type.icon" />
              </div>
              <div class="d-flex flex-column mr-4">
                <span>{{ gift.ware.name_fa }}</span>
                <span class="mt-1">{{ gift.count }} عدد</span>
              </div>
            </div>
            <div>
              <v-badge
                color="rgba(171, 203, 255)"
                inline
                :content="gift.ware.type.verbose_name"
                v-if="gift.ware.type.name === 'Materials'"
              ></v-badge>
              <v-badge
                color="rgba(194, 170, 101, 1)"
                inline
                :content="gift.ware.type.verbose_name"
                v-if="gift.ware.type.name === 'Tools'"
              ></v-badge>
              <v-badge
                color="rgba(237, 28, 36, 1)"
                inline
                :content="gift.ware.type.verbose_name"
                v-if="gift.ware.type.name === 'Sample'"
              ></v-badge>
              <v-badge
                color="rgba(122, 204, 199, 1)"
                inline
                :content="gift.ware.type.verbose_name"
                v-if="gift.ware.type.name === 'Gift'"
              ></v-badge>
            </div>
          </div>
        </v-card>
      </div>
      <v-bottom-sheet
        :retain-focus="false"
        max-width="576px"
        v-model="btnSheet"
      >
        <v-sheet :retain-focus="false" class="modals pa-6 stock-sheet">
          <div class="d-flex flex-column align-center">
            <v-img
              class="mb-8"
              :max-width="156"
              cover
              src="@/assets/images/rafiki.svg"
            />
            <p>قصد مصرف چه تعداد {{ modalData.ware.name_fa }} را دارید؟</p>
            <label class="visit-choice">مأموریت مرتبط
              <select v-model="selectedVisit" required>
                <option value="">انتخاب مأموریت</option>
                <option v-for="visit in visits" :key="visit.id" :value="visit.id">{{ visit.building && (visit.building.verbose_name || visit.building.code) || 'بازدید' }} · {{ visit.type && (visit.type.verbose_name || visit.type.title) || visit.id }}</option>
              </select>
            </label>
            <p v-if="visitError" class="stock-error" role="alert">{{ visitError }}</p>
            <p v-else-if="!visits.length" class="stock-hint">مأموریت قابل انتخابی برای ثبت مصرف پیدا نشد.</p>
            <div class="counter-wrapper">
              <button type="button" @click="useAllWare" class="usage-text">مصرف تمام موجودی</button>
              <div class="add-item" role="group" aria-label="تعداد مصرف">
                <button type="button" :disabled="plusBtn" aria-label="افزایش تعداد" @click="increaseCount"><v-icon small>mdi-plus</v-icon></button>
                <span class="mx-4 persian">{{ count }}</span>
                <button type="button" :disabled="minesBtn" aria-label="کاهش تعداد" @click="decreaseCount"><v-icon small>mdi-minus</v-icon></button>
              </div>
            </div>
          </div>

          <div class="d-flex mt-5">
            <Button class="confirm-btn" title="ثبت" :disabled="sending || !selectedVisit || count < 1" @click="sendData" />
          </div>
          <p v-if="error" class="stock-error" role="alert">{{ error }}</p>
        </v-sheet>
      </v-bottom-sheet>
      <v-snackbar v-model="snackbar" :timeout="timeout" color="success" top>
        مصرف قطعه برای مأموریت ثبت شد.
      </v-snackbar>
    </div>
  </div>
</template>
<script>
import Button from "../../components/Button/Button.vue";
import EmptyContainer from "@/components/emptyContainer.vue";
import BaseTopBar from "@/components/Topbar/BaseTopbar.vue";
import Skeleton from "@/components/Skeleton/index.vue";
import { persistentRequestKey, clearRequestKey, pageRows, errorMessage } from '@/utils/clientRequests';
export default {
  name: "Profile",
  components: {
    Button,
    EmptyContainer,
    BaseTopBar,
    Skeleton,
  },
  data() {
    return {
      giftData: [],
      initialLoading: true,
      stockError: '',
      data: null,
      btnSheet: false,
      modalData: {
        ware: {
          name_fa: "",
        },
      },
      count: 0,
      minesBtn: true,
      plusBtn: false,
      snackbar: false,
      timeout: 2000,
      visits: [],
      visitError: '',
      selectedVisit: '',
      sending: false,
      error: '',
    };
  },

  computed: {
    availableStock() { return this.giftData.filter(item => Number(item.count) > 0 && item.ware && item.ware.type); },
  },

  mounted() {
    this.getgiftData();
    this.loadVisits();
  },
  methods: {
    async loadVisits() {
      this.visitError = '';
      try {
      const response = await this.$ApiServiceLayer.get(
        this.$PATH.RELATIVE_PATH.GET.VISIT_LIST + '?p=' + this.$STORE.state.userConfig.selectedProject + '&limit=100',
        this.$PATH.SERVICE_NAME.AUTH
      );
      if (response.status === 200) {
        this.visits = pageRows(response.data);
        const routeVisit = Number(this.$route.query.visit);
        if (this.visits.some(visit => visit.id === routeVisit)) this.selectedVisit = routeVisit;
      } else this.visitError = errorMessage(response);
      } catch (error) { this.visitError = 'مأموریت‌ها دریافت نشدند. صفحه را تازه کنید.'; }
    },
    async getgiftData() {
      this.initialLoading = true;
      this.stockError = '';
      try {
      const res = await this.$ApiServiceLayer.get(
        this.$PATH.RELATIVE_PATH.GET.WAREHOUSE_LIST +
          "?p=" +
          this.$STORE.state.userConfig.selectedProject +
          "&me=true",
        this.$PATH.SERVICE_NAME.EMPTY
      );
      if (res.status === 200) {
        this.data = pageRows(res.data)[0] || null;
        this.giftData = this.data && Array.isArray(this.data.stock_count) ? this.data.stock_count : [];
      } else this.stockError = errorMessage(res);
      } catch (error) { this.stockError = 'موجودی دریافت نشد. دوباره تلاش کنید.'; }
      finally { this.initialLoading = false; }
    },
    useAllWare() {
      this.count = Math.max(0, Number(this.modalData.count) || 0);
      this.plusBtn = true;
      this.minesBtn = this.count === 0;
    },
    decreaseCount() {
      this.count = Math.max(0, this.count - 1);
      this.plusBtn = false;
      if (this.count === 0) {
        this.minesBtn = true;
      } else {
        this.minesBtn = false;
      }
    },
    increaseCount() {
      this.count = Math.min(Number(this.modalData.count) || 0, this.count + 1);
      if (this.count > 0) {
        this.minesBtn = false;
      }
      if (this.count === this.modalData.count) {
        this.plusBtn = true;
      } else {
        this.plusBtn = false;
      }
    },
    openGiftModal(data) {
      this.modalData = data;
      this.btnSheet = !this.btnSheet;
      this.count = 0;
      this.minesBtn = true;
      this.plusBtn = false;
      this.error = '';
    },
    async sendData() {
      if (this.sending || !this.selectedVisit || !this.data || !Number.isSafeInteger(Number(this.count)) || Number(this.count) < 1 || Number(this.count) > Number(this.modalData.count)) return;
      this.sending = true;
      this.error = '';
      try {
      const data = {
        lines: [
          {
            ware: this.modalData.ware.id,
            amount: parseInt(this.count * -1),
            location: null,
            user: this.data.id,
            side: "FROM",
            involved: "USER",
          },
          {
            ware: this.modalData.ware.id,
            amount: parseInt(this.count),
            location: null,
            user: null,
            side: "TO",
            involved: null,
          },
        ],
        description: `مصرف ${this.count} ${this.modalData.ware.name_fa} توسط ${this.data.username}`,
        kind: 'CONSUME',
        visit: this.selectedVisit,
      };
      const keyScope = 'expert-consumption.' + this.$STORE.state.userConfig.selectedProject + '.' + this.modalData.ware.id;
      data.request_key = persistentRequestKey(keyScope, data);
      const res = await this.$ApiServiceLayer.post(
        this.$PATH.RELATIVE_PATH.POST.WARE_TRANSACTION +
          "?p=" +
          this.$STORE.state.userConfig.selectedProject,
        this.$PATH.SERVICE_NAME.EMPTY,
        data
      );
      if (res.status === 200) {
        clearRequestKey(keyScope, data.request_key);
        this.btnSheet = false;
        this.getgiftData();
        this.snackbar = true;
      } else this.error = errorMessage(res);
      } catch (error) { this.error = 'ثبت مصرف انجام نشد. دوباره تلاش کنید.'; }
      finally { this.sending = false; }
    },
  },
};
</script>
<style scoped>
.cards-shadow {
  padding: 24px;
  box-shadow: 0px 0px 3px 0px rgba(16, 24, 40, 0.1) !important;
  margin-bottom: 16px;
}
.cards-shadow:focus-visible { outline: 3px solid #357ae1; outline-offset: 2px; }
.usage-text {
  color: #357ae1;
  font-size: 13px;
  font-weight: 700;
  min-height: 44px;
  padding: 0 8px;
}
.usage-text:hover {
  cursor: pointer;
}

.counter-wrapper {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}
.add-item {
  display: flex;
  justify-content: center;
  align-items: center;
  border: 1px solid rgba(122, 204, 199, 1);
  border-radius: 10px;
  padding: 2px;
}
.add-item button { min-width: 44px; min-height: 44px; border-radius: 8px; }
.add-item button:disabled { opacity: .4; }
.usage-text:focus-visible,.add-item button:focus-visible { outline: 3px solid #357ae1; outline-offset: 2px; }
.stock-state { padding: 24px; border: 1px solid #d5e4ec; border-radius: 14px; background: #fff; color: #3d5c6f; }
.stock-state button { display: block; min-height: 44px; margin-top: 8px; color: #245f86; font-weight: 700; }
.stock-sheet { max-height: calc(100dvh - 24px); overflow-y: auto; }
.stock-error { color: #a32131; font-size: 13px; margin-top: 10px; }
.stock-hint { color: #4b6475; font-size: 13px; margin-top: 10px; }
.visit-choice { display: grid; gap: 8px; width: 100%; margin: 12px 0; color: #3b5365; font-size: 13px; }
.visit-choice select { min-height: 44px; width: 100%; padding: 0 10px; border: 1px solid #b9d1df; border-radius: 10px; background: #fff; color: #173d59; }
.visit-choice select:focus-visible { outline: 3px solid #357ae1; outline-offset: 2px; }
.modals {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  border-radius: 8px 8px 0 0;
}
</style>
