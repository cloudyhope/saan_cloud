<template>
  <div>
    <Topbar title="برنامه‌ریزی مأموریت" />
    <p v-if="pendingPlanId" class="pending-plan" role="status">برنامه ساخته شد، اما فعال‌سازی آن کامل نشد. برای تلاش دوباره «ثبت» را بزنید.</p>
    <fieldset class="containers" :disabled="!!pendingPlanId">
      <date-picker
        :disabled="disableDate || !!pendingPlanId"
        placeholder="انتخاب تاریخ"
        color="#357AE1"
        v-model="date"
        format="YYYY-MM-DDTHH:mm:00"
        display-format="jYYYY/jMM/jD"
      />
      <div class="d-flex align-center">
        <v-checkbox v-model="disableDate" color="#357AE1"></v-checkbox>
        این ویزیت تاریخ ندارد.
      </div>
      <div class="d-flex align-center">
        <v-checkbox v-model="isLastDay" color="#357AE1"></v-checkbox>
        ویزیت روز آخر
      </div>
      <div>
        <label class="field-label" for="plan-visit-type">نوع ویزیت</label>
        <select id="plan-visit-type" v-model="selectedVisitType" class="input__styles">
          <option class="placeholder" :value="null" disabled selected>
            نوع ویزیت
          </option>
          <option
            v-for="visitType in visitTypeList"
            :value="visitType.id"
            :key="visitType.id"
          >
            {{ visitType.verbose_name }}
          </option>
        </select>
        <label class="field-label" for="plan-expert">کارشناس</label>
        <select id="plan-expert" v-model="selectedPromoter" class="input__styles">
          <option :value="null" disabled selected>نام پروموتر</option>
          <option
            v-for="promoter in promoterLists"
            :value="promoter.promoter.username"
            :key="'promoter' + promoter.id"
          >
            {{ promoter.promoter.first_name }}
            {{ promoter.promoter.last_name }}
          </option>
        </select>
        <label class="field-label" for="plan-building">کد ساختمان</label>
        <input id="plan-building"
          placeholder="کد ساختمان را وارد کنید."
          type="text"
          class="input__styles"
          v-model="selectedOutletCode"
        />
        <label class="field-label" for="plan-turn">نوبت ویزیت (اختیاری)</label>
        <input id="plan-turn"
          placeholder="نوبت ویزیت را وارد کنید."
          type="number" min="1" inputmode="numeric"
          class="input__styles"
          v-model="selectedVisitTurn"
        />
      </div>
    </fieldset>
    <OverlayButton
      :disabled="disableSubmitButton"
      :title="pendingPlanId ? 'تلاش دوباره برای فعال‌سازی' : 'ثبت'"
      @click="submitHandler"
      :loading="loading"
    />
    <v-snackbar color="red" v-model="alert">
      {{ alertText }}
    </v-snackbar>
    <v-snackbar color="#357AE1" v-model="successAlert">
      برنامه با موفقیت ثبت شد.
    </v-snackbar>
  </div>
</template>
<script>
import Topbar from "../../components/Topbar/backTopBar.vue";
import Button from "../../components/Button/Button.vue";
import OverlayButton from "../../components/Button/overlayButton.vue";
import VuePersianDatetimePicker from "vue-persian-datetime-picker";
import { errorMessage, pageRows } from '@/utils/clientRequests';

export default {
  name: "Profile",
  components: {
    Topbar,
    Button,
    OverlayButton,
    // FullLoading,
    datePicker: VuePersianDatetimePicker,
  },
  data() {
    return {
      date: "",
      disableDate: false,
      selectedVisitType: null,
      visitTypeList: [],
      promoterLists: [],
      selectedPromoter: null,
      selectedOutletCode: "",
      selectedVisitTurn: null,
      isLastDay: false,
      alert: false,
      alertText: '',
      successAlert: false,
      loading: false,
      pendingPlanId: null,
    };
  },
  computed: {
    disableSubmitButton() {
      const isDateMissing = !this.disableDate && !this.date;
      const isPromoterMissing = !this.selectedPromoter;
      const isOutletMissing = !this.selectedOutletCode;

      return this.loading || (!this.pendingPlanId && (!this.selectedVisitType || isDateMissing || isPromoterMissing || isOutletMissing));
    },
  },
  mounted() {
    this.getVisitType();
    this.fetchPromoterLists();
  },
  methods: {
    async getVisitType() {
      const res = await this.$ApiServiceLayer.get(
        this.$PATH.RELATIVE_PATH.GET.VISIT_TYPE +
          "?p=" +
          this.$STORE.state.userConfig.selectedProject,
        this.$PATH.SERVICE_NAME.AUTH,
      );
      if (res.status === 200) {
        this.visitTypeList = pageRows(res.data);
      }
    },
    async fetchPromoterLists() {
      const res = await this.$ApiServiceLayer.get(
        this.$PATH.RELATIVE_PATH.MULTI.SUPERVISOR_LIST_CREATE +
          "?p=" +
          this.$STORE.state.userConfig.selectedProject +
          "&me=true",
        this.$PATH.SERVICE_NAME.AUTH,
      );
      if (res.status === 200) {
        this.promoterLists = pageRows(res.data);
      }
    },
    async submitHandler() {
      if (this.disableSubmitButton) return;
      this.loading = true;
      this.alert = false;
      try {
        if (!this.pendingPlanId) {
          const res = await this.$ApiServiceLayer.post(
            this.$PATH.RELATIVE_PATH.MULTI.CREATE_ACTION_PLAN +
              '?p=' + this.$STORE.state.userConfig.selectedProject,
            this.$PATH.SERVICE_NAME.AUTH,
            {
              project: this.$STORE.state.userConfig.selectedProject,
              actions: [{
                building_code: this.selectedOutletCode,
                expert_phone_number: this.selectedPromoter,
                ...(this.selectedVisitTurn ? { visit_turn: Number(this.selectedVisitTurn) } : {}),
                is_last_day: this.isLastDay,
              }],
              has_due_date: !this.disableDate,
              due_date: this.disableDate ? null : this.date,
              visit_type: this.selectedVisitType,
            },
          );
          const errors = res.data && Array.isArray(res.data.errors) ? res.data.errors : [];
          const created = res.data && Array.isArray(res.data.successfuls) ? res.data.successfuls[0] : null;
          if (res.status !== 200 || errors.length || !created || !created.id) {
            this.alertText = errors.length ? errorMessage({ status: res.status, data: errors }) : errorMessage(res);
            this.alert = true;
            return;
          }
          this.pendingPlanId = created.id;
        }
          const success = await this.$ApiServiceLayer.post(
            this.$PATH.RELATIVE_PATH.MULTI.BULK_UPDATE +
              "?p=" + this.$STORE.state.userConfig.selectedProject,
            this.$PATH.SERVICE_NAME.AUTH,
            {
              is_active: true,
              id: [this.pendingPlanId],
            },
          );
          if (success.status === 200) {
            this.successAlert = true;
            this.pendingPlanId = null;
            this.selectedOutletCode = '';
            this.selectedVisitTurn = null;
            this.isLastDay = false;
            this.date = '';
            this.disableDate = false;
            this.selectedVisitType = null;
            this.selectedPromoter = null;
          } else {
            this.alertText = errorMessage(success);
            this.alert = true;
          }
      } catch (error) {
        this.alertText = 'ارتباط برقرار نشد. دوباره تلاش کنید.';
        this.alert = true;
      } finally {
        this.loading = false;
      }
    },
  },
};
</script>
<style lang="scss" scoped>
.containers {
  padding: 24px;
  margin-top: 40px;
  border: 0;
  min-width: 0;
}
.pending-plan { margin: 16px 24px 0; padding: 12px; border-radius: 10px; background: #fff7e8; color: #754410; }
.field-label { display: block; margin: 0 0 8px; font-weight: 600; }
</style>
<style lang="scss">
.vpd-input-group {
  box-shadow: 0px 1px 2px 0px rgba(16, 24, 40, 0.05);
  height: 44px;
  background: #fff;
  label {
    width: 50px;
    border-radius: 0 8px 8px 0;
  }
  input {
    border-radius: 8px 0 0 8px;
  }
}
.input__styles {
  border-radius: 8px;
  border: 1px solid var(--Gray-300, #d0d5dd);
  background: var(--Base-White, #fff);
  box-shadow: 0px 1px 2px 0px rgba(16, 24, 40, 0.05);
  width: 100%;
  height: 44px;
  text-indent: 10px;
  margin-bottom: 32px;
}
.placeholder {
  color: #c1c1c1;
}
</style>
