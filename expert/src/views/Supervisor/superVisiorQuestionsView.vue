<template>
    <div>
      <Topbar title="سوالات" />
      <FullLoading v-if="loading" />
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
              :disabled = true
            >
              <v-radio label="بله" :value="true"></v-radio>
              <v-radio label="خیر" :value="false"></v-radio>
            </v-radio-group>
            <v-radio-group
              v-if="answerType.answer_type.name === 'Triple'"
              v-model="questions.submitted_answer.bool"
              row
              @change="radioGroup(questions, answerType)"
              :disabled = true

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
              :disabled = true

            >
              <v-radio label="۱" :value="1"></v-radio>
              <v-radio label="۲" :value="2"></v-radio>
              <v-radio label="۳" :value="3"></v-radio>
              <v-radio label="۴" :value="4"></v-radio>
              <v-radio label="۵" :value="5"></v-radio>
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
              :disabled = true
              ></textarea>
              <button
                @click="radioGroup(questions, answerType)"
                class="textarea-btn"
              :disabled = true

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
              :disabled = true

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
                  :disabled = true
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
                <input
                  v-model="questions.submitted_answer.text"
                  class="type-input"
                  type="text"
                  @input="validatorHandler(questions, answerType)"
              :disabled = true
                />
                <button
                  class="submit-btn"
                  @click="radioGroup(questions, answerType)"
                  :disabled = true

                >
                  ثبت
                </button>
              </div>
              <span class="err-message" v-if="answerType.showErr">
                {{ answerType.validation.regex_error_msg_fa }}
              </span>
            </div>
            <v-radio-group
              v-if="answerType.answer_type.name === 'RadioChoice'"
              v-model="questions.submitted_answer.radio"
              @change="radioGroup(questions, answerType)"
              :disabled = true

            >
              <v-radio
                v-for="answersQus in questions.question.radio_choices"
                :key="answersQus.id + 'radios' + questions.question.id"
                :label="answersQus.answer"
                :value="answersQus"
              :disabled = true

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
              :disabled = true
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
                :disabled = true
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
                :disabled = true

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
  import Topbar from "../../components/Topbar/backPrps.vue";
  import FullLoading from "../../components/Loading/fullLoading.vue";
  import Multiselect from "vue-multiselect";
  
  export default {
    name: "Profile",
    components: {
      OverlayButton,
      EmptyContainer,
      Topbar,
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
        disableSaveBtn: false,
        minesBtn: false,
        plusBtn: false,
        timer: null,
        title: null,
        max: 99,
      };
    },
  
    mounted() {
      this.getQuestion();
    },
  
    methods: {
      regexValidatorHandler(questions, answerType) {
        (answerType);
        let regexVal = answerType.validation.regex;
        if (answerType.validation.regex !== null) {
          if (questions.submitted_answer.text !== null) {
            let x = questions.submitted_answer.text.match(new RegExp(regexVal));
            ("x", x);
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
            minCountDisabled = true;
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
        return [minCountDisabled, maxCountDisabled];
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
        (questions);
        questions.submitted_answer.number = questions.submitted_answer.number + 1;
        this.radioGroup(questions, answerType);
      },
      decrease(questions, answerType) {
        questions.submitted_answer.number = questions.submitted_answer.number - 1;
        this.radioGroup(questions, answerType);
      },
      async getQuestion() {
        const url = window.location.href;
        this.visitId = url.split("/").slice(-1)[0];
        const type = url.split("/").slice(-2)[0];
  
        const res = await this.$ApiServiceLayer.get(
          this.$PATH.RELATIVE_PATH.GET.GET_QUESTIONS +
            this.visitId +
            "/" +
            "?question_type=" +
            type +
            "&p=" +
            this.$STORE.state.userConfig.selectedProject,
          this.$PATH.SERVICE_NAME.AUTH
        );
        if (res.status === 200) {
          ("ld", res.data);
          this.listQuestions = res.data;
          for (let i of this.listQuestions) {
            i.submitted_answer.loading = false;
            for (let x of i.question.answer_params) {
              // x.disabled = this.regexValidatorHandler(i,x)
              // this.validatorHandler(i,x)
              x.disabled = true;
              x.showErr = false;
            }
            if (i.submitted_answer.id == null) {
              i.submitted_answer.bool = undefined;
            }
          }
        }
      },
      async radioGroup(questions, answerType) {
        ("ld", questions, answerType);
        this.loading = true;
        questions.submitted_answer.loading = true;
        this.minesBtn = true;
        this.plusBtn = true;
        const data = {
          visit: this.visitId,
          question: questions.question.id,
        };
        ("md", questions.submitted_answer[answerType.answer_type.field]);
        if (
          typeof questions.submitted_answer[answerType.answer_type.field] === "object" &&
          typeof questions.submitted_answer[answerType.answer_type.field] !== null &&
          answerType.answer_type.name !== "Multichoice" &&
          answerType.answer_type.name !== "Triple"
        ) {
          data[answerType.answer_type.field] =
            questions.submitted_answer[answerType.answer_type.field].id;
        } else {
          data[answerType.answer_type.field] = questions.submitted_answer[answerType.answer_type.field];
        }
  
        const res = await this.$ApiServiceLayer.post(
          this.$PATH.RELATIVE_PATH.POST.POST_QUESTIONS + "?p=" + this.$STORE.state.userConfig.selectedProject,
          this.$PATH.SERVICE_NAME.AUTH,
          data
        );
        (res);
        if (res.status === 200) {
          questions.submitted_answer.loading = true;
          this.plusBtn = false;
          this.loading = false;
          this.getQuestion();
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
