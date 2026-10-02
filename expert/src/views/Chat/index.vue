<template>
  <div>
    <BaseTopBar title="چت با پشتیبان" />
    <!-- <div class="guide_box">
        لطفا جهت استعلام قیمت از نیروی اجرایی، تمامی اطلاعات کالای درخواستی خود را به
        صورت یکجا بنویسید. به طور مثال: "لطفا قیمت خرید قسطی آیفون ۱۳، ۱۲۸ گیگ،
        با رنگ آبی، ارسال بفرمایید"
      </div> -->
    <div class="chat_containers">
      <Skeleton
        v-if="skeleton"
        type="chat-bubble"
        :count="cardSkeletonNumber"
        :loading="true"
      />

      <template v-else>
        <div
          v-for="conversation in conversationMessage"
          :key="conversation.id"
        >
          <div
            :class="
              conversation.user.username === userData.username
                ? 'general_style my_style'
                : 'general_style others_style'
            "
          >
            <p
              v-if="
                conversation.user.extended.first_name === '' ||
                conversation.user.extended.last_name === '' ||
                conversation.user.extended.first_name === null ||
                conversation.user.extended.last_name === null
              "
            >
              ناشناس
            </p>
            <p v-else>
              {{ conversation.user.extended.first_name }}
              {{ conversation.user.extended.last_name }}
            </p>
            <div>{{ conversation.body }}</div>
            <span class="date_time">
              {{ getTimeOnly(conversation.datetime_created_fa) }}</span
            >
          </div>
        </div>
      </template>
    </div>
    <div class="fixed-box">
      <button
        :disabled="disabledSentChat"
        @click="createMessage()"
        class="send-button"
      >
        <v-progress-circular
          v-if="loading"
          indeterminate
          color="#fff"
          size="20"
          rotate="360"
        ></v-progress-circular>
        <img v-else src="@/assets/images/Icons/telegram-send.svg" />
      </button>
      <input
        type="text"
        class="input-box"
        v-model="textMessage"
        placeholder="اینجا تایپ کنید..."
      />
    </div>
  </div>
</template>

<script>
import BaseTopBar from "@/components/Topbar/BaseTopbar.vue";
import Skeleton from "@/components/Skeleton/index.vue";

export default {
  components: {
    Skeleton,
    BaseTopBar,
  },
  data: () => ({
    userData: {},
    conversationData: {},
    conversationMessage: [],
    textMessage: "",
    loading: false,
    intervalId: null,
    watchTrigger: 0,
    cardSkeletonNumber: 8,
    skeleton: true,
  }),
  computed: {
    disabledSentChat() {
      if (this.textMessage === "" || this.textMessage === null) {
        return true;
      } else {
        return false;
      }
    },
  },
  async created() {
    const id = this.$route.query.conversationId;
    if (id !== null && id !== undefined) {
      this.conversationData.id = id;
    } else {
      this.conversationData = {};
    }
    await this.getUserData();
    if (Object.keys(this.conversationData).length !== 0) {
      this.getUserMessage();
    } else {
      await this.getConversationList();
      this.getUserMessage();
    }
    this.intervalId = setInterval(() => {
      this.watchTrigger += 1;
    }, 10000);
  },

  beforeDestroy() {
    if (this.intervalId) {
      clearInterval(this.intervalId);
    }
  },
  methods: {
    async getUserData() {
      const res = await this.$ApiServiceLayer.get(
        this.$PATH.RELATIVE_PATH.MULTI.STORE_SETTING,
        this.$PATH.SERVICE_NAME.CORE
      );
      if (res.status === 200) {
        this.userData = res.data[0];
      }
    },
    async getConversationList() {
      const resData = await this.$ApiServiceLayer.get(
        this.$PATH.RELATIVE_PATH.MULTI.CONVERSATION_LIST_CREATE +
          "?store_loyalty_plan=" +
          this.$route.params.id +
          "&creator=" +
          this.userData.id +"&p=" + this.$STORE.state.userConfig.selectedProject,
        this.$PATH.SERVICE_NAME.UTILS
      );
      if (resData.status === 200) {
        if (resData.data.length !== 0) {
          this.conversationData = resData.data[0];
        }
        this.skeleton = false;
      }
    },
    async createMessage() {
      this.loading = true;
      if (Object.keys(this.conversationData).length === 0) {
        const resCreateChat = await this.$ApiServiceLayer.post(
          this.$PATH.RELATIVE_PATH.MULTI.CONVERSATION_LIST_CREATE + "?p=" + this.$STORE.state.userConfig.selectedProject,
          this.$PATH.SERVICE_NAME.UTILS,
          {
            creator: this.userData.id,
            store_loyalty_plan: this.$route.params.id,
            title: "استعلام قیمت",
            subject: "استعلام قیمت",
          }
        );
        if (resCreateChat.status === 201) {
          this.conversationData = resCreateChat.data;
          this.createUserMessage();
        }
      } else {
        this.createUserMessage();
      }
    },
    async createUserMessage() {
      const resCreateMessage = await this.$ApiServiceLayer.post(
        this.$PATH.RELATIVE_PATH.MULTI.CONVERSATION_MESSAGE_LIST,
        this.$PATH.SERVICE_NAME.UTILS,
        {
          conversation: this.conversationData.id,
          body: this.textMessage,
        }
      );
      if (resCreateMessage.status === 201) {
        this.loading = false;
        this.conversationMessage = [
          ...this.conversationMessage,
          resCreateMessage.data,
        ];
        this.getUserMessage();
        this.textMessage = "";
      }
    },
    async getUserMessage() {
      if (Object.keys(this.conversationData).length !== 0) {
        const isFirstLoad = this.conversationMessage.length === 0;
        if (isFirstLoad) {
          this.skeleton = true;
        }
        const resCreateMessage = await this.$ApiServiceLayer.get(
          this.$PATH.RELATIVE_PATH.MULTI.CONVERSATION_MESSAGE_LIST +
            "?conversation=" +
            this.conversationData.id +
            "&ordering=datetime_created",
          this.$PATH.SERVICE_NAME.UTILS
        );
        if (resCreateMessage.status === 200) {
          this.conversationMessage = resCreateMessage.data;
          this.seenConversation();
        }
        this.skeleton = false;
      }
    },
    async seenConversation() {
      const resSeenConversation = await this.$ApiServiceLayer.put(
        this.$PATH.RELATIVE_PATH.MULTI.CONVERSATION_SEEN,
        this.$PATH.SERVICE_NAME.UTILS,
        {
          conversation_id: this.conversationData.id,
          is_seen: true,
        }
      );
      //   if (resSeenConversation.status === 200) {
      //   console.log()
      //     }
    },
    getTimeOnly(datetime) {
      if (datetime) {
        return datetime.split(" ")[1];
      }
      return "";
    },
  },
  watch: {
    watchTrigger(newValue, oldValue) {
      this.getUserMessage();
    },
  },
};
</script>

<style lang="scss" scoped>
.chat_containers {
  margin: 72px 20px 100px 20px;
  //   height: 100vh;
  height: calc(100vh - 92px - 70px);
  overflow-y: auto;
  padding-top: 116px;
  
}
.general_style {
  padding: 8px 12px;
  margin-bottom: 24px;
  clear: both;
  max-width: 50%;
  font-size: 16px;
  p {
    font-size: 8px;
    margin-bottom: 8px;
    font-family: "IRANYekanRegular" !important;
  }
}
.my_style {
  border-radius: 12px 12px 0px 12px;
  background-color: #d16d51;
  float: right;
  text-align: right;
}
.others_style {
  background: rgba(85, 85, 85, 0.2);
  border-radius: 12px 12px 12px 0px;
  float: left;
  text-align: left;
}
.date_time {
  font-size: 8px;
  float: left;
  margin-top: 8px;
  font-family: "IRANYekanfa" !important;
}
.fixed-box {
  position: fixed;
  bottom: 0;
  width: 100%;
  background-color: var(--darken-background);
  padding: 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;

  .input-box {
    flex: 1;
    background-color: transparent;
    box-shadow: 0px 1px 3px 0px rgba(16, 24, 40, 0.1) inset;
    border-radius: 8px;
    color: #000;
    padding: 14px 12px;
    margin-right: 10px;

    &::placeholder {
      color: rgba(157, 157, 157, 1);
    }
  }

  .send-button {
    background-color: #357AE1;
    border: none;
    border-radius: 8px;
    padding: 10px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    &:disabled {
      background: #ECECEC;
    }
    .icon-send {
      color: #fff;
      font-size: 18px;
    }
  }
}
.skeleton-container {
  display: flex;
  flex-direction: column;
}

.skeleton {
  width: 161px;
  max-height: 100px;
  margin: 5px 0;
  align-self: flex-start;
}

.skeleton-left {
  align-self: flex-start;
}

.skeleton-right {
  align-self: flex-end;
}
.guide_box {
    padding: 20px;
    border: rgba(55, 55, 55, 1);
    background-color: rgba(35, 33, 34);
    position: fixed;
    top: 72px;
  }
</style>
