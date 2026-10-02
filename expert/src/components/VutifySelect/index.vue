<template>
  <div class="edit-container" :class="{ checkIsNull: checkIsNull }">
    <div class="input-icon" v-if="Icon">
      <img :src="Icon" alt="" />
    </div>
    <div class="simple-label" v-if="label">{{ label }}</div>

    <div class="input-container">
      <div
        class="select-wrapper"
        :class="{ readonly: readonly, 'is-open': isOpen }"
      >
        <input
          readonly
          :placeholder="placeholder"
          :value="selectedLabel"
          :disabled="disabled"
          required="required"
          :id="id"
          @click="handleClick"
          :class="{ 'has-value': selectedLabel }"
          :style="{
            direction: !ltr ? 'rtl' : 'ltr',
          }"
        />
      </div>

      <transition name="fade">
        <div v-show="isOpen" class="dropdown-menu">
          <div
            v-for="item in options"
            :key="item[itemValue]"
            class="dropdown-item"
            @click="selectOption(item)"
          >
            {{ item[itemText] }}
          </div>
        </div>
      </transition>
      
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
    id: String,
    value: {},
    options: {
      type: Array,
      required: true,
    },
    description: String,
    readonly: Boolean,
    errors: {
      default: () => [],
    },
    placeholder: String,
    ltr: Boolean,
    disabled: {
      type: Boolean,
      default: false,
    },
    label: String,
    itemText: {
      type: String,
      default: 'label'
    },
    itemValue: {
      type: String,
      default: 'value'
    }
  },
  data() {
    return {
      isOpen: false,
      checkIsNull: false,
    };
  },
  computed: {
    selectedLabel() {
      if (!this.value || !this.options) return '';
      const selected = this.options.find(opt => opt[this.itemValue] === this.value);
      return selected ? selected[this.itemText] : '';
    },
  },
  methods: {
    handleClick(event) {
      if (!this.disabled && !this.readonly) {
        event.stopPropagation();
        this.isOpen = !this.isOpen;
      }
    },
    selectOption(item) {
      this.$emit('input', item[this.itemValue]);
      this.isOpen = false;
      this.checkIsNull = false;
    },
    focusOut() {
      if (!this.value) {
        this.checkIsNull = true;
      }
    },
  },
  mounted() {
    document.addEventListener('click', this.closeDropdown);
  },
  beforeDestroy() {
    document.removeEventListener('click', this.closeDropdown);
  },
};
</script>

<style scoped lang="scss">
.edit-container {
  display: flex;
  flex-direction: column;
  width: 100%;
  position: relative;
  margin-bottom: 20px;

  &.checkIsNull {
    border: 1px solid var(--red-color);
    border-radius: 12px;
    
    label {
      color: #d20032;
    }
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
  z-index: 3;

  img {
    margin-bottom: 5px;
  }
}
.simple-label {
    font-size: 14px;
    margin-bottom: 8px;
}
.input-container {
  width: 100%;
  position: relative;

  input {
    width: 100%;
    border: 1px solid var(--darken-color);
    border-radius: 12px;
    height: 48px;
    font-size: 14px;
    background-color: transparent !important;
    padding: 5px 15px;
    color: #666; // placeholder color
    box-shadow: 0px 0px 3px 0px rgba(16, 24, 40, 0.1);
    &.has-value {
      color: #000; // selected value color
    }

    &::placeholder {
      color: #666;
    }
  }
}

.select-wrapper {
  position: relative;
  cursor: pointer;

  &.is-open input {
    border-color: var(--primary-color, #4a5568);
  }

  &::after {
    content: '';
    position: absolute;
    left: 10px;
    top: 50%;
    transform: translateY(-50%);
    width: 0;
    height: 0;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 5px solid #666;
    pointer-events: none;
  }

  &.is-open::after {
    transform: translateY(-50%) rotate(180deg);
  }
}

.dropdown-menu {
  position: absolute;
  top: calc(100% + 5px);
  left: 0;
  right: 0;
  background: #fff;
  border: 1px solid var(--darken-color);
  border-radius: 8px;
  max-height: 200px;
  overflow-y: auto;
  z-index: 1000;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.dropdown-item {
  padding: 12px 16px;
  cursor: pointer;
  color: #333;
  transition: background-color 0.2s;
  font-size: 14px;

  &:hover {
    background-color: #f5f5f5;
  }

  &:not(:last-child) {
    border-bottom: 1px solid #eee;
  }
}

.placeholder-text {
  position: absolute;
  top: -9px;
  right: 30px;
  z-index: 9;
  font-size: 10px;
  color: #fff;
  background-color: #ffffff;
  padding: 0px 10px;
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

// Add transition animation
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.2s, transform 0.2s;
}

.fade-enter, .fade-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}
</style> 