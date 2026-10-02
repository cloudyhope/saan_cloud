<template>
	<div class="containers">
		<div class="warning">
			<div class="d-flex">
				<img src="../../assets/images/iconPack/carbon_warning-square.svg" />
				<span class="text">توجه</span>
			</div>
			<div>
				<ul>
					<li>
						با کلیک بر روی هر کدام از سوالات می توانید تصاویر و توضیحات مربوط به آن را در ۳ ویزیت
						ذکر شده مشاهده کنید.
					</li>
				</ul>
			</div>
		</div>
		<div class="outlet-detail">
			<span class="details">نام مشتری:{{ listData[0].outlet.name }}</span>
			<span class="details">آدرس مشتری:{{ listData[0].outlet.address }}</span>
			<span class="details">کد مشتری:{{ listData[0].outlet.code }}</span>
			<span class="details">شهر مشتری:{{ listData[0].outlet.city.name }}</span>
			<div class="mt-2">
				<button @click="showVisits(listData[0].outlet.id)" class="btns ml-2">
					مشاهده ویزیت‌ها
				</button>
				<button @click="action(listData[0].outlet.id)" class="btns">تاریخچه گزارش تخلف</button>
			</div>
		</div>
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
						<th>سوال</th>
						<th>پاسخ ثبت شده</th>
						<th>نوبت ویزیت</th>
					</tr>
				</template>

				<template #TableBody>
					<tr v-for="(item, index) in listData" :key="item.id">
						<td class="persian-number">
							{{ 1 + index }}
						</td>
						<td style="cursor: pointer" @click="warningDetailPage(item.id)">
							{{ item.question.text }}
						</td>
						<td v-if="item.answers[0].bool === false">خیر</td>
						<td v-else>بله</td>
						<td class="d-flex justify-content-center w-100">
							<div v-for="visits in item.answers" :key="visits.id">
								<span class="persian-number">{{ visits.visit.visit_turn }}</span>
								<!-- <span v-if="i < visits.length -1 ">,</span> -->
								<span>&nbsp;</span>
							</div>
						</td>
					</tr>
				</template>
			</Tableview>
			<b-modal size="xl" v-model="modalShow" hide-footer>
				<Tableview
					:hover="true"
					:bordered="true"
					:showNoContent="showContnetFunc2"
					:showNoData="showDataFunc2"
				>
					<template #TableTitle>
						<tr>
							<th>ردیف</th>
							<th>گزارش</th>
							<th>نوبت</th>
							<th>تاریخ</th>
						</tr>
					</template>

					<template #TableBody>
						<tr v-for="(item, index) in modalData" :key="item.id">
							<td class="persian-number">
								{{ 1 + index }}
							</td>
							<td class="td-desc">{{ item.description }}</td>
							<td class="persian-number">{{ item.visit.visit_turn }}</td>
							<td>
								<date-picker
									v-model="item.visit.start_datetime"
									type="datetime"
									format="YYYY-MM-DD HH:mm"
									display-format="jYYYY-jMM-jDD HH:mm"
									:timezone="true"
									:disabled="true"
								/>
							</td>
						</tr>
					</template>
				</Tableview>
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
			listData: 0,
			modalData: 0,
			modalShow: false,
		};
	},
	computed: {
		showContnetFunc() {
			return this.listData === 0;
		},
		showDataFunc() {
			if (this.listData.length !== undefined) {
				return this.listData.length === 0;
			}
			return false;
		},
		showContnetFunc2() {
			return this.modalData === 0;
		},
		showDataFunc2() {
			if (this.modalData.length !== undefined) {
				return this.modalData.length === 0;
			}
			return false;
		},
	},
	mounted() {
		this.getWarningDetail();
	},
	methods: {
		async getWarningDetail() {
			const url = window.location.href;
			const lastParam = url.split('/').slice(-1)[0];
			const res = await this.$ApiServiceLayer.get(
				this.$PATH.RELATIVE_PATH.GET.WARNING_API +
					'?outlet=' +
					lastParam +
					'&p=' +
					this.$STORE.state.userConfig.setProjectId,

				this.$PATH.SERVICE_NAME.AUTH,
			);
			if (res.status === 200) {
				this.listData = res.data;
			}
		},
		showVisits(id) {
			let routeData = this.$router.resolve({
				name: 'storeManagementAcceptedvisits',
				params: { outlet: id },
			});
			window.open(routeData.href);
		},
		async action(id) {
			const res = await this.$ApiServiceLayer.get(
				this.$PATH.RELATIVE_PATH.MULTI.INFRACTIONS_ACTIONS +
					'?visit__outlet__id=' +
					id +
					'&ordering=-start_datetime' +
					'&p=' +
					this.$STORE.state.userConfig.setProjectId,
				this.$PATH.SERVICE_NAME.AUTH,
			);
			if (res.status === 200) {
				this.modalData = res.data;
				this.modalShow = true;
			}
		},
		warningDetailPage(id) {
			let routeData = this.$router.resolve({ name: 'warningDetailPage', params: { id: id } });
			window.open(routeData.href);
		},
	},
};
</script>
<style lang="scss" scoped>
.containers {
	padding: 24px;
	.warning {
		display: flex;
		flex-direction: column;
		border: 1px solid #ffecb4;
		background: #fff3cd;
		padding: 16px;
		margin-bottom: 32px;
		ul {
			margin-bottom: 0 !important;
			padding: 10px 35px;
		}
		li {
			list-style: none;
		}
		.text {
			color: #664d03;
			font-size: 16px;
			margin-right: 15px;
		}
	}
	.outlet-detail {
		border: 1px dashed #c4c4c4;
		border-radius: 2px;
		padding: 16px;
		margin-bottom: 50px;
		.details {
			display: flex;
			align-items: center;
			font-size: 14px;
			margin-top: 8px;
			font-family: 'IRANYekanfa' !important;
		}
		.btns {
			border: 1px solid #285595;
			border-radius: 2px;
			background: #fff;
			padding: 5px;
			color: #285595;
			font-size: 14px;
		}
	}
	.box {
		// border: 1px solid #c4c4c4;
		background: #fff;
		padding: 24px;
		border-radius: 2px;
		margin-bottom: 16px;
		border-radius: 8px;
	}
	.persian-number {
		font-family: 'IRANYekanfa' !important;
	}
}
</style>
<style>
label {
	margin: 0 !important;
}


</style>
