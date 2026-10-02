<template>
	<div class="main-container">
		<div class="vin-input-container">
			<table class="vin-table">
				<thead>
					<tr>
						<th></th>
						<th>شماره موبایل نیروی اجرایی</th>
						<th>کد ساختمان</th>
						<th>آسانسورهای برنامه</th>
						<th></th>
						<th class="delete" @click="deleteAll">حذف همه موارد</th>
					</tr>
				</thead>
				<tbody>
					<tr v-for="(item, index) in actionModel" :key="item.id" class="td-data">
						<td class="line">{{ index + 1 }}.</td>
						<td>
							<input type="text" v-model="item.promoter_phone_number" class="data-input" @input="emitRows" />
						</td>
						<td>
							<input type="text" v-model="item.outlet_code" class="data-input" aria-label="کد ساختمان" @input="resetElevators(item)" />
						</td>
						<td class="elevator-picker">
							<button type="button" class="add-item" :disabled="!item.outlet_code || item.lookupStatus === 'loading'" @click="loadElevators(item)">{{ item.lookupStatus === 'loading' ? 'در حال دریافت...' : 'انتخاب آسانسور' }}</button>
							<div v-if="item.lookupStatus === 'ready'" class="elevator-options">
								<label v-for="row in item.elevators" :key="row.elevator.id"><input type="checkbox" :value="row.elevator.id" v-model="item.elevator_ids" @change="emitRows" />{{ row.elevator.title || ('آسانسور ' + row.elevator.id) }}</label>
								<small v-if="!item.elevators.length">آسانسوری به این ساختمان متصل نیست؛ برنامه برای کل ساختمان ثبت می‌شود.</small>
							</div>
							<small v-if="item.lookupStatus === 'error'" role="alert">ساختمان یا آسانسورها دریافت نشدند. کد را بررسی و دوباره تلاش کنید.</small>
						</td>
						<td>
							<!-- <button
								@click="openGuideModal"
								v-if="actionModel.length === index + 1"
								class="add-item"
							>
								<img src="../../assets/images/iconPack/guide.svg" />
							</button> -->
							<button @click="addItem" v-if="actionModel.length === index + 1" class="add-item">
								<img src="@/assets/images/iconPack/plus-green.svg" />
								افزودن
							</button>
						</td>
						<td class="delete" @click="deleteItem(item.id, index)">
							<!-- <span class="iconify delete-border" data-icon="fluent:delete-20-regular"></span> -->
							<img class="iconify delete-border" src="@/assets/images/iconPack/red-trash.svg" />
						</td>
					</tr>
				</tbody>
			</table>
		</div>
		<div class="file-vin-container">
			<div class="title-file-text-container">
				<p>برای ورود گروهی، <a href="/action-plan-template.xlsx" download="saan-action-plan-template.xlsx">فایل نمونه سان</a> را دریافت کنید. هر ردیف یک ساختمان و شماره کارشناس دارد؛ شناسه‌های آسانسور اختیاری‌اند و با «;» جدا می‌شوند.</p>
			</div>
			<div class="upload-box">
				<input type="file" accept=".xlsx,.csv" aria-label="بارگذاری فایل برنامه" :disabled="isUploading" @change="senExcelFile" />
				<div class="icon">
					<!-- <span class="iconify" data-icon="ic:outline-file-upload"></span> -->
					<img class="iconify" src="@/assets/images/iconPack/upload.svg" />
				</div>
				<span class="upload-text">{{ isUploading ? 'در حال خواندن فایل...' : 'انتخاب فایل XLSX یا CSV' }}</span>
				<p>حداکثر ۲ مگابایت و ۲۰۰ ردیف</p>
			</div>
			<p v-if="uploadError" class="upload-error" role="alert">{{ uploadError }}</p>
		</div>
		<b-modal size="lg" v-model="guideModal" hide-footer hide-header centered>
			<div class="p-4">
				<div class="row d-flex">
					<div class="col d-flex flex-column">
						<label for="html">استان:</label>
						<select @change="getCityOnChange" v-model="pickProvince" class="form-select inputs">
							<option v-for="province in provinceLists" :value="province.id" :key="province.id">
								{{ province.name }}
							</option>
						</select>
					</div>
					<div class="col d-flex flex-column">
						<label for="html">شهر:</label>
						<select v-model="pickCity" class="form-select inputs">
							<option v-for="city in cityLists" :value="city.city.id" :key="city.city.id">
								{{ city.city.name }}
							</option>
						</select>
					</div>
					<div class="col d-flex flex-column">
						<label for="html">نوع مشتری:</label>
						<select v-model="pickOtlet" class="form-select inputs">
							<option v-for="outlet in outletCat" :value="outlet.id" :key="outlet.id">
								<span>{{ outlet.verbose_name }}</span>
							</option>
						</select>
					</div>
				</div>
				<div class="mt-3 w-100 d-flex justify-content-end">
					<button :disabled="disabledSearch" @click="outletCodeResult" class="add-item ml-0">
						جستجو
					</button>
				</div>
			</div>
		</b-modal>
		<b-modal size="lg" scrollable v-model="outletCodeModal" hide-footer centered>
			<div class="w-100 d-flex justify-content-center" v-if="loading">
				<b-spinner  label="Spinning"></b-spinner>
			</div>
			<Tableview v-else :hover="true" :bordered="true" :showNoContent="showContnetFunc"
					:showNoData="showDataFunc">
				<template #TableTitle>
					<tr>
						<th>ردیف</th>
						<th>شهر</th>
						<th>نوع مشتری</th>
						<th>نام مشتری</th>
						<th>آدرس</th>
						<th>کد</th>
					</tr>
				</template>

				<template #TableBody>
					<tr v-for="(item, index) in outletList" :key="item.id">
						<td class="persian-number">
							{{ index + 1 }}
						</td>
						<td>{{ item.city.name }}</td>
						<td>
							<span v-if="item.category.name === 'ChainStore'">مشتری زنجیره ای</span>
							<span v-if="item.category.name === 'MultiBrand'">مولتی برند</span>
							<span v-if="item.category.name === 'BrandShop'">برند شاپ</span>
						</td>
						<td>{{ item.name }}</td>
						<td>{{ item.address }}</td>
						<td
							ref="mylink"
							v-b-tooltip.hover
							title="برای کپی کردن کد روی کد کلیک کنید."
							@click="copyText(item.code)"
							class="coppy-code"
						>
							{{ item.code }}
						</td>
					</tr>
				</template>
			</Tableview>
		</b-modal>
	</div>
</template>
<script>
import Tableview from '../../components/Tableview/index.vue';

export default {
	data() {
		return {
			guideModal: false,
			cityLists: [],
			provinceLists: [],
			pickProvince: '',
			pickCity: '',
			pickOtlet: '',
			outletCat: [],
			outletList: 0,
			outletCodeModal: false,
			message: '',
			loading:false,
			isUploading: false,
			uploadError: '',
			nextRowId: 2,
			actionModel: [{ id: 1, promoter_phone_number: null, outlet_code: '', elevator_ids: [], elevators: [], lookupStatus: '' }],
		};
	},
	components: {
		Tableview,
	},
	mounted() { this.emitRows(); },
	props: {
		fromParent: {
			type: Boolean,
			default: false,
		},
		vinParent: {
			type: Array,
		},
	},
	computed: {
		disabledSearch() {
			if (this.pickProvince === '' || this.pickProvince === null) {
				return true;
			} else {
				return false;
			}
		},
		showContnetFunc() {
            return this.outletList === 0
        },
        showDataFunc() {
            if (this.outletList.length !== undefined){
                return this.outletList.length === 0
            }
            return false
        },
	},
	methods: {
		emitRows() { this.$emit('sendPhoneNumber', this.actionModel); },
		resetElevators(item) {
			item.elevator_ids = [];
			item.elevators = [];
			item.lookupStatus = '';
			this.emitRows();
		},
		async loadElevators(item) {
			const code = (item.outlet_code || '').trim();
			if (!code) return;
			item.lookupStatus = 'loading';
			try {
				const response = await this.$ApiServiceLayer.get(
					'/api/visit/BuildingListCreate/?p=' + this.$STORE.state.userConfig.setProjectId + '&code=' + encodeURIComponent(code),
					this.$PATH.SERVICE_NAME.EMPTY,
				);
				const rows = response.status === 200 ? (Array.isArray(response.data) ? response.data : response.data.results || []) : [];
				const building = rows.find(row => row.code === code);
				if (!building) { item.lookupStatus = 'error'; return; }
				item.elevators = building.elevators || [];
				item.lookupStatus = 'ready';
			} catch (_) { item.lookupStatus = 'error'; }
		},
		retainIndices(indices) {
			this.actionModel = this.actionModel.filter((_, index) => indices.includes(index));
			if (!this.actionModel.length) this.actionModel = [{ id: 1, promoter_phone_number: '', outlet_code: '', elevator_ids: [], elevators: [], lookupStatus: '' }];
			this.emitRows();
		},
		addItem() {
			if (
				!this.actionModel[this.actionModel.length - 1].promoter_phone_number ||
				!this.actionModel[this.actionModel.length - 1].outlet_code
			) {
				this.$notify({
					group: 'tc',
					type: 'danger',
					text: 'تکمیل هر دو بخشِ شماره نیروی اجرایی و کد مشتری جهت ثبت برنامه الزامی است.',
				});
			} else {
				this.actionModel.push({
					id: this.nextRowId++,
					promoter_phone_number: '',
					outlet_code: '',
					elevator_ids: [], elevators: [], lookupStatus: '',
				});
				this.$emit('sendPhoneNumber', this.actionModel);
			}
		},
		outletCodeResult() {
			this.outletCodeModal = !this.outletCodeModal;
			this.guideModal = !this.guideModal;
			this.loading = true;
			this.getOutletList();
		},
		openGuideModal() {
			this.guideModal = !this.guideModal;
			this.getCity();
			this.getProvince();
			this.getOutletCat();
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
		async getOutletList() {
			const res = await this.$ApiServiceLayer.get(
				this.$PATH.RELATIVE_PATH.GET.GET_OUTLET_LIST +
					'?p=' +
					this.$STORE.state.userConfig.setProjectId + '&city=' + this.pickCity + '&city__province=' + this.pickProvince + '&category=' + this.pickOtlet,
				this.$PATH.SERVICE_NAME.AUTH,
			);
			if (res.status === 200) {
				this.loading = false;
				this.outletList = res.data;
			}
		},
		async copyText(code) {
			try {
				await navigator.clipboard.writeText(code);
				this.$notify({
					group: 'tc',
					type: 'success',
					text: ' کد با موفقیت کپی شد!',
				});
			} catch (err) {
				(err);
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
		async getOutletCat() {
			const res = await this.$ApiServiceLayer.get(
				this.$PATH.RELATIVE_PATH.GET.OUTLET_CAT + '?p=' + this.$STORE.state.userConfig.setProjectId,
				this.$PATH.SERVICE_NAME.AUTH,
			);
			if (res.status === 200) {
				this.outletCat = res.data;
			}
		},
		getCityOnChange() {
			this.selectedkCity = this.pickProvince;
			this.getCity();
		},
		deleteItem(id, index) {
			if (index === 0 && this.actionModel.length === 1) {
				return false;
			} else {
			this.actionModel.splice(index, 1);
			this.emitRows();
			}
		},
		deleteAll() {
			this.actionModel = [];
			this.actionModel.push({ id: 1, promoter_phone_number: null, outlet_code: '', elevator_ids: [], elevators: [], lookupStatus: '' });
			this.nextRowId = 2;
			this.$emit('sendPhoneNumber', this.actionModel);
		},
		async senExcelFile(e) {
			const file = e.target.files && e.target.files[0];
			if (!file) return;
			this.uploadError = '';
			if (!/\.(xlsx|csv)$/i.test(file.name) || file.size > 2 * 1024 * 1024) {
				this.uploadError = 'فقط XLSX یا CSV تا ۲ مگابایت پذیرفته می‌شود.';
				return;
			}
			this.isUploading = true;
			try {
				const form = new FormData();
				form.append('file', file);
				const res = await this.$ApiServiceLayer.post(
					this.$PATH.RELATIVE_PATH.POST.UPLOAD_EXCEL_FILE + '?p=' + this.$STORE.state.userConfig.setProjectId,
					'', form,
				);
				if (res.status !== 200 || !res.data || !Array.isArray(res.data.data)) {
					this.uploadError = res.data && res.data.file ? String(res.data.file[0]) : 'خواندن فایل انجام نشد. قالب نمونه را بررسی کنید.';
					return;
				}
				this.actionModel = res.data.data.map((row, index) => ({
					id: index + 1,
					promoter_phone_number: row.expert_phone_number,
					outlet_code: row.building_code,
					elevator_ids: row.elevator_ids || [], elevators: [], lookupStatus: '',
				}));
				this.nextRowId = this.actionModel.length + 1;
				this.emitRows();
			} catch (_) {
				this.uploadError = 'ارتباط برقرار نشد. دوباره تلاش کنید.';
			} finally { this.isUploading = false; }
		},
	},
};
</script>
<style lang="scss" scoped>
.vin-input-container {
	width: 100%;
	margin-bottom: 20px;
	overflow-x: auto;
	.vin-table {
		width: 100%;
		min-width: 920px;
		text-align: right;
		tr {
			width: 100%;
			height: 60px;
			.line {
				border-right: 3px solid #357AE1;
				font-family: 'IRANYekanfa' !important;
				padding: 10px;
			}
			th {
				width: 25%;
				text-align: right;
				&:first-child {
					width: 5%;
				}
			}
		}
	}
	.td-data {
		margin-bottom: 20px;
	}
}
.delete {
	color: #f54545;
	cursor: pointer;
	text-align: center !important;
	.iconify {
		font-size: 50px;
	}
	.delete-border {
		border: 1px solid #f54545;
		border-radius: 8px;
		padding: 10px;
		width: 42px;
	}
}
.data-input {
	width: 240px;
	height: 48px;
	border: 1px solid #c4c4c4;
	border-radius: 8px;
	margin-left: 16px;
	box-sizing: border-box;
	text-indent: 10px;
	font-family: 'IRANYekanfa' !important;
}
.elevator-picker { min-width: 230px; padding: 8px 4px; }
.elevator-picker small { display: block; color: #75501d; line-height: 1.5; }
.elevator-options { display: grid; gap: 5px; max-height: 150px; overflow-y: auto; margin-top: 6px; }
.elevator-options label { display: flex; gap: 7px; align-items: center; font-size: 12px; cursor: pointer; }
.elevator-options input { width: 18px; height: 18px; }
.upload-error { color: #932d24; background: #fff0ee; padding: 10px 14px; border-radius: 8px; margin-top: 10px; }
.add-item {
	background: none;
	padding: 8px;
	border: 1px solid #357AE1;
	border-radius: 8px;
	color: #357AE1;
	margin-left: 8px;
	&:disabled {
		background: #f1f1f1;
		color: #535656;
		border-radius: 8px;
		border: none;
		padding: 8px;
	}
}
.inputs {
	width: 100%;
	height: 38px;
	border: 1px solid #c4c4c4;

	border-radius: 4px;
}
.title-file-text-container {
	width: 100%;
	display: flex;
	text-align: right;
	margin-top: 100px;
	p,
	span {
		font-size: 14px;
	}
	span {
		color: #357AE1;
		cursor: pointer;
	}
}
.upload-box {
	width: 100%;
	height: 200px;
	background: #f8f8f8;
	margin-top: 24px;
	border-radius: 8px;
	border: 2px dashed #357AE1;
	display: flex;
	justify-content: center;
	align-items: center;
	flex-direction: column;
	position: relative;
	.upload-text {
		color: #357AE1;
	}
	input {
		position: absolute;
		width: 100%;
		height: 100%;
		top: 0;
		left: 0;
		opacity: 0;
	}
	.icon {
		margin-bottom: 20px;
		.iconify {
			font-size: 40px;
			color: #404041cc;
		}
	}
	p {
		color: #404041;
	}
}
.coppy-code {
	&:hover {
		cursor: pointer;
	}
}
// .counter-container {
// 	width: 100px;
// 	height: 50px;
// 	border: 1px solid #c4c4c4;
// 	position: relative;
// 	display: flex;
// 	// margin: 0 auto;
// 	.input-container {
// 		width: 100%;
// 		input {
// 			width: 100%;
// 			height: 100%;
// 			border: none;
// 			text-indent: 10px;
// 			&:focus {
// 				outline: none;
// 			}
// 		}
// 		input[type='number']::-webkit-inner-spin-button,
// 		input[type='number']::-webkit-outer-spin-button {
// 			-webkit-appearance: none;
// 			margin: 0;
// 		}
// 	}
// 	.arrow-container {
// 		width: 50px;
// 		flex: 1;
// 		display: flex;
// 		flex-direction: column;

// 		.arrow {
// 			width: 30px;
// 			height: 100%;
// 			border-right: 1px solid #c4c4c4;
// 			cursor: pointer;
// 			display: flex;
// 			justify-content: center;
// 			align-items: center;
// 		}
// 		.up {
// 			border-bottom: 1px solid #c4c4c4;
// 		}
// 	}
// }
</style>
