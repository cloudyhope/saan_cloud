<template>
	<div class="create-warehouse">
		<div class="box">
			<div>اطلاعات کالا</div>
			<div class="d-flex flex-row align-items-center mt-3">
				<div class="row mt-3 w-100">
					<div class="col-lg-6 col-sm-12">
						<Materialnput label="نام انگلیسی کالا" v-model="enName" inputType="text" />
					</div>
					<div class="col-lg-6 col-sm-12">
						<Materialnput label="نام فارسی کالا" v-model="faName" />
					</div>
					<div class="col-lg-6 col-sm-12">
						<Materialnput label="کد کالا" v-model="productCode" />
					</div>
					<div class="col-lg-6 col-sm-12"></div>
					<div class="col-lg-6 col-sm-12">
						<label for="ware-unit">واحد اندازه‌گیری:</label>
						<select id="ware-unit" style="width: 100%" v-model="unit" class="search-input">
							<option
								v-for="measurment in wareMeasurment"
								:value="measurment.id"
								:key="measurment.id"
							>
								<span>{{ measurment.unit_fa }}</span>
							</option>
						</select>
					</div>
					<div class="col-lg-6 col-sm-12">
						<label for="ware-type">نوع کالا:</label>
						<select id="ware-type" style="width: 100%" v-model="productType" class="search-input">
							<option v-for="types in wareType" :value="types.id" :key="types.id">
								<span>{{ types.verbose_name }}</span>
							</option>
						</select>
					</div>
					<div class="col-lg-12 col-sm-12">
						<b-form-textarea
							id="textarea"
							v-model="textareaProduct"
							placeholder="توضیحات"
							rows="3"
							max-rows="6"
						></b-form-textarea>
					</div>
					<div class="d-flex col-lg-6 col-sm-12 mt-3">
						<input class="ml-2" v-model="checkBox" type="checkbox" />
						<span>این کالا مصرفی می باشد.</span>
					</div>
					<div class="col-lg-12 col-sm-12 mt-3" v-if="checkBox">
						<span>لطفا نوع ویزیت های خود را انتخاب کنید.</span>
						<b-form-group>
							<b-form-checkbox-group v-model="selected">
								<b-form-checkbox v-for="visit in visitTypeList" :key="visit.id" :value="visit.id">{{
									visit.verbose_name
								}}</b-form-checkbox>
							</b-form-checkbox-group>
						</b-form-group>
					</div>
				</div>
			</div>
			<div class="button-container">
				<button @click="openModal" :disabled="checkEmpty" class="continue">ثبت</button>
			</div>
			<b-modal size="lg" v-model="modal" hide-footer centered>
				<div class="my-4">
					<div>لطفا انبار مد نظر جهت ذخیره این کالا را انتخاب کرده و مقدار ورودی را وارد کنید:</div>
					<div class="d-flex justify-content-between align-items-center my-3">
						<div class="w-100">
							<label for="opening-quantity">مقدار: </label>
							<input id="opening-quantity" v-model="useInputValue" type="number" min="1" step="1" class="inputs w-75" />
						</div>
						<div class="d-flex justify-content-end align-items-end w-100">
							<label for="opening-location">انبار:</label>
							<select id="opening-location" v-model="pickLocation" class="inputs w-75">
								<option v-for="location in locationLists" :value="location.id" :key="location.id">
									{{ location.name_fa }}
								</option>
							</select>
						</div>
					</div>
					<!-- <b-form-textarea
						id="textarea"
						v-model="textareaTransaction"
						placeholder="توضیحات"
						rows="3"
						max-rows="6"
						class="mb-3"
					></b-form-textarea> -->
					<div class="d-flex justify-content-end">
						<button @click="postData" :disabled="checkModalEmpty || busy" class="confirm-item">{{ busy ? 'در حال ثبت…' : 'ثبت' }}</button>
					</div>
				</div>
			</b-modal>
		</div>
	</div>
</template>
<script>
import { persistentRequestKey, clearRequestKey } from '@/utils/idempotency';
// import Tableview from '../../components/Tableview/index.vue';
import Materialnput from '../../components/MaterialInput/indx.vue';

export default {
	components: {
		Materialnput,
	},
	data() {
		return {
			enName: null,
			faName: null,
			productCode: null,
			textareaProduct: null,
			// textareaTransaction: null,
			checkBox: false,
			wareType: [],
			productType: null,
			unit: null,
			visitTypeList: [],
			selected: [],
			wareMeasurment: [],
			modal: false,
			pickLocation: '',
			locationLists: [],
			useInputValue: null,
			busy: false,
		};
	},
	mounted() {
		this.getWareType();
		this.getVisitType();
		this.getWareMeasurement();
	},
	computed: {
		checkEmpty() {
			return !String(this.enName || '').trim() || !String(this.faName || '').trim() ||
				!String(this.productCode || '').trim() || !this.productType || !this.unit ||
				(this.checkBox && !this.selected.length);
		},
		checkModalEmpty() {
			if (
				!Number.isSafeInteger(Number(this.useInputValue)) ||
				Number(this.useInputValue) <= 0 ||
				this.pickLocation === null ||
				this.pickLocation === '' 
			) {
				return true;
			} else {
				return false;
			}
		},
	},
	methods: {
		async getWareType() {
			const res = await this.$ApiServiceLayer.get(
				this.$PATH.RELATIVE_PATH.MULTI.WAREHOUSE_TYPE +
					'?p=' +
					this.$STORE.state.userConfig.setProjectId,
				this.$PATH.SERVICE_NAME.EMPTY,
			);
			if (res.status === 200) {
				this.wareType = res.data;
			}
		},
		async getWareMeasurement() {
			const res = await this.$ApiServiceLayer.get(
				this.$PATH.RELATIVE_PATH.MULTI.UNIT_LIST_CREATE +
					'?p=' +
					this.$STORE.state.userConfig.setProjectId,
				this.$PATH.SERVICE_NAME.EMPTY,
			);
			if (res.status === 200) {
				this.wareMeasurment = res.data;
			}
		},
		async postData() {
			if (this.busy || this.checkModalEmpty) return;
			this.busy = true;
			try {
				const project = this.$STORE.state.userConfig.setProjectId;
				const payload = {
					name_en: this.enName || '',
					name_fa: this.faName,
					identifier: this.productCode,
					description: this.textareaProduct || '',
					type: this.productType,
					unit: this.unit,
					is_for_use: this.checkBox,
					quantity: Number(this.useInputValue),
					location: this.pickLocation,
					visit_types: this.checkBox ? [...this.selected] : [],
				};
				const keyScope = 'opening.' + project + '.' + this.productCode;
				payload.request_key = persistentRequestKey(keyScope, payload);
				const result = await this.$ApiServiceLayer.post(
					this.$PATH.RELATIVE_PATH.POST.WARE_OPENING_STOCK + '?p=' + project,
					this.$PATH.SERVICE_NAME.EMPTY, payload,
				);
				if (result.status !== 201 && result.status !== 200) throw new Error(this.$ApiServiceLayer.getErrorMessage(result));
				clearRequestKey(keyScope, payload.request_key);
				this.$router.push({ name: 'listWareHouse' });
			} catch (error) {
				this.$notify({ group: 'tc', type: 'error', text: error.message || 'ثبت کالا انجام نشد.' });
			} finally {
				this.busy = false;
			}
		},
		async getVisitType() {
			const res = await this.$ApiServiceLayer.get(
				this.$PATH.RELATIVE_PATH.GET.VISIT_TYPE + '?p=' + this.$STORE.state.userConfig.setProjectId,
				this.$PATH.SERVICE_NAME.AUTH,
			);
			if (res.status === 200) {
				this.visitTypeList = res.data;
			}
		},
		async getLocationLists() {
			const res = await this.$ApiServiceLayer.get(
				this.$PATH.RELATIVE_PATH.MULTI.LOCATION_LIST_CREATE +
					'?p=' +
					this.$STORE.state.userConfig.setProjectId,
				this.$PATH.SERVICE_NAME.EMPTY,
			);
			if (res.status === 200) {
				this.locationLists = res.data;
			}
		},
		openModal() {
			this.modal = !this.modal;
			this.getLocationLists();
		},
	},
};
</script>
<style lang="scss" scoped>
.create-warehouse {
	padding: 32px 50px;
	.box {
		padding: 24px;
		border-radius: 2px;
		margin-bottom: 16px;
		background: #fff;
		border-radius: 8px;
		box-shadow: 0px 4px 4px rgba(214, 214, 214, 0.6);
		.search-input {
			text-indent: 10px;
			height: 40px;
			border: 1px solid #c4c4c4;
			padding: 0 9px;
			border-radius: 2px;
			font-family: 'IRANYekanfa' !important;
			border-radius: 4px;
			margin: 8px 0;
		}
	}
	.button-container {
		display: flex;
		justify-content: flex-end;
		margin-top: 12px;
		.continue {
			border: none;
			background: #357AE1;

			border-radius: 8px;
			color: #fff;
			margin-left: 8px;
			padding: 8px 16px;
			width: 10%;
			&:disabled {
				background: #f1f1f1;
				color: #535656;
				border-radius: 8px;
				border: none;
				padding: 8px;
			}
		}
	}
}
.inputs {
	margin-top: 16px;
	width: 25%;
	height: 38px;
	border: 1px solid #c4c4c4;
	padding: 0 9px;
	border-radius: 4px;
	margin-right: 4px;
}
.confirm-item {
	background: none;
	padding: 8px;
	border: 1px solid #357AE1;
	border-radius: 4px;
	background: #357AE1;
	color: #fff;
	margin-left: 8px;
	min-width: 75px;
	&:disabled {
		border: none;
		background: #c4c4c4;
	}
}
</style>
