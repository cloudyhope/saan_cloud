<template>
  <div :class="wrapperClass">
    <VisitCardSkeleton v-if="type === 'visit'" :count="count" />
    <ListCardSkeleton
      v-else-if="type === 'list'"
      :count="count"
      :two-line="twoLine"
    />
    <ChatHistorySkeleton v-else-if="type === 'chat-history'" :count="count" />
    <ChatBubbleSkeleton
      v-else-if="type === 'chat-bubble'"
      :count="count"
      :max-width="maxWidth"
      :bubble-height="bubbleHeight"
    />
    <ListRowSkeleton v-else-if="type === 'list-row'" :count="count" />
    <v-sheet v-else class="pa-3">
      <v-skeleton-loader
        v-for="n in count"
        :key="'default-skeleton-' + n"
        class="mx-auto"
        :class="{ 'mt-4': n > 1 }"
        type="card"
      />
    </v-sheet>
  </div>
</template>

<script>
import VisitCardSkeleton from "./VisitCardSkeleton.vue";
import ListCardSkeleton from "./ListCardSkeleton.vue";
import ChatHistorySkeleton from "./ChatHistorySkeleton.vue";
import ChatBubbleSkeleton from "./ChatBubbleSkeleton.vue";
import ListRowSkeleton from "./ListRowSkeleton.vue";

export default {
  name: "Skeleton",
  components: {
    VisitCardSkeleton,
    ListCardSkeleton,
    ChatHistorySkeleton,
    ChatBubbleSkeleton,
    ListRowSkeleton,
  },
  props: {
    type: {
      type: String,
      default: "card",
      validator: (v) =>
        [
          "visit",
          "list",
          "chat-history",
          "chat-bubble",
          "list-row",
          "card",
        ].includes(v),
    },
    loading: {
      type: Boolean,
      default: true,
    },
    count: {
      type: Number,
      default: 3,
    },
    twoLine: {
      type: Boolean,
      default: false,
    },
    maxWidth: {
      type: String,
      default: "161px",
    },
    bubbleHeight: {
      type: String,
      default: "50px",
    },
    wrapperClass: {
      type: String,
      default: "",
    },
  },
};
</script>
