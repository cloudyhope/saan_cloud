<template>
  <div class="follow-order">
    <div class="box list-box">
      <div>
        <Tableview
          :recordCount="totalDataCount"
          :page="page"
          :hover="true"
          :bordered="true"
          :showNoContent="loadingList"
          :showNoData="!loadingList && dataPackage.length === 0"
          :errorMessage="listError"
          @retry="getDataPackage(20, 20 * (page - 1))"
        >
          <template #footer
            ><pagination
              :disabled="loadingList"
              v-model="page"
              :per-page="20"
              :records="totalDataCount"
              @paginate="myCallback"
          /></template>

          <template #TableTitle>
            <tr>
              <th>ردیف</th>
              <th>عنوان</th>
              <th>نوع</th>
              <th>توضیحات</th>
              <th>تصویر</th>
              <th>وضعیت</th>
            </tr>
          </template>

          <template #TableBody>
            <tr v-for="(item, index) in dataPackage" :key="item.id">
              <td class="persian-number">
                {{ 20 * (page - 1) + 1 + index }}
              </td>
              <td>{{ item.title_fa || item.title }}</td>
              <td>{{ item.type?.title_fa || item.type?.title }}</td>
              <td>
                <span class="cell-text" :title="item.body_copy">{{ item.body_copy || '—' }}</span>
              </td>
              <td>
                <button
                  v-if="item.image_1"
                  type="button"
                  class="media-thumbnail"
                  :aria-label="'مشاهده تصویر ' + (item.title_fa || item.title || '')"
                  @click="openImageModal(item.image_1, item.title_fa)"
                >
                  <img :src="item.image_1" :alt="item.image_1_alter || item.title_fa" />
                </button>
                <span v-else>-</span>
              </td>
              <td>
                <span :class="item.is_active ? 'status-active' : 'status-inactive'">
                  {{ item.is_active ? 'فعال' : 'غیرفعال' }}
                </span>
              </td>
            </tr>
          </template>
        </Tableview>
      </div>
    </div>

    <b-modal
      v-model="showImageModal"
      :title="modalImageTitle"
      modal-class="media-image-modal"
      size="lg"
      centered
      hide-footer
    >
      <div class="image-modal-content">
        <img :src="modalImageUrl" :alt="modalImageTitle" class="modal-image" />
      </div>
    </b-modal>
  </div>
</template>
<script>
import Tableview from '../../components/Tableview/index.vue';
import Pagination from '@/components/ListPagination/index.vue';

export default {
  components: {
    Tableview,
    Pagination,
  },
  data() {
    return {
      loadingList: true,
      listError: '',
      dataPackage: [],
      totalDataCount: 0,
      page: 1,
      showImageModal: false,
      modalImageUrl: '',
      modalImageTitle: '',
    };
  },
  async mounted() {
    this.getDataPackage();
  },
  computed: {
    showContnetFunc() {
      return this.dataPackage === 0;
    },
    showDataFunc() {
      if (this.dataPackage.length !== undefined) {
        return this.dataPackage.length === 0;
      }
      return false;
    },
  },
  methods: {
    async getDataPackage(limit = 20, offset = 0) {
      this.loadingList = true;
      this.listError = '';
      try {
        const res = await this.$ApiServiceLayer.get(
          this.$PATH.RELATIVE_PATH.MULTI.MEDIA_LIST_CREATE +
            '?p=' +
            this.$STORE.state.userConfig.setProjectId +
            '&limit=' +
            limit +
            '&offset=' +
            offset,
          ''
        );
        if (res.status !== 200) {
          this.listError = this.$ApiServiceLayer.getErrorMessage(res);
          return;
        }
        if (res.status === 200) {
          this.dataPackage = res.data.results;
          this.totalDataCount = res.data.count;
        }
      } finally {
        this.loadingList = false;
      }
    },
    async myCallback() {
      await this.getDataPackage(20, 20 * (this.page - 1));
    },
    openImageModal(imageUrl, imageTitle) {
      this.modalImageUrl = imageUrl;
      this.modalImageTitle = imageTitle || 'تصویر';
      this.showImageModal = true;
    },
    closeImageModal() {
      this.showImageModal = false;
      this.modalImageUrl = '';
      this.modalImageTitle = '';
    },
  },
  watch: {},
};
</script>
<style lang="scss" scoped>
.media-thumbnail {
  padding: 0;
  border: 1px solid var(--admin-border);
  border-radius: 9px;
  background: #f5f7fb;
  overflow: hidden;
}
.media-thumbnail img {
  display: block;
  width: 48px;
  height: 48px;
  object-fit: cover;
}

.follow-order {
  .status-active {
    background-color: #d4edda;
    color: #155724;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 12px;
    font-weight: 500;
  }

  .status-inactive {
    background-color: #f8d7da;
    color: #721c24;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 12px;
    font-weight: 500;
  }

  .image-modal-content {
    text-align: center;
    padding: 10px;
  }

  .modal-image {
    max-width: 100%;
    max-height: 70vh;
    border-radius: 8px;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    object-fit: contain;
  }
}
</style>

<style>
.media-image-modal .modal-header .close {
  padding: 0;
  margin: 0;
}
</style>
