<template>
  <v-col class="p-0 save-button">
    <v-card elevation="0" class="button-card">
      <div class="d-flex justify-space-between w-100" style="gap: 10px; padding: 12px 20px;">
        <button
          v-if="shouldShowLeft"
          type="button"
          class="btn"
          :class="[btnTypeLeft]"
          :disabled="disabledLeft"
          :style="{
            ...styleObjLeft,
            backgroundColor: disabledLeft ? '#ECECEC' : '#4285F4',
            borderColor: styleObjLeft?.['border-color'] && !disabledLeft ? styleObjLeft['border-color'] : 'transparent',
            color: disabledLeft ? btnTextColorLeft : '#fff'
          }"
          @click="$emit('click-left')"
        >
          <v-progress-circular
            class="ml-2"
            v-if="loadingLeft"
            indeterminate
            color="#fff"
            size="20"
            rotate="360"
          ></v-progress-circular>
          <div>
            <div v-if="!loadingLeft">
              <span v-if="titleLeft">{{ titleLeft }}</span>
            </div>
          </div>
        </button>
        <button
          v-if="shouldShowRight"
          type="button"
          class="btn"
          :class="[btnTypeRight]"
          :disabled="disabledRight"
          :style="{
            ...styleObjRight,
            backgroundColor: disabledRight ? '#ECECEC' : styleObjRight?.['background-color'] || '#4285F4',
            borderColor: styleObjRight?.['border-color'] && !disabledRight ? styleObjRight['border-color'] : 'transparent',
            color: disabledRight ? btnTextColorRight : '#4285F4'
          }"
          @click="$emit('click-right')"
        >
          <v-progress-circular
            class="ml-2"
            v-if="loadingRight"
            indeterminate
            color="#fff"
            size="20"
            rotate="360"
          ></v-progress-circular>
          <div>
            <div v-if="!loadingRight">
              <span v-if="titleRight">{{ titleRight }}</span>
            </div>
          </div>
        </button>
      </div>
    </v-card>
  </v-col>
</template>

<script>
export default {
  inheritAttrs: false,
  props: {
    titleLeft: {
      type: String,
    },
    titleRight: {
      type: String,
    },
    disabledLeft: {
      type: Boolean,
      default: false,
    },
    disabledRight: {
      type: Boolean,
      default: false,
    },
    btnTypeLeft: {
      type: String,
      default: "outline-primary",
    },
    btnTypeRight: {
      type: String,
      default: "outline-primary",
    },
    btnTextColorLeft: {
      type: String,
    },
    btnTextColorRight: {
      type: String,
    },
    styleObjLeft: {
      type: Object,
    },
    styleObjRight: {
      type: Object,
    },
    loadingLeft: {
      type: Boolean,
      default: false,
    },
    loadingRight: {
      type: Boolean,
      default: false,
    },
    hideLeft: {
      type: Boolean,
      default: true,
    },
    hideRight: {
      type: Boolean,
      default: true,
    },
  },
  computed: {
    btnColorClassLeft() {
      return `btn-${this.btnTypeLeft}`;
    },
    btnColorClassRight() {
      return `btn-${this.btnTypeRight}`;
    },
    btnStyleObjLeft() {
      return {
        ...this.styleObjLeft,
        color: this.btnTextColorLeft,
      };
    },
    btnStyleObjRight() {
      return {
        ...this.styleObjRight,
        color: this.btnTextColorRight,
      };
    },
    shouldShowLeft() {
      return this.hideLeft;
    },
    shouldShowRight() {
      // console.log("hideRight value:", this.hideRight);
      // If hideRight is undefined or false, show the button
      return this.hideRight;
    },
  },
};
</script>

<style lang="scss" scoped>


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
  flex-grow: 1;
  margin: 0 5px;
  width: 50%;
  border-radius: 8px;
  padding: 14px;
  border: 1px solid;
  font-size: 16px;
  font-weight: 700;
  &.w-100 {
    width: 100%;
    margin: 0;
  }
  &:disabled {
    background-color: #ECECEC;
    cursor: not-allowed;
    color: #A7A7A8;
  }
}


.save-button {
  position: fixed;
  bottom: 0;
  margin-top: 0;
  padding: 0 0 env(safe-area-inset-bottom);
  max-width: 576px;
  z-index: 3;
  box-shadow: 0 -8px 25px rgba(18, 58, 82, .1);
}


</style>
