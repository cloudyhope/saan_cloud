<template>
  <div class="answer-input" :class="'kind-' + kind">
    <!-- Yes / No (and the three-way variant) save on tap -->
    <div v-if="kind === 'YesNo' || kind === 'Triple'" class="segmented" role="radiogroup" :aria-label="label">
      <button v-for="option in boolOptions" :key="String(option.value)" type="button" role="radio"
              class="segment" :class="['tone-' + option.tone, { selected: isBool(option.value) }]"
              :aria-checked="isBool(option.value) ? 'true' : 'false'" :disabled="locked"
              @click="emit({ bool: option.value })">
        <v-icon size="19">{{ option.icon }}</v-icon>{{ option.title }}
      </button>
    </div>

    <div v-else-if="kind === 'Score'" class="score-row" role="radiogroup" :aria-label="label">
      <button v-for="score in 5" :key="score" type="button" role="radio" class="score"
              :class="{ selected: answer.score === score }" :aria-checked="answer.score === score ? 'true' : 'false'"
              :aria-label="'امتیاز ' + score" :disabled="locked" @click="emit({ score })">{{ fa(score) }}</button>
      <div class="score-scale" aria-hidden="true"><span>ضعیف</span><span>عالی</span></div>
    </div>

    <div v-else-if="kind === 'Number'" class="number-row">
      <button type="button" class="step-btn" aria-label="افزودن" :disabled="locked || (maxValue !== null && numberDraft >= maxValue)" @click="bump(1)"><v-icon size="22">mdi-plus</v-icon></button>
      <input class="number-field" inputmode="numeric" :aria-label="label" :value="numberText" :disabled="locked"
             :placeholder="readonly ? 'بدون پاسخ' : 'عدد'" @input="typeNumber($event.target.value)" @blur="commitNumber" @keydown.enter.prevent="commitNumber" />
      <button type="button" class="step-btn" aria-label="کم کردن" :disabled="locked || numberDraft === null || numberDraft <= minValue" @click="bump(-1)"><v-icon size="22">mdi-minus</v-icon></button>
      <span v-if="question.short_text" class="number-unit">{{ question.short_text }}</span>
    </div>

    <div v-else-if="kind === 'Price'" class="inline-field">
      <div class="money"><input inputmode="numeric" :aria-label="label" :value="priceText" :disabled="locked"
                                :placeholder="readonly ? 'بدون پاسخ' : 'مبلغ'" @input="typePrice($event.target.value)" @keydown.enter.prevent="savePrice" /><span>ریال</span></div>
      <button v-if="!readonly" type="button" class="save-btn" :disabled="locked || !priceDirty" @click="savePrice">ثبت</button>
    </div>

    <div v-else-if="kind === 'Input'" class="inline-field">
      <input class="text-field" :aria-label="label" :value="textDraft" :disabled="locked" :maxlength="maxLength || 255"
             :placeholder="readonly ? 'بدون پاسخ' : 'پاسخ کوتاه'" @input="textDraft = $event.target.value" @keydown.enter.prevent="saveText" />
      <button v-if="!readonly" type="button" class="save-btn" :disabled="locked || !textDirty" @click="saveText">ثبت</button>
    </div>

    <div v-else-if="kind === 'Description'" class="description">
      <textarea :aria-label="label" rows="4" :value="descriptionDraft" :disabled="locked" :maxlength="maxLength || null"
                :placeholder="readonly ? 'بدون پاسخ' : 'توضیحات خود را بنویسید…'" @input="descriptionDraft = $event.target.value" />
      <div v-if="!readonly" class="description-foot">
        <span class="counter">{{ fa((descriptionDraft || '').length) }}{{ maxLength ? ' / ' + fa(maxLength) : '' }} نویسه</span>
        <button type="button" class="save-btn" :disabled="locked || !descriptionDirty" @click="saveDescription">ثبت توضیحات</button>
      </div>
    </div>

    <div v-else-if="kind === 'RadioChoice'" class="choices" role="radiogroup" :aria-label="label">
      <button v-for="choice in question.radio_choices || []" :key="choice.id" type="button" role="radio" class="choice"
              :class="{ selected: selectedId(answer.radio) === choice.id }" :aria-checked="selectedId(answer.radio) === choice.id ? 'true' : 'false'"
              :disabled="locked" @click="emit({ radio: choice.id })">
        <span class="mark radio" aria-hidden="true" />{{ choice.answer }}
      </button>
      <p v-if="!(question.radio_choices || []).length" class="field-note">گزینه‌ای برای این پرسش تعریف نشده است.</p>
    </div>

    <div v-else-if="kind === 'DropDownList'" class="select-wrap">
      <select :aria-label="label" :value="selectedId(answer.dropdown) || ''" :disabled="locked" @change="pickDropdown($event.target.value)">
        <option value="" disabled>{{ readonly ? 'بدون پاسخ' : 'یک گزینه را انتخاب کنید' }}</option>
        <option v-for="choice in question.dropdown_choices || []" :key="choice.id" :value="choice.id">{{ choice.answer }}</option>
      </select>
      <v-icon class="select-icon" size="20">mdi-chevron-down</v-icon>
    </div>

    <div v-else-if="kind === 'Multichoice'" class="choices">
      <button v-for="choice in question.answer_choices || []" :key="choice.id" type="button" role="checkbox" class="choice"
              :class="{ selected: multiDraft.includes(choice.id) }" :aria-checked="multiDraft.includes(choice.id) ? 'true' : 'false'"
              :disabled="locked" @click="toggle(choice.id)">
        <span class="mark check" aria-hidden="true"><v-icon v-if="multiDraft.includes(choice.id)" size="15" color="white">mdi-check</v-icon></span>{{ choice.answer }}
      </button>
      <div v-if="!readonly" class="multi-foot">
        <span class="counter">{{ fa(multiDraft.length) }} گزینه انتخاب شده{{ choiceRule }}</span>
        <button type="button" class="save-btn" :disabled="locked || !multiDirty || !!multiError" @click="emit({ multichoice: multiDraft.slice() })">ثبت انتخاب‌ها</button>
      </div>
    </div>

    <p v-else class="field-note">این نوع پاسخ ({{ kind }}) در اپ پشتیبانی نمی‌شود؛ با پشتیبانی هماهنگ کنید.</p>
    <p v-if="localError" class="field-error" role="alert">{{ localError }}</p>
  </div>
</template>

<script>
const DIGITS = { '۰': '0', '۱': '1', '۲': '2', '۳': '3', '۴': '4', '۵': '5', '۶': '6', '۷': '7', '۸': '8', '۹': '9',
  '٠': '0', '١': '1', '٢': '2', '٣': '3', '٤': '4', '٥': '5', '٦': '6', '٧': '7', '٨': '8', '٩': '9' };
const latin = value => String(value == null ? '' : value).replace(/[۰-۹٠-٩]/g, d => DIGITS[d]);

export default {
  name: 'AnswerInput',
  props: {
    question: { type: Object, required: true },
    answer: { type: Object, required: true },
    param: { type: Object, required: true },
    saving: { type: Boolean, default: false },
    readonly: { type: Boolean, default: false },
  },
  data() {
    return { textDraft: '', descriptionDraft: '', priceDraft: null, numberDraft: null, multiDraft: [], localError: '' };
  },
  computed: {
    kind() { return this.param.answer_type && this.param.answer_type.name; },
    rules() { return this.param.validation || {}; },
    locked() { return this.readonly || this.saving; },
    label() { return this.question.text; },
    maxLength() { return this.rules.max_lenght || null; },
    minValue() { return this.rules.min_value != null ? this.rules.min_value : 0; },
    maxValue() { return this.rules.max_value != null ? this.rules.max_value : null; },
    boolOptions() {
      const base = [{ value: true, title: 'بله', icon: 'mdi-check', tone: 'yes' }, { value: false, title: 'خیر', icon: 'mdi-close', tone: 'no' }];
      return this.kind === 'Triple' ? [...base, { value: null, title: 'ندارد', icon: 'mdi-minus', tone: 'none' }] : base;
    },
    numberText() { return this.numberDraft === null ? '' : this.fa(this.numberDraft, false); },
    priceText() { return this.priceDraft === null ? '' : this.fa(this.priceDraft); },
    textDirty() { return (this.textDraft || '') !== (this.answer.text || ''); },
    descriptionDirty() { return (this.descriptionDraft || '') !== (this.answer.description || ''); },
    priceDirty() { return this.priceDraft !== (this.answer.price == null ? null : this.answer.price); },
    savedMulti() { return (this.answer.multichoice || []).map(item => (typeof item === 'object' ? item.id : item)); },
    multiDirty() { return [...this.multiDraft].sort().join() !== [...this.savedMulti].sort().join(); },
    multiError() {
      const count = this.multiDraft.length;
      if (this.rules.min_choice_count != null && count < this.rules.min_choice_count) return 'min';
      if (this.rules.max_choice_count != null && this.rules.max_choice_count > 0 && count > this.rules.max_choice_count) return 'max';
      return '';
    },
    choiceRule() {
      const { min_choice_count: min, max_choice_count: max } = this.rules;
      if (max) return ` · حداکثر ${this.fa(max)}${min ? '، حداقل ' + this.fa(min) : ''}`;
      return min ? ` · حداقل ${this.fa(min)}` : '';
    },
  },
  watch: {
    answer: { immediate: true, deep: true, handler: 'sync' },
  },
  methods: {
    fa(value, grouping = true) {
      if (value === null || value === undefined || value === '') return '';
      return Number(value).toLocaleString('fa-IR', { useGrouping: grouping });
    },
    sync() {
      this.textDraft = this.answer.text || '';
      this.descriptionDraft = this.answer.description || '';
      this.priceDraft = this.answer.price == null ? null : Number(this.answer.price);
      this.numberDraft = this.answer.number == null ? null : Number(this.answer.number);
      this.multiDraft = this.savedMulti.slice();
      this.localError = '';
    },
    emit(payload) { if (!this.locked) { this.localError = ''; this.$emit('save', payload); } },
    isBool(value) { return this.answer.id != null && this.answer.bool === value; },
    selectedId(choice) { return choice && typeof choice === 'object' ? choice.id : choice || null; },
    typeNumber(raw) {
      const clean = latin(raw).replace(/[^0-9-]/g, '');
      this.numberDraft = clean === '' || clean === '-' ? null : Number(clean);
    },
    bump(step) {
      const next = (this.numberDraft === null ? 0 : this.numberDraft) + step;
      if (next < this.minValue || (this.maxValue !== null && next > this.maxValue)) return;
      this.numberDraft = next;
      this.commitNumber();
    },
    commitNumber() {
      if (this.numberDraft === null) return;
      if (this.numberDraft < this.minValue || (this.maxValue !== null && this.numberDraft > this.maxValue)) {
        this.localError = this.rules.value_error_msg_fa || `عدد باید بین ${this.fa(this.minValue)} و ${this.fa(this.maxValue)} باشد.`;
        return;
      }
      if (this.numberDraft === this.answer.number) return;
      this.emit({ number: this.numberDraft });
    },
    typePrice(raw) {
      const clean = latin(raw).replace(/[^0-9]/g, '');
      this.priceDraft = clean === '' ? null : Number(clean);
    },
    savePrice() {
      if (!this.priceDirty) return;
      if (this.priceDraft !== null && this.maxValue !== null && this.priceDraft > this.maxValue) {
        this.localError = this.rules.value_error_msg_fa || 'مبلغ بیش از حد مجاز است.';
        return;
      }
      this.emit({ price: this.priceDraft });
    },
    saveText() {
      if (!this.textDirty) return;
      const value = (this.textDraft || '').trim();
      if (this.rules.regex && value) {
        let valid = true;
        try { valid = new RegExp(this.rules.regex).test(value); } catch (_) { valid = true; }
        if (!valid) { this.localError = this.rules.regex_error_msg_fa || 'مقدار واردشده معتبر نیست.'; return; }
      }
      if (this.rules.min_lenght && value.length < this.rules.min_lenght) {
        this.localError = this.rules.lenght_error_msg_fa || `حداقل ${this.fa(this.rules.min_lenght)} نویسه لازم است.`;
        return;
      }
      this.emit({ text: value });
    },
    saveDescription() {
      if (!this.descriptionDirty) return;
      const value = (this.descriptionDraft || '').trim();
      if (this.rules.min_lenght && value.length < this.rules.min_lenght) {
        this.localError = this.rules.lenght_error_msg_fa || `حداقل ${this.fa(this.rules.min_lenght)} نویسه لازم است.`;
        return;
      }
      this.emit({ description: value });
    },
    pickDropdown(value) { if (value) this.emit({ dropdown: Number(value) }); },
    toggle(id) {
      this.localError = '';
      this.multiDraft = this.multiDraft.includes(id) ? this.multiDraft.filter(item => item !== id) : [...this.multiDraft, id];
      if (this.multiError === 'max') this.localError = this.rules.choice_count_error_msg_fa || `حداکثر ${this.fa(this.rules.max_choice_count)} گزینه قابل انتخاب است.`;
    },
  },
};
</script>

<style scoped>
.answer-input { margin-top: 12px; }
.segmented { display: grid; grid-template-columns: repeat(auto-fit, minmax(84px, 1fr)); gap: 8px; }
.segment { display: inline-flex; align-items: center; justify-content: center; gap: 6px; min-height: 48px; border-radius: 13px;
  border: 1.5px solid #d6e3eb; background: #fff; color: #33566b; font-weight: 800; font-size: 14px; }
.segment.selected.tone-yes { background: #e4f3e9; border-color: #49a07c; color: #155e43; }
.segment.selected.tone-no { background: #fbeae8; border-color: #d98a83; color: #8a2f2a; }
.segment.selected.tone-none { background: #eef2f5; border-color: #9fb2bf; color: #44596a; }
.score-row { display: grid; grid-template-columns: repeat(5, 1fr); gap: 8px; }
.score { min-height: 48px; border-radius: 13px; border: 1.5px solid #d6e3eb; background: #fff; font-size: 17px; font-weight: 800; color: #33566b; }
.score.selected { background: linear-gradient(140deg, #102f4d, #1d608b); border-color: transparent; color: #fff; }
.score-scale { grid-column: 1 / -1; display: flex; justify-content: space-between; color: var(--vf-soft); font-size: 11px; margin-top: -2px; }
.number-row { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.step-btn { width: 48px; height: 48px; border-radius: 13px; border: 1.5px solid #d6e3eb; background: #f7fafc; color: var(--vf-brand); display: grid; place-items: center; }
.number-field { width: 96px; height: 48px; border-radius: 13px; border: 1.5px solid #d6e3eb; text-align: center; font-size: 18px; font-weight: 800; color: var(--vf-ink); background: #fff; }
.number-unit { color: var(--vf-muted); font-size: 12.5px; }
.inline-field { display: flex; gap: 8px; align-items: stretch; }
.text-field, .money { flex: 1; min-width: 0; height: 48px; border-radius: 13px; border: 1.5px solid #d6e3eb; background: #fff; }
.text-field { padding: 0 13px; font-size: 14px; color: var(--vf-ink); }
.money { display: flex; align-items: center; padding: 0 12px; gap: 6px; }
.money input { flex: 1; min-width: 0; height: 100%; border: 0; outline: none; font-size: 16px; font-weight: 800; color: var(--vf-ink); text-align: left; direction: ltr; background: transparent; }
.money span { color: var(--vf-muted); font-size: 12px; font-weight: 700; }
.save-btn { flex: none; min-height: 44px; padding: 0 16px; border-radius: 12px; background: linear-gradient(140deg, #102f4d, #1d608b);
  color: #fff; font-weight: 800; font-size: 13px; }
.save-btn:disabled { background: #e2eaef; color: #8aa2b1; }
.description textarea { width: 100%; min-height: 112px; padding: 12px 13px; border-radius: 13px; border: 1.5px solid #d6e3eb;
  background: #fff; font-size: 14px; line-height: 1.9; color: var(--vf-ink); resize: vertical; }
.description-foot, .multi-foot { display: flex; align-items: center; justify-content: space-between; gap: 10px; margin-top: 8px; flex-wrap: wrap; }
.counter { color: var(--vf-muted); font-size: 11.5px; }
.choices { display: grid; gap: 8px; }
.choice { display: flex; align-items: center; gap: 10px; width: 100%; min-height: 50px; padding: 10px 13px; text-align: right;
  border-radius: 13px; border: 1.5px solid #d6e3eb; background: #fff; color: #24475b; font-size: 13.5px; font-weight: 600; line-height: 1.6; }
.choice.selected { border-color: #2c7fb0; background: #eef7fc; color: #123f5d; }
.mark { flex: none; width: 22px; height: 22px; display: grid; place-items: center; border: 2px solid #a9bfcc; background: #fff; }
.mark.radio { border-radius: 50%; }
.mark.check { border-radius: 7px; }
.choice.selected .mark.radio { border: 7px solid #1d608b; }
.choice.selected .mark.check { background: #1d608b; border-color: #1d608b; }
.select-wrap { position: relative; }
.select-wrap select { width: 100%; height: 50px; padding: 0 14px 0 40px; border-radius: 13px; border: 1.5px solid #d6e3eb; background: #fff;
  font-size: 14px; color: var(--vf-ink); appearance: none; -webkit-appearance: none; }
.select-icon { position: absolute; left: 12px; top: 50%; transform: translateY(-50%); pointer-events: none; }
.field-note { color: var(--vf-muted); font-size: 12px; margin: 6px 0 0; }
.field-error { color: var(--vf-danger); font-size: 12px; font-weight: 700; margin: 8px 0 0; }
button:disabled { cursor: not-allowed; }
.segment:disabled:not(.selected), .score:disabled:not(.selected), .choice:disabled:not(.selected) { opacity: .65; }
input:disabled, textarea:disabled, select:disabled { background: #f6f9fb; color: #46616f; }
</style>
