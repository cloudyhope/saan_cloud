<template>
	<div>
		<div class="empty-container" v-if="uploadedFileLists.length === 0">
			<h4>هیچ فایلی وجود ندارد!</h4>
		</div>
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
							<th>نوع فایل</th>
							<th>نام</th>
							<th>آیکون</th>
							<th>لینک فایل</th>
							<th>عملیات</th>
						</tr>
					</template>

					<template #TableBody>
						<tr v-for="(item, index) in uploadedFileLists" :key="item.id">
							<td class="persian-number">
								{{ index + 1 }}
							</td>
							<td>
								<span v-if="item.type === 'EDU'">آموزش</span>
								<span v-if="item.type === 'ETC'">سایر</span>
							</td>
							<td>
								{{ item.name }}
							</td>
							<td>
								<img
									@click="watchItems(item.icon)"
									class="watch-items"
									src="../../assets/images/iconPack/eye.svg"
								/>
							</td>
							<td>
								<img
									@click="watchItems(item.file)"
									class="watch-items"
									src="../../assets/images/iconPack/eye.svg"
								/>
							</td>
							<td>
								<img
									v-b-tooltip.hover
									title="ویرایش"
									@click="editData(item)"
									class="eye-icon ml-2"
									src="../../assets/images/iconPack/basil_edit-outline.svg"
								/>
								<img
									@click="deleteItemFunc(item.id)"
									class="delete-icon"
									src="@/assets/images/iconPack/red-trash.svg"
								/>
							</td>
						</tr>
					</template>
				</Tableview>
				<!-- <div class="d-flex justify-content-end">
			<button @click="confirmItems" class="confirm-item">ثبت نهایی</button>
		</div> -->
			</div>
			<b-modal size="lg" v-model="editModal" hide-footer>
				<div class="d-flex mb-4">
					<div class="d-flex flex-column ml-3">
						<label for="html">نام</label>
						<input class="form-select" type="text" v-model="modalUserData.name" />
					</div>
					<div class="d-flex flex-column">
						<label for="html">ترتیب</label>
						<input class="form-select" type="text" v-model="modalUserData.priority" />
					</div>
				</div>
				<div class="mb-3">
					<label for="html">توضیحات</label>
					<textarea v-model="modalUserData.description" class="textarea"></textarea>
				</div>
				<div class="d-flex justify-content-end align-items-end">
					<button @click="editBtn" class="accept">تایید</button>
					<button class="remove-filtes" @click="editModal = false">بستن</button>
				</div>
			</b-modal>
			<b-modal v-model="deleteItemModal" hide-footer hide-header centered>
				<div class="p-3">
					<div>آیا از حذف خود اطمینان دارید؟</div>
					<div class="d-flex justify-content-end mt-4">
						<button @click="deleteItem" class="confirm-item">بله</button>
						<button @click="deleteItemModal = !deleteItemModal" class="reject-item">خیر</button>
					</div>
				</div>
			</b-modal>
		</div>
	</div>
</template>

<script>
import Tableview from '../../components/Tableview/index.vue';

export default {
	components: {
		Tableview,
	},
	data() {
		return {
			uploadedFileLists: 0,
			deleteItemModal: false,
			ids: null,
			editModal: false,
			modalUserData: {},
		};
	},
	mounted() {
		this.getUploadedFile();
	},
	computed: {
		showContnetFunc() {
			return this.uploadedFileLists === 0;
		},
		showDataFunc() {
			if (this.uploadedFileLists.length !== undefined) {
				return this.uploadedFileLists.length === 0;
			}
			return false;
		},
	},
	methods: {
		async getUploadedFile() {
			const res = await this.$ApiServiceLayer.get(
				this.$PATH.RELATIVE_PATH.MULTI.UPLOAD_FILE +
					'?p=' +
					this.$STORE.state.userConfig.setProjectId,
				this.$PATH.SERVICE_NAME.EMPTY,
			);
			if (res.status === 200) {
				this.uploadedFileLists = res.data;
			}
		},
		watchItems(file) {
			file;
			window.open(file);
		},
		deleteItemFunc(ids) {
			this.deleteItemModal = !this.deleteItemModal;
			this.ids = ids;
		},
		editData(item) {
			this.editModal = true;
			this.modalUserData = { ...item };
			console.log(this.modalUserData);
		},
		async editBtn() {
			const data = {
				name: this.modalUserData.name,
				description: this.modalUserData.description,
				priority: this.modalUserData.priority,
			};
			const res = await this.$ApiServiceLayer.patch(
				this.$PATH.RELATIVE_PATH.MULTI.FILE_EDIT +
					this.modalUserData.id +
					'/' +
					'?p=' +
					this.$STORE.state.userConfig.setProjectId,
				this.$PATH.SERVICE_NAME.ORDER,
				data,
			);
			if (res.status === 200) {
				this.$notify({
					group: 'tc',
					type: 'success',
					text: 'تغییرات با موفقیت اعمال شد!',
				});
				this.getUploadedFile();
				this.editModal = false;
			}
		},
		async deleteItem() {
			const res = await this.$ApiServiceLayer.delete(
				this.$PATH.RELATIVE_PATH.MULTI.EDIT_UPLOAD_FILE + this.ids + '/' + '?p=' +
				this.$STORE.state.userConfig.setProjectId,
				this.$PATH.SERVICE_NAME.AUTH,
				{},
			);
			if (res.status === 204) {
				this.deleteItemModal = !this.deleteItemModal;
				this.$notify({
					group: 'tc',
					type: 'success',
					text: 'فایل با موفقیت حذف شد!',
				});
				this.getUploadedFile();
			}
		},
		// async confirmItems() {
		// 	const itemIds = this.uploadedFileLists.map((item) => item.id);
		// 	const res = await this.$ApiServiceLayer.post(
		// 		this.$PATH.RELATIVE_PATH.MULTI.BULK_UPDATE,
		// 		this.$PATH.SERVICE_NAME.AUTH,
		// 		{
		// 			is_active: true,
		// 			id: itemIds,
		// 		},
		// 	);
		// 	if (res.status === 200) {
		// 		this.$router.push({ name: 'newAction' });
		// 	}
		// },
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
.form-select {
	width: 100%;
	border: 1px solid #c4c4c4;
	height: 38px;
	padding: 0 9px;
	border-radius: 2px;
	color: #828282;
	border-radius: 4px;
}
.accept {
	height: 38px;
	background: #357AE1;
	border-radius: 2px;
	color: #fff;
	border: none !important;
	margin-left: 10px;
	width: 100px;
	border-radius: 4px;
	padding: 0 16px;
	min-width: 64px;
}
.remove-filtes {
	padding: 0 16px;
	border: 1px solid #357AE1;
	border-radius: 2px;
	color: #357AE1;
	height: 38px;
	background: #fff;
	border-radius: 4px;
	min-width: 64px;
}
.textarea {
	border: 1px solid #c4c4c4;
	width: 100%;
	border-radius: 4px;
	min-height: 100px;
	padding: 10px;
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
.eye-icon {
	width: 32px;
	cursor: pointer;
}
</style>
