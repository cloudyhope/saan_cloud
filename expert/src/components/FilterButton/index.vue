<template>
  <div class="filter-button-wrapper">
    <button
      class="filter-btn"
      @click="sheet = !sheet"
      :class="{ active: isActive }"
    >
      <img
        v-if="icon"
        :src="require(`@/assets/images/Icons/${icon}.svg`)"
        class="custom-icon"
      />
      {{ text }}
    </button>

    <v-bottom-sheet v-model="sheet">
      <v-sheet class="px-6 py-4" height="400px">
        <div class="d-flex justify-space-between align-center mb-4">
          <h3>{{ text }}</h3>
          <v-btn icon @click="sheet = false">
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </div>

        <!-- Content slot for bottom sheet -->
        <slot name="sheet-content"></slot>
      </v-sheet>
    </v-bottom-sheet>
  </div>
</template>

<script>
export default {
  name: "FilterButton",
  props: {
    icon: {
      type: String,
      default: "",
    },
    text: {
      type: String,
      required: true,
    },
    isActive: {
      type: Boolean,
      default: false,
    },
  },

  data() {
    return {
      sheet: false,
    };
  },
};
</script>

<style scoped>
.filter-button-wrapper {
  flex: 1;
  width: 100%;
  margin-bottom: 28px;
}
.filter-btn {
  display: flex;
  align-items: center;
  background-color: #fff;
  box-shadow: 0px 0px 3px 0px rgba(16, 24, 40, 0.1) !important;
  border-radius: 8px;
  margin: 4px;
  padding: 0 8px;
  height: 40px;
  width: 100%;
  margin: 0;
}
.custom-icon {
  margin-left: 8px;
}
.active {
  background-color: #eaf1fb !important;
  color: #1976d2;
}
</style>
