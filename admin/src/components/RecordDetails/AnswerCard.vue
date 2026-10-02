<template>
  <article class="answer-card">
    <div class="answer-card-heading">
      <span class="question-number">{{ index + 1 }}</span>
      <div class="question-copy">
        <h3>{{ question.text || question.short_text || 'سؤال' }}</h3>
        <p v-if="question.description">{{ question.description }}</p>
      </div>
      <button
        v-if="editable"
        type="button"
        class="icon-action"
        :aria-label="'ویرایش پاسخ: ' + question.text"
        @click="$emit('edit', answer)"
      >
        <ActionIcon name="edit" />
      </button>
    </div>
    <div class="answer-values">
      <div
        v-for="type in question.answer_type"
        :key="type.id"
        class="answer-value"
        :class="{
          'answer-description': type.name === 'Description',
          'answer-missing': value(type.name) === 'پاسخ ثبت نشده',
        }"
      >
        <span class="answer-type-label">{{ labels[type.name] || type.name }}</span>
        <span v-if="type.name === 'Score'" class="answer-stars" aria-hidden="true"
          ><span v-for="star in 5" :key="star" :class="{ filled: star <= answer.score }"
            >★</span
          ></span
        >
        <span class="answer-text">{{ value(type.name) }}</span>
      </div>
      <p v-if="!question.answer_type || !question.answer_type.length" class="detail-muted">
        نوع پاسخ مشخص نشده است.
      </p>
    </div>
  </article>
</template>
<script>
import { questionOf, answerValue } from '@/utils/detailValues';
export default {
  props: { answer: { type: Object, required: true }, index: Number, editable: Boolean },
  data: () => ({
    labels: {
      YesNo: 'بله / خیر',
      Triple: 'سه‌حالته',
      Score: 'امتیاز',
      RadioChoice: 'انتخاب گزینه',
      DropDownList: 'انتخاب از فهرست',
      Multichoice: 'چند انتخابی',
      Input: 'پاسخ کوتاه',
      Description: 'توضیحات',
      Number: 'عدد',
      Price: 'مبلغ',
    },
  }),
  computed: {
    question() {
      return questionOf(this.answer);
    },
  },
  methods: {
    value(type) {
      return answerValue(this.answer, type);
    },
  },
};
</script>
