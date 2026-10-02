<template>
  <div class="edit-container" :class="{ 'has-error': errors.length > 0 || checkIsNull }">
    <img v-if="Icon" class="input-icon" :src="Icon" alt="" />
    <div class="input-container" :class="{ reversed: reverseCurrencyAndClearButton }">
      <label :for="inputId" v-if="label"
        >{{ label }}<span v-if="required" class="required-mark" aria-hidden="true"> *</span></label
      >
      <div class="input-control">
        <input
          ref="inputElement"
          :id="inputId"
          :type="inputType"
          :inputmode="inputMode"
          :maxlength="maxlength"
          :value="value"
          :placeholder="placeholder"
          :readonly="readonly"
          :disabled="disabled"
          :required="required"
          :aria-invalid="errors.length > 0 || checkIsNull"
          :aria-describedby="description || errors.length ? inputId + '-hint' : null"
          :style="{ direction: ltr ? 'ltr' : 'rtl', paddingLeft: inputLeftPadding }"
          @input="$emit('input', $event.target.value)"
          @keyup.enter="$emit('onEnter')"
          @focus="focusOn"
          @blur="focusOut"
        />
        <span v-if="currency" class="currency" :style="{ color: currencyColor }">{{
          currency
        }}</span>
        <button
          v-if="leftIcon"
          type="button"
          class="left-icon"
          :disabled="leftIconDisable || disabled"
          @click="$emit('leftIconClick')"
          :aria-label="leftIconLabel || 'عملیات ورودی'"
        >
          <img :src="leftIcon" alt="" />
        </button>
        <button
          v-if="showClearButton && hasValue"
          type="button"
          class="clear-button"
          :disabled="disabled || readonly"
          aria-label="پاک کردن مقدار"
          @click="$emit('clearButtonClick')"
        >
          ×
        </button>
      </div>
      <p
        v-if="description || errors.length"
        :id="inputId + '-hint'"
        class="description"
        :class="{ error: errors.length }"
      >
        {{ errors.length ? errors[0] : description }}
      </p>
    </div>
  </div>
</template>
<script>
export default {
  props: {
    Icon: String,
    leftIcon: String,
    leftIconLabel: String,
    leftIconDisable: Boolean,
    id: String,
    label: String,
    value: {},
    inputType: { type: String, default: 'text' },
    description: String,
    currency: String,
    readonly: Boolean,
    disabled: Boolean,
    required: Boolean,
    errors: { type: Array, default: () => [] },
    showClearButton: {},
    placeholder: String,
    ltr: Boolean,
    currencyColor: String,
    reverseCurrencyAndClearButton: Boolean,
    inputMode: String,
    maxlength: Number,
  },
  data() {
    return { checkIsNull: false };
  },
  computed: {
    inputId() {
      return this.id || 'admin-input-' + this._uid;
    },
    hasValue() {
      return this.value !== null && this.value !== undefined && this.value !== '';
    },
    inputLeftPadding() {
      return this.currency ? '72px' : this.leftIcon || this.showClearButton ? '44px' : '12px';
    },
  },
  watch: {
    value() {
      if (this.hasValue) this.checkIsNull = false;
    },
  },
  methods: {
    focusOn() {
      this.$emit('focusOn');
    },
    focusOut() {
      this.checkIsNull = this.required && !this.hasValue;
      this.$emit('focusOut');
    },
    setInputFocus() {
      this.$refs.inputElement.focus();
    },
  },
};
</script>
<style scoped>
.edit-container {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin-bottom: 18px;
}
.input-icon {
  width: 24px;
  height: 24px;
  margin-top: 38px;
}
.input-container {
  position: relative;
  flex: 1;
  min-width: 0;
}
.input-control {
  position: relative;
}
input {
  width: 100%;
  min-height: 44px;
  border: 1px solid #ced7e5;
  border-radius: 9px;
  background: #fff;
  color: var(--admin-text);
  padding: 10px 12px;
  font-size: 13px;
  line-height: 22px;
}
label {
  display: block;
  margin-bottom: 7px;
  font-size: 13px;
  font-weight: 500;
  line-height: 1.8;
  color: #4e5c74;
}
input:focus {
  border-color: var(--admin-primary);
  box-shadow: 0 0 0 3px var(--admin-primary-soft);
}
input:disabled,
input:read-only {
  background: #f8fafc;
}
.description {
  margin: 6px 4px 0;
  font-size: 11px;
  color: var(--admin-muted);
  line-height: 1.7;
}
.has-error input {
  border-color: var(--admin-danger);
}
.error,
.has-error label {
  color: var(--admin-danger);
}
.required-mark {
  color: var(--admin-danger);
}
.currency,
.left-icon,
.clear-button {
  position: absolute;
  left: 8px;
  top: 6px;
  min-height: 34px;
  display: flex;
  align-items: center;
  font-size: 12px;
  color: var(--admin-muted);
}
.left-icon,
.clear-button {
  border: 0;
  background: transparent;
  justify-content: center;
  width: 32px;
}
.left-icon img {
  width: 18px;
  height: 18px;
}
.clear-button {
  font-size: 22px;
}
.reversed .currency {
  left: 40px;
}
.reversed .clear-button {
  left: 8px;
}
</style>
