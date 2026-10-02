<template>
    <div>
      <BaseTopBar title="سوالات متداول" />
      <Faq/>
    </div>
  </template>
  <script>
import BaseTopBar from "@/components/Topbar/BaseTopbar.vue";
import Faq from "@/components/FaqComponent/index.vue";
  
  export default {
    components: {
        BaseTopBar,
      Faq
    },
  };
  </script>
  