<template>
	<div>
		<Loading v-if="loading" />
		<div class="empty-container" v-if="!loading && actionPlanList.length === 0">
			<h4>هیچ برنامه ای وجود ندارد!</h4>
		</div>
		<div v-else class="action-list">
			<div class="warning-box">
				<img src="@/assets/images/iconPack/warning.svg" />
				<span class="mr-2">توجه</span>
				<ul>
					<li>
						لیست زیر در حال حاضر در وضعیت غیرفعال قرار دارد. در صورت تایید دکمه ثبت نهایی را بزنید.
					</li>
					<li>
						در جدول زیر می توانید لیست برنامه درخواستی خود را ببینید. در صورت نیاز می توانید هر کدام
						از موارد را پاک کرده و مجدد از صفحه ی ثبت برنامه روزانه با دیتای صحیح ثبت کنید.
					</li>
				</ul>
			</div>
			<div class="box">
				<pagination
					v-model="page"
					:per-page="20"
					:records="totalDataCount"
					@paginate="myCallback"
				/>
				<Tableview
					:hover="true"
					:bordered="true"
					:showNoContent="showContnetFunc"
					:showNoData="showDataFunc"
				>
					<template #TableTitle>
						<tr>
							<th>ردیف</th>
							<!-- <th>نام نیروی اجرایی</th>
							<th>شماره نیروی اجرایی</th> -->
							<th>شهر</th>
							<th>نام ساختمان</th>
							<th>آدرس</th>
							<th>تاریخ برنامه</th>
							<th>عملیات</th>
							<th>
								<div class="divcheckbox">
									<span class="choice" >انتخاب</span>
									<input  type="checkbox" :checked="allSelected" @click="selectAllPlanLists" />
								</div>
							</th>
						</tr>
					</template>

					<template #TableBody>
						<tr v-for="(item, index) in actionPlanList" :key="item.id">
							<td class="persian-number">
								{{ index + 1 }}
							</td>
							<!-- <td>{{ item.promoter.first_name }} {{ item.promoter.last_name }}</td>
							<td>{{ item.promoter.username }}</td> -->
							<td>{{ item.building.city.name }}</td>
							<td>{{ item.building.name }}</td>
							<td>{{ item.building.address }}</td>
							<td>
								<date-picker
									v-model="item.due_date"
									type="datetime"
									format="YYYY-MM-DD HH:mm"
									display-format="jYYYY-jMM-jDD HH:mm"
									:timezone="true"
									:disabled="true"
								/>
							</td>
							<td>
								<img
									@click="deleteItemFunc(item.id)"
									class="delete-icon"
									src="@/assets/images/iconPack/red-trash.svg"
								/>
							</td>
							<td>
								<input
									type="checkbox"
									:checked="selectedPlanList.includes(item.id)"
									@change="toggleItemSelection(item.id)"
								/>
							</td>
						</tr>
					</template>
				</Tableview>
				<div class="d-flex justify-content-end">
					<button @click="deleteSelectedModals = true" class="delete-item">حذف</button>
					<button @click="confirmItems" class="confirm-item">ثبت نهایی</button>
				</div>
			</div>
			<b-modal v-model="deleteItemModal" hide-footer hide-header centered>
				<div class="p-3">
					<div>آیا از حذف خود اطمینان دارید؟</div>
					<div class="d-flex justify-content-end mt-4">
						<button @click="deleteItem" class="confirm-item">بله</button>
						<button @click="deleteItemModal = !deleteItemModal" class="reject-item">خیر</button>
					</div>
				</div>
			</b-modal>

			<b-modal v-model="deleteSelectedModals" hide-footer hide-header centered>
				<div class="p-3">
					<div>آیا از حذف خود اطمینان دارید؟</div>
					<div class="d-flex justify-content-end mt-4">
						<button @click="deleteItems" class="confirm-item">بله</button>
						<button @click="deleteSelectedModals = !deleteSelectedModals" class="reject-item">
							خیر
						</button>
					</div>
				</div>
			</b-modal>
		</div>
	</div>
</template>

<script>
import Tableview from '../../components/Tableview/index.vue';
import Pagination from 'vue-pagination-2';
import Loading from '../../components/Loading/index.vue';
export default {
	components: {
		Tableview,
		Pagination,
		Loading,
	},
	data() {
		return {
			actionPlanList: 0,
			deleteItemModal: false,
			ids: null,
			page: 1,
			totalDataCount: 0,
			loading: false,

			selectedPlanList: [],
			deleteSelectedModals: false,
			saveSelectedModals: false,
		};
	},
	computed: {
		showContnetFunc() {
			return this.actionPlanList === 0;
		},
		showDataFunc() {
			if (this.actionPlanList.length !== undefined) {
				return this.actionPlanList.length === 0;
			}
			return false;
		},
		allSelected() {
			return this.selectedPlanList.length == this.actionPlanList.length;
		},
	},
	mounted() {
		this.getActionPlanLists();
	},
	methods: {
		async getActionPlanLists(limit = 20, offset = 0) {
			this.loading = true;
			try {
				const res = await this.$ApiServiceLayer.get(
					this.$PATH.RELATIVE_PATH.GET.ACTION_PLAN_LISTS +
						'?limit=' +
						limit +
						'&offset=' +
						offset +
						'&p=' +
						this.$STORE.state.userConfig.setProjectId +
						'&is_active=false',
					this.$PATH.SERVICE_NAME.AUTH
				);
				if (res.status === 200) {
					this.loading = false;
					this.actionPlanList = res.data.results;
					this.actionPlanList;
					this.totalDataCount = res.data.count;
				}
			} finally {
				this.loading = false;
			}
		},
		selectAllPlanLists() {
			if (this.selectedPlanList.length == this.actionPlanList.length) {
				this.selectedPlanList = [];
			} else {
				this.actionPlanList.forEach((element) => {
					const id = element.id;
					if (!this.selectedPlanList.includes(id)) {
						this.selectedPlanList.push(id);
					}
				});
			}
		},
		toggleItemSelection(ids) {
			const index = this.selectedPlanList.indexOf(ids);
			if (index !== -1) {
				this.selectedPlanList.splice(index, 1);
			} else {
				this.selectedPlanList.push(ids);
			}
		},
		deleteItemFunc(ids) {
			this.deleteItemModal = !this.deleteItemModal;
			this.ids = ids;
		},
		async deleteItem() {
			const res = await this.$ApiServiceLayer.delete(
				this.$PATH.RELATIVE_PATH.MULTI.EDIT_ACTION_PLAN + this.ids + '/' + '?p=' +
					this.$STORE.state.userConfig.setProjectId,
				this.$PATH.SERVICE_NAME.AUTH,
				{},
			);
			if (res.status === 204) {
				this.deleteItemModal = !this.deleteItemModal;
				this.$notify({
					group: 'tc',
					type: 'success',
					text: 'برنامه با موفقیت حذف شد!',
				});
				this.getActionPlanLists();
			}
		},
		async myCallback() {
			await this.getTicketList(20, 20 * (this.page - 1));
		},
		async deleteItems() {
			const itemIds = this.actionPlanList.map((item) => item.id);
			const res = await this.$ApiServiceLayer.post(
				this.$PATH.RELATIVE_PATH.MULTI.BULK_UPDATE + '?p=' +
					this.$STORE.state.userConfig.setProjectId,
				this.$PATH.SERVICE_NAME.AUTH,
				{
					is_active: false,
					is_deleted: true,
					id: itemIds,
				},
			);
			if (res.status === 200) {
				this.selectedPlanList = [];
				location.reload();
			}
		},
		async confirmItems() {
			const itemIds = this.actionPlanList.map((item) => item.id);
			const res = await this.$ApiServiceLayer.post(
				this.$PATH.RELATIVE_PATH.MULTI.BULK_UPDATE + '?p=' +
				this.$STORE.state.userConfig.setProjectId,
				this.$PATH.SERVICE_NAME.AUTH,
				{
					is_active: true,
					is_deleted: false,
					id: itemIds,
				},
			);
			if (res.status === 200) {
				location.reload();
			}
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
	.warning-box {
		padding: 16px;
		color: #664d03;
		background: #fff3cd;
		li {
			margin: 0px 34px;
			list-style: disc;
		}
	}
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

.delete-item {
	padding: 8px;
	background: #f54545;
	border: #f54545;
	border-radius: 4px;
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
<style>


.divcheckbox {
    display: flex;
    justify-content: space-evenly;
}

input[type="checkbox"] {
    box-sizing: border-box;
    padding: 0;
    -webkit-appearance: none;
    outline: none;
    background-color: #fff;
    width: 15px;
    height: 15px;
    cursor: pointer;
    border: 1px solid #000;
    border-radius: 4px;
    position: relative;
	margin-top:3px;
}

input[type="checkbox"]:checked::before {
    content: '✔';
    display: block;
    color:#63a8a4;
    font-size: 12px;
    position: absolute;
    top: -2px;
    left: 2px;
}

</style>
