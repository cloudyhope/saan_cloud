<template>
	<div class="follow-order">
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
					<select @change="getPromoterListsOnChange" v-model="pickCity" class="form-select">
						<option v-for="city in cityLists" :value="city.city.id" :key="city.city.id">
							{{ city.city.name }}
						</option>
					</select>
				</div>
				<div class="col">
					<label for="html">نوع مشتری:</label>
					<select v-model="pickStore" class="form-select">
						<option v-for="outlet in outletCat" :value="outlet.id" :key="outlet.id">
							<span>{{ outlet.verbose_name }}</span>
						</option>
					</select>
				</div>
				<div class="col">
					<label for="html">نیروی اجرایی:</label>
					<select v-model="pickPromoter" class="form-select">
						<option v-for="promoter in promoterLists" :value="promoter.user.id" :key="promoter.id">
							{{ promoter.user.first_name }} {{ promoter.user.last_name }}
						</option>
					</select>
				</div>

				<div class="col">
					<label for="html">نام سرپرست:</label>
					<select v-model="pickSupervisor" class="form-select">
						<option v-for="superVisior in superVisiorLists" :value="superVisior.user.id"
							:key="superVisior.id">
							{{ superVisior.user.first_name }} {{ superVisior.user.last_name }}
						</option>
					</select>
				</div>
			</div>
			<div class="row mt-3">
				<div class="col d-flex flex-column">
					<label for="html">نوبت:</label>
					<input class="inputs" v-model="visitTurn" />
				</div>
				<div class="col d-flex flex-column">
					<label for="html">کد مشتری:</label>
					<input class="inputs" v-model="storeCode" />
				</div>

				<div class="col">
					<label for="html">انتخاب تاریخ:</label>
					<input type="text" id="start-time" class="custom-input inputs" />
					<date-picker key="start-date" v-model="rangeDate" range clearable format="YYYY-MM-DDTHH:mm:00"
						display-format="jMMMM jD" custom-input=".custom-input" />
				</div>

				<div class="col">
					<label for="due-date">تاریخ اجرا:</label>
					<input id="due-date" type="text" class="inputs" />
					<date-picker key="due-date" v-model="dueDate" clearable format="YYYY-MM-DD"
						display-format="jMMMM jD" custom-input="#due-date" />
				</div>
				<div class="col d-flex flex-row align-items-end w-100">
					<button @click="getDataPackage((limit = 20), (offset = 0))" class="accept">تایید</button>
					<button class="remove-filtes" @click="removeFilter">حذف فیلتر</button>

					<!-- <img class="trash-icon" @click="removeFilter" src="../../assets/images/iconPack/trash-icon.png"> -->
				</div>
			</div>
		</div>
		<div class="box">
			<div class="d-flex justify-content-between">
				<pagination v-model="page" :per-page="20" :records="totalDataCount" @paginate="myCallback" />
				<div class="d-flex flex-row align-items-center">
					<span class="ordering-title">مرتب سازی بر اساس تاریخ:</span>
					<b-form-select v-model="selected" :options="options" class="ordering" value-field="item"
						text-field="name"
						@change="getDataPackage((limit = 20), (offset = 0), (order = selected))"></b-form-select>
				</div>
			</div>
			<div>
				<Tableview :hover="true" :bordered="true" :showNoContent="showContnetFunc" :showNoData="showDataFunc">
					<template #TableTitle>
						<tr>
							<th>ردیف</th>
							<th>شهر</th>
							<th>نام مشتری</th>
							<th>ادرس مشتری</th>
							<th>کد مشتری</th>
							<th>نام نیروی اجرایی</th>
							<th>نام سرپرست</th>
							<!-- <th>شماره نیروی اجرایی</th> -->
							<th>تاریخ اجرا</th>
							<th>نوبت</th>
							<th>وضعیت</th>
							<th>مشاهده</th>
						</tr>
					</template>

					<template #TableBody>
						<tr v-for="(item, index) in dataPackage" :key="item.id">
							<td class="persian-number">
								{{ 20 * (page - 1) + 1 + index }}
							</td>
							<td>{{ item.outlet.city.name }}</td>
							<td>{{ item.outlet.name }}</td>
							<td class="persian-number">{{ item.outlet.address }}</td>
							<td class="persian-number">{{ item.outlet.code }}</td>
							<td>{{ item.promoter.first_name }} {{ item.promoter.last_name }}</td>
							<td>
								{{ item.supervisors[0].supervisor.first_name }}
								{{ item.supervisors[0].supervisor.last_name }}
							</td>
							<!-- <td class="persian-number">
								{{ item.promoter.username }}
							</td> -->
							<td class="custom-td">
								<!-- <date-picker
								v-model="date"
								format="YYYY-MM-DD"
								display-format="jYYYY-jMM-jDD"
								custom-input=".custom-input"
								/> -->

								<date-picker v-model="item.due_date" type="datetime" format="YYYY-MM-DD"
									display-format="jYYYY-jMM-jDD" :timezone="true" :disabled="true" />
								<!-- <span class="custom-input"></span>
								{{ item..substring(0, 10) }} -->
							</td>
							<td class="persian-number">{{ item.visit_turn }}</td>
							<td>
								<select style="border-radius: 4px; padding: 2px" v-model="item.supervision_status"
									@change="changeVisitStatus(item)">
									<option value="0">سرکشی نشده</option>
									<option value="1">در حال سرکشی</option>
									<option value="2">تکمیل شده</option>
									<option value="3">تایید شده</option>
									<option value="4">رد شده</option>
								</select>
								<!-- <span v-if="item.status === '0'">ویزیت نشده</span>
								<span v-if="item.status === '1'">تکمیل نشده</span>
								<span v-if="item.status === '2'">تکمیل شده</span>
								<span v-if="item.status === '3'">تایید شده</span>
								<span v-if="item.status === '4'">رد شده</span> -->
							</td>
							<td>
                <RowActions :items="[{ label: 'مشاهده جزئیات', icon: 'view', action: () => supervisiorDetail(item.id) }]" />
              </td>
						</tr>
					</template>
				</Tableview>
			</div>
		</div>
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
			cityLists: [],
			promoterLists: [],
			provinceLists: [],
			superVisiorLists: [],
			dueDate: '',
			pickSupervisor: '',
			pickCity: '',
			pickProvince: '',
			pickPromoter: '',
			visitTurn: '',
			storeCode: '',
			pickStore: '',
			selectedkCity: '',
			outletCat: [],
			page: 1,
			totalDataCount: 0,
			selected: '-start_datetime',
			options: [
				{ item: '-start_datetime', name: 'نزولی' },
				{ item: 'start_datetime', name: 'صعودی' },
			],
			rangeDate: ['', ''],
		};
	},
	mounted() {
		this.getDataPackage();
		this.getCity();
		this.getPromoterLists();
		this.getProvince();
		this.getOutletCat();
		this.getSuperVisiorLists();
	},
	computed: {
		selectedPromoterId() {
			return this.pickPromoter.id;
		},
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
		getCityOnChange() {
			this.selectedkCity = this.pickProvince;
			this.getCity();
		},
		getPromoterListsOnChange() {
			this.getPromoterLists();
		},
		removeFilter() {
			this.pickCity = '';
			this.pickPromoter = '';
			this.visitTurn = '';
			this.storeCode = '';
			this.pickProvince = '';
			this.pickStore = '';
			this.rangeDate = ['', ''];
			this.selectedkCity = '';
			this.getDataPackage();
			this.getCity();
			this.getProvince();
			this.dueDate = '';
			this.pickSupervisor = '';

			this.getPromoterLists();
		},
		async getOutletCat() {
			const res = await this.$ApiServiceLayer.get(
				this.$PATH.RELATIVE_PATH.GET.OUTLET_CAT + '?p=' + this.$STORE.state.userConfig.setProjectId,
				this.$PATH.SERVICE_NAME.AUTH,
			);
			if (res.status === 200) {
				this.outletCat = res.data;
			}
		},
		async getDataPackage(limit = 20, offset = 0) {
			if (this.rangeDate[0] !== '' && this.rangeDate[1] == undefined) {
				this.rangeDate[1] = this.rangeDate[0].slice(0, 11) + '23:59:59';
			} else if (this.rangeDate[0] === null || this.rangeDate[0] === undefined) {
				this.rangeDate[0] = '';
			}
			const res = await this.$ApiServiceLayer.get(
				this.$PATH.RELATIVE_PATH.GET.GET_VISIT_LIST +
				'?outlet__city=' +
				this.pickCity +
				'&outlet__city__province=' +
				this.pickProvince +
				'&promoter=' +
				this.pickPromoter +
				'&outlet__category=' +
				this.pickStore +
				'&outlet__code=' +
				this.storeCode +
				'&visit_turn=' +
				this.visitTurn +
				'&limit=' +
				limit +
				'&offset=' +
				offset +
				'&supervisor=' +
				this.pickSupervisor +
				'&due_date=' +
				this.dueDate +
				'&ordering=' +
				this.selected +
				'&start_datetime__gte=' +
				this.rangeDate[0] +
				'&start_datetime__lte=' +
				this.rangeDate[1] +
				'&p=' +
				this.$STORE.state.userConfig.setProjectId +
				'&type__has_supervision=' +
				true,
				this.$PATH.SERVICE_NAME.AUTH,
			);
			if (res.status === 200) {
				this.dataPackage = res.data.results;
				this.totalDataCount = res.data.count;
			}
		},
		async myCallback() {
			await this.getDataPackage(20, 20 * (this.page - 1));
		},
		supervisiorDetail(id) {
			let routeData = this.$router.resolve({ name: 'supervisionAnswerLists', params: { id: id } });
			window.open(routeData.href);
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
		async changeVisitStatus(item) {
			const res = await this.$ApiServiceLayer.patch(
				this.$PATH.RELATIVE_PATH.MULTI.SUPERVISION_VISIT_STATUS + item.id + '/' + '?p=' +
				this.$STORE.state.userConfig.setProjectId,
				this.$PATH.SERVICE_NAME.AUTH,
				{
					supervision_status: item.supervision_status,
					rejection_reason: item.status === '4' ? 'nadarad' : '',
				},
			);
			if (res.status === 200) {
				this.$notify({
					group: 'tc',
					type: 'success',
					text: 'وضعیت با موفقیت تغییر پیدا کرد!',
				});
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
				{},
			);
			if (res.status === 200) {
				'city:', res.data;
				this.cityLists = res.data;
			}
		},
		async getPromoterLists() {
			const res = await this.$ApiServiceLayer.get(
				this.$PATH.RELATIVE_PATH.GET.GET_PROMOTER_LIST +
				'?p=' +
				this.$STORE.state.userConfig.setProjectId +
				'&city=' +
				this.pickCity,
				this.$PATH.SERVICE_NAME.AUTH,
			);
			if (res.status === 200) {
				'promoter:', res.data;
				this.promoterLists = res.data;
			}
		},
	},
};
</script>
<style lang="scss" scoped>
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
}
</style>
<!--  -->
