<template>
	<div class="transaction">
		<!-- <div class="box">
			<span class="title">فیلترها</span>

			<div class="row mt-3">
				<div class="col d-flex flex-column">
					<label for="html">کاربر:</label>
					<select v-model="pickCreator" class="form-select">
						<option v-for="creator in creatorList" :value="creator.user.id" :key="creator.id">
							{{ creator.user.first_name }} {{ creator.user.last_name }}
						</option>
					</select>
				</div>
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
			</div>
			<div class="row mt-3">
				<div class="col d-flex flex-column"></div>
				<div class="col d-flex">
					<button @click="getDataPackage((limit = 20), (offset = 0))" class="accept">تایید</button>
					<button class="remove-filtes" @click="removeFilter">حذف فیلتر</button>
				</div>
			</div>
		</div> -->
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
							<th>شناسه انتقال</th>
							<th>نوع انتقال</th>
							<th>کاربر</th>
							<th>انبار</th>
							<th>مقدار</th>
							<th>نام کالا</th>
							<th>تاریخ</th>
							<th>مجری</th>
						</tr>
					</template>

					<template #TableBody>
						<tr v-for="(item, index) in transactionLineList" :key="item.id">
							<td class="persian-number">
								{{ 20 * (page - 1) + 1 + index }}
							</td>
							<td class="persian-number">{{ item.transaction.id }}</td>
							<td>{{ kindLabel(item.transaction.movement_kind) || item.type?.verbose_name || 'گردش قدیمی' }}</td>
							<td v-if="item.user !== null">
								{{ item.user.first_name }} {{ item.user.last_name }}
							</td>
							<td v-else>-</td>
							<td v-if="item.location !== null">{{ item.location.name_fa }}</td>
							<td v-else>-</td>
							<td
								:class="{ negative: isNegative(item.amount), positive: !isNegative(item.amount) }"
								class="persian-number"
							>
								{{ item.amount }}
							</td>
							<td>{{ item.ware.name_fa }}</td>
							<td class="persian-number">
								<date-picker
									v-model="item.transaction.datetime_created"
									type="datetime"
									format="YYYY-MM-DD HH:mm"
									display-format="jYYYY-jMM-jDD HH:mm"
									:timezone="true"
									:disabled="true"
								/>
							</td>
							<td>
								{{ item.transaction.creator.first_name }} {{ item.transaction.creator.last_name }}
							</td>
							<td></td>
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
			creatorList: [],
			transactionList: [],
			transactionLineList: 0,
			pickCreator: null,
			totalDataCount: 0,
			page: 1,
			rangeDate: [],
		};
	},
	mounted() {
		this.getCreatorLists();
		this.getTransactionLine();
	},
	computed: {
		showContnetFunc() {
			return this.transactionLineList === 0;
		},
		showDataFunc() {
			if (this.transactionLineList.length !== undefined) {
				return this.transactionLineList.length === 0;
			}
			return false;
		},
	},
	methods: {
		kindLabel(kind) {
			return ({ RECEIPT: 'دریافت', OPENING: 'موجودی افتتاحی', TRANSFER: 'انتقال',
				RETURN: 'برگشت به انبار', CONSUME: 'مصرف', SCRAP: 'ضایعات' })[kind] || '';
		},
		async getCreatorLists() {
			const res = await this.$ApiServiceLayer.get(
				this.$PATH.RELATIVE_PATH.GET.ROLE_ASSIGNMENT +
					'?p=' +
					this.$STORE.state.userConfig.setProjectId +
					'&role__title_abbreviation__in=V,S,M,F,P',
				this.$PATH.SERVICE_NAME.AUTH,
			);
			if (res.status === 200) {
				this.creatorList = res.data;
				console.log(res.data);
			}
		},
		async getTransactionLine(limit = 20, offset = 0) {
			const url = window.location.href;
			const lastParam = url.split('/').slice(-1)[0];
			const res = await this.$ApiServiceLayer.get(
				this.$PATH.RELATIVE_PATH.MULTI.TRANSACTION_LINE_LIST_CREATE +
					'?ware=' +
					lastParam +
					'&limit=' +
					limit +
					'&offset=' +
					offset +
					'&ordering=-transaction__datetime_created' + '&p=' +
					this.$STORE.state.userConfig.setProjectId,
				this.$PATH.SERVICE_NAME.EMPTY,
			);
			if (res.status === 200) {
				this.transactionLineList = res.data.results;
				this.totalDataCount = res.data.count;
			}
		},
		async myCallback() {
			await this.getTransactionLine(20, 20 * (this.page - 1));
		},
		isNegative(number) {
			return number < 0;
		},
	},
};
</script>
<style lang="scss" scoped>
.transaction {
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
		.inputs {
			width: 100%;
			height: 38px;
			border: 1px solid #c4c4c4;
			padding: 0 9px;
			border-radius: 2px;
			font-family: 'IRANYekanfa' !important;
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
		.form-select {
			width: 100%;
			border: 1px solid #c4c4c4;
			height: 38px;
			padding: 0 9px;
			border-radius: 2px;
			color: #828282;
			border-radius: 4px;
		}
		.negative {
			color: red;
			font-weight: bold;
			direction: ltr;
		}
		.positive {
			color: green;
		}
	}
	.persian-number {
		font-family: 'IRANYekanfa' !important;
	}
}
</style>
