<template>
  <div>
    <BaseTopBar :arrow="false" title="آکادمی" />

    <!-- <EmptyContainer /> -->
    <div>
      <div class="academy_container">
        <div class="academy_test" @click="goToSurvey">
          <div class="d-flex align-center gap-2">
            <img src="@/assets/images/Icons/tests.svg" alt="academy" />
            <h3>آزمون‌ها</h3>
          </div>
          <div>
            <Button height="32px" textColor="#2EA1FF" padding="7px 12px" background="#F4F9FF" borderColorProps="#357AE1" title="شروع" />

          </div>
        </div>
        <div class="d-flex align-center gap-2 mb-3">
          <img src="@/assets/images/Icons/tutorial.svg" alt="academy" />
          <h3>آموزش سان‌اپ</h3>
        </div>
        <Skeleton
          v-if="initialLoading"
          type="list-row"
          :count="5"
          :loading="true"
        />
        <div v-else class="box-container">
          <template v-for="(item, index) in academyList">
            <div class="box" :key="item.id" @click="goToAcademy(item.id)">
              <span>{{ item.title_fa }}</span>
              <img
                src="@/assets/images/Icons/chevron-left-rounded.svg"
                alt="arrow-right"
              />
            </div>
            <v-divider
              v-if="index !== academyList.length - 1"
              :key="`divider-${index}`"
              class="my-0"
            ></v-divider>
          </template>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import EmptyContainer from "../../components/emptyContainer.vue";
import Button from "@/components/Button/Button.vue";
import BaseTopBar from "@/components/Topbar/BaseTopbar.vue";
import Skeleton from "@/components/Skeleton/index.vue";

export default {
  name: "Academy",
  components: {
    EmptyContainer,
    BaseTopBar,
    Button,
    Skeleton,
  },
  data() {
    return {
      academyList: [],
      initialLoading: true,
    };
  },
  mounted() {
    this.getAcademyList();
  },
  methods: {
    async getAcademyList() {
      this.initialLoading = true;
      const res = await this.$ApiServiceLayer.get(
        this.$PATH.RELATIVE_PATH.GET.MEDIA_TYPE_LIST +
          "?p=" +
          this.$STORE.state.userConfig.selectedProject,
        this.$PATH.SERVICE_NAME.EMPTY,
        {}
      );
      if (res.status === 200) {
        this.academyList = res.data;
      }
      this.initialLoading = false;
    },
    goToAcademy(id) {
      this.$router.push({ name: "academyDetail", params: { id: id } });
    },
    goToSurvey() {
      this.$router.push({ name: "surveyList"});
    },
  },
};
</script>

<style lang="scss" scoped>
.academy_container {
  padding: 21px;
  .academy_test {
      box-shadow: 0px 0px 3px 0px rgba(16, 24, 40, 0.1);
      width: 100%;
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 12px;
      border-radius: 8px;
      background-color: #fff;
      margin-bottom: 24px;
    }
  .box-container {
    display: flex;
    flex-direction: column;
    background-color: #fff;
    padding: 18px 12px;
    box-shadow: 0px 0px 3px 0px rgba(16, 24, 40, 0.1);
    border-radius: 8px;
    
    .box {
      display: flex;
      justify-content: space-between;
      margin: 12px 0;
      &:first-child {
        margin-top: 0;
      }
      &:last-child {
        margin-bottom: 0;
      }
    }
  }
}
</style>
