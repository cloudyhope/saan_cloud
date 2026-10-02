<template>
  <div class="edit-container" :class="{ checkIsNull: checkIsNull }">
    <div class="input-icon">
      <img :src="Icon" alt="" />
    </div>
    <div
      class="input-container"
      :class="{
        'reverse-currency-and-clear-button': reverseCurrencyAndClearButton,
      }"
    >
      <span v-if="value" class="placeholder-text">{{ placeholder }}</span>
      <input
        ref="inputElement"
        :placeholder="placeholder"
        :readonly="readonly"
        :class="{ readonly: readonly }"
        :type="inputType"
        :id="id"
        required="required"
        :value="value"
        :disabled="disabled"
        @input="
          (e) => {
            this.$emit('input', e.target.value);
          }
        "
        @keyup.enter="enterBtn"
        @focus="focusOn()"
        @blur="focusOut()"
        :style="{
          direction: !ltr ? 'rtl' : 'ltr',
          paddingLeft: inputLeftPadding,
        }"
      />
      <label :for="id" :class="{ filled: readonly && value, active: isActiveLabel }">{{
        label
      }}</label>
      <span
        @click="onLeftIconClick()"
        class="currency"
        :class="{ 'disable-icon': leftIconDisable }"
      >
        <img v-if="leftIcon" :src="leftIcon" />
      </span>
      <span
        v-if="showClearButton"
        class="clear-button"
        @click="clearButtonClick()"
      >
        <!-- <img src="@/assets/img/public/cancel.svg" alt /> -->
      </span>
      <div v-if="description && errors.length == 0" class="description">
        {{ description }}
      </div>
      <div v-if="errors.length > 0" class="description error">
        {{ errors[0] }}
      </div>
    </div>
  </div>
</template>

<script>
export default {
  props: {
    Icon: String,
    leftIcon: String,
    leftIconDisable: Boolean,
    id: String,
    label: String,
    value: {},
    inputType: {
      default: "text",
      type: String,
    },
    description: String,
    currency: String,
    readonly: Boolean,
    errors: {
      default: () => {
        return [];
      },
    },
    showClearButton: {},
    placeholder: String,
    ltr: Boolean,
    currencyColor: String,
    reverseCurrencyAndClearButton: Boolean,
    disabled: {
      type: Boolean,
      default: false,
    },
  },
  data() {
    return {
      checkIsNull: false,
    };
  },
  computed: {
    isActiveLabel() {
      return this.disabled && this.value;
    },
    inputLeftPadding() {
      if (this.ltr) {
        if (this.currency) return "60px";
        else if (this.showClearButton) return "32px";
      }

      return 0;
    },
  },
  methods: {
    emitToParent() {
      this.$emit("input", this.value);
    },
    enterBtn() {
      this.$emit("onEnter");
    },
    focusOn() {
      this.$emit("focusOn");
    },
    focusOut() {
      console.log(this.value);
      let focusOutInput = this.value;
      if (focusOutInput === null || focusOutInput === "") {
        this.checkIsNull = true;
      } else {
        this.checkIsNull = false;
      }

      this.$emit("focusOut");
    },
    onLeftIconClick() {
      if (!this.leftIconDisable) {
        this.$emit("leftIconClick");
      }
    },
    clearButtonClick() {
      this.$emit("clearButtonClick");
    },
    setInputFocus() {
      document.getElementById(this.id).focus();
    },
  },
};
</script>

<style scoped lang="scss">
/* Chrome, Safari, Edge, Opera */
input::-webkit-outer-spin-button,
input::-webkit-inner-spin-button {
  -webkit-appearance: none;
  margin: 0;
}

/* Firefox */
input[type="number"] {
  -moz-appearance: textfield;
}
.edit-container {
  display: flex;
  width: 100%;
  position: relative;
  margin-bottom: 20px;
  &.checkIsNull {
    input {
      border: none; /* Remove the border when checkIsNull class is active */

      &:focus {
        border: none; /* Remove focus border when checkIsNull class is active */
      }
    }

    label {
      color: #d20032; /* Change label color when checkIsNull class is active */
    }
  }

  input {
    width: 100%;
    /* Your existing input styles */

   
  }
  .placeholder-text {
    position: absolute;
    top: -9px;
    right: 30px;
    z-index: 9;
    font-size: 10px;
    transition: width 2s;
    color: #fff;
    background-color: #ffffff;
    padding: 0px 10px;
  }
}
.input-icon {
  position: absolute;
  right: 10px;
  top: 10px;
  width: 24px;
  height: 24px;
  text-align: center;
  transform: rotate(272deg);

  img {
    margin-bottom: 5px;
  }
}
.input-container {
  width: 100%;
  position: relative;
  input {
    width: 100%;
    border: 1px solid var(--darken-color);
    border-radius: 12px;
    color: #fff;
    height: 48px;
    font-size: 14px;
    background-color: transparent !important;
    position: relative;
    padding: 5px 10px;
    z-index: 2;
    box-shadow: 0px 0px 3px 0px rgba(16, 24, 40, 0.1);

    &::placeholder {
      color: #fff;
    }
    &.readonly {
      -webkit-touch-callout: none; /* iOS Safari */
      -webkit-user-select: none; /* Safari */
      -moz-user-select: none; /* Firefox */
      -ms-user-select: none; /* Internet Explorer/Edge */
      user-select: none;
    }

    &:focus {
      outline: none;
    }
    &:focus ~ label {
      top: 0px;
      height: 12px;
      font-size: 12px;
      font-weight: 300;
      font-stretch: normal;
      font-style: normal;
      line-height: 1;
      letter-spacing: normal;
      text-align: right;
      color: var(--mnx-darken-gray-color);
      background: var(--background-color);
      padding: 0 10px;
      z-index: 2222;
      color: #828282;
    }
    &:valid ~ label {
      top: 0px;
      padding: 0 10px;
      height: 12px;
      font-size: 10px;
      font-weight: 300;
      font-stretch: normal;
      font-style: normal;
      line-height: 1;
      letter-spacing: normal;
      text-align: right;
      color: var(--mnx-darken-gray-color);
      background: var(--background-color);
      z-index: 222;
    }
    // &:valid {
    // 	border-bottom: 2px solid #828282;
    // }
  }
  label {
    position: absolute;
    top: 40%;
    right: 1%;
    height: 0;
    transform: translateY(-50%);
    font-size: 12px;
    font-weight: normal;
    font-stretch: normal;
    font-style: normal;
    line-height: 0.86;
    letter-spacing: normal;
    text-align: right;
    color: #000;
    transition: all 0.2s;
    padding: 0 10px;
    // background-color: #fff;

    &.filled {
      top: 0;
      height: 12px;
      font-family: IRANYekan;
      font-size: 10px;
      font-weight: 300;
      font-stretch: normal;
      font-style: normal;
      line-height: 1;
      letter-spacing: normal;
      text-align: right;
      background-color: #fff;
      color: #404141;
      padding: 0 10px;
      z-index: 222;
    }

    &.active {
      top: 0;
      padding: 0 10px;
      height: 12px;
      font-size: 10px;
      font-weight: 300;
      font-stretch: normal;
      font-style: normal;
      line-height: 1;
      letter-spacing: normal;
      text-align: right;
      color: var(--mnx-darken-gray-color);
      background: var(--background-color);
      z-index: 222;
    }
  }
  .description {
    font-size: 10px;
    color: var(--mnx-black-color);
    margin-right: 10px;
    padding-top: 6px;
    &.error {
      color: red;
    }
  }
  span.currency {
    position: absolute;
    font-size: 14px;
    color: var(--mnx-black-color);
    left: 0;
    z-index: 50;

    &.disable-icon {
      filter: grayscale(1);
      opacity: 0.3;
    }
  }
  span.clear-button {
    position: absolute;
    left: 32px;
    z-index: 50;
    top: -1px;
  }
}

.reverse-currency-and-clear-button {
  .currency {
    left: 32px !important;
  }

  .clear-button {
    left: 0 !important;
  }
}
.checkIsNull {
  border: 1px solid var(--red-color);
  border-radius: 12px !important;
  input { 
    &:focus {
      border: none;
    }
    &:focus ~ label {
      color: #d20032;
    }
  }
  label {
    color: #d20032;
  }
}

</style>
