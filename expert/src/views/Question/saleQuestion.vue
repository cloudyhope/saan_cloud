<template>
  <div>
    <Topbar title="ثبت اطلاعات" />
    <FullLoading v-if="loading" />
    <div class="containers">
      <v-card
        v-for="questions in listQuestions"
        :key="questions.question.id"
        elevation="0"
        class="mb-4 pa-4"
      >
        <span>{{ questions.question.text }}</span>
        <v-sheet
          v-for="answerType in questions.question.answer_type"
          :key="questions.question.id + answerType.id"
        >
          <v-radio-group
            v-if="answerType.name === 'YesNo'"
            v-model="questions.submitted_answer.bool"
            row
            @change="radioGroup(questions, answerType)"
          >
            <v-radio label="بله" :value="true"></v-radio>
            <v-radio label="خیر" :value="false"></v-radio>
          </v-radio-group>
          <v-radio-group
            v-if="answerType.name === 'Score'"
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
          <v-radio-group
            v-if="answerType.name === 'Triple'"
            v-model="questions.submitted_answer.bool"
            row
            @change="radioGroup(questions, answerType)"
          >
            <v-radio label="بله" :value="true"></v-radio>
            <v-radio label="خیر" :value="false"></v-radio>
            <v-radio label="ندارد" :value="null"></v-radio>
          </v-radio-group>
          <div class="texteara-div" v-if="answerType.name === 'Description'">
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
          <div v-if="answerType.name === 'Multichoice'">
            <div
              v-for="answersQus in questions.question.answer_choices"
              :key="answersQus.id"
            >
              <v-checkbox
                v-model="questions.submitted_answer.multichoice"
                :label="answersQus.answer"
                :value="answersQus.id"
                :disabled="
                  questions.submitted_answer.multichoice.length >= max &&
                  questions.submitted_answer.multichoice.indexOf(
                    answersQus.id
                  ) == -1
                "
              ></v-checkbox>
            </div>
            <div class="btn-container">
              <button
                class="submit-btn"
                @click="radioGroup(questions, answerType)"
                :disabled=" questions.submitted_answer.multichoice.length < 1 "
              >
                ثبت
              </button>
            </div>
          </div>
        </v-sheet>
      </v-card>
    </div>
    <EmptyContainer />
    <OverlayButton
      @click="saveBtn"
      title="ذخیره اطلاعات"
      :disabled="disableSaveBtn"
    />
  </div>
</template>

<script>
import OverlayButton from "../../components/Button/overlayButton.vue";
import EmptyContainer from "../../components/emptyContainer.vue";
import Topbar from "../../components/Topbar/backTopBar.vue";
import FullLoading from "../../components/Loading/fullLoading.vue";

export default {
  name: "Profile",
  components: {
    OverlayButton,
    EmptyContainer,
    Topbar,
    FullLoading,
  },
  data() {
    return {
      listQuestions: [],
      answerType: [],
      switch1: [[]],
      visitId: null,
      loading: false,
      disableSaveBtn: false,
      max: 3,
    };
  },

  mounted() {
    this.getQuestion();
  },
  computed: {
    disabled() {
      if (this.selected.length === 3) {
        return true;
      } else {
        return false;
      }
    },
  },
  methods: {
    async getQuestion() {
      const url = window.location.href;
      this.visitId = url.split("/").slice(-1)[0];
      const type = url.split("/").slice(-2)[0];

      const res = await this.$ApiServiceLayer.get(
        this.$PATH.RELATIVE_PATH.GET.GET_QUESTIONS +
          this.visitId +
          "/?type=" +
          type +
          "&p=" + this.$STORE.state.userConfig.selectedProject,
        this.$PATH.SERVICE_NAME.AUTH
      );
      if (res.status === 200) {
        (res.data);
        this.listQuestions = res.data;
        for (let i of this.listQuestions) {
          if (i.submitted_answer.id == null) {
              i.submitted_answer.bool = undefined
            }
          let tmp = [];
          for (let j of i.question.answer_type) {
            tmp.push(null);
          }
          this.switch1.push(tmp);
        }
        // const response = await this.$ApiServiceLayer.get(
        //   this.$PATH.RELATIVE_PATH.GET.VISIT_PAGE_SETTING + this.visitId,
        //   this.$PATH.SERVICE_NAME.AUTH
        // );
        // if (response.status === 200) {
        //   for (let i of response.data.questions) {
        //     if (i.question_type === type) {
        //       this.disableSaveBtn = !i.status;
        //     }
        //   }
        // }
      }
    },
    async radioGroup(questions, answerType) {
      this.loading = true;
      const data = {
        visit: this.visitId,
        question: questions.question.id,
      };
      // data[answerType.field] =
      //   this.switch1[this.listQuestions.indexOf(questions)][
      //     questions.question.answer_type.indexOf(answerType)
      //   ];

      data[answerType.field] = questions.submitted_answer[answerType.field];

      (data);
      const res = await this.$ApiServiceLayer.post(
        this.$PATH.RELATIVE_PATH.POST.POST_QUESTIONS + "?p=" + this.$STORE.state.userConfig.selectedProject,
        this.$PATH.SERVICE_NAME.AUTH,
        data
      );
      (res);
      if (res.status === 200) {
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
  margin-bottom: 10px;
}
.submit-btn[disabled] {
  background: #cec4c4;
}
.btn-container {
  width: 100%;
  display: flex;
  justify-content: flex-end;
}
</style>
