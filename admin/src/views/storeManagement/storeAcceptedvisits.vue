<template>
	<div class="follow-order">
		<div class="box">
			<span class="title">فیلترها</span>
			<div class="row mt-3">
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
						<option v-for="promoter in promoterLists" :value="promoter.id" :key="promoter.id">
							{{ promoter.user.first_name }} {{ promoter.user.last_name }}
						</option>
					</select>
				</div>
				<div class="col d-flex flex-column">
					<label for="html">نوبت:</label>
					<input class="inputs" v-model="visitTurn" />
				</div>
				<div class="col d-flex flex-column">
					<label for="html">کد مشتری:</label>
					<input class="inputs" v-model="storeCode" />
				</div>
				<div class="col d-flex flex-row align-items-end w-100">
					<button @click="getDataPackage(limit = 20 , offset= 0)" class="accept">تایید</button>
					<button class="remove-filtes" @click="removeFilter">حذف فیلتر</button>
				</div>
			</div>
		</div>
		<div class="box">
			<div>
				<div class="d-flex">
					<pagination
						v-model="page"
						:per-page="20"
						:records="totalDataCount"
						@paginate="myCallback"
					/>
				</div>
				<Tableview
					:hover="true"
					:bordered="true"
					:showNoContent="showContnetFunc"
					:showNoData="showDataFunc"
				>
					<template #TableTitle>
						<tr>
							<th>ردیف</th>
							<th>شهر</th>
							<th>نام مشتری</th>
							<th>ادرس مشتری</th>
							<th>کد مشتری</th>
							<th>نام نیروی اجرایی</th>
							<!-- <th>شماره نیروی اجرایی</th> -->
							<th>تاریخ ویزیت</th>
							<th>نوبت</th>
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
							<td>{{ item.outlet.address }}</td>
							<td>{{ item.outlet.code }}</td>
							<td>{{ item.promoter.first_name }} {{ item.promoter.last_name }}</td>
							<!-- <td class="persian-number">
								{{ item.promoter.username }}
							</td> -->
							<td class="persian-number">
								<date-picker
									v-model="item.start_datetime"
									type="datetime"
									format="YYYY-MM-DD HH:mm"
									display-format="jYYYY-jMM-jDD HH:mm"
									:timezone="true"
									:disabled="true"

								/>
								<!-- {{ item.start_datetime.substring(0, 10) }} -->
							</td>
							<td class="persian-number">{{ item.visit_turn }}</td>
							<td>
                <RowActions :items="[{ label: 'مشاهده جزئیات', icon: 'view', action: () => visitDetail(item.id) }]" />
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
			pickCity: '',
			pickPromoter: '',
			visitTurn: '',
			storeCode: '',
			page: 1,
			totalDataCount: 0,

		};
	},
	mounted() {
		this.getDataPackage();
		this.getCity();
		this.getPromoterLists();
	},
	computed: {
		selectedPromoterId() {
			return this.pickPromoter.id;
		},
		selectedCityId() {
			return this.pickCity.id;
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
		removeFilter() {
			this.pickCity = '';
			this.pickPromoter = '';
			this.visitTurn = '';
			this.storeCode = '';
			this.getDataPackage();
		},
		async getDataPackage(limit = 20, offset = 0) {
			const url = window.location.href;
			const lastParam = url.split('/').slice(-1)[0];
			const res = await this.$ApiServiceLayer.get(
				this.$PATH.RELATIVE_PATH.GET.GET_VISIT_LIST +
					'?status=3' +
					'&outlet=' + lastParam +
					'&outlet__city=' +
					this.pickCity +
					'&promoter=' +
					this.pickPromoter +
					'&outlet__code=' +
					this.storeCode +
					'&visit_turn=' +
					this.visitTurn +
					'&limit=' +
					limit +
					'&offset=' +
					offset +
					'&ordering=visit_turn' +
					'&p=' + this.$STORE.state.userConfig.setProjectId
					,
				this.$PATH.SERVICE_NAME.AUTH,
			);
			if (res.status === 200) {
				this.dataPackage = res.data.results;
				('dataPackage:', this.dataPackage);
				this.totalDataCount = res.data.count;
			}
		},
		async myCallback() {
			await this.getDataPackage(20, 20 * (this.page - 1));
		},
		async getCity() {
			const res = await this.$ApiServiceLayer.get(
				this.$PATH.RELATIVE_PATH.GET.GET_CITY_LIST + '?p=' + this.$STORE.state.userConfig.setProjectId,
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
		visitDetail(id) {
			let routeData = this.$router.resolve({ name: 'answerListCustomers', params: { id: id } });
			window.open(routeData.href);
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
		width: 50%;
		border-radius: 4px;

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
.eye-icon {
	width: 32px;
	cursor: pointer;
}
.remove-filtes {
	width: 50%;
	border: 1px solid #357AE1;
	border-radius: 2px;
	color: #357AE1;
	height: 38px;
	background: #fff;
}
</style>
