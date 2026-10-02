<template>
	<div class="action-managment">
		<div class="warning-box">
			<img src="@/assets/images/iconPack/warning.svg" />
			<span class="mr-2">توجه</span>
			<ul>
				<li>
					جهت ایجاد برنامه روزانه شماره‌ی موبایل نیروی اجرایی و کد ساختمان مورد نظر را در باکس‌های مربوطه
					وارد کنید و برای ثبت هر مورد دکمه‌ی [+] را بزنید.
				</li>
				<li>همچنین می‌توانید در صورت زیاد بودن تعداد برنامه‌ها، از بخش آپلود اکسل استفاده کنید.</li>
				<li>
					در صورت استفاده از بخش آپلود حتما از فایل نمونه استفاده کنید و سرستون های آنرا تغییر
					ندهید.
				</li>
			</ul>
		</div>
		<div class="card">
			<div class="card-body d-flex flex-column">
				<h5 class="mb-4">تعیین زمان و نوع برنامه</h5>
				<span>لطفا تاریخ اجرای این برنامه را انتخاب کنید.</span>
				<input type="text" :disabled="status" class="custom-input inputs" />
				<date-picker
					v-model="dataPicker"
					clearable
					format="YYYY-MM-DDTHH:mm:00"
					display-format="jMMMM jD"
					custom-input=".custom-input"
					:disabled="status"
				/>
				<div class="d-flex align-items-center mt-3">
					<input class="ml-3" type="checkbox" v-model="status" />
					<span>این برنامه تاریخ مشخصی برای اجرا ندارد.</span>
				</div>
				<hr />
				<div>
					<span>لطفا نوع برنامه خود را انتخاب کنید.</span>
					<div>
						<select v-model="visitTypeSelected" class="form-select inputs">
							<option v-for="visit in visitTypeList" :value="visit.id" :key="visit.id">
								{{ visit.verbose_name }}
							</option>
						</select>
					</div>
				</div>
				<hr />

				<!-- <div class="d-flex align-center">
					<input class="ml-3" type="checkbox" v-model="isLastDay" />
					ویزیت روز آخر
				</div> -->
			</div>
		</div>
		<div class="card">
			<div class="card-body">
				<PickAction ref="pickAction" @sendPhoneNumber="getTableData" />
				<div v-if="resultSuccessCount" class="result-success" role="status">{{ resultSuccessCount }} ردیف ثبت شد. ردیف‌های خطادار برای اصلاح باقی ماندند.</div>
				<div v-if="resultError" class="result-error" role="alert">{{ resultError }}</div>
				<ul v-if="resultErrors.length" class="result-errors" role="alert"><li v-for="(item, index) in resultErrors" :key="index">ردیف {{ item.index + 1 }}، کد {{ item.building_code }}: {{ item.message }}</li></ul>
			</div>
			<div class="button-container">
				<button :disabled="checkEmpty || loading" @click="continueProcess" class="continue">{{ loading ? 'در حال ثبت...' : 'مرحله بعد' }}</button>
			</div>
		</div>
		<loading v-if="loading" />
	</div>
</template>
<script>
import PickAction from '../../components/pickAction/index.vue';
import Loading from '../../components/Loading/index.vue';

export default {
	components: {
		PickAction,
		Loading,
	},
	data() {
		return {
			dataPicker: '',
			phoneNumber: null,
			status: false,
			visitTypeList: [],
			visitTypeSelected: null,
			loading: false,
			isLastDay: false,
			buildingCode: '',
			resultError: '',
			resultErrors: [],
			resultSuccessCount: 0,
		};
	},
	mounted() {
		this.getVisitType();
	},
	computed: {
		checkEmpty() {
			if (
				this.phoneNumber &&
				this.phoneNumber.length &&
				this.phoneNumber.every(row => row.outlet_code && row.promoter_phone_number &&
					row.lookupStatus !== 'loading' && row.lookupStatus !== 'error') &&
				this.visitTypeSelected !== null &&
				(this.dataPicker !== '' || this.status === true)
			) {
				return false;
			} else {
				return true;
			}
		},
	},
	methods: {
		getTableData(value) {
			this.phoneNumber = value;
		},
		async getVisitType() {
			const res = await this.$ApiServiceLayer.get(
				this.$PATH.RELATIVE_PATH.GET.VISIT_TYPE + '?p=' + this.$STORE.state.userConfig.setProjectId,
				this.$PATH.SERVICE_NAME.AUTH,
			);
			if (res.status === 200) {
				this.visitTypeList = res.data;
				this.visitTypeList;
			}
		},
		async continueProcess() {
			if (this.checkEmpty || this.loading) return;
			this.loading = true;
			this.resultError = '';
			this.resultErrors = [];
			this.resultSuccessCount = 0;
			try {
				const res = await this.$ApiServiceLayer.post(
					this.$PATH.RELATIVE_PATH.MULTI.CREATE_ACTION_PLAN +
						'?p=' +
						this.$STORE.state.userConfig.setProjectId,
					this.$PATH.SERVICE_NAME.AUTH,
					{
						project: this.$STORE.state.userConfig.setProjectId,
						actions: this.phoneNumber.map(row => ({
							building_code: row.outlet_code.trim(),
							expert_phone_number: row.promoter_phone_number.trim(),
							elevator_ids: row.elevator_ids || [],
							is_last_day: this.isLastDay,
							is_active: false,
						})),
						has_due_date: !this.status,
						due_date: this.status ? null : this.dataPicker,
						visit_type: this.visitTypeSelected,
					}
				);
				if (res.status !== 200) { this.resultError = 'ثبت برنامه انجام نشد. تاریخ، نوع خدمت و پروژه را بررسی کنید.'; return; }
				this.resultErrors = res.data.errors || [];
				this.resultSuccessCount = (res.data.successfuls || []).length;
				if (this.resultErrors.length) {
					this.$refs.pickAction.retainIndices(this.resultErrors.map(item => item.index));
				} else if (this.resultSuccessCount) {
					this.$router.push({ name: 'listActionPlan' });
				}
			} catch (error) {
				this.resultError = 'ارتباط با سرور برقرار نشد. دوباره تلاش کنید.';
			} finally {
				this.loading = false;
			}
		},
		openLoading() {
			this.$refs.loading.open();
		},
	},
};
</script>
<style lang="scss" scoped>
.action-managment {
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
	.card {
		border: none;
		margin-top: 50px;
		box-shadow: 0px 4px 4px rgba(214, 214, 214, 0.6);
		border-radius: 8px;
		padding: 24px;
		.inputs {
			margin-top: 16px;
			width: 25%;
			height: 38px;
			border: 1px solid #c4c4c4;
			padding: 0 9px;
			border-radius: 4px;
		}
	}
}
.result-success { margin-top: 16px; padding: 12px; border-radius: 8px; background: #e7f5e9; color: #17542d; }
.result-error, .result-errors { margin-top: 16px; padding: 12px 16px; border-radius: 8px; background: #fff0ef; color: #922b21; }
.button-container {
	display: flex;
	justify-content: flex-end;
	margin-top: 12px;
	.continue {
		border: none;
		background: #357AE1;
		padding: 8px;
		border-radius: 8px;
		color: #fff;
		margin-left: 8px;
		&:disabled {
			background: #f1f1f1;
			color: #535656;
			border-radius: 8px;
			border: none;
			padding: 8px;
		}
	}
}
</style>
