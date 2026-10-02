<template>
  <div>
    <BaseTopBar title="سوالات" />

    <FullLoading v-if="loading" />
    <div class="question-tools">
      <button type="button" class="location-button" @click="captureLocation">{{ locationLabel }}</button>
      <p v-if="answerError" class="answer-error" role="alert">{{ answerError }}</p>
    </div>
    <div class="containers">
      <v-card
        v-for="questions in listQuestions"
        :key="questions.question.id"
        class="mb-4 pa-4 quest-cards"
      >
        <div class="d-flex flex-column">
          <span class="quest-questions">{{ questions.question.text }}</span>
          <span class="desc">{{ questions.question.description }}</span>
        </div>
        <v-sheet
          v-for="answerType in questions.question.answer_params"
          :key="questions.question.id + answerType.answer_type.id"
        >
          <v-radio-group
            v-if="answerType.answer_type.name === 'YesNo'"
            v-model="questions.submitted_answer.bool"
            row
            @change="radioGroup(questions, answerType)"
          >
            <v-radio label="بله" :value="true"></v-radio>
            <v-radio label="خیر" :value="false"></v-radio>
          </v-radio-group>
          <v-radio-group
            v-if="answerType.answer_type.name === 'Triple'"
            v-model="questions.submitted_answer.bool"
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
              id="txt"
              rows="5"
              v-model="questions.submitted_answer.description"
            ></textarea>
            <button
              @click="radioGroup(questions, answerType)"
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
                :label="answersQus.answer"
                :value="answersQus.id"
                @change="validatorHandler(questions, answerType)"
              ></v-checkbox>
            </div>
            <div class="btn-container">
              <div class="err-container">
              <span class="err-message" v-if="answerType.showErr">
                {{ answerType.validation.choice_count_error_msg_fa }}
              </span>
            </div>
              <button
                class="submit-btn"
                @click="radioGroup(questions, answerType)"
                :disabled=" answerType.disabled"
              >
                ثبت
              </button>
            </div>
          </div>

          <v-radio-group
            v-if="answerType.answer_type.name === 'RadioChoice'"
            v-model="questions.submitted_answer.radio"
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
            :custom-label="customLabel"
            placeholder="لطفا یک مورد را انتخاب نمایید"
            selectLabel=""
            class="mt-4"
          >
          </Multiselect>

          <!-- <div v-if="answerType.name === 'RadioChoice'">
            <div
              v-for="answersQus in questions.question.answer_choices"
              :key="answersQus.id"
            >
              <v-radio-group
                v-model="questions.submitted_answer.radioChoice"
                :label=""
                :value="answersQus.id"
               
              ></v-radio-group>
            </div>
            <div class="btn-container">
              
            </div>
          </div> -->
          <div
            class="d-flex justify-space-between mt-2"
            v-if="answerType.answer_type.name === 'Input'"
          >
          
            <div class="quest-container">
              <div class="d-flex justify-space-between mb-2">
                <div class="input-question-container">
              <span v-if="questions.question.short_text !== null" class="ml-2"
              >{{ questions.question.short_text }}:</span
            >
              <input
                v-model="questions.submitted_answer.text"
                class="type-input"
                type="text"
                @input="validatorHandler(questions, answerType)"
              />
            </div>
                
                <button
                  class="submit-btn"
                  @click="radioGroup(questions, answerType)"
                  :disabled="answerType.disabled"
                >
                  ثبت
                </button>
              </div>
              <span class="err-message" v-if="answerType.showErr">
                {{ answerType.validation.regex_error_msg_fa }}
              </span>
            </div>
          </div>

          <div
            class="number-container"
            v-if="answerType.answer_type.name === 'Number'"
          >
            <span class="number-text"
              >{{ questions.question.short_text }}:</span
            >
            <div class="input-contianer">
              <v-icon
                :disabled="plusBtn"
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
                :disabled="questions.submitted_answer.number <= 0"
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
      @click="$router.go(-1)"
      title="ذخیره اطلاعات"
      :disabled="disableSaveBtn"
    /> -->
  </div>
</template>

<script>
import OverlayButton from "../../components/Button/overlayButton.vue";
import EmptyContainer from "../../components/emptyContainer.vue";
import Topbar from "../../components/Topbar/backPrps.vue";
import FullLoading from "../../components/Loading/fullLoading.vue";
import Multiselect from "vue-multiselect";
import BaseTopBar from "@/components/Topbar/BaseTopbar.vue";
export default {
  name: "Profile",
  components: {
    OverlayButton,
    EmptyContainer,
    Topbar,
    FullLoading,
    Multiselect,
    BaseTopBar
  },
  data() {
    return {
      listQuestions: [],
      answerType: [],
      switch1: [[]],
      surveyId: null,
      loading: false,
      disableSaveBtn: false,
      minesBtn: false,
      plusBtn: false,
      timer: null,
      title: null,
      max: 99,
      inputTextErr: "",
      inputSnackbar: false,
      latitude: null,
      longitude: null,
      locationLabel: 'افزودن موقعیت (اختیاری)',
      answerError: '',
      // minCountDisabled: Boolean,
      // maxCountDisabled: Boolean,
    };
  },
  mounted() {
    this.getQuestion();
  },
  methods: {
    captureLocation() {
      if (!navigator.geolocation) {
        this.locationLabel = 'موقعیت مکانی در این دستگاه در دسترس نیست';
        return;
      }
      this.locationLabel = 'در حال دریافت موقعیت…';
      navigator.geolocation.getCurrentPosition(
        position => {
          this.latitude = position.coords.latitude;
          this.longitude = position.coords.longitude;
          this.locationLabel = 'موقعیت ثبت شد';
        },
        () => { this.locationLabel = 'دسترسی به موقعیت داده نشد؛ تلاش دوباره'; },
        { timeout: 10000, maximumAge: 60000 }
      );
    },
    regexValidatorHandler(questions, answerType) {
      (answerType)
      let regexVal = answerType.validation.regex;
      if (answerType.validation.regex !== null) {
        if (questions.submitted_answer.text !== null) {
          let x = questions.submitted_answer.text.match(new RegExp(regexVal));
          ('x',x)
          if (x !== null) {
            // answerType.disabled = false;
            return false;
          } else {
            // answerType.disabled = true;
            return true;
          }
        } else {
          // answerType.disabled = true;
          return true;
        }
      } else {
        // answerType.disabled = false;
        return false;
      }
    },
    periodValidatorHandler(questions, answerType) {
      let minVal = answerType.validation.min_choice_count;
      let maxVal = answerType.validation.max_choice_count;
      var maxCountDisabled = false;
      var minCountDisabled = false;

      if (answerType.validation.min_choice_count !== null) {
        if (minVal <= questions.submitted_answer.multichoice.length) {

          // answerType.disabled = false;
          minCountDisabled = false;
        } else {
          // answerType.disabled = true;
         minCountDisabled =true;
        }
      } else {
        // answerType.disabled = true;
        minCountDisabled = true;
      }
      if (answerType.validation.max_choice_count !== null) {
        if (maxVal >= questions.submitted_answer.multichoice.length) {
          // answerType.disabled = false;
          maxCountDisabled = false;
        } else {
          // answerType.disabled = true;
          maxCountDisabled = true;
        }
      } else {
        // answerType.disabled = true;
        maxCountDisabled = true;
      }
      // if (minCountDisabled === false && maxCountDisabled === false) {
      //   answerType.disabled = false;
      // } else {
      //   answerType.disabled = true;
      // }
      return [minCountDisabled, maxCountDisabled]
    },
    customLabel({ id, answer }) {
      return `${answer}`;
    },
    increase(questions, answerType) {
      (questions);
      questions.submitted_answer.number = questions.submitted_answer.number + 1;
      this.radioGroup(questions, answerType);
    },
    decrease(questions, answerType) {
      questions.submitted_answer.number = questions.submitted_answer.number - 1;
      this.radioGroup(questions, answerType);
    },
    validatorHandler(i,x) {
      let regval = false;
            let periodval = [false,false];
            if (x.answer_type.name === 'Input'){
              regval = this.regexValidatorHandler(i, x);
          }
          if (x.answer_type.name === 'Multichoice'){

            periodval = this.periodValidatorHandler(i, x);
          }
            x.disabled = !(!regval && !periodval[0] && !periodval[1])
            x.showErr = x.disabled;
    },
    async getQuestion() {
      const url = window.location.href;
      this.surveyId = url.split("/").slice(-2)[0];
      const id = url.split("/").slice(-1)[0];

      const res = await this.$ApiServiceLayer.get(
        this.$PATH.RELATIVE_PATH.GET.SURVEY_QUESTIONS +
          this.surveyId +
          "/" +
          "?survey_question_type=" +
          id +
          "&p=" +
          this.$STORE.state.userConfig.selectedProject,
        this.$PATH.SERVICE_NAME.AUTH
      );
      if (res.status === 200) {
        (res.data);
        this.listQuestions = res.data;

        for (let i of this.listQuestions) {
          i.submitted_answer.loading = false;
          if (i.submitted_answer.id == null) {
            i.submitted_answer.bool = undefined;
          }
          for (let x of i.question.answer_params) {
            // x.disabled = this.regexValidatorHandler(i,x)
          // this.validatorHandler(i,x)
          x.disabled = true;
          x.showErr = false;
          }
          for (let q of i.question.dropdown_choices) {
            q.name = q.answer;
          }
        }
      }
    },
    async radioGroup(questions, answerType) {
      if (questions.submitted_answer.loading) return;
      this.answerError = '';
      this.loading = true;
      questions.submitted_answer.loading = true;
      this.minesBtn = true;
      this.plusBtn = true;
      const data = {
        survey_fill_out: parseInt(this.surveyId),
        survey_question: questions.question.id,
        longitude:this.longitude,
        latitude:this.latitude,
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
          this.$PATH.RELATIVE_PATH.POST.POST_SURVEY_QUESTIONS,
          this.$PATH.SERVICE_NAME.AUTH,
          data
        );
        if (res.status === 200) {
          await this.getQuestion();
        } else {
          this.answerError = 'پاسخ ذخیره نشد. دوباره تلاش کنید.';
        }
      } catch (error) {
        this.answerError = 'ارتباط برقرار نشد. پاسخ را دوباره ثبت کنید.';
      } finally {
        questions.submitted_answer.loading = false;
        this.plusBtn = false;
        this.minesBtn = false;
        this.loading = false;
      }
    },

    saveBtn() {
      this.$router.push({ name: "surveyDetail" });
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
  margin-top: 10px;
}

.textarea-btn {
  position: absolute;
  bottom: 10px;
  left: 10px;
  background: #357AE1;
  color: #fff;
  padding: 5px;
  border-radius: 2px;
  width: 60px;
}
.quest-container {
  width: 100%;
  display: flex;
  flex-direction: column;
}
.quest-cards {
  box-shadow: 0px 0px 3px 0px rgba(16, 24, 40, 0.1) !important;

}
.quest-questions {
  font-size: 14px;
  margin-bottom: 4px;
}
.desc {
  font-size: 10px;
  color: #c4c4c4;
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
  border-radius: 4px;
  color: #fff;
  width: 60px;
  height: 30px;
}
.btn-container {
  width: 100%;
  display: flex;
  margin-bottom: 10px;
  align-items: center;
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
.type-input {
  height: 30px;
  border-radius: 4px;
  text-indent: 5px;
  width: 75%;
  border: 1px solid #d9d9d9;
}
.number-container {
  display: flex;
  align-items: center;
  width: 100%;
  margin-top: 10px;
}
.number-text {
  width: 20%;
  font-size: 14px;
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
.input-question-container {
  width: 100%;
}
</style>
<style>
.question-tools { margin: 12px 24px; }
.location-button { min-height: 44px; padding: 8px 14px; border: 1px solid #357ae1; border-radius: 10px; color: #1754a2; background: #fff; }
.location-button:focus-visible { outline: 3px solid #1754a2; outline-offset: 2px; }
.answer-error { margin-top: 8px; color: #ad2031; }
.v-application--is-rtl .v-input--selection-controls__input {
  margin-left: 0 !important;
}
.v-input {
  text-align: right !important;
}
</style>
<style src="vue-multiselect/dist/vue-multiselect.min.css"></style>
