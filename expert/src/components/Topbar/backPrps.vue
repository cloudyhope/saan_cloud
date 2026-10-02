<template>
    <v-card flat height="48px" tile>
      <v-toolbar
        :class="scrolled ? 'scroll' : ''"
        fixed
        class="topbar"
        color="#fff"
        dense
      >
      
        <v-toolbar-title class="title-name">{{ title }}</v-toolbar-title>
        <v-spacer></v-spacer>
        <v-img @click="backButton" max-width="20" src="@/assets/images/Icons/back.svg" />
     
        <!-- <v-icon class="backicon" color="#404041" @click="backButton"
          >mdi-chevron-right</v-icon
        > -->
       
      </v-toolbar>
    </v-card>
  </template>
  <script>
  import store from "@/store/index";
  
  export default {
    props: {
    title: String,
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
      handleScroll() {
        this.scrolled = window.scrollY > 0;
        (this.scrolled);
      },
      backButton() {
        history.go(-1)
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
  .v-sheet {
    box-shadow: none !important;
  }
  .v-icon.v-icon {
      font-size: 24px;
  }
  .topbar {
    /* padding-right: 8px !important; */
    position: fixed;
    max-width: 576px;
    width: 100%;
    z-index: 2;
    box-shadow: 0px 0px 4px rgba(220, 220, 221, 0.6);
  }
  .scroll {
    box-shadow: 0px 0px 5px rgba(196, 196, 196, 0.3) !important;
  }
  
  </style>
  