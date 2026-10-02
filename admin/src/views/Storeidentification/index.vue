<template>
	<div class="visit">
		<div class="box search-width">
			<span class="title">فیلترها</span>
			<div class="row mt-3">
				<div class="col d-flex flex-column">
					<label for="html">شهر:</label>
					<select v-model="pickCity" class="form-select">
						<option v-for="city in filterLists.cities" :value="city" :key="city">
							{{ city }}
						</option>
					</select>
				</div>
				<div class="col">
					<label for="html">موقعیت مشتری:</label>
					<select v-model="pickSituation" class="form-select">
						<option
							v-for="situation in filterLists.store_situation"
							:value="situation"
							:key="situation"
						>
							{{ situation }}
						</option>
					</select>
				</div>
				<div class="col">
					<label for="html">تاریخ ویزیت:</label>
					<select v-model="pickTime" class="form-select">
						<option v-for="startDate in filterLists.start_date" :value="startDate" :key="startDate">
							{{ startDate }}
						</option>
					</select>
				</div>

				<div class="col d-flex flex-row align-items-end w-100">
					<button @click="getStoreIdentification((limit = 20), (offset = 0))" class="accept">
						تایید
					</button>
					<button class="remove-filtes" @click="removeFilter">حذف فیلتر</button>
				</div>
			</div>
			<div class="row mt-3">
				<div class="col">
					<label for="html">موجودی محصولات پاکشوما:</label>
					<b-form-select
						v-model="selectedInventory"
						:options="optionsInventory"
						class="form-select"
						value-field="item"
						text-field="name"
					></b-form-select>
					<!-- <select v-model="inventory" class="form-select">
						<option :value=true>بله</option>
						<option :value=false>خیر</option>
					</select> -->
				</div>
				<div class="col">
					<label for="html">همکاری:</label>
					<b-form-select
						v-model="selectedCooperation"
						:options="optionsCooperation"
						class="form-select"
						value-field="item"
						text-field="name"
					></b-form-select>
				</div>
				<div class="col"></div>
				<div class="col"></div>
			</div>
		</div>
		<div class="box">
			<div>
				<div class="d-flex">
					<pagination
						v-model="page"
						:per-page="20"
						:records="totalDataCount"
						@paginate="myCallback"
					/>
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
							<th>تاریخ شروع</th>
							<th>شناسه پاسخ‌دهنده</th>
							<th>استان</th>
							<th>شهر</th>
							<th>تصویر سردرب</th>
							<th>موقعیت مشتری</th>
							<th>نام مشتری</th>
							<th>نام صاحب مشتری</th>
							<th>آدرس</th>
							<th>کد پستی</th>
							<th>تلفن</th>
							<th>موبایل</th>
							<th>شماره کارت بانکی یا شبا</th>
							<th>برند یا عنوان تابلو</th>
							<th>متراژ مشتری</th>
							<th>موجودی پاکشوما</th>
							<th>محصول پاکشوما</th>
							<th>ویزیت مجدد</th>
							<th>تصویر کارت ویزیت</th>
							<th>تصویر ویترین</th>
							<th>تصویر گیفت اهدایی</th>
							<th>تصویر</th>
							<th>تصویر سردرب</th>
							<th>نیروی اجرایی</th>
							<th>لوکیشن</th>
						</tr>
					</template>

					<template #TableBody>
						<tr v-for="(item, index) in StoreIdentification" :key="item.id">
							<td class="persian-number">
								{{ 20 * (page - 1) + 1 + index }}
							</td>
							<td class="persian-number">
								{{ item.start_date }}


							</td>
							<td>{{ item.porslineid }}</td>
							<td>{{ item.province }}</td>
							<td>{{ item.city }}</td>
							<td>
								<img @click="callStoreFrontImg(item)" class="images" :src="item.storefront_photo" />
								<!-- <span class="image-prev" @click="callStoreFrontImg(item)">مشاهده</span> -->
							</td>
							<td>{{ item.store_situation }}</td>
							<td>{{ item.store_name }}</td>
							<td class="persian-number">{{ item.store_owner }}</td>
							<td>{{ item.store_address }}</td>
							<td class="persian-number">{{ item.postalcode }}</td>
							<td class="persian-number">{{ item.phone }}</td>
							<td class="persian-number">{{ item.mobile }}</td>
							<td class="persian-number">{{ item.banknum }}</td>
							<td class="persian-number">{{ item.boardlable }}</td>
							<td class="persian-number">{{ item.meter }}</td>
							<td>
								<span v-if="item.isavailable === true">بله</span>
								<span v-if="item.isavailable === false">خیر</span>
							</td>
							<td>
								<img @click="callPakshomaProduct(item)" class="images" :src="item.pakshoma_photo" />
							</td>
							<td>
								<span v-if="item.hamakri === true">بله</span>
								<span v-if="item.hamakri === false">خیر</span>
							</td>
							<td>
								<img @click="callVisitCardImg(item)" class="images" :src="item.visitcard_photo" />
								<!-- <span class="image-prev" @click="callVisitCardImg(item)">مشاهده</span> -->
							</td>
							<td>
								<img @click="callVitrinPhoto(item)" class="images" :src="item.vitrin_photo" />
								<!-- <span class="image-prev" @click="callVitrinPhoto(item)">مشاهده</span> -->
								<!-- <a :href="item.vitrin_photo">مشاهده</a> -->
							</td>
							<td>
								<img @click="callGiftPhoto(item)" class="images" :src="item.gift_photo" />
								<!-- <span class="image-prev" @click="callGiftPhoto(item)">مشاهده</span> -->

								<!-- <a :href="item.gift_photo">مشاهده</a> -->
							</td>
							<td>
								<img @click="callPopPhoto(item)" class="images" :src="item.pop_photo" />
								<!-- <span class="image-prev" @click="callPopPhoto(item)">مشاهده</span> -->

								<!-- <a :href="item.pop_photo">مشاهده</a> -->
							</td>
							<td>
								<img @click="callSelfiePhoto(item)" class="images" :src="item.selfie_photo" />
								<!-- <span class="image-prev" @click="callSelfiePhoto(item)">مشاهده</span> -->

								<!-- <a :href="item.selfie_photo">مشاهده</a> -->
							</td>
							<td>{{ item.promoter_code }}</td>
							<td>
								<a class="watch" @click='locations(item.location)'>مشاهده</a>
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
			StoreIdentification: 0,
			filterLists: {},
			promoterLists: [],
			pickCity: '',
			pickTime: '',
			pickSituation: '',
			inventory: '',
			page: 1,
			totalDataCount: 0,
			imageModal: false,
			imageUrl: null,
			selectedCooperation: null,
			selectedInventory: null,
			optionsCooperation: [
				{ item: true, name: 'بله' },
				{ item: false, name: 'خیر' },
			],
			optionsInventory: [
				{ item: true, name: 'بله' },
				{ item: false, name: 'خیر' },
			],
		};
	},
	mounted() {
		this.getStoreIdentification();
		this.getFilters();
		this.getPromoterLists();
	},
	computed: {
		showContnetFunc() {
			return this.StoreIdentification === 0;
		},
		showDataFunc() {
			if (this.StoreIdentification.length !== undefined) {
				return this.StoreIdentification.length === 0;
			}
			return false;
		},
	},
	methods: {
		removeFilter() {
			this.pickCity = '';
			this.pickTime = '';
			this.pickSituation = '';
			this.inventory = '';
			this.selectedCooperation = null;
			this.selectedInventory = null;
			this.getStoreIdentification();
		},
		callStoreFrontImg(item) {
			this.imageModal = true;
			this.imageUrl = item.storefront_photo;
		},
		callVisitCardImg(item) {
			this.imageModal = true;
			this.imageUrl = item.visitcard_photo;
		},
		callPakshomaProduct(item) {
			this.imageModal = true;
			this.imageUrl = item.pakshoma_photo;
		},
		callVitrinPhoto(item) {
			this.imageModal = true;
			this.imageUrl = item.vitrin_photo;
		},
		callGiftPhoto(item) {
			this.imageModal = true;
			this.imageUrl = item.gift_photo;
		},

		callPopPhoto(item) {
			this.imageModal = true;
			this.imageUrl = item.pop_photo;
		},
		callSelfiePhoto(item) {
			this.imageModal = true;
			this.imageUrl = item.selfie_photo;
		},
		async getStoreIdentification(limit = 20, offset = 0) {
			const res = await this.$ApiServiceLayer.get(
				this.$PATH.RELATIVE_PATH.GET.GET_CENSUS +
					'?city=' +
					this.pickCity +
					'&store_situation=' +
					this.pickSituation +
					'&start_date=' +
					this.pickTime +
					'&isavailable=' +
					this.selectedInventory +
					'&hamakri=' +
					this.selectedCooperation +
					'&limit=' +
					limit +
					'&offset=' +
					offset +
					'&ordering=-start_date' +
					'&p=' + this.$STORE.state.userConfig.setProjectId
					,
				this.$PATH.SERVICE_NAME.AUTH,
			);
			if (res.status === 200) {
				(res.data);
				this.StoreIdentification = res.data.results;
				this.totalDataCount = res.data.count;
			}
		},
		async myCallback() {
			await this.getStoreIdentification(20, 20 * (this.page - 1));
		},
		async getFilters() {
			const res = await this.$ApiServiceLayer.get(
				this.$PATH.RELATIVE_PATH.GET.CENCUS_FILTER_VALUE + '?p=' + this.$STORE.state.userConfig.setProjectId,
				this.$PATH.SERVICE_NAME.AUTH,
			);
			if (res.status === 200) {
				('city:', res.data);
				this.filterLists = res.data;
			}
		},
		locations(location) {
			// let routeData = this.$router.resolve({ name: 'storeManagementAcceptedvisits', params: { outlet: id } });
			// window.open(routeData.href);
			window.open(location, '_blank');

		}
	},
};
</script>
<style lang="scss" scoped>
.visit {
	padding: 32px 50px;
	.box {
		// border: 1px solid #c4c4c4;
		padding: 24px;
		border-radius: 2px;
		margin-bottom: 16px;
		background: #fff;
		border-radius: 8px;

		.title {
			font-weight: 700;
			font-size: 18px;
		}
		.package-number {
			height: 38px;
			text-indent: 10px;
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
		text-indent: 15px;
		border-radius: 4px;

	}
	.close-modal {
		background: #fff;
		max-height: 110px;
		border: 1px solid #d3dff2 !important;
		color: #404041;
	}
	.accept {
		height: 38px;
		background: #357AE1;
		border-radius: 2px;
		color: #fff;
		border: none !important;
		margin-left: 10px;
		width: 180px;
		border-radius: 4px;

	}
}
.search-width {
	max-width: 1100px !important;
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
.modal-img {
	width: 100%;
}
.image-prev {
	color: #007bff;
	cursor: pointer;
}
.trash-icon {
	max-width: 40px;
}
.images {
	max-width: 60px;
	border-radius: 4px;
}
.watch {
	cursor: pointer;
}
</style>
