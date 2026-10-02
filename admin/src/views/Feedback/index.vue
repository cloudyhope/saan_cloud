<template>
	<div class="follow-order">
		<div class="box">
			<span class="title">فیلترها</span>

			<div class="row mt-3">


                <div class="col d-flex flex-column">
					<label for="html">کد مشتری:</label>
					<input class="inputs" v-model="storeCode" />
				</div>
				<div class="col d-flex flex-column">
					<label for="html">نوبت ویزیت</label>
					<input class="inputs" v-model="visitTurn" />
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
				<pagination
					v-model="page"
					:per-page="20"
					:records="totalDataCount"
					@paginate="myCallback"
				/>
				<!-- <div class="d-flex flex-row align-items-center">
					<span class="ordering-title">مرتب سازی بر اساس :</span>
					<b-form-select
						v-model="selected"
						:options="options"
						class="ordering"
						value-field="item"
						text-field="name"
						@change="getDataPackage((limit = 10), (offset = 0), (order = selected))"
					></b-form-select>
				</div> -->
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
							<th>بازخورد</th>
							<th>کد مشتری</th>
                            <th>نام مشتری</th>
							<th>نوبت</th>
							<th>تاریخ ویزیت</th>
                            <th>مشاهده ویزیت ها</th>
						</tr>
					</template>

					<template #TableBody>
						<tr v-for="(item, index) in dataPackage" :key="item.id">
							<td class="persian-number">
								{{ 20 * (page - 1) + 1 + index }}
							</td>
							<td>{{ item.visit_comment }}</td>
							<td class="persian-number">{{ item.outlet.code }}</td>
                            <td>{{  item.outlet.name }}</td>
							<td class="persian-number">{{ item.visit_turn }}</td>
							<td>
                                <date-picker
									v-model="item.start_datetime"
									type="datetime"
									format="YYYY-MM-DD HH:mm"
									display-format="jYYYY-jMM-jDD HH:mm"
									:timezone="true"
									:disabled="true"

								/>
                                </td>
                                <td>
								<img
									@click="detail(item.id)"
									class="eye-icon"
									src="../../assets/images/iconPack/eye.svg"
								/>
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

export default {
	components: {
		Tableview,
		Pagination,
	},
	data() {
		return {
			dataPackage: 0,
			pickProvince: '',
			pickCity: '',
            visitTurn:'',
			storeCode: '',
			selectedkCity:'',
			page: 1,
			totalDataCount: 0,

			rangeDate: [],
		};
	},
	mounted() {
		this.getDataPackage();
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
            return this.dataPackage === 0
        },
        showDataFunc() {
            if (this.dataPackage.length !== undefined){
                return this.dataPackage.length === 0
            }
            return false
        },
	},
	methods: {
		removeFilter() {

			this.storeCode = '';
			this.visitTurn = ''
			this.getDataPackage();

		},

		async getDataPackage(limit = 20, offset = 0) {
			const res = await this.$ApiServiceLayer.get(
				this.$PATH.RELATIVE_PATH.GET.GET_VISIT_LIST + '?visit_comment__isnull=false' +
					'&outlet__code=' +
					this.storeCode +
					'&visit_turn=' +
					this.visitTurn +
					'&limit=' +
					limit +
					'&offset=' +
					offset +
					'&ordering=-start_datetime' +
					'&p=' + this.$STORE.state.userConfig.setProjectId
					,
				this.$PATH.SERVICE_NAME.AUTH,
			);
			if (res.status === 200) {
				this.dataPackage = res.data.results;
				('sd:', this.dataPackage);
				this.totalDataCount = res.data.count;
			}
		},
		async myCallback() {
			await this.getDataPackage(20, 20 * (this.page - 1));
		},
		detail(id) {
			let routeData = this.$router.resolve({ name: 'answerList', params: { id: id } });
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
		background: #fff;
		padding: 24px;
		border-radius: 2px;
		margin-bottom: 16px;
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
		width: 50%;
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
		min-width: 180px;
	}
	.ordering {
		max-width: 100px;
	}
	.show-date {
		border: none;
		text-indent: 55px;
		background: #fff;
	}

	.eye-icon {
		width: 32px;
		cursor: pointer;
	}
}
</style>
