<template>
	<div>
		<EmptyState v-if="fileLists.length === 0" kind="documents" title="هیچ فایلی وجود ندارد" />
		<div v-else class="action-list">
			<div class="box">
				<Tableview
					:hover="true"
					:bordered="true"
					:showNoContent="showContnetFunc"
					:showNoData="showDataFunc"
				>
					<template #TableTitle>
						<tr>
							<th>ردیف</th>
							<th>نام آموزش</th>
							<th>توضیحات</th>
							<th>نمایش</th>
						</tr>
					</template>

					<template #TableBody>
						<tr v-for="(item, index) in fileLists" :key="item.id">
							<td class="persian-number">
								{{ index + 1 }}
							</td>

							<td>
								<img class="icons ml-2" :src="item.icon" />
								<span>{{ item.name }}</span>
							</td>
							<td v-if="item.description === null">-</td>
							<td v-else>{{ item.description }}</td>
							<td @click="openVideoModal(item.file)">
								<img class="icons" src="../../assets/images/iconPack/solar_play-broken.svg" />
							</td>
						</tr>
					</template>
				</Tableview>
				<!-- <div class="d-flex justify-content-end">
			<button @click="confirmItems" class="confirm-item">ثبت نهایی</button>
		</div> -->
			</div>
			<b-modal size="lg" v-model="videoModal" hide-footer hide-header centered>
				<video width="100%" height="600" controls>
					<source :src="files" type="video/mp4" />
				</video>
			</b-modal>
		</div>
	</div>
</template>

<script>
import Tableview from '../../components/Tableview/index.vue';

import EmptyState from '@/components/EmptyState/index.vue';
export default {
	components: { EmptyState,
		Tableview,
	},
	data() {
		return {
			fileLists: 0,
			videoModal: false,
			files: null,
		};
	},
	mounted() {
		this.getUploadedFile();
	},
	computed: {
		showContnetFunc() {
			return this.fileLists === 0;
		},
		showDataFunc() {
			if (this.fileLists.length !== undefined) {
				return this.fileLists.length === 0;
			}
			return false;
		},
	},
	methods: {
		async getUploadedFile() {
			const res = await this.$ApiServiceLayer.get(
				this.$PATH.RELATIVE_PATH.MULTI.UPLOAD_FILE + '?project__isnull=' + true + '&p=' +
				this.$STORE.state.userConfig.setProjectId,
				this.$PATH.SERVICE_NAME.EMPTY,
			);
			if (res.status === 200) {
				this.fileLists = res.data;
			}
		},
		openVideoModal(file) {
			this.videoModal = !this.videoModal;
			this.files = file;
		},
	},
};
</script>
<style lang="scss" scoped>
.empty-container {
	display: flex;
	justify-content: center;
	align-items: center;
	height: 80vh;
}
.action-list {
	width: 100%;
	padding: 24px;
	min-height: 80vh;
	.box {
		margin-top: 16px;
		padding: 24px;
		border-radius: 2px;
		margin-bottom: 16px;
		background: #fff;
		border-radius: 8px;
		box-shadow: 0px 4px 4px rgba(214, 214, 214, 0.6);
	}
	.icons {
		max-width: 32px;
	}
	.persian-number {
		font-family: 'IRANYekanfa' !important;
	}
	.watch-items {
		cursor: pointer;
	}
	.delete-icon {
		width: 32px;
	}
}
.confirm-item {
	background: none;
	padding: 8px;
	border: 1px solid #357AE1;
	border-radius: 4px;
	background: #357AE1;
	color: #fff;
	margin-left: 8px;
	min-width: 75px;
}
.reject-item {
	border: 1px solid #357AE1;
	background: #fff;
	color: #000;
	width: 75px;
	border-radius: 4px;
	color: #357AE1;
	padding: 8px;
}
</style>
