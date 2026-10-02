<template>
	<div class="pic-page">
		<div class="box">
			<span class="title">فیلترها</span>
			<div class="row mt-3">
				<div class="col d-flex flex-column">
					<label for="html">استان:</label>
					<select @change="getCityOnChange" v-model="pickProvince" class="form-select">
						<option v-for="province in provinceLists" :value="province.id" :key="province.id">
							{{ province.name }}
						</option>
					</select>
				</div>
				<div class="col d-flex flex-column">
					<label for="html">شهر:</label>
					<select v-model="pickCity" class="form-select">
						<option v-for="city in cityLists" :value="city.city.id" :key="city.city.id">
							{{ city.city.name }}
						</option>
					</select>
				</div>
				<div class="col d-flex flex-column">
					<label for="html">کد مشتری:</label>
					<input class="inputs" v-model="storeCode" />
				</div>
				<!-- <div class="col d-flex flex-column">
					<label for="html">نوع مشتری:</label>
					<select v-model="pickStore" class="form-select">
						<option :value="1">برند شاپ</option>
						<option :value="2">مشتری زنجیره ای</option>
						<option :value="3">مولتی برند</option>
					</select>
				</div> -->

				<!-- <div class="col d-flex flex-row align-items-end w-100">
					<button @click="getDataPackage((limit = 10), (offset = 0))" class="accept">تایید</button>
					<button class="remove-filtes" @click="removeFilter">حذف فیلتر</button>

				</div> -->
			</div>
			<div class="row mt-3">
				<div class="col d-flex flex-column">
					<label for="html">تاریخ ویزیت:</label>
					<input type="text" class="custom-input inputs" />
					<date-picker
						v-model="rangeDate"
						range
						clearable
						format="YYYY-MM-DDTHH:mm:00"
						display-format="jMMMM jD"
						custom-input=".custom-input"
					/>
				</div>

				<div class="col d-flex flex-column">
					<label for="html">پرومتر:</label>
					<select v-model="selectRoleAssigment" class="form-select">
						<option v-for="role in roleAssigmentData" :value="role.user.id" :key="role.id">
							{{ role.user.first_name }} {{ role.user.last_name }}
						</option>
					</select>
				</div>
				<div class="col d-flex flex-column">
					<label for="html">وضعیت بررسی:</label>
					<select v-model="checkStatus" class="form-select">
						<option :value="true">بررسی شده</option>
						<option :value="false">بررسی نشده</option>
					</select>
				</div>
			</div>
			<div class="row mt-3">
				<div class="col"></div>
				<div class="col"></div>
				<div class="col d-flex align-items-end w-100 justify-content-end">
					<button @click="getDataPackage((limit = 20), (offset = 0))" class="accept">تایید</button>
					<button class="remove-filtes" @click="removeFilter">حذف فیلتر</button>
				</div>
			</div>
		</div>
		<div>
			<div class="table-box">
				<div class="d-flex justify-content-between">
					<pagination
						v-model="page"
						:per-page="20"
						:records="totalDataCount"
						@paginate="myCallback"
					/>
					<div class="d-flex flex-row align-items-center">
						<span class="ordering-title">مرتب سازی بر اساس تاریخ:</span>
						<b-form-select
							v-model="selected"
							:options="options"
							class="ordering"
							value-field="item"
							text-field="name"
							@change="getDataPackage((limit = 20), (offset = 0), (order = selected))"
						></b-form-select>
					</div>
				</div>
				<Tableview
					:hover="true"
					:bordered="true"
					:showNoContent="showContnetFunc"
					:showNoData="showDataFunc"
				>
					<template #TableTitle>
						<tr>
							<th class="table-header">ردیف</th>
							<th class="table-header">تصویر</th>
							<th class="table-header">نام نیرو</th>
							<th class="table-header">شهر</th>
							<th class="table-header">نام مشتری</th>
							<th class="table-header">کد مشتری</th>
							<th class="table-header">بررسی شده</th>
							<th class="table-header">تاریخ</th>
							<th class="table-header">نوبت</th>
							<th class="table-header">مشاهده</th>
						</tr>
					</template>

					<template #TableBody>
						<tr v-for="(item, index) in dataPackage" :key="item.id">
							<td class="table-cell persian-number">
								{{ 20 * (page - 1) + 1 + index }}
							</td>
							<td class="table-cell">
								<img @click="callModalimage(item)" class="answers-images" :src="item.link" />
							</td>
							<td class="table-cell">{{ item.visit.promoter.first_name }} {{ item.visit.promoter.last_name }}</td>
							<td class="table-cell">{{ item.visit.building.city.name }}</td>
							<td class="table-cell">{{ item.visit.building.name }}</td>
							<td class="table-cell persian-number">
								{{ item.visit.building.code }}
							</td>
							<td class="table-cell">
								<CustomSwitch
									:modelValue="item.is_checked"
									@change="(newValue) => changeImageStatus(item, newValue)"
								/>
							</td>
							<td class="table-cell">
								<date-picker
									v-model="item.datetime_created"
									type="datetime"
									format="YYYY-MM-DD HH:mm"
									display-format="jYYYY-jMM-jDD HH:mm"
									:timezone="true"
									:disabled="true"
								/>
							</td>
							<td class="table-cell persian-number">{{ item.visit.visit_turn }}</td>
							<td class="table-cell">
								<img
									@click="visitDetail(item)"
									class="eye-icon"
									src="../../assets/images/iconPack/eye.svg"
								/>
							</td>
						</tr>
					</template>
				</Tableview>
				<b-modal hide-footer hide-header size="lg" centered v-model="imageModal">
					<img class="modal-img" :src="imageUrl" />
				</b-modal>
			</div>
		</div>
	</div>
</template>

<script>
import Tableview from '../../components/Tableview/index.vue';
import Pagination from 'vue-pagination-2';
import CustomSwitch from '../../components/CustomSwitch/index.vue';

export default {
	components: {
		Tableview,
		Pagination,
		CustomSwitch,
	},
	data() {
		return {
			dataPackage: 0,
			cityLists: [],
			provinceLists: [],
			pickProvince: '',
			pickCity: '',
			selectedkCity: '',
			storeCode: '',
			pickStore: '',
			visitTurn: '',
			pickPromoter: [],
			roleAssigmentData: [],
			rangeDate: ['', ''],
			imageModal: false,
			imageUrl: '',
			checkStatus: '',
			selectRoleAssigment: '',
			page: 1,
			type: {},
			checked: false,
			queryStates: window.location.href.split('/').slice(-1)[0],
			totalDataCount: 0,
			selected: '-datetime_last_change',
			options: [
				{ item: '-datetime_last_change', name: 'نزولی' },
				{ item: 'datetime_last_change', name: ' صعودی' },
			],
		};
	},
	async mounted() {
		// this.queryStates =  window.location.search;
		await this.getType();
		this.getDataPackage();
		this.getCity();
		this.getProvince();
		this.$router.afterEach(this.handleUrlChange);
		this.getRoleAssigmentData();
	},

	computed: {
		selectedCityId() {
			return this.pickCity.id;
		},
		selectedProvinceId() {
			return this.pickProvince.id;
		},
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
		async handleUrlChange(to, from) {
			'sss', to.params.id, from.params.id;
			this.queryStates = to.params.id;

			await this.getType();
			this.getDataPackage();
			this.getCity();
			this.getProvince();
		},
		removeFilter() {
			this.pickCity = '';
			this.storeCode = '';
			this.pickProvince = '';
			this.selectedkCity = '';
			this.checkStatus = '';
			this.visitTurn = '';
			this.selectRoleAssigment = '';
			this.rangeDate = ['', ''];
			this.getDataPackage();
			this.getCity();
		},
		callModalimage(item) {
			this.imageModal = true;
			this.imageUrl = item.link;
		},
		getCityOnChange() {
			this.selectedkCity = this.pickProvince;
			this.getCity();
		},
		async getType() {
			const res = await this.$ApiServiceLayer.get(
				this.$PATH.RELATIVE_PATH.GET.MENU_EDIT + '/' + this.queryStates + '/' + '?p=' +
				this.$STORE.state.userConfig.setProjectId,
				this.$PATH.SERVICE_NAME.AUTH,
			);
			if (res.status === 200) {
				this.type = res.data;
			}
		},
		async getDataPackage(limit = 20, offset = 0) {
			if (this.rangeDate[0] !== '' && this.rangeDate[1] == undefined) {
				this.rangeDate[1] = this.rangeDate[0].slice(0, 11) + '23:59:59';
			} else if (this.rangeDate[0] === null || this.rangeDate[0] === undefined) {
				this.rangeDate[0] = '';
			}
			const res = await this.$ApiServiceLayer.get(
				this.$PATH.RELATIVE_PATH.GET.GET_PHOTO_LIST +
					'?type__name__in=' +
					this.type.frontend_api_queryparams +
					'&visit__outlet__city=' +
					this.pickCity +
					'&visit__outlet__city__province=' +
					this.pickProvince +
					'&visit__outlet__code=' +
					this.storeCode +
					'&visit__outlet__category=' +
					this.pickStore +
					'&visit__promoter=' +
					this.selectRoleAssigment +
					'&is_checked=' +
					this.checkStatus +
					'&datetime_created__gte=' +
					this.rangeDate[0] +
					'&datetime_created__lte=' +
					this.rangeDate[1] +
					'&visit__visit_turn=' +
					this.visitTurn +
					'&limit=' +
					limit +
					'&offset=' +
					offset +
					'&ordering=' +
					this.selected +
					'&p=' +
					this.$STORE.state.userConfig.setProjectId,
				this.$PATH.SERVICE_NAME.AUTH,
			);
			if (res.status === 200) {
				this.dataPackage = res.data.results;
				for (let i of this.dataPackage) {
					if (i.visit.outlet.city === null) {
						i.visit.outlet.city = {};
						i.visit.outlet.city.name = '-';
					}
				}
				this.totalDataCount = res.data.count;
			}
		},
		async getRoleAssigmentData() {
			const res = await this.$ApiServiceLayer.get(
				this.$PATH.RELATIVE_PATH.GET.ROLE_ASSIGNMENT +
					'?p=' +
					this.$STORE.state.userConfig.setProjectId,
				this.$PATH.SERVICE_NAME.AUTH,
			);
			if (res.status === 200) {
				this.roleAssigmentData = res.data;
				console.log(this.roleAssigmentData);
			}
		},
		async changeImageStatus(item, newValue) {
			// Update the UI immediately
			item.is_checked = newValue;

			const res = await this.$ApiServiceLayer.patch(
				this.$PATH.RELATIVE_PATH.MULTI.DELETE_IMAGE + item.id + '/' + '?p=' +
				this.$STORE.state.userConfig.setProjectId,
				this.$PATH.SERVICE_NAME.AUTH,
				{ is_checked: newValue },
			);
			if (res.status === 200) {
				this.$notify({
					group: 'tc',
					type: 'success',
					text: 'وضعیت بررسی عکس با موفقیت تغییر کرد!',
				});
			} else {
				// If API call fails, revert the switch to its previous state
				item.is_checked = !newValue;
			}
		},
		async getProvince() {
			const res = await this.$ApiServiceLayer.get(
				this.$PATH.RELATIVE_PATH.GET.GET_PROVINCE_LIST +
					'?p=' +
					this.$STORE.state.userConfig.setProjectId,
				this.$PATH.SERVICE_NAME.AUTH,
			);
			if (res.status === 200) {
				this.provinceLists = res.data;
			}
		},
		async getCity() {
			const res = await this.$ApiServiceLayer.get(
				this.$PATH.RELATIVE_PATH.GET.GET_CITY_LIST +
					'?city__province=' +
					this.selectedkCity +
					'&p=' +
					this.$STORE.state.userConfig.setProjectId,
				this.$PATH.SERVICE_NAME.AUTH,
			);
			if (res.status === 200) {
				this.cityLists = res.data;
			}
		},
		async myCallback() {
			await this.getDataPackage(20, 20 * (this.page - 1));
		},
		visitDetail(items) {
			if (items.type.is_for_supervision === true) {
				let routeData = this.$router.resolve({
					name: 'supervisionAnswerLists',
					params: { id: items.visit.id },
				});
				window.open(routeData.href);
			} else {
				let routeData = this.$router.resolve({
					name: 'answerListCustomers',
					params: { id: items.visit.id },
				});
				window.open(routeData.href);
			}
		},
	},
	watch: {
		queryStates: {
			handler(value) {
				value;
			},
		},
		immediate: true, // This ensures the watcher is triggered upon creation
	},
};
</script>
<style lang="scss" scoped>
.pic-page {
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
			border-radius: 4px;
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
			width: 50%;
			border-radius: 4px;
		}
	}
	.table-box {
		background: #fff;
		border-radius: 8px;
		padding: 24px;
	}
	.remove-filtes {
		width: 50%;
		border: 1px solid #357AE1;
		border-radius: 2px;
		color: #357AE1;
		height: 38px;
		background: #fff;
		border-radius: 4px;
	}
}
/* Removed conflicting styles - now handled in table-cell styles */

.persian-number {
	font-family: 'IRANYekanfa' !important;
}
.modal-img {
	width: 100%;
}
/* Eye icon styles moved to table-cell section for better organization */
.ordering-title {
	min-width: 200px;
}

/* Table styling improvements */
.table-header {
	font-weight: 600;
	padding: 12px 8px;
	text-align: center;
	vertical-align: middle;
	border-bottom: 2px solid #dee2e6;
	white-space: nowrap;
}

.table-cell {
	padding: 12px 8px;
	text-align: center;
	vertical-align: middle;
	// border-bottom: 1px solid #dee2e6;
	white-space: nowrap;
	overflow: hidden;
	text-overflow: ellipsis;
	max-width: 150px;
}

.table-cell:nth-child(1) { /* ردیف */
	width: 60px;
}

.table-cell:nth-child(2) { /* تصویر */
	width: 120px;
}

.table-cell:nth-child(3) { /* نام نیرو */
	width: 120px;
}

.table-cell:nth-child(4) { /* شهر */
	width: 100px;
}

.table-cell:nth-child(5) { /* نام مشتری */
	width: 150px;
}

.table-cell:nth-child(6) { /* کد مشتری */
	width: 100px;
}

.table-cell:nth-child(7) { /* بررسی شده */
	width: 100px;
}

.table-cell:nth-child(8) { /* تاریخ */
	width: 120px;
}

.table-cell:nth-child(9) { /* نوبت */
	width: 60px;
}

.table-cell:nth-child(10) { /* مشاهده */
	width: 80px;
}

/* Ensure table doesn't break layout */
.table-box table {
	width: 100%;
	border-collapse: collapse;
	table-layout: fixed;
}

/* Improve image display */
.answers-images {
	max-width: 100px;
	max-height: 60px;
	object-fit: cover;
	border-radius: 4px;
	cursor: pointer;
}

/* Improve eye icon */
.eye-icon {
	width: 24px;
	height: 24px;
	cursor: pointer;
	transition: opacity 0.2s;
}

.eye-icon:hover {
	opacity: 0.7;
}
</style>
<style>





/* Table layout styles moved to table-cell section for better organization */
.td-desc {
	border: 1px solid #ddd;
	max-width: 28ch;
	word-wrap: break-word;
}
td:after {
	content: '\00A0';
}
.tr-desc {
	width: 30%;
}
</style>
