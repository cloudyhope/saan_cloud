<template>
  <v-card flat tile class="pr-1">
        <v-toolbar
          :class="scrolled ? 'scroll' : ''"
          fixed
          class="topbar"
          color="#F0F0F1"
          dense
        >
          <v-icon class="backicon" color="#404041" @click="returnHome"
            >mdi-close</v-icon
          >
          <v-toolbar-title class="title-name">{{ title }}</v-toolbar-title>
          <span class="prop-tilte" v-if="propTitle"> {{ propTitle }}</span>
          <v-spacer></v-spacer>
           <v-btn icon>
        <v-icon @click="routeToCart" class="ml-3">mdi-cart-outline</v-icon>
      </v-btn>
        </v-toolbar>
  </v-card>
</template>
<script>
export default {
  props: {
    propTitle: {
      type: String,
    },

  },
  data() {
    return {
      scrolled: false,
    };
  },
  created() {
    window.addEventListener("scroll", this.handleScroll);
  },
  destroyed() {
    window.removeEventListener("scroll", this.handleScroll);
  },
  methods: {
    returnHome() {
      this.$router.push({ name: "tasks" });
    },
    routeToCart() {
      this.$router.push({ name: "cart" });
    },
    handleScroll() {
      this.scrolled = window.scrollY > 0;
      (this.scrolled);
    },
  },
  computed: {
    title() {
      return this.$route.meta.title;
    },
  },
};
</script>
<style scoped>
.title-name {
  font-size: 18px;
  margin-right: 16px;
  color: #404041;
  font-weight: 700;
}
.prop-tilte {
  font-weight: 400;
  font-size: 16px;
  margin-right: 26px;
}
.v-sheet {
  box-shadow: none !important;
}
.topbar {
  /* padding-right: 8px !important; */
  position: fixed;
  max-width: 570px;
  width: 100%;
  z-index: 2;
}
.scroll {
  box-shadow: 0px 0px 5px rgba(196, 196, 196, 0.3) !important;
}
</style>
