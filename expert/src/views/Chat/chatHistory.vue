<template>
  <div>
    <BaseTopBar title="پیام‌های من" />
    <div class="chat_container">
      <Skeleton
        v-if="initialLoading"
        type="chat-history"
        :count="skeletonNumber"
        :loading="true"
      />
      <div class="empty_state" v-else-if="emptyState">
        <img src="@/assets/images/empty-chat-history.svg" />
      </div>
      <div v-else>
        <div
          @click="chatConversationHandler(conversation)"
          class="cards"
          v-for="conversation in conversationData"
          :key="conversation.id"
        >
          <div class="d-flex align-center">
            <img class="ml-2" src="@/assets/images/Icons/chat-avatar.svg" />
            <div>
              <p v-if="conversation.creator.username === userData.username">
                {{ conversation.store_loyalty_plan.store.name_fa }}
              </p>
              <p
                v-else-if="
                  conversation.creator.username !== userData.username ||
                  conversation.creator.extended.first_name !== '' ||
                  conversation.creator.extended.last_name !== '' ||
                  conversation.creator.extended.first_name !== null ||
                  conversation.creator.extended.last_name !== null
                "
              >
                {{ conversation.creator.extended.first_name }}
                {{ conversation.creator.extended.last_name }}
              </p>

              <p v-else>ناشناس</p>
              <span class="last_message_body">{{
                conversation.last_message.body
              }}</span>
            </div>
          </div>
          <div class="d-flex flex-column align-end">
            <p class="date_time">{{ conversation.date_created_fa }}</p>
            <span
              v-if="conversation.unseen_count > 0"
              class="unread_message_count"
              >{{ conversation.unseen_count_persian }}</span
            >
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import BaseTopBar from "@/components/Topbar/BaseTopbar.vue";
import Skeleton from "@/components/Skeleton/index.vue";

export default {
  components: {
    BaseTopBar,
    Skeleton,
  },
  data: () => ({
    conversationData: [],
    initialLoading: true,
    skeletonNumber: 4,
    userData: {},
    emptyState: false,
  }),
  async mounted() {
    await this.getUserData();
    await this.getConversationList();
  },

  methods: {
    async getConversationList() {
      this.initialLoading = true;
      const resData = await this.$ApiServiceLayer.get(
        this.$PATH.RELATIVE_PATH.MULTI.CONVERSATION_LIST_CREATE,
        this.$PATH.SERVICE_NAME.UTILS
      );
      if (resData.status === 200) {
        this.conversationData = resData.data;
      }
      this.emptyState = this.conversationData.length === 0;
      this.initialLoading = false;
    },
    chatConversationHandler(conversation) {
      this.$router.push({
        name: "onlineChat",
        query: { conversationId: conversation.id },
      });
    },
    async getUserData() {
      const res = await this.$ApiServiceLayer.get(
        this.$PATH.RELATIVE_PATH.MULTI.STORE_SETTING,
        ""
      );
      if (res.status === 200) {
        this.userData = res.data[0];
      }
    },
  },
};
</script>

<style lang="scss" scoped>
.chat_container {
  margin: 72px 20px;
  .cards {
    display: flex;
    align-items: center;
    padding: 12px;
    justify-content: space-between;
    border-bottom: 1px solid var(--darken-color);

    .date_time {
      font-family: "IRANYekanfa" !important;
      font-size: 12px;
    }
    .last_message_body {
      color: var(--Neutral-100);
    }
    .unread_message_count {
      background: var(--primary-color);
      border-radius: 50%;
      display: flex;
      justify-content: center;
      align-items: center;
      width: 18px;
      height: 18px;
      padding: 8px;
    }
    p {
      margin-bottom: 4px;
    }
  }
}
.empty_state {
  display: flex;
  justify-content: center;
  align-items: center;
  margin-top: 140px;
}
</style>
