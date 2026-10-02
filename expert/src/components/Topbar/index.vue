<template>
  <v-card height="48px" tile>
      <v-toolbar dense :class="scrolled ? 'scroll' : ''" fixed class="topbar" color="#fff">
        <v-toolbar-title class="title-name">{{ title }}</v-toolbar-title>
      </v-toolbar>
  </v-card>
</template>
<script>

export default {
  data(){
      return{
        scrolled: false
      }
    },
    methods: {
  handleScroll () {
    this.scrolled = window.scrollY > 0;
    (this.scrolled)
  }
},
created () {
  window.addEventListener('scroll', this.handleScroll);
},
destroyed () {
  window.removeEventListener('scroll', this.handleScroll);
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
  font-weight: 700;

}
.v-sheet {
  box-shadow: none !important;
}
.topbar {
  /* padding-right: 8px !important; */
  position: fixed;
  max-width: 576px;
  width: 100%;
  z-index: 2;
  box-shadow: 0px 0px 4px rgba(220, 220, 221, 0.6) !important;

}
.shadows {
  max-height: 20px;
}
.scroll {
    box-shadow: 0px 0px 5px rgba(196, 196, 196, 0.3) !important;
}
</style>
