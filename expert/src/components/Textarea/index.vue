<template>
  <div class="textarea_container">
    <h3>{{ title }}</h3>
    <textarea
      v-model="text"
      :placeholder="placeholder"
      :style="{ borderRadius: '12px' }"
      @input="handleInput"
      :disabled="disabled"
    ></textarea>
  </div>
</template>

<script>
export default {
  props: {
    title: {
      type: String,
      default: "Title",
    },
    placeholder: {
      type: String,
      default: "Enter your text here...",
    },
    disabled: {
      type: Boolean,
      default: false, // Default to not disabled if not provided by parent
    },
  },
  data() {
    return {
      text: "",
    };
  },
  methods: {
    handleInput() {
      this.$emit("textarea-updated", this.text);
    },
  },
};
</script>

<style scoped>
.textarea_container {
  color: var(--border-dark);
} 

textarea {
  width: 100%;
  padding: 10px;
  box-sizing: border-box;
  font-size: 14px;
  margin-top: 10px;
  min-height: 112px;
  color: #fff;
  box-shadow: 0px 1px 3px 0px rgba(16, 24, 40, 0.1) inset;
  border: 1px solid rgba(236, 236, 236, 1);


}

h3 {
  font-size: 14px;
  margin-bottom: 10px;
}
</style>
