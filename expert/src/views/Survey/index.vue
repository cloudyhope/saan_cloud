<template>
    <div>
    <BaseTopBar title="آزمون های فعال" />

      <Skeleton v-if="initialLoading" type="list" :count="4" wrapper-class="ma-5" :loading="true" />

      <EmptyState v-else-if="surveyList.length === 0" kind="documents" title="هنوز پرسشنامه‌ای تعریف نشده" description="پرسشنامه‌های شما پس از تعریف توسط شرکت اینجا دیده می‌شوند." />
      <div v-else class="ma-5">
        <!-- <span class="titles">پرسشنامه ها ({{surveyList.length}} عدد)</span> -->
        <v-card v-for="survey in surveyList" :key="survey.id" @click="surveyDetail(survey)" class="cards-shadow pa-4">
          <div class="d-flex justify-space-between align-center">
            <div class="d-flex align-center">
              <div class="img-container">
                <v-img max-width="36" :src="survey.icon" />
              </div>
              <div class="contents">
                <span class="header mb-1">{{survey.verbose_name}}</span>
              </div>
            </div>
            <div>
              <v-img src="@/assets/images/Icons/chevron-left-rounded.svg"/>
            </div>
          </div>
        </v-card>
        <EmptyContainer/>
      </div>
    </div>
  </template>
  
  <script>
  import EmptyContainer from "@/components/emptyContainer.vue";
  import Button from "@/components/Button/Button.vue";
  import BaseTopBar from "@/components/Topbar/BaseTopbar.vue";
  import Skeleton from "@/components/Skeleton/index.vue";
  import EmptyState from "@/components/EmptyState/index.vue";
  export default {
    components: { EmptyState,
      EmptyContainer,
      Button,
      BaseTopBar,
      Skeleton,
    },
    data() {
      return {
        surveyList: [],
        initialLoading: true,
      };
    },
    computed: {
        },
  
      
    created() {
      this.getData();
     
    },
    mounted() {
    },
  
    methods: {
      async getData() {
        this.initialLoading = true;
        const res = await this.$ApiServiceLayer.get(
          this.$PATH.RELATIVE_PATH.MULTI.SURVEY_LIST +"?p=" +
          this.$STORE.state.userConfig.selectedProject + '&is_active=true' + '&category=1',
          this.$PATH.SERVICE_NAME.AUTH
        );
        if (res.status === 200) {
          this.surveyList = res.data;
        }
        this.initialLoading = false;
      },
      async surveyDetail(survey) {
        const res = await this.$ApiServiceLayer.post(
          this.$PATH.RELATIVE_PATH.MULTI.SURVEY_FILL_OUT,
          this.$PATH.SERVICE_NAME.AUTH,
          {survey:survey.id}
        );
        if (res.status === 201) {
        this.$router.push({ name: "surveyDetail" , params: {id: res.data.id,survey_id:survey.id}, });
        
        }
      },
    },
  };
  </script>
  
  <style scoped>
  .cards-shadow {
    box-shadow: 0px 0px 3px 0px rgba(16, 24, 40, 0.1) !important;


  }
  .titles {
    font-size: 16px;
    font-weight: 700;
  }
  .img-container {
    background: #EAF1FB;
    border-radius: 2px;
    padding: 14px;
    max-width: 64px;
    max-height: 64px;
  }
  .contents {
    display: flex;
    flex-direction: column;
    margin-right: 12px;
  }
  .header {
    font-size: 12px;
    font-weight: 700;
  }
  .empty-state-img {
  margin: 48px 70px;
}
.empty-state-txt {
  text-align: center;
  font-size: 18px;
}

  </style>
  