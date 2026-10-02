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
					<select v-model="pickCity" class="form-select">
						<option v-for="city in cityLists" :value="city.city.id" :key="city.city.id">
							{{ city.city.name }}
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
                <div class="col d-flex flex-column">
					<label for="html">کد مشتری:</label>
					<input class="inputs" v-model="storeCode" />
				</div>
				<div class="col d-flex flex-row align-items-end w-100">
					<button @click="getDataPackage((limit = 20), (offset = 0))" class="accept">تایید</button>
					<button class="remove-filtes" @click="removeFilter">حذف فیلتر</button>

					<!-- <img class="trash-icon" @click="removeFilter" src="../../assets/images/iconPack/trash-icon.png"> -->
				</div>
			</div>
			<div class="row mt-3">



				<div class="col">
					<label for="html">انتخاب تاریخ:</label>
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
					<!-- <label for="html">نوبت:</label>
					<input class="inputs" v-model="visitTurn" /> -->
				</div>
				<div class="col"></div>
				<div class="col"></div>
				<div class="col"></div>
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
							<th>نام پرسش‌نامه</th>
							<th>نام نیروی اجرایی</th>
							<th>شهر</th>
							<th>استان</th>
							<th>تاریخ</th>
							<th>احراز هویت</th>
							<th>موبایل پرسش‌شونده</th>
							<th>وضعیت</th>
							<th>مشاهده</th>
						</tr>
					</template>

					<template #TableBody>
						<tr v-for="(item, index) in dataPackage" :key="item.id">
							<td class="persian-number">
								{{ 20 * (page - 1) + 1 + index }}
							</td>
							<td>{{ item.survey.verbose_name }}</td>
							<td>{{ item.user.first_name }} {{ item.user.last_name }}</td>
							<td v-if="item.city !== null" class="persian-number">{{ item.city.name }}</td>
							<td v-else></td>
							<td v-if="item.province !== null" class="persian-number">{{ item.province.name }}</td>
							<td v-else></td>
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

								<date-picker
									v-model="item.datetime_created"
									type="datetime"
									format="YYYY-MM-DD HH:mm"
									display-format="jYYYY-jMM-jDD HH:mm"
									:timezone="true"
									:disabled="true"
								/>
								<!-- <span class="custom-input"></span>
								{{ item.datetime_created.substring(0, 10) }} -->
							</td>
							<td v-if="item.phone_verified === 'false'">انجام نشده</td>
							<td v-else>انجام شده</td>
							<td class="persian-number">{{ item.phone_number }}</td>
							<td>
								<select
									style="border-radius: 4px; padding: 2px"
									v-model="item.status"
									@change="changeSurveyStatus(item)"
								>
									<option value="0">تکمیل نشده</option>
									<option value="1">تکمیل شده</option>
									<option value="2">تایید شده</option>
								</select>
								<!-- <span v-if="item.status === '0'">ویزیت نشده</span>
								<span v-if="item.status === '1'">تکمیل نشده</span>
								<span v-if="item.status === '2'">تکمیل شده</span>
								<span v-if="item.status === '3'">تایید شده</span>
								<span v-if="item.status === '4'">رد شده</span> -->
							</td>
							<td>
                <RowActions :items="[{ label: 'مشاهده جزئیات', icon: 'view', action: () => surveyDetail(item.id) }]" />
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
			dataPackage:0,
			cityLists: [],
			promoterLists: [],
			provinceLists: [],
			pickCity: '',
			pickProvince: '',
			pickPromoter: '',
			visitTurn: '',
			storeCode: '',
			selectedkCity: '',
			surveyName: [],
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
		this.getSurveyNameLists();
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
		removeFilter() {
			this.pickCity = '';
			this.pickPromoter = '';
			this.visitTurn = '';
			this.storeCode = '';
			this.pickProvince = '';
			this.rangeDate = ['', ''];
			this.selectedkCity = '';
			this.getDataPackage();
			this.getCity();
			this.getProvince();
		},

		async getDataPackage(limit = 20, offset = 0) {
			if (this.rangeDate[0] !== '' && this.rangeDate[1] == undefined) {
				this.rangeDate[1] = this.rangeDate[0].slice(0, 11) + '23:59:59';
			} else if (this.rangeDate[0] === null || this.rangeDate[0] === undefined) {
				this.rangeDate[0] = '';
			}
			// ?survey=&user=&province=&city=&longitude=&latitude=&phone_verified=&phone_number=&is_closed=&is_deleted=&status=&datetime_created=&datetime_last_change=
			const res = await this.$ApiServiceLayer.get(
				this.$PATH.RELATIVE_PATH.MULTI.SURVEY_LISTS +
					'?city=' +
					this.pickCity +
					'&province=' +
					this.pickProvince +
					'&survey=1' +
					'&user=' +
					this.pickPromoter +
					'&limit=' +
					limit +
					'&offset=' +
					offset +
					'&ordering=' +
					this.selected +
					'&start_datetime__gte=' +
					this.rangeDate[0] +
					'&start_datetime__lte=' +
					this.rangeDate[1] +
                    'status=1' +
					'&p=' + this.$STORE.state.userConfig.setProjectId
                    ,
				this.$PATH.SERVICE_NAME.AUTH,
			);
			if (res.status === 200) {
				this.dataPackage = res.data.results;
				('ds', this.dataPackage);
				this.totalDataCount = res.data.count;
			}
		},
		async myCallback() {
			await this.getDataPackage(20, 20 * (this.page - 1));
		},
		surveyDetail(id) {
			let routeData = this.$router.resolve({ name: 'surveyAnswerList', params: { id: id } });
			window.open(routeData.href);
		},
		async getProvince() {
			const res = await this.$ApiServiceLayer.get(
				this.$PATH.RELATIVE_PATH.GET.GET_PROVINCE_LIST + '?p=' + this.$STORE.state.userConfig.setProjectId,
				this.$PATH.SERVICE_NAME.AUTH,
			);
			if (res.status === 200) {
				this.provinceLists = res.data;
			}
		},
		async changeSurveyStatus(item) {
			const res = await this.$ApiServiceLayer.patch(
				this.$PATH.RELATIVE_PATH.MULTI.SURVEY_EDIT + item.id + '/' + '?p=' +
				this.$STORE.state.userConfig.setProjectId,
				this.$PATH.SERVICE_NAME.AUTH,
				{ status: item.status, rejection_reason: item.status === '4' ? 'nadarad' : '' },
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
				this.$PATH.RELATIVE_PATH.GET.GET_CITY_LIST + '?city__province=' + this.selectedkCity + '&p=' + this.$STORE.state.userConfig.setProjectId,
				this.$PATH.SERVICE_NAME.AUTH,
			);
			if (res.status === 200) {
				('city:', res.data);
				this.cityLists = res.data;
			}
		},
		async getPromoterLists() {
			const res = await this.$ApiServiceLayer.get(
				this.$PATH.RELATIVE_PATH.GET.GET_PROMOTER_LIST + '?p=' + this.$STORE.state.userConfig.setProjectId,
				this.$PATH.SERVICE_NAME.AUTH,
			);
			if (res.status === 200) {
				('promoter:', res.data);
				this.promoterLists = res.data;
			}
		},
		async getSurveyNameLists() {
			const res = await this.$ApiServiceLayer.get(
				this.$PATH.RELATIVE_PATH.MULTI.SURVEY_NAME + '?p=' + this.$STORE.state.userConfig.setProjectId,
				this.$PATH.SERVICE_NAME.AUTH,
			);
			if (res.status === 200) {
				('surve', res.data);
				this.surveyName = res.data;
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
