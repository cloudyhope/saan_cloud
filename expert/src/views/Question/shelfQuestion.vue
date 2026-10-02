<template>
  <div>
    <BaseTopBar title="سوالات" />

    <FullLoading v-if="loading" />
    <v-alert v-if="requestError" type="error" outlined role="alert" class="mx-5 mt-4">{{ requestError }} <v-btn text color="error" @click="retryFailedAction">تلاش دوباره</v-btn></v-alert>
    <div class="containers">
      <v-card
        v-for="questions in listQuestions"
        :key="questions.question.id"
        class="mb-4 pa-4 quest-cards"
      >
        <div class="d-flex flex-column">
          <span class="quest-questions">{{ questions.question.text }}</span>
          <span class="desc">{{ questions.question.description }}</span>
          <span v-if="questions.submitted_answer.loading" class="answer-save-status" role="status">در حال ثبت پاسخ…</span>
        </div>

        <v-sheet
          v-for="answerType in questions.question.answer_params"
          :key="questions.question.id + answerType.answer_type.id"
        >
          <v-radio-group
            v-if="answerType.answer_type.name === 'YesNo'"
            v-model="questions.submitted_answer.bool"
            :disabled="questions.submitted_answer.loading"
            row
            @change="radioGroup(questions, answerType)"
          >
              <v-radio label="بله" :value="true"></v-radio>
            <v-radio label="خیر" :value="false"></v-radio>
          </v-radio-group>
          <v-radio-group
            v-if="answerType.answer_type.name === 'Triple'"
            v-model="questions.submitted_answer.bool"
            :disabled="questions.submitted_answer.loading"
            row
            @change="radioGroup(questions, answerType)"
          >
            <v-radio label="بله" :value="true"></v-radio>
            <v-radio label="خیر" :value="false"></v-radio>
            <v-radio label="ندارد" :value="null"></v-radio>
          </v-radio-group>
          <v-radio-group
            v-if="answerType.answer_type.name === 'Score'"
            v-model="questions.submitted_answer.score"
            :disabled="questions.submitted_answer.loading"
            row
            @change="radioGroup(questions, answerType)"
          >
            <v-radio class="perisan" label="۱" :value="1"></v-radio>
            <v-radio class="perisan" label="۲" :value="2"></v-radio>
            <v-radio class="perisan" label="۳" :value="3"></v-radio>
            <v-radio class="perisan" label="۴" :value="4"></v-radio>
            <v-radio class="perisan" label="۵" :value="5"></v-radio>
          </v-radio-group>
          <div
            class="texteara-div"
            v-if="answerType.answer_type.name === 'Description'"
          >
            <textarea
              class="textarea"
              :id="'answer-description-' + questions.question.id"
              :aria-label="'شرح پاسخ ' + questions.question.text"
              rows="5"
              v-model="questions.submitted_answer.description"
              :disabled="questions.submitted_answer.loading"
            ></textarea>
            <button
              @click="radioGroup(questions, answerType)"
              :disabled="questions.submitted_answer.loading"
              class="textarea-btn"
            >
              ثبت
            </button>
          </div>
          <div v-if="answerType.answer_type.name === 'Multichoice'">
            <div
              v-for="answersQus in questions.question.answer_choices"
              :key="answersQus.id"
            >
              <v-checkbox
                v-model="questions.submitted_answer.multichoice"
                :disabled="questions.submitted_answer.loading"
                :label="answersQus.answer"
                :value="answersQus.id"
                @change="validatorHandler(questions, answerType)"
              ></v-checkbox>
            </div>
            <div class="btn-container">
              <div class="err-container">
                <span class="err-message" v-if="answerType.showErr">
                  {{ (answerType.validation || {}).choice_count_error_msg_fa || 'تعداد گزینه‌های انتخابی معتبر نیست.' }}
                </span>
              </div>
              <button
                class="submit-btn"
                @click="radioGroup(questions, answerType)"
                :disabled="answerType.disabled || questions.submitted_answer.loading"
              >
                ثبت
              </button>
            </div>
          </div>
          <div class="quest-container">
            <div
              class="d-flex justify-space-between mb-2"
              v-if="answerType.answer_type.name === 'Input'"
            >
              <div class="input-question-container">
                <span v-if="questions.question.short_text !== null" class="ml-2"
                  >{{ questions.question.short_text }}:</span
                >
                <input
                  v-model="questions.submitted_answer.text"
                  :disabled="questions.submitted_answer.loading"
                  class="type-input"
                  type="text"
                  @input="validatorHandler(questions, answerType)"
                  :aria-label="questions.question.text"
                />
              </div>

              <button
                class="submit-btn"
                @click="radioGroup(questions, answerType)"
                :disabled="answerType.disabled || questions.submitted_answer.loading"
              >
                ثبت
              </button>
            </div>
            <span class="err-message" v-if="answerType.showErr">
              {{ (answerType.validation || {}).regex_error_msg_fa || 'مقدار واردشده معتبر نیست.' }}
            </span>
          </div>
          <v-radio-group
            v-if="answerType.answer_type.name === 'RadioChoice'"
            v-model="questions.submitted_answer.radio"
            :disabled="questions.submitted_answer.loading"
            @change="radioGroup(questions, answerType)"
          >
            <v-radio
              v-for="answersQus in questions.question.radio_choices"
              :key="answersQus.id + 'radios' + questions.question.id"
              :label="answersQus.answer"
              :value="answersQus"
            ></v-radio>
          </v-radio-group>
          <Multiselect
            v-if="answerType.answer_type.name === 'DropDownList'"
            :options="questions.question.dropdown_choices"
            @select="radioGroup(questions, answerType)"
            v-model="questions.submitted_answer.dropdown"
            :disabled="questions.submitted_answer.loading"
            :custom-label="customLabel"
            placeholder="لطفا یک مورد را انتخاب نمایید"
            selectLabel=""
            class="mt-4"
          >
          </Multiselect>
          <div
            class="number-container"
            v-if="answerType.answer_type.name === 'Number'"
          >
            <span class="number-text"
              >{{ questions.question.short_text }}:</span
            >
            <div class="input-contianer">
              <v-icon
                :disabled="questions.submitted_answer.loading"
                @click="increase(questions, answerType)"
                size="small"
                >mdi-plus</v-icon
              >
              <span
                v-if="
                  questions.submitted_answer.loading !== true &&
                  questions.submitted_answer.number !== null
                "
                class="mx-2"
                >{{ questions.submitted_answer.number }}</span
              ><span
                v-if="
                  questions.submitted_answer.loading !== true &&
                  questions.submitted_answer.number === null
                "
                class="mx-2"
                >0</span
              >
              <v-progress-circular
                :width="2"
                :size="10"
                indeterminate
                color="#c4c4c4"
                class="mx-3"
                v-if="questions.submitted_answer.loading"
              ></v-progress-circular>
              <v-icon
                :disabled="questions.submitted_answer.loading || questions.submitted_answer.number <= 0"
                @click="decrease(questions, answerType)"
                size="small"
                >mdi-minus</v-icon
              >
            </div>
          </div>
          <!-- <input
              type="number"
              class="number-input"
              v-model="questions.submitted_answer.number"
              @change="radioGroup(questions, answerType)"
            /> -->
        </v-sheet>
      </v-card>
    </div>
    <EmptyContainer />
    <!-- <OverlayButton
      @click="saveBtn"
      title="ذخیره اطلاعات"
      :disabled="disableSaveBtn"
    /> -->
  </div>
</template>

<script>
import OverlayButton from "../../components/Button/overlayButton.vue";
import EmptyContainer from "../../components/emptyContainer.vue";
import BaseTopBar from "@/components/Topbar/BaseTopbar.vue";
import FullLoading from "../../components/Loading/fullLoading.vue";
import Multiselect from "vue-multiselect";

export default {
  name: "Profile",
  components: {
    OverlayButton,
    EmptyContainer,
    BaseTopBar,
    FullLoading,
    Multiselect,
  },
  data() {
    return {
      listQuestions: [],
      answerType: [],
      switch1: [[]],
      visitId: null,
      loading: false,
      requestError: '',
      pendingRetry: null,
      disableSaveBtn: false,
      minesBtn: false,
      plusBtn: false,
      timer: null,
      title: null,
      max: 99,
      latitude: null,
      longitude: null,
    };
  },

  mounted() {
    this.getQuestion();
  },
  created() {
    // const success = (position) => {
    //   this.latitude = position.coords.latitude;
    //   this.longitude = position.coords.longitude;
    // };

    // const error = (err) => {
    //   err;
    // };
    // navigator.geolocation.getCurrentPosition(success, error);
  },
  methods: {
    regexValidatorHandler(questions, answerType) {
      const pattern = answerType.validation && answerType.validation.regex;
      if (!pattern) return false;
      try { return !new RegExp(pattern).test(questions.submitted_answer.text || ''); }
      catch (_) { return false; }
    },
    periodValidatorHandler(questions, answerType) {
      const rules = answerType.validation || {};
      const count = (questions.submitted_answer.multichoice || []).length;
      return [rules.min_choice_count != null && count < rules.min_choice_count,
        rules.max_choice_count != null && count > rules.max_choice_count];
    },
    validatorHandler(i, x) {
      let regval = false;
      let periodval = [false, false];
      if (x.answer_type.name === "Input") {
        regval = this.regexValidatorHandler(i, x);
      }
      if (x.answer_type.name === "Multichoice") {
        periodval = this.periodValidatorHandler(i, x);
      }
      x.disabled = !(!regval && !periodval[0] && !periodval[1]);
      x.showErr = x.disabled;
    },
    customLabel({ id, answer }) {
      return `${answer}`;
    },
    increase(questions, answerType) {
      questions.submitted_answer.number = questions.submitted_answer.number + 1;
      this.radioGroup(questions, answerType);
    },
    decrease(questions, answerType) {
      questions.submitted_answer.number = questions.submitted_answer.number - 1;
      this.radioGroup(questions, answerType);
    },
    async getQuestion() {
      this.visitId = this.$route.params.id;
      const type = this.$route.params.type;
      this.loading = true;
      this.requestError = '';
      this.pendingRetry = null;
      try {
        const res = await this.$ApiServiceLayer.get(
          this.$PATH.RELATIVE_PATH.GET.GET_QUESTIONS + this.visitId +
            '/?question_type=' + encodeURIComponent(type) + '&p=' +
            this.$STORE.state.userConfig.selectedProject,
          this.$PATH.SERVICE_NAME.AUTH
        );
        if (res.status !== 200 || !Array.isArray(res.data)) {
          this.requestError = 'دریافت پرسش‌ها ممکن نشد. دوباره تلاش کنید.';
          return;
        }
        this.listQuestions = res.data;
        for (const row of this.listQuestions) {
          row.submitted_answer.loading = false;
          for (const param of row.question.answer_params) {
            param.disabled = true;
            param.showErr = false;
          }
          if (row.submitted_answer.id == null) row.submitted_answer.bool = undefined;
        }
      } catch (_) {
        this.requestError = 'دریافت پرسش‌ها ممکن نشد. اتصال اینترنت را بررسی کنید.';
      } finally {
        this.loading = false;
      }
    },
    retryFailedAction() {
      if (this.pendingRetry) this.radioGroup(this.pendingRetry.questions, this.pendingRetry.answerType);
      else this.getQuestion();
    },
    async radioGroup(questions, answerType) {
      if (questions.submitted_answer.loading) return;
      this.requestError = '';
      this.pendingRetry = null;
      questions.submitted_answer.loading = true;
      const data = {
        visit: this.visitId,
        question: questions.question.id,
        longitude: this.longitude,
        latitude: this.latitude,
      };
      if (
        typeof questions.submitted_answer[answerType.answer_type.field] ===
          "object" &&
        typeof questions.submitted_answer[answerType.answer_type.field] !==
          null &&
        answerType.answer_type.name !== "Multichoice" &&
        answerType.answer_type.name !== "Triple"
      ) {
        data[answerType.answer_type.field] =
          questions.submitted_answer[answerType.answer_type.field].id;
      } else {
        data[answerType.answer_type.field] =
          questions.submitted_answer[answerType.answer_type.field];
      }

      try {
        const res = await this.$ApiServiceLayer.post(
          this.$PATH.RELATIVE_PATH.POST.POST_QUESTIONS + '?p=' + this.$STORE.state.userConfig.selectedProject,
          this.$PATH.SERVICE_NAME.AUTH, data
        );
        if (res.status !== 200) {
          this.requestError = 'پاسخ ثبت نشد. مقدار را بررسی کنید و دوباره بفرستید.';
          this.pendingRetry = { questions, answerType };
          return;
        }
        if (res.data && res.data.id) questions.submitted_answer.id = res.data.id;
      } catch (_) {
        this.requestError = 'پاسخ ثبت نشد. اتصال اینترنت را بررسی کنید و دوباره تلاش کنید.';
        this.pendingRetry = { questions, answerType };
      } finally {
        questions.submitted_answer.loading = false;
      }
    },
    saveBtn() {
      this.$router.push({ name: "storeDetail" });
    },
  },
};
</script>
<style>
.containers {
  margin: 12px 24px;
}
.v-input--radio-group.v-input--radio-group--row .v-radio {
  margin: 0 !important;
}
.v-icon.v-icon {
  font-size: 16px;
}
.perisan {
}
.texteara-div {
  display: inline-block;
  position: relative;
  border: 1px solid #cdcdcd;
  width: 100%;
}
.type-input {
  height: 30px;
  border-radius: 4px;
  text-indent: 5px;
  width: 75%;
  border: 1px solid #d9d9d9;
}
.textarea-btn {
  position: absolute;
  bottom: 10px;
  left: 10px;
  background: #357AE1;
  color: #fff;
  padding: 5px;
  border-radius: 8px;
  width: 60px;
}
.input-question-container {
  width: 100%;
}

.textarea {
  display: block;
  width: 100%;
}
.submit-btn {
  display: flex;
  justify-content: center;
  align-items: center;
  background: #357AE1;
  border-radius: 8px;
  color: #fff;
  width: 60px;
  height: 30px;
  margin-bottom: 10px;
}
.btn-container {
  width: 100%;
  display: flex;
  margin-bottom: 10px;
  align-items: center;
}
.quest-container {
  width: 100%;
  display: flex;
  flex-direction: column;
}
.err-container {
  width: 90%;
}
.err-message {
  color: #ff2f2f;
}
.number-input {
  border: 1px solid #c4c4c4;
  border-radius: 2px;
  width: 50px;
}
.number-container {
  display: flex;
  align-items: center;
  width: 100%;
  margin-top: 10px;
}
.number-text {
  width: 30%;
  font-size: 14px;
}
.quest-cards {
  box-shadow: 0px 4px 4px rgba(214, 214, 214, 0.6) !important;
}
.quest-questions {
  font-size: 14px;
  margin-bottom: 4px;
}
.desc {
  font-size: 10px;
  color: #c4c4c4;
}

.input-contianer {
  border: 1px solid #c4c4c4;
  display: flex;
  align-items: center;
  justify-content: space-evenly;
  border-radius: 2px;
  padding: 2px;
  width: 80px;
  height: 30px;
  border-radius: 4px;
}
.submit-btn[disabled] {
  background: #cec4c4;
}
.answer-save-status { color: #236180; font-size: 12px; margin-top: 5px; }
</style>
<style>
.v-input__slot {
  background: #fff !important;
}
.v-application--is-rtl .v-input--selection-controls__input {
  margin-left: 0 !important;
}
.multiselect {
  text-align: right !important;
}
.multiselect__content {
  padding-left: 0 !important;
}
.multiselect__option--highlight {
  background: #357AE1 !important;
}
.multiselect__select {
  display: none !important;
}
.multiselect__tags {
  padding: 8px 20px 0 8px !important;
}
</style>
<style src="vue-multiselect/dist/vue-multiselect.min.css"></style>
