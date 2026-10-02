<template>
	<div class="follow-order">
		<div class="box">
			<span class="title">فیلترها</span>
			<div class="d-flex justify-content-between w-50">
				<div class="w-50 ml-4">
					<label for="html">نام سرپرست:</label>
					<select v-model="filterSelectedSupervisor" class="form-select">
						<option
							v-for="superVisior in superVisiorLists"
							:value="superVisior.user.id"
							:key="superVisior.id"
						>
							{{ superVisior.user.first_name }} {{ superVisior.user.last_name }}
						</option>
					</select>
				</div>
				<div class="w-50">
					<label for="html">نام نیروی اجرایی:</label>
					<select v-model="filterSelectedPromoter" class="form-select">
						<option
							v-for="promoter in promoterLists"
							:value="promoter.user.id"
							:key="promoter.id"
							class="w-100"
						>
							{{ promoter.user.first_name }} {{ promoter.user.last_name }}
						</option>
					</select>
				</div>
			</div>
			<div class="d-flex justify-content-end mt-4">
				<button @click="getDataPackage()" class="confirm-item">تایید</button>
				<button @click="removeFilter()" class="reject-item">حذف فیلتر</button>
			</div>
		</div>
		<div class="box">
			<div class="d-flex justify-content-between">
				<pagination
					v-model="page"
					:per-page="20"
					:records="totalDataCount"
					@paginate="myCallback"
				/>
				<div class="d-flex flex-row align-items-center">
					<button class="create_btn" @click="openCreateAssignRoleModal">ایجاد</button>
				</div>
			</div>
			<div>
				<Tableview
					:hover="true"
					:bordered="true"
					:showNoContent="showContnetFunc"
					:showNoData="showDataFunc"
				>
					<template #TableTitle>
						<tr>
							<th>ردیف</th>
							<th>نام نیروی اجرایی</th>
							<th>موبایل نیروی اجرایی</th>
							<th>نام سرپرست</th>
							<th>موبایل سرپرست</th>
							<th>عملیات</th>
						</tr>
					</template>

					<template #TableBody>
						<tr v-for="(item, index) in dataPackage" :key="`list-` + item.id">
							<td class="persian-number">
								{{ 20 * (page - 1) + 1 + index }}
							</td>
							<td>{{ item.promoter.first_name }} {{ item.promoter.last_name }}</td>
							<td class="persian-number">{{ item.promoter.username }}</td>
							<td>{{ item.supervisor.first_name }} {{ item.supervisor.last_name }}</td>
							<td class="persian-number">{{ item.supervisor.username }}</td>
							<td>
                <RowActions :items="[{ label: 'حذف', icon: 'delete', action: () => deleteItemFunc(item), danger: true }]" />
              </td>
						</tr>
					</template>
				</Tableview>
			</div>
		</div>
		<b-modal v-model="changeActiveStatusModal" hide-footer hide-header centered>
			<div class="p-3">
				<div>آیا از انجام این عملیات اطمینان دارید؟</div>
				<div class="d-flex justify-content-end mt-4">
					<button @click="changeActivestatus" class="confirm-item">بله</button>
					<button @click="!changeActiveStatusModal" class="reject-item">خیر</button>
				</div>
			</div>
		</b-modal>
		<b-modal v-model="modal" hide-footer hide-header centered>
			<div class="p-3">
				<div class="d-flex justify-content-between w-100">
					<div class="w-100 ml-2">
						<label for="html">نام سرپرست:</label>
						<select v-model="selectedSupervisor" class="form-select">
							<option
								v-for="superVisior in superVisiorLists"
								:value="superVisior.user.id"
								:key="superVisior.id"
							>
								{{ superVisior.user.first_name }} {{ superVisior.user.last_name }}
							</option>
						</select>
					</div>
					<div class="w-100">
						<label for="html">نام نیروی اجرایی:</label>
						<select v-model="selectedPromoter" class="form-select">
							<option
								v-for="promoter in promoterLists"
								:value="promoter.user.id"
								:key="promoter.id"
								class="w-100"
							>
								{{ promoter.user.first_name }} {{ promoter.user.last_name }}
							</option>
						</select>
					</div>
				</div>
				<div class="d-flex justify-content-end mt-4">
					<button @click="submitModalHandler" class="confirm-item">ثبت</button>
					<button @click="modal = false" class="reject-item">بستن</button>
				</div>
			</div>
		</b-modal>
	</div>
</template>
<script>
import Tableview from '../../components/Tableview/index.vue';
import Pagination from 'vue-pagination-2';

import RowActions from '@/components/RowActions/index.vue';
export default {
	components: { RowActions,
		Tableview,
		Pagination,
	},
	data() {
		return {
			dataPackage: 0,
			selectedUser: {},
			page: 1,
			totalDataCount: 0,
			changeActiveStatusModal: false,
			modal: false,
			superVisiorLists: [],
			promoterLists: [],
			selectedSupervisor: null,
			selectedPromoter: null,
			filterSelectedPromoter: '',
			filterSelectedSupervisor: '',
		};
	},
	mounted() {
		this.getDataPackage();
		this.getSuperVisiorLists();
		this.getPromoterLists();
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
			let res = await this.$ApiServiceLayer.get(
				this.$PATH.RELATIVE_PATH.MULTI.SUPERVISOR_LIST_CREATE +
					'?limit=' +
					limit +
					'&offset=' +
					offset +
					'&is_active=true' +
					'&promoter=' +
					this.filterSelectedPromoter +
					'&supervisor=' +
					this.filterSelectedSupervisor +
					'&p=' +
					this.$STORE.state.userConfig.setProjectId +
					'&ordering=-id',
				this.$PATH.SERVICE_NAME.AUTH,
			);
			if (res.status === 200) {
				this.dataPackage = res.data.results;

				this.totalDataCount = res.data.count;
			}
		},
		removeFilter() {
			this.filterSelectedPromoter = '';
			this.filterSelectedSupervisor = '';
			this.getDataPackage();
		},
		async submitModalHandler() {
			let res = await this.$ApiServiceLayer.post(
				this.$PATH.RELATIVE_PATH.MULTI.SUPERVISOR_LIST_CREATE + '?p=' +
				this.$STORE.state.userConfig.setProjectId,
				this.$PATH.SERVICE_NAME.AUTH,
				{
					is_active: true,
					promoter: this.selectedPromoter,
					supervisor: this.selectedSupervisor,
					project: this.$STORE.state.userConfig.setProjectId,
				},
			);
			if (res.status === 201) {
				this.modal = false;
				this.$notify({
					group: 'tc',
					type: 'success',
					text: ' عملیات با موفقیت انجام شد!',
				});
			}
			this.getDataPackage();
		},
		deleteItemFunc(item) {
			this.changeActiveStatusModal = !this.changeActiveStatusModal;
			this.selectedUser = item;
			console.log(this.selectedUser);
		},
		async getSuperVisiorLists() {
			const res = await this.$ApiServiceLayer.get(
				this.$PATH.RELATIVE_PATH.GET.ROLE_ASSIGNMENT +
					'?p=' +
					this.$STORE.state.userConfig.setProjectId +
					'&role__title_abbreviation=V',
				this.$PATH.SERVICE_NAME.AUTH,
			);
			if (res.status === 200) {
				this.superVisiorLists = res.data;
			}
		},
		async getPromoterLists() {
			const res = await this.$ApiServiceLayer.get(
				this.$PATH.RELATIVE_PATH.GET.ROLE_ASSIGNMENT +
					'?p=' +
					this.$STORE.state.userConfig.setProjectId +
					'&role__title_abbreviation=P',
				this.$PATH.SERVICE_NAME.AUTH,
			);
			if (res.status === 200) {
				this.promoterLists = res.data;
			}
		},
		async changeActivestatus() {
			let res = await this.$ApiServiceLayer.delete(
				this.$PATH.RELATIVE_PATH.MULTI.SUPERVISOR_EDIT +
					this.selectedUser.id +
					'/' +
					'?p=' +
					this.$STORE.state.userConfig.setProjectId,
				this.$PATH.SERVICE_NAME.AUTH,
				{
					is_active: false,
					supervisor: this.selectedUser.supervisor.id,
					promoter: this.selectedUser.promoter.id,
					project: this.selectedUser.project.id,
				},
			);
			if (res.status === 204) {
				this.changeActiveStatusModal = false;
				this.$notify({
					group: 'tc',
					type: 'success',
					text: 'دسترسی با موفقیت حذف گردید.',
				});
				this.getDataPackage();
			}
		},
		openCreateAssignRoleModal() {
			this.modal = true;
		},

		async myCallback() {
			await this.getDataPackage(20, 20 * (this.page - 1));
		},
	},
};
</script>
<style lang="scss" scoped>
.confirm-item {
	background: none;
	padding: 8px;
	border: 1px solid #357AE1;
	border-radius: 4px;
	background: #357AE1;
	color: #fff;
	margin-left: 8px;
	min-width: 124px;
	height: 42px;
}
.reject-item {
	border: 1px solid #357AE1;
	background: #fff;
	color: #000;
	width: 75px;
	border-radius: 4px;
	color: #357AE1;
	padding: 8px;
	min-width: 124px;
	height: 42px;
}
.follow-order {
	padding: 32px 50px;
	.box {
		// border: 1px solid #c4c4c4;
		padding: 24px;
		border-radius: 2px;
		margin-bottom: 16px;
		background: #fff;
		border-radius: 8px;
		box-shadow: 0px 4px 4px rgba(214, 214, 214, 0.6);

		.title {
			font-weight: 700;
			font-size: 18px;
		}
		.package-number {
			height: 38px;
			text-indent: 10px;
		}
		.inputs {
			width: 100%;
			height: 38px;
			border: 1px solid #c4c4c4;
			padding: 0 9px;
			border-radius: 2px;
			font-family: 'IRANYekanfa' !important;
			border-radius: 4px;
		}
	}
	.persian-number {
		font-family: 'IRANYekanfa' !important;
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
	}
	.create_btn {
		border: 1px solid #357AE1;
		border-radius: 2px;
		background-color: #357AE1;
		color: #fff;
		border-radius: 4px;
		padding: 4px 12px;
	}
	.ordering-title {
		min-width: 200px;
	}
	.ordering {
		max-width: 100px;
	}
	.show-date {
		border: none;
		text-indent: 55px;
		background: #fff;
	}
	.custom-td {
		min-width: 160px;
	}
	.eye-icon {
		width: 32px;
		cursor: pointer;
	}
	.icon-complement {
		padding: 0px 5px;
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
</style>
<!--  -->
