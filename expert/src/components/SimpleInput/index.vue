<template>
  <div class="custom-input">
    <label class="input-label">{{ title }}</label>
    <div class="input-container">
      <input
        v-model="formattedInputValue"
        :type="inputType"
        :inputmode="inputMode"
        :placeholder="placeholderText"
        :disabled="isDisabled"
        class="input-field"
        :class="{ 'input-field-disabled': isDisabled }"
        :style="{
          'text-align': centerInput ? 'center' : 'right',
          'border-radius': inputFieldBorderRadius,
        }"
        @input="handleInputValue"
      />
      <div v-if="showAmountInput" class="rial-label">ریال</div>
    </div>
  </div>
</template>

<script>
export default {
  name: "CustomInput",
  props: {
    title: {
      type: String,
      required: true,
    },
    placeholderText: {
      type: String,
      default: "",
    },
    showAmountInput: {
      type: Boolean,
      default: true,
    },
    centerInput: {
      type: Boolean,
      default: true,
    },
    formatWithCommas: {
      type: Boolean,
      default: false, // Default to not formatting with commas
    },
    isDisabled: {
      type: Boolean,
      default: false, // Default to not disabled
    },
    inputType: {
      type: String,
      default: "text", // Default input type to text
    },
    inputMode:{
      type: String,
      default: "none", // Default input type to input mode
    }
  },
  computed: {
    // inputMode() {
    //   return this.inputType === "number" ? "numeric" : null;
    // },
    inputFieldBorderRadius() {
      return this.showAmountInput ? "0 12px 12px 0" : "12px";
    },
    formattedInputValue: {
      get() {
        // Get the formatted value based on props
        if (this.inputValue && this.inputValue.length > 0) {
          return this.formatWithCommas
            ? this.formatWithCommasFunction(this.inputValue)
            : this.inputValue;
        } else {
          return this.inputValue;
        }
      },
      set(newValue) {
        // Update the inputValue when the formatted value changes
        this.inputValue = newValue.replace(/,/g, ""); // Remove commas before updating the data
      },
    },
  },
  data() {
    return {
      inputValue: "",
    };
  },
  methods: {
    handleInputValue() {
      this.$emit("input-text", this.inputValue); // Emit event to parent with textarea content
    },
    formatWithCommasFunction(value) {
      // Format number with commas every three digits
      return value.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    },
  },
};
</script>

<style scoped>
.custom-input {
  margin-bottom: 20px;
}

.input-label {
  font-weight: bold;
  margin-bottom: 6px;
  display: block;
}

.input-container {
  display: flex;
  align-items: center;
}

.rial-label {
  padding: 12px;
  box-shadow: 0px 1px 3px 0px rgba(16, 24, 40, 0.1) inset;
  border-right: none;
  border-top-left-radius: 12px;
  border-bottom-left-radius: 12px;
  height: 42px;
}

.input-field {
  flex: 1;
  padding: 12px;
  color: var(--white-color);
  outline: none;
  height: 42px;
  font-family: "IRANYekanfa" !important;
}

.input-field-disabled {
  background-color: var(--disabled-background-color);
  color: var(--disabled-text-color);
  cursor: not-allowed;
  opacity: 0.6;
}

/* Default border-radius for the input field */
.input-field {
  border-radius: 0 12px 12px 0;
}

/* Override border-radius if showAmountInput is false */
.input-field-border-radius {
  border-radius: 12px;
}
input {
  box-shadow: 0px 1px 3px 0px rgba(16, 24, 40, 0.1) inset;
}
</style>
