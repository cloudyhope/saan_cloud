<template>
	<div class="add-store">
		<div class="box">
			<div class="title">اطلاعات مشتری</div>
			<div class="row mt-3">
				<div class="col-lg-6 col-sm-12">
					<Materialnput label="نام مشتری" v-model="nameModel" inputType="text" />
				</div>
				<div class="col-lg-6 col-sm-12">
					<Materialnput label="تلفن" v-model="telModel" />
				</div>
				<div class="col-lg-6 col-sm-12">
					<Materialnput label="کد مشتری" v-model="storeCodeModel" />
				</div>
				<div class="col-lg-6 col-sm-12">
					<Materialnput label="کد مشتری" v-model="customersCodeModel" />
				</div>
				<div class="col-lg-6 col-sm-12">
					<label for="html">نوع مشتری:</label>
					<select style="width: 100%" v-model="pickStore" class="search-input">
						<option v-for="outlet in outletCat" :value="outlet.id" :key="outlet.id">
							<span>{{ outlet.verbose_name }}</span>
						</option>
					</select>
				</div>
			</div>
		</div>
		<div class="box">
			<div class="title">اطلاعات صاحب مشتری</div>
			<div class="row mt-3">
				<div class="col-lg-6 col-sm-12">
					<Materialnput label="نام و نام خانودگی" v-model="userNameModel" inputType="text" />
				</div>
				<div class="col-lg-6 col-sm-12">
					<Materialnput label="موبایل" v-model="mobileModel" />
				</div>
				<div class="col-lg-6 col-sm-12">
					<Materialnput label="کد ملی" v-model="nationalCodeModel" />
				</div>
			</div>
		</div>
		<div class="box">
			<div class="title">محل مشتری</div>
			<div class="row mt-3">
				<div class="col-lg-6 col-sm-12">
					<label for="html">استان:</label>
					<select
						style="width: 100%"
						@change="getCityOnChange"
						v-model="pickProvince"
						class="search-input"
					>
						<option
							v-for="province in provinceLists"
							:value="province.id"
							:key="`province-` + province.id"
						>
							{{ province.name }}
						</option>
					</select>
				</div>
				<div class="col-lg-6 col-sm-12">
					<label for="html">شهر:</label>
					<select style="width: 100%" v-model="pickCity" class="search-input">
						<option v-for="city in cityLists" :value="city.city.id" :key="`city-` + city.city.id">
							{{ city.city.name }}
						</option>
					</select>
				</div>
				<div class="col-lg-6 col-sm-12">
					<Materialnput label="کد پستی" v-model="postalCodeModel" />
				</div>
				<div v-if="Object.keys(mapData).length > 0" class="col-lg-12 col-sm-12">
					<Materialnput label="آدرس" v-model="mapData.address" />
				</div>
			</div>
			<div class="map-text">لطفا محل مشتری را بر روی نقشه انتخاب کنید.</div>
			<Map @child-event="handleChildEvent" />
			<div class="d-flex justify-content-end mt-4">
				<button :disabled="checkData" class="accept" @click="submitBtn">ذخیره</button>
			</div>
		</div>
	</div>
</template>
<script>
import Materialnput from '../../components/MaterialInput/indx.vue';
import Map from '../../components/Map/index.vue';
export default {
	components: {
		Materialnput,
		Map,
	},
	data() {
		return {
			nameModel: '',
			telModel: '',
			storeCodeModel: '',
			customersCodeModel: '',
			userNameModel: '',
			mobileModel: '',
			nationalCodeModel: '',
			cityLists: [],
			provinceLists: [],
			pickCity: '',
			pickProvince: '',
			postalCodeModel: '',
			pickStore: '',
			outletCat: [],
			mapData: {},
			text: false,
		};
	},

	mounted() {
		// this.getRoles();
		this.getProvince();
		this.getOutletCat();
		'sdadsdas', this.mapData;
	},
	computed: {
		checkData() {
			if (
				this.nameModel === '' ||
				// this.telModel === '' ||
				this.storeCodeModel === '' ||
				// this.customersCodeModel === '' ||
				// this.userNameModel === '' ||
				// this.mobileModel === '' ||
				// this.nationalCodeModel === '' ||
				this.pickCity === '' ||
				// this.postalCodeModel === '' ||
				this.pickStore === '' ||
				Object.keys(this.mapData).length === 0
			) {
				return true;
			} else {
				return false;
			}
		},
	},
	methods: {
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
				'city:', res.data;
				this.cityLists = res.data;
			}
		},
		async getdataEditMode() {
			const res = await this.$ApiServiceLayer.get(
				this.$PATH.RELATIVE_PATH.GET.OUTLET_CAT + '?p=' + this.$STORE.state.userConfig.setProjectId,
				this.$PATH.SERVICE_NAME.AUTH,
			);
			if (res.status === 200) {
				this.outletCat = res.data;
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
		getCityOnChange() {
			this.selectedkCity = this.pickProvince;
			this.getCity();
		},
		handleChildEvent(data) {
			this.mapData = data;
		},
		async submitBtn() {
			const data = {
				name: this.nameModel,
				address: this.mapData.address,
				city: this.pickCity,
				longitude: this.mapData.geom.coordinates[0],
				latitude: this.mapData.geom.coordinates[1],
				postal_code: this.postalCodeModel,
				phone: this.telModel,
				mobile_phone: this.mobileModel,
				owner_national_code: this.nationalCodeModel,
				owner_name: this.userNameModel,
				period: 1,
				visit_count: 0,
				code: this.storeCodeModel,
				customer_code: this.customersCodeModel,
				category: this.pickStore,
				is_active: true,
				is_visiting: false,
				more_info: [],
			};
			const res = await this.$ApiServiceLayer.post(
				this.$PATH.RELATIVE_PATH.POST.CREATE_OUTLET + '?p=' +
				this.$STORE.state.userConfig.setProjectId,
				this.$PATH.SERVICE_NAME.ORDER,
				data,
			);
			res;
			if (res.status === 201) {
				(this.nameModel = ''),
					(this.telModel = ''),
					(this.storeCodeModel = ''),
					(this.customersCodeModel = ''),
					(this.userNameModel = ''),
					(this.mobileModel = ''),
					(this.nationalCodeModel = ''),
					(this.pickCity = ''),
					(this.pickProvince = ''),
					(this.postalCodeModel = ''),
					(this.pickStore = ''),
					(this.mapData = {});
				this.$notify({
					group: 'tc',
					type: 'success',
					text: 'اطلاعات مشتری با موفقیت ذخیره شد.',
				});
			}
		},
	},
};
</script>
<style lang="scss" scoped>
.add-store {
	padding: 32px 50px;
	.box {
		padding: 24px;
		border-radius: 2px;
		margin-bottom: 16px;
		background: #fff;
		border-radius: 8px;
		box-shadow: 0px 4px 4px rgba(214, 214, 214, 0.6);
	}
	.title {
		margin-bottom: 8px;
	}
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
	.accept {
		background: #357AE1;
		border-radius: 2px;
		color: #fff;
		padding: 8px 40px;
		border: none !important;
		margin-left: 10px;
		border-radius: 4px;
	}
	.map-text {
		display: flex;
		justify-content: center;
		width: 100%;
		background: rgba(244, 245, 247, 0.8);
		border-radius: 8px 8px 0 0;
		margin-bottom: -20px;
		position: sticky;
		z-index: 9999;
		font-size: 14px;
	}
	.accept:disabled {
		background: #c4c4c4;
	}
}
</style>
