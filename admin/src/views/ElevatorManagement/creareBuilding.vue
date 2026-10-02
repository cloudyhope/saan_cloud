<template>
	<div class="follow-order">
		<div class="box">
			<span class="title">افزودن گروه ساختمان جدید</span>
			<div class="form-container">
				<div class="row mt-4">
					<div class="col-md-6 col-lg-4 mb-3">
						<label for="buildingName">نام ساختمان:</label>
						<input
							id="buildingName"
							v-model="verbose_name"
							class="inputs"
							placeholder="نام ساختمان را وارد کنید"
						/>
					</div>

					<div class="col-md-6 col-lg-4 mb-3">
						<label for="buildingCode">کد ساختمان:</label>
						<input
							id="buildingCode"
							v-model="code"
							class="inputs"
							placeholder="کد ساختمان را وارد کنید"
						/>
					</div>

					<!-- <div class="col-md-6 col-lg-4 mb-3">
						<label for="buildingType">نوع ساختمان:</label>
						<select id="buildingType" @change="getBuildingType" v-model="type" class="form-select">
							<option value="" disabled selected>انتخاب کنید</option>
							<option value="Complex">مجتمع</option>
							<option value="Apartment">ساختمان</option>
						</select>
					</div> -->

					<div class="col-md-6 col-lg-4 mb-3">
						<label for="province">استان:</label>
						<select
							id="province"
							v-model="pickProvince"
							class="form-select"
							@change="getCityOnChange"
						>
							<option value="" disabled selected>انتخاب کنید</option>
							<option v-for="province in provinceLists" :value="province.id" :key="province.id">
								{{ province.name }}
							</option>
						</select>
					</div>

					<div class="col-md-6 col-lg-4 mb-3">
						<label for="city">شهر:</label>
						<select
							id="city"
							v-model="selectedkCity"
							class="form-select"
							:disabled="!cityLists.length"
						>
							<option value="" disabled selected>انتخاب کنید</option>
							<option v-for="city in cityLists" :value="city.city.id" :key="city.city.id">
								{{ city.city.name }}
							</option>
						</select>
					</div>
					<div class="col-md-6 col-lg-4 mb-3" v-if="complexInput">
						<label for="city">انتخاب مجتمع:</label>
						<select id="city" v-model="selectedComplex" class="form-select">
							<option value="" disabled selected>انتخاب کنید</option>
							<option v-for="complex in complexList" :value="complex.id" :key="complex.id">
								{{ complex.verbose_name }}
							</option>
						</select>
					</div>

					<div class="col-md-12 col-lg-12 mb-3">
						<div v-if="Object.keys(mapData).length > 0">
							<input class="inputs" label="آدرس" v-model="mapData.address" />
						</div>
						<div class="map-text">لطفا محل مشتری را بر روی نقشه انتخاب کنید.</div>
						<Map @child-event="handleChildEvent" />
						<div class="d-flex justify-content-end mt-4"></div>
					</div>
				</div>

				<div class="mt-4 d-flex justify-content-end">
					<button :disabled="isFormValid" @click="submitForm" class="btn accept">
						ثبت ساختمان
					</button>
				</div>
			</div>
		</div>
	</div>
</template>

<script>
import Map from '../../components/Map/index.vue';
export default {
	components: {
		Map,
	},
	data() {
		return {
			selectedProvince: '',
			provinceLists: [],
			cityLists: [],
			mapData: {},
			selectedkCity: '',
			pickProvince: '',
			verbose_name: '',
			type: '',
			address: '',
			code: '',
			complexInput: false,
			complexList: [],
			selectedComplex: '',
		};
	},

	mounted() {
		this.getProvinceList();
	},
	computed: {
		isFormValid() {
			if (
				this.verbose_name !== '' &&
				this.code !== '' &&
				
				this.selectedkCity !== '' &&
				this.pickProvince !== '' &&
				Object.keys(this.mapData).length > 0 &&
				this.mapData.address &&
				(!this.complexInput || (this.complexInput && this.selectedComplex !== ''))
			) {
				return false;
			}
			return true;
		},
	},
	methods: {
		async getProvinceList() {
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
		getBuildingType() {
			if (this.type === 'Apartment') {
				this.complexInput = true;
				this.getComplexList();
			} else {
				this.complexInput = false;
			}
		},
		async getCityOnChange() {
			//   if (!this.selectedProvince) return;
			this.selectedkCity = this.pickProvince;
			this.getCity();
		},
		handleChildEvent(data) {
			this.mapData = data;
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
		async getComplexList() {
			const res = await this.$ApiServiceLayer.get(
				this.$PATH.RELATIVE_PATH.MULTI.VISIT_BUILDING_LIST_CREATE +
					'?p=' +
					this.$STORE.state.userConfig.setProjectId +
					'&is_active=true' +
					'&parent__isnull=true',
				'',
			);
			if (res.status === 200) {
				this.complexList = res.data;
			}
		},
        
		async submitForm() {
			const data = {
				verbose_name: this.verbose_name,
				code: this.code,
				type: this.$route.params.id ? 'Apartment' : 'Complex',
				address: this.mapData.address,
				city: this.selectedkCity,
				parent: this.$route.params.id ? this.$route.params.id : null,
				longitude: this.mapData.geom.coordinates[0],
				latitude: this.mapData.geom.coordinates[1],
			};
			const res = await this.$ApiServiceLayer.post(
				this.$PATH.RELATIVE_PATH.MULTI.VISIT_BUILDING_LIST_CREATE,
				'',
				data,
			);
			console.log(res);
			if (res.status === 201) {
				this.$notify({
					group: 'tc',
					type: 'success',
					text: 'ساختمان با موفقیت ثبت شد',
				});
				this.verbose_name = '';
				this.code = '';
				this.type = '';
				this.selectedkCity = '';
				this.pickProvince = '';
				this.mapData = {};
				this.selectedComplex = '';
			}
		},
	},
};
</script>

<style lang="scss" scoped>
.follow-order {
	padding: 32px 50px;

	.box {
		padding: 24px;
		border-radius: 8px;
		margin-bottom: 16px;
		background: #fff;
		box-shadow: 0px 4px 4px rgba(214, 214, 214, 0.6);

		.title {
			font-weight: 700;
			font-size: 18px;
		}
	}

	.inputs {
		width: 100%;
		height: 38px;
		border: 1px solid #c4c4c4;
		padding: 0 9px;
		border-radius: 4px;
		font-family: 'IRANYekanfa' !important;
	}

	.address-input {
		height: 80px;
		padding: 9px;
		resize: none;
	}

	.form-select {
		width: 100%;
		border: 1px solid #c4c4c4;
		height: 38px;
		padding: 0 9px;
		border-radius: 4px;
		color: #828282;
	}

	.accept {
		height: 38px;
		background: #357ae1;
		border-radius: 4px;
		color: #fff;
		border: none !important;
		width: 120px;
	}

	.remove-filtes {
		border: 1px solid #357ae1;
		border-radius: 4px;
		color: #357ae1;
		height: 38px;
		background: #fff;
		width: 100px;
	}

	.form-check-input {
		margin-left: 8px;
	}

	.form-check-label {
		margin-right: 8px;
	}
}

@media (max-width: 768px) {
	.follow-order {
		padding: 16px;

		.box {
			padding: 16px;
		}
	}
}
</style>
