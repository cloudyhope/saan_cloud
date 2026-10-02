<template>
  <v-col class="p-0 save-button">
    <v-card color="#fff" class="button-card">
      <button
        type="button"
        class="btn"
        :class="[btnColorClass, outline, btnTextColorClass]"
        :style="styleObj"
        v-bind="$attrs"
        v-on="$listeners"
        :disabled="disabled"
      >
        <v-progress-circular
          class="ml-2"
          v-if="loading"
          indeterminate
          color="#fff"
          size="20"
          rotate="360"
        ></v-progress-circular>
        <div>
          <div v-if="!loading">
            <span v-if="title">{{ title }}</span>
          </div>
        </div>
      </button>
    </v-card>
  </v-col>
</template>

<script>
export default {
  inheritAttrs: false,
  props: {
    title: {
      type: String,
    },
    disabled: {
      type: Boolean,
      default: false,
    },
    btnImageUrl: {
      type: String,
    },
    btnType: {
      type: String,
      default: "outline-primary",
    },
    btnTextColor: {
      type: String,
    },
    btnBorderColor: {
      type: String,
    },
    btnSize: {
      type: String,
    },
    outline: {
      type: Boolean,
    },
    flat: {
      type: Boolean,
    },
    gradient: {
      type: Boolean,
    },
    relief: {
      type: Boolean,
    },
    square: {
      type: Boolean,
    },
    round: {
      type: Boolean,
    },
    block: {
      type: Boolean,
    },
    icon: {
      type: Boolean,
    },
    roundedCircle: {
      type: Boolean,
    },
    disabled: {
      type: Boolean,
    },
    loading: {
      type: Boolean,
      default: false,
    },
    styleObj: {
      type: Object,
    },
  },
  computed: {
    btnDisable() {
      if (this.disabled === true) {
        ("hello");
      }
    },
    btnSizeClass() {
      if (this.btnSize) {
        return `btn-${this.btnSize}`;
      }
      return false;
    },
    btnColorClass() {
      ("1", this.outline);
      if (this.flat) {
        return `btn-flat-${this.btnType}`;
      }
      if (this.gradient) {
        return `bg-gradient-${this.btnType}`;
      }
      if (this.relief) {
        return `btn-relief-${this.btnType}`;
      }
      if (this.square) {
        if (this.outline) {
          return `btn-outline-${this.btnType} square`;
        }
        return `btn-${this.btnType} square`;
      }
      if (this.round) {
        if (this.outline) {
          return `btn-outline-${this.btnType} round`;
        }
        return `btn-${this.btnType} round`;
      }
      if (this.outline) {
        ("2", this.outline);
        return `btn-outline-${this.btnType}`;
      }
      return `btn-${this.btnType}`;
    },
    btnTextColorClass() {
      if (this.btnTextColor) {
        return `text-${this.btnTextColor}`;
      }
      return false;
    },
    btnBorderColorClass() {
      if (this.btnBorderColor) {
        return `border-${this.btnBorderColor}`;
      }
      return false;
    },
    btnIconClass() {
      if (this.icon) {
        return `btn-icon`;
      }
      return false;
    },
    roundedCircleClass() {
      if (this.roundedCircle) {
        return `rounded-circle`;
      }
      return false;
    },
    blockBtnClass() {
      if (this.block) {
        return `btn-block`;
      }
      return false;
    },
  },
};
</script>

<style lang="scss" scoped>
button {
  &:disabled {
    background: #F1F1F1;
    box-shadow: unset !important;
    cursor: no-drop;
    color: #535656;
  }
}

.button-image {
  width: 14px;
  height: 14px;
  margin-top: 4px;
  &.has-margin {
    margin-right: 8px;
  }
}
.btn {
  display: flex;
  justify-content: center;
  align-items: center;
}
.btn-text {
  display: flex;
  align-items: center;
  justify-content: center;
  span {
    font-size: 14px;
  }
  &:hover {
    color: #fff;
    span {
      color: #fff !important;
    }
    .iconify {
      color: #fff !important;
      margin-left: 10px;
      margin-top: 3px;
    }
  }
}
.btn-outline-primary {
  background: #357AE1;;
  color:#fff;
  width: 100%;
  border-radius: 12px !important;
  height: 48px;
  font-size: 16px;
  font-weight: 600;
}
.save-button {
  position: fixed;
  bottom: 0;
  // margin-top: 0;
  padding: 0;
  max-width: 576px;
  z-index: 3;
  margin: auto !important;
}

.button-card {
  padding: 20px;
  
}
.v-sheet:not(.v-sheet--outlined) {
  box-shadow: 0px 0px 3px 0px rgba(16, 24, 40, 0.1)!important;
  
}
</style>
