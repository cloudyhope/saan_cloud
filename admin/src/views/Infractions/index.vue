<template>
	<div class="follow-order">
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
					<label for="html">کد مشتری:</label>
					<input class="inputs" v-model="storeCode" />
				</div>

				<div class="col d-flex flex-row align-items-end w-100">
					<button @click="getDataPackage((limit = 20), (offset = 0))" class="accept">تایید</button>
					<button class="remove-filtes" @click="removeFilter">حذف فیلتر</button>

					<!-- <img class="trash-icon" @click="removeFilter" src="../../assets/images/iconPack/trash-icon.png"> -->
				</div>
			</div>
		</div>
		<div class="box">
			<div class="d-flex justify-content-between">
				<pagination
					v-model="page"
					:per-page="20"
					:records="totalDataCount"
					@paginate="myCallback"
				/>
				<div class="d-flex flex-row align-items-center">
					<span class="ordering-title">مرتب سازی بر اساس :</span>
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
			<div>
				<Tableview
					:hover="true"
					:bordered="true"
					:showNoContent="dataPackage && !dataPackage.length"
				>
					<template #TableTitle>
						<tr>
							<th>ردیف</th>

							<th>شهر</th>
							<th class="tr-desc">شرح</th>
							<th>کد مشتری</th>
							<th>نام مشتری</th>
							<!-- <th>نام مدیر</th> -->
							<th>نوبت ویزیت</th>
							<th>تاریخ ویزیت</th>
							<th>عملیات</th>
						</tr>
					</template>

					<template #TableBody>
						<tr v-for="(item, index) in dataPackage" :key="item.id">
							<td class="persian-number">
								{{ 20 * (page - 1) + 1 + index }}
							</td>

							<td>{{ item.visit.outlet.city.name }}</td>
							<td class="td-desc">{{ item.description }}</td>
							<td class="persian-number">{{ item.visit.outlet.code }}</td>
							<td>{{ item.visit.outlet.name }}</td>
							<!-- <td>{{ item.visit.outlet.owner_name }}</td> -->
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
							<td>
								<div class="d-flex justify-content-center">
									<b-button class="p-1" v-b-tooltip.hover title="تاریخچه گزارشات" variant="primary">
										<img
											@click="action(item.visit.outlet.id)"
											class="eye-icon"
											src="../../assets/images/iconPack/actions.png"
										/>
									</b-button>
									<b-button class="p-1" v-b-tooltip.hover title="مشاهده ویزیت" variant="primary">
										<img
											@click="detail(item.visit.id)"
											class="eye-icon"
											src="../../assets/images/iconPack/eye.svg"
										/>
									</b-button>
									<b-button class="p-1" v-b-tooltip.hover title="نمایش بازخورد" variant="primary">
										<img
											v-if="!item.visit.visit_comment"
											@click="comment(item.visit.id)"
											class="eye-icon"
											src="../../assets/images/iconPack/outline-mode-comment.svg"
										/>
										<img
											v-if="item.visit.visit_comment"
											@click="comment(item.visit.id)"
											class="eye-icon"
											src="../../assets/images/iconPack/outline-insert-comment.svg"
										/>
									</b-button>
								</div>
							</td>
						</tr>
					</template>
				</Tableview>
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
				<b-modal size="lg" v-model="modalCommentShow" hide-footer>
					<p>کاربر: {{ modalName }} {{ modalLastName }}</p>
					<span class="mb-4">بازخورد:</span>
					<b-form-textarea

						v-model="modalCommentData"
						placeholder=""
						rows="3"
						max-rows="6"
						class="mt-2"
						style="border-radius: 4px;"
					></b-form-textarea>
					<div class="d-flex flex-row justify-content-end w-100 mt-3">
						<button @click="acceptComment" class="accept-modal">تایید</button>
						<button class="close-modal" @click="modalCommentShow = false">
							بستن
						</button>
					</div>
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
			pickProvince: '',
			pickCity: '',
			selectedkCity: '',
			storeCode: '',
			page: 1,
			totalDataCount: 0,
			selected: '-visit__start_datetime',
			options: [
				{ item: 'visit__start_datetime', name: 'صعودی' },
				{ item: '-visit__start_datetime', name: 'نزولی' },
			],
			rangeDate: [],
			modalShow: false,
			modalData: [],
			modalCommentData: null,
			modalCommentShow: false,
			commentVisitId: '',
			modalName: '',
			modalLastName: '',
		};
	},
	mounted() {
		this.getDataPackage();
		this.getCity();
		this.getProvince();
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
		removeFilter() {
			this.pickCity = '';
			this.storeCode = '';
			this.pickProvince = '';
			this.getDataPackage();
			this.getCity();
			this.comment();
		},
		getCityOnChange() {
			this.selectedkCity = this.pickProvince;
			this.getCity();
		},
		async getDataPackage(limit = 20, offset = 0) {
			const res = await this.$ApiServiceLayer.get(
				this.$PATH.RELATIVE_PATH.GET.REJECTED_REPORT +
					'?visit__outlet__city=' +
					this.pickCity +
					'&visit__outlet__city__province=' +
					this.pickProvince +
					'&visit__outlet__code=' +
					this.storeCode +
					'&limit=' +
					limit +
					'&offset=' +
					offset +
					'&ordering=' +
					this.selected + '&p=' + this.$STORE.state.userConfig.setProjectId,
				this.$PATH.SERVICE_NAME.AUTH,
			);
			if (res.status === 200) {
				this.dataPackage = res.data.results;
				('sd:', this.dataPackage);
				this.totalDataCount = res.data.count;
			}
		},
		async myCallback() {
			await this.getDataPackage(20, 20 * (this.page - 1));
		},
		detail(id) {
			let routeData = this.$router.resolve({
				name: 'answerListCustomers',
				params: { id: id },
			});
			window.open(routeData.href);
		},
		async action(id) {
			const res = await this.$ApiServiceLayer.get(
				this.$PATH.RELATIVE_PATH.MULTI.INFRACTIONS_ACTIONS + '?visit__outlet__id=' + id + '&ordering=-start_datetime' + '&p=' + this.$STORE.state.userConfig.setProjectId,
				this.$PATH.SERVICE_NAME.AUTH,
			);
			if (res.status === 200) {
				this.modalData = res.data;
				this.modalShow = true;
			}
		},
		async comment(id) {
			this.commentVisitId = id;
			const res = await this.$ApiServiceLayer.get(
				this.$PATH.RELATIVE_PATH.MULTI.ADD_COMMENT + id + '/' + '?p=' + this.$STORE.state.userConfig.setProjectId,
				this.$PATH.SERVICE_NAME.AUTH,
			);
			if (res.status === 200) {
				if (res.data.comment_publisher !== null) {
					this.modalCommentData = res.data.visit_comment;
					this.modalName = res.data.comment_publisher.first_name;
					this.modalLastName = res.data.comment_publisher.last_name;
					this.modalCommentShow = true;
				} else {
					this.modalCommentData = null;
					this.modalName = '';
					this.modalLastName = '';
					this.modalCommentShow = true;
				}
			}
		},
		async acceptComment() {
			const res = await this.$ApiServiceLayer.put(
				this.$PATH.RELATIVE_PATH.MULTI.ADD_COMMENT + this.commentVisitId + '/' + '?p=' +
				this.$STORE.state.userConfig.setProjectId,
				this.$PATH.SERVICE_NAME.AUTH,
				{
					visit_comment: this.modalCommentData,
				},
			);
			if (res.status === 200) {
				this.$notify({
					group: 'tc',
					type: 'success',
					text: 'بازخورد با موفقیت تغییر کرد!',
				});
				this.modalCommentShow = false;
			}
		},
		async getProvince() {
			const res = await this.$ApiServiceLayer.get(
				this.$PATH.RELATIVE_PATH.GET.GET_PROVINCE_LIST + '?p=' + this.$STORE.state.userConfig.setProjectId,
				this.$PATH.SERVICE_NAME.AUTH,
			);
			if (res.status === 200) {
				this.provinceLists = res.data;
			}
		},
		async getCity() {
			const res = await this.$ApiServiceLayer.get(
				this.$PATH.RELATIVE_PATH.GET.GET_CITY_LIST + '?city__province=' + this.selectedkCity + '&p=' + this.$STORE.state.userConfig.setProjectId,
				this.$PATH.SERVICE_NAME.AUTH,
			);
			if (res.status === 200) {
				('city:', res.data);
				this.cityLists = res.data;
			}
		},
	},
};
</script>
<style lang="scss" scoped>
.follow-order {
	padding: 32px 50px;
	.box {
		// border: 1px solid #c4c4c4;
		background: #fff;
		padding: 24px;
		border-radius: 2px;
		margin-bottom: 16px;
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
			border-radius: 2px;
			font-family: 'IRANYekanfa' !important;
		}
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
	.remove-filtes {
		width: 50%;
		border: 1px solid #357AE1;
		border-radius: 2px;
		color: #357AE1;
		height: 38px;
		background: #fff;
		border-radius: 4px;

	}
	.ordering-title {
		min-width: 180px;
		border-radius: 4px;
	}
	.ordering {
		max-width: 100px;
	}
	.show-date {
		border: none;
		text-indent: 55px;
		background: #fff;
	}

	.eye-icon {
		width: 32px;
		cursor: pointer;
	}
}
.accept-modal {
	height: 38px;
	background: #357AE1;
	border-radius: 2px;
	color: #fff;
	border: none !important;
	margin-left: 10px;
	min-width: 100px;
	border-radius: 4px;
}
.close-modal {
	height: 38px;
	background: #fff;
	border-radius: 2px;
	border: 1px solid;
	min-width: 100px;
}
.persian-number {
		font-family: 'IRANYekanfa' !important;
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
