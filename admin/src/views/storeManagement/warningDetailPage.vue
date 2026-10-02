<template>
	<div class="containers">
		<div class="outlet-detail">
			<span class="details">نام مشتری:{{ outletData.name }}</span>
			<span class="details">آدرس مشتری:{{ outletData.address }}</span>
			<span class="details">کد مشتری:{{ outletData.code }}</span>
			<span class="details">شهر مشتری:{{ outletData.city.name }}</span>
			<div class="mt-2">
				<button @click="showVisits(outletData.id)" class="btns ml-2">مشاهده ویزیت‌ها</button>
				<button @click="action(outletData.id)" class="btns">تاریخچه گزارش تخلف</button>
				<b-modal size="xl" v-model="modalShow" hide-footer>
					<Tableview
						:hover="true"
						:bordered="true"
						:showNoContent="showContnetFunc"
						:showNoData="showDataFunc"
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
								<td class="persian-number">
									<date-picker
										v-model="item.visit.start_datetime"
										type="datetime"
										format="YYYY-MM-DDTHH:mm:00"
										display-format="jMMMM jD"
										:disabled="true"
									/>
								</td>
							</tr>
						</template>
					</Tableview>
				</b-modal>
			</div>
		</div>
		<div v-for="answer in answerData.answers" :key="answer.id" class="box">
			<div class="d-flex justify-content-between">
				<div class="d-flex flex-column">
					<h5 class="persian-number">ویزیت {{ answer.visit.visit_turn }}</h5>
					<span class="mb-2">{{ answer.question.text }}</span>
					<span class="answer-box" v-if="answer.bool === true">بله</span>
					<span class="answer-box" v-if="answer.bool === false">خیر</span>
					<textarea
						style="border-radius: 4px"
						:disabled="true"
						rows="4"
						cols="50"
						v-model="answer.question.short_text"
					/>
				</div>
				<div class="d-flex align-items-end mr-2">
					<div v-for="img in answer.images" :key="'img' + img.id">
						<img @click="showImageModal(img.link)" class="images" :src="img.link" />
					</div>
				</div>
				<b-modal hide-footer hide-header size="lg" centered v-model="imageModal">
					<img class="modal-img" :src="imageUrl" />
				</b-modal>
			</div>
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
			answerData: [],
			imageModal: false,
			imageUrl: null,
			outletData: [],
			modalShow: false,
			modalData: 0,
		};
	},
	computed: {
		showContnetFunc() {
			return this.modalData === 0;
		},
		showDataFunc() {
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
				this.$PATH.RELATIVE_PATH.GET.ALARM_LIST +
					lastParam +
					'/' +
					'?p=' +
					this.$STORE.state.userConfig.setProjectId,

				this.$PATH.SERVICE_NAME.AUTH,
			);
			if (res.status === 200) {
				this.outletData = res.data.outlet;
				'lol', this.outletData;
				for (let answer of res.data.answers) {
					answer.images = [];
				}
				this.answerData = res.data;
				for (let answer of this.answerData.answers) {
					let x = await this.getImageList(
						answer.visit.id,
						this.answerData.question.report_category.id,
					);
					answer.images = x;
				}
				'hb', this.answerData;
			}
		},

		async getImageList(visitId, reportCat) {
			const res = await this.$ApiServiceLayer.get(
				this.$PATH.RELATIVE_PATH.GET.GET_PHOTO_LIST +
					'?visit=' +
					visitId +
					'&type__report_category=' +
					reportCat +
					'&p=' +
					this.$STORE.state.userConfig.setProjectId,
				this.$PATH.SERVICE_NAME.AUTH,
			);
			if (res.status === 200) {
				this.images = res.data;
				'images:', res.data;
			}
			return res.data;
		},
		showImageModal(url) {
			this.imageModal = true;
			this.imageUrl = url;
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
	},
};
</script>
<style lang="scss" scoped>
.containers {
	padding: 24px;
	.outlet-detail {
		border: 1px dashed #c4c4c4;
		border-radius: 2px;
		padding: 16px;
		margin-bottom: 14px;
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
		padding: 24px;
		margin-bottom: 14px;
		background: #fff;
		border-radius: 8px;

		.answer-box {
			display: flex;
			justify-content: center;
			border: 1px dotted #c4c4c4;
			padding: 5px;
			max-width: 45px;
			border-radius: 4px;
			margin-bottom: 0.5rem;
		}
		.images {
			padding: 0.25rem;
			border: 1px solid #dee2e6;
			border-radius: 0.25rem;
			height: auto;
			width: 120px;
			margin-left: 10px;
		}
	}
}
.modal-img {
	width: 100%;
}
.persian-number {
	font-family: 'IRANYekanfa' !important;
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
</style>
<style>
label {
	margin: 0 !important;
}


</style>
