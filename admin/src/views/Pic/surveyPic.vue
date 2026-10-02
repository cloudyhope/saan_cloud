<template>
	<div class="pic-page">
		<div class="box">
			<span class="title">فیلترها</span>
			<div class="row mt-3">
				<div class="col d-flex flex-column">
					<label for="html">استان:</label>
					<select @change="getCityOnChange" v-model="pickProvince" class="form-select">
						<option v-for="province in provinceLists" :value="province.id" :key="province.id">
							{{ province.name }}
						</option>
					</select>
				</div>
				<div class="col d-flex flex-column">
					<label for="html">شهر:</label>
					<select v-model="pickCity" class="form-select">
						<option v-for="city in cityLists" :value="city.city.id" :key="city.city.id">
							{{ city.city.name }}
						</option>
					</select>
				</div>
				<div class="col d-flex flex-column">
                    <label for="html">نیروی اجرایی:</label>
					<select v-model="pickPromoter" class="form-select">
						<option v-for="promoter in promoterLists" :value="promoter.id" :key="promoter.id">
							{{ promoter.user.first_name }} {{ promoter.user.last_name }}
						</option>
					</select>
				</div>
				<!-- <div class="col d-flex flex-column">
					<label for="html">نوع مشتری:</label>
					<select v-model="pickStore" class="form-select">
						<option :value="1">برند شاپ</option>
						<option :value="2">مشتری زنجیره ای</option>
						<option :value="3">مولتی برند</option>
					</select>
				</div> -->

				<!-- <div class="col d-flex flex-row align-items-end w-100">
					<button @click="getDataPackage((limit = 10), (offset = 0))" class="accept">تایید</button>
					<button class="remove-filtes" @click="removeFilter">حذف فیلتر</button>

				</div> -->
			</div>
			<div class="row mt-3">
				<div class="col d-flex flex-column">
					<label for="html">تاریخ :</label>
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
				<div class="col d-flex flex-column">
					<label for="html">وضعیت بررسی:</label>
					<select v-model="checkStatus" class="form-select">
						<option :value="true">بررسی شده</option>
						<option :value="false">بررسی نشده</option>
					</select>
				</div>
                <div class="col d-flex flex-column">
					<label for="html">نام پرسشنامه:</label>
					<select v-model="pickQuestionnaire" class="form-select">
						<option v-for="survey in surveyList" :value="survey.id" :key="survey.id">
							{{ survey.verbose_name }}
						</option>
					</select>
				</div>

			</div>
            <div class="row mt-3">
                <div class="col"></div>
                <div class="col"></div>
                <div class="col d-flex flex-row align-items-end w-100 justify-content-end">
					<button @click="getDataPackage((limit = 20), (offset = 0))" class="accept">تایید</button>
					<button class="remove-filtes" @click="removeFilter">حذف فیلتر</button>
				</div>
            </div >

		</div>
		<div>
			<div class="table-box">
				<div class="d-flex justify-content-between">
					<pagination
						v-model="page"
						:per-page="20"
						:records="totalDataCount"
						@paginate="myCallback"
					/>
					<div class="d-flex flex-row align-items-center">
						<span class="ordering-title">مرتب سازی بر اساس تاریخ:</span>
						<b-form-select
							v-model="selected"
							:options="options"
							class="ordering"
							value-field="item"
							text-field="name"
							@change="getDataPackage((limit = 20), (offset = 0), (order = selected))"
						></b-form-select>
					</div>
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
							<th>تصویر</th>
							<th>شهر</th>
							<th>نام پرسشنامه</th>
							<th>بررسی شده</th>
							<th>تاریخ</th>
							<th>مشاهده</th>
						</tr>
					</template>

					<template #TableBody>
						<tr v-for="(item, index) in dataPackage" :key="item.id">
							<td class="persian-number">
								{{ 20 * (page - 1) + 1 + index }}
							</td>
							<td><img @click="callModalimage(item)" class="answers-images" :src="item.link" /></td>
							<td>{{ item.survey_fill_out.city.name }}</td>
							<td>{{ item.survey_fill_out.survey.verbose_name }}</td>
							<td>
								<b-form-checkbox
									:options="item.is_checked"
									v-model="item.is_checked"
									@change="changeImageStatus(item)"
									name="check-button"
									switch
								>
								</b-form-checkbox>
							</td>
							<td>
								<date-picker
									v-model="item.datetime_created"
									type="datetime"
									format="YYYY-MM-DD HH:mm"
									display-format="jYYYY-jMM-jDD HH:mm"
									:timezone="true"
									:disabled="true"
								/>
							</td>
							<td>
								<img
									@click="surveyDetail(item)"
									class="eye-icon"
									src="../../assets/images/iconPack/eye.svg"
								/>
							</td>
						</tr>
					</template>
				</Tableview>
				<b-modal hide-footer hide-header size="lg" centered v-model="imageModal">
					<img class="modal-img" :src="imageUrl" />
				</b-modal>
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
			cityLists: [],
			provinceLists: [],
            surveyList:[],
            promoterLists:[],
			pickProvince: '',
			pickCity: '',
			selectedkCity: '',
			promoterCode: '',
			checkStatus: '',
			pickPromoter: '',
			rangeDate: ['', ''],
			imageModal: false,
            pickQuestionnaire:null,
			imageUrl: '',
			page: 1,
			type: {},
			checked: false,
			queryStates: window.location.href.split('/').slice(-1)[0],
			totalDataCount: 0,
			selected: '-datetime_last_change',
			options: [
				{ item: '-datetime_last_change', name: 'نزولی' },
				{ item: 'datetime_last_change', name: ' صعودی' },
			],
		};
	},
	async mounted() {
		// this.queryStates =  window.location.search;
		await this.getType();
		this.getDataPackage();
		this.getCity();
		this.getProvince();
		this.$router.afterEach(this.handleUrlChange);
        this.getSurveyList();
        this.getPromoterLists();
	},

	computed: {
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
		async handleUrlChange(to, from) {
			('sss', to.params.id, from.params.id);
			this.queryStates = to.params.id;

			await this.getType();
			this.getDataPackage();
			this.getCity();
			this.getProvince();
            this.getSurveyList();
        this.getPromoterLists();
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
		removeFilter() {
			this.pickCity = '';
			this.promoterCode = '';
			this.pickProvince = '';
			this.selectedkCity = '';
			this.checkStatus = '';
			this.rangeDate = ['', ''];
			this.pickPromoter = '';
			this.getDataPackage();
			this.getCity();
		},
		callModalimage(item) {
			this.imageModal = true;
			this.imageUrl = item.link;
		},
		getCityOnChange() {
			this.selectedkCity = this.pickProvince;
			this.getCity();
		},
		async getType() {
			const res = await this.$ApiServiceLayer.get(
				this.$PATH.RELATIVE_PATH.GET.MENU_EDIT + '/' + this.queryStates + '/' + '?p=' +
				this.$STORE.state.userConfig.setProjectId,
				this.$PATH.SERVICE_NAME.AUTH,
			);
			if (res.status === 200) {
				this.type = res.data;
			}
		},
        async getSurveyList() {
			const res = await this.$ApiServiceLayer.get(
				this.$PATH.RELATIVE_PATH.MULTI.SURVEY_NAME + '?p=' +
					this.$STORE.state.userConfig.setProjectId,
				this.$PATH.SERVICE_NAME.AUTH,
			);
			if (res.status === 200) {
				this.surveyList = res.data
			}
		},
		async getDataPackage(limit = 20, offset = 0) {
			if (this.rangeDate[0] !== '' && this.rangeDate[1] == undefined) {
				this.rangeDate[1] = this.rangeDate[0].slice(0, 11) + '23:59:59';
			} else if (this.rangeDate[0] === null || this.rangeDate[0] === undefined) {
				this.rangeDate[0] = '';
			}
			const res = await this.$ApiServiceLayer.get(
				this.$PATH.RELATIVE_PATH.MULTI.SURVEY_PHOTO_LIST +
					'?survey_photo_type__name=' +
					this.type.frontend_api_queryparams +
					'&survey_fill_out__city=' +
					this.pickCity +
					'&survey_fill_out__province=' +
					this.pickProvince +
					'&survey_fill_out__outlet__code=' +
					this.promoterCode +
					'&survey_fill_out__survey.name=' +
					this.pickQuestionnaire +
					'&datetime_created__gte=' +
					this.rangeDate[0] +
					'&datetime_created__lte=' +
					this.rangeDate[1] +
					'&is_checked=' +
					this.checkStatus +
					'&limit=' +
					limit +
					'&offset=' +
					offset +
					'&ordering=' +
					this.selected +
					'&p=' +
					this.$STORE.state.userConfig.setProjectId + '&survey_fill_out__user=' + this.pickPromoter,
				this.$PATH.SERVICE_NAME.AUTH,
			);
			if (res.status === 200) {
				this.dataPackage = res.data.results;
				for(let i of this.dataPackage) {
					if (i.survey_fill_out.city === null) {
						i.survey_fill_out.city = {}
						i.survey_fill_out.city.name = '-'
					}
				}
				this.totalDataCount = res.data.count;
			}
		},
		async changeImageStatus(item) {
			const res = await this.$ApiServiceLayer.patch(
				this.$PATH.RELATIVE_PATH.MULTI.SURVEY_DELETE_IMAGE + item.id + '/' + '?p=' +
				this.$STORE.state.userConfig.setProjectId,
				this.$PATH.SERVICE_NAME.AUTH,
				{ is_checked: item.is_checked },
			);
			if (res.status === 200) {
				this.$notify({
					group: 'tc',
					type: 'success',
					text: 'وضعیت بررسی عکس با موفقیت تغییر کرد!',
				});
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
		async myCallback() {
			await this.getDataPackage(20, 20 * (this.page - 1));
		},
		surveyDetail(item) {
			let routeData = this.$router.resolve({
				name: 'surveyAnswerListCustomers',
				params: { id: item.survey_fill_out.id },
			});
			window.open(routeData.href);
		},
	},
	watch: {
		queryStates: {
			handler(value) {
				(value);
			},
		},
		immediate: true, // This ensures the watcher is triggered upon creation
	},
};
</script>
<style lang="scss" scoped>
.pic-page {
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
		.inputs {
			width: 100%;
			height: 38px;
			border: 1px solid #c4c4c4;
			padding: 0 9px;
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
	}
	.table-box {
		background: #fff;
		border-radius: 8px;
		padding: 24px;
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
}
.answers-images {
	max-width: 120px;
}

.persian-number {
	font-family: 'IRANYekanfa' !important;
}
.modal-img {
	width: 100%;
}
.eye-icon {
	width: 32px;
	cursor: pointer;
}
.ordering-title {
	min-width: 200px;
}
</style>
<style>





table {
	table-layout: fixed;
}
.td-desc {
	border: 1px solid #ddd;
	max-width: 28ch;
	word-wrap: break-word;
}
td:after {
	content: '\00A0';
}
.tr-desc {
	width: 30%;
}
</style>
