<template>
	<div class="user-managment-edit">
		<Loading v-if="loading" />
		<div class="box">
			<span>جستجوی کاربر</span>
			<div class="mt-2">
				<input
					v-model="searchNumberInput"
					class="search-input"
					type="text"
					@input="validateMobileNumber"
					placeholder="شماره همراه"
				/>
				<button :disabled="isValidMobileNumberBtn" @click="searchUser" class="search">جستجو</button>
			</div>
		</div>
		<div v-if="showClientForm">
			<div class="box">
				<span>اطلاعات مشتری</span>
				<div class="row mt-3">
					<div class="col-12 mb-4">
						<div class="user-name">
							<span class="text ml-2">نام کاربری :</span>
							<span class="persian">{{ phoneNumber }}</span>
						</div>
					</div>

					<div class="col-lg-6 col-md-6 col-sm-12 mb-4">
						<label class="form-label">نوع ویزیت</label>
						<div class="custom-dropdown">
							<div class="dropdown-header" @click="toggleDropdown">
								<span class="dropdown-title">
									<span v-if="selectedVisitTypes.length === 0">انتخاب کنید</span>
									<span v-else>{{ getSelectedVisitTypeNames }}</span>
								</span>
								<span class="dropdown-arrow" :class="{ 'dropdown-arrow-up': isDropdownOpen }"
									>▼</span
								>
							</div>
							<div class="dropdown-list" v-show="isDropdownOpen">
								<div v-for="item in visitType" :key="item.id" class="dropdown-item">
									<label class="checkbox-container">
										<input
											type="checkbox"
											:id="`visit-type-${item.id}`"
											:value="item.id"
											v-model="selectedVisitTypes"
										/>
										<span class="checkmark"></span>
										<span class="item-text">{{ item.verbose_name }}</span>
									</label>
								</div>
							</div>
						</div>
					</div>

					<div class="col-lg-6 col-md-6 col-sm-12 mb-4">
						<label class="form-label">نوع مشتری</label>
						<select v-model="type" class="form-control">
							<option value="" disabled selected>انتخاب کنید</option>
							<option value="Business">کسب و کار</option>
							<option value="Customer">شخصی</option>
						</select>
					</div>

					<div class="col-lg-6 col-md-6 col-sm-12 mb-4">
						<label class="form-label">نام فارسی</label>
						<input v-model="faName" type="text" class="form-control" />
					</div>

					<div class="col-lg-6 col-md-6 col-sm-12 mb-4">
						<label class="form-label">نام انگلیسی</label>
						<input v-model="enName" type="text" class="form-control" />
					</div>
				</div>
				<div class="d-flex justify-content-end">
					<button :disabled="isSubmitBtnDisabled" @click="submitHandler" class="submit-btn">
						ثبت و ذخیره
					</button>
				</div>
			</div>
		</div>
	</div>
</template>

<script>
// import Materialnput from '../../components/MaterialInput/indx.vue';
import Loading from '../../components/Loading/index.vue';

export default {
	components: {
		// Materialnput,
		Loading,
	},
	data() {
		return {
			phoneNumber: null,
			searchNumberInput: '',
			isValidMobileNumber: false,
			loading: false,
			visitType: [],
			selectedVisitTypes: [],
			isDropdownOpen: false,
			type: '',
			faName: '',
			enName: '',
			user: null,
			showClientForm: false,
		};
	},

	mounted() {
		this.getVisitType();
		document.addEventListener('click', this.closeDropdownOutside);
	},

	beforeDestroy() {
		document.removeEventListener('click', this.closeDropdownOutside);
	},
	computed: {
		isValidMobileNumberBtn() {
			// Regular expression for Iranian mobile numbers
			const iranMobileRegex = /^(\+98|0)?9\d{9}$/;

			// Check if the entered mobile number matches the regex
			const x = iranMobileRegex.test(this.searchNumberInput);
			if (x === false) {
				return true;
			} else {
				return false;
			}
		},
		isSubmitBtnDisabled() {
			if (
				this.type === '' ||
				this.faName === '' ||
				this.enName === '' ||
				this.selectedVisitTypes.length === 0
			) {
				return true;
			} else {
				return false;
			}
		},
		getSelectedVisitTypeNames() {
			if (this.selectedVisitTypes.length === 0) return '';
			const selectedNames = this.selectedVisitTypes
				.map((id) => {
					const item = this.visitType.find((type) => type.id === id);
					return item ? item.verbose_name : '';
				})
				.filter((name) => name);
			if (selectedNames.length > 2) {
				return `${selectedNames.length} مورد انتخاب شده`;
			}

			// Otherwise show the names
			return selectedNames.join('، ');
		},
	},
	methods: {
		toggleDropdown() {
			this.isDropdownOpen = !this.isDropdownOpen;
		},

		closeDropdownOutside(event) {
			if (this.$refs.visitDropdown && !this.$refs.visitDropdown.contains(event.target)) {
				this.isDropdownOpen = false;
			}
		},

		async searchUser() {
			this.loading = true;
			try {
				this.phoneNumber = this.searchNumberInput;
				const res = await this.$ApiServiceLayer.get(
					this.$PATH.RELATIVE_PATH.GET.GET_USER_LIST +
						'?p=' +
						this.$STORE.state.userConfig.setProjectId +
						'&user__username=' +
						this.searchNumberInput +
						'&is_deleted=false',
					this.$PATH.SERVICE_NAME.EMPTY
				);
				if (res.status === 200) {
					if (res.data.length === 0) {
						this.loading = false;

						this.$notify({
							group: 'tc',
							type: 'warning',
							text: 'کاربر مورد نظر یافت نشد ،برای ثبت آن فرم اطلاعات کاربر را تکمیل کنید.',
						});
					} else if (res.data.length > 0) {
						this.user = res.data[0];
						this.$notify({
							group: 'tc',
							type: 'success',
							text: `مشتری مورد نظر ${this.searchNumberInput} یافت شد ،برای ثبت آن فرم اطلاعات کاربر را تکمیل کنید.`,
						});
						this.showClientForm = true;
						this.getVisitType();
					}
					this.loading = false;
				}
			} finally {
				this.loading = false;
			}
		},
		async getVisitType() {
			const res = await this.$ApiServiceLayer.get(
				this.$PATH.RELATIVE_PATH.GET.VISIT_TYPE + '?p=' + this.$STORE.state.userConfig.setProjectId,
				this.$PATH.SERVICE_NAME.AUTH,
			);
			if (res.status === 200) {
				this.visitType = res.data;
			}
		},

		validateMobileNumber() {
			// Remove non-digit characters from the input
			this.searchNumberInput = this.searchNumberInput.replace(/\D/g, '');

			// Limit the input to 11 characters
			if (this.searchNumberInput.length > 11) {
				this.searchNumberInput = this.searchNumberInput.slice(0, 11);
			}

			// Define the regex pattern for an Iranian mobile number
			const iranMobileRegex = /^09\d{9}$/;

			// Test the input against the regex pattern
			this.isValidMobileNumber = iranMobileRegex.test(this.searchNumberInput);
		},
		async submitHandler() {
			const data = {
				type: this.type,
				name_fa: this.faName,
				name: this.enName,
				visit_types: this.selectedVisitTypes,
			};
			const res = await this.$ApiServiceLayer.post(
				this.$PATH.RELATIVE_PATH.MULTI.CLIENT_LIST_CREATE +
					'?p=' +
					this.$STORE.state.userConfig.setProjectId,
				this.$PATH.SERVICE_NAME.EMPTY,
				data,
			);
			if (res.status === 201) {
				const secondData = {
					client: res.data.id,
					user: this.user.id,
				};
				const response = await this.$ApiServiceLayer.post(
					this.$PATH.RELATIVE_PATH.MULTI.USER_CLIENT_LIST_CREATE +
						'?p=' +
						this.$STORE.state.userConfig.setProjectId,
					this.$PATH.SERVICE_NAME.EMPTY,
					secondData,
				);
				if (response.status === 201) {
					this.$notify({
						group: 'tc',
						type: 'success',
						text: 'اطلاعات مشتری با موفقیت ثبت شد.',
					});
					this.showClientForm = false;
					this.searchNumberInput = '';
					this.type = '';
					this.faName = '';
					this.enName = '';
					this.selectedVisitTypes = [];
					this.user = null;
				}
			}
		},
	},
};
</script>

<style lang="scss" scoped>
.user-managment-edit {
	padding: 24px;
	@media (min-width: 768px) {
		padding: 32px 50px;
	}

	.box {
		padding: 20px;
		margin-bottom: 20px;
		background: #fff;
		border-radius: 12px;
		box-shadow: 0 5px 15px rgba(0, 0, 0, 0.08);

		span {
			font-weight: 600;
			font-size: 16px;
		}

		.form-label {
			display: block;
			margin-bottom: 8px;
			font-size: 14px;
			font-weight: 500;
		}

		.user-name {
			display: flex;
			align-items: center;
			width: 100%;
			background: #f8f9fa;
			border-radius: 8px;
			padding: 16px;

			.text {
				font-size: 14px;
				color: #555;
				margin-left: 8px;
			}

			.persian {
				font-family: 'IRANYekanfa' !important;
				font-weight: 500;
			}
		}

		.form-control {
			height: 44px;
			border: 1px solid #e0e0e0;
			border-radius: 8px;
			padding: 0 16px;
			width: 100%;
			font-family: 'IRANYekanfa' !important;
			transition: border-color 0.2s;

			&:focus {
				outline: none;
				border-color: #357ae1;
				box-shadow: 0 0 0 3px rgba(53, 122, 225, 0.1);
			}
		}

		.search-input {
			height: 44px;
			border: 1px solid #e0e0e0;
			padding: 0 16px;
			border-radius: 8px;
			font-family: 'IRANYekanfa' !important;
			margin: 8px 4px;
			width: 100%;
			max-width: 300px;
		}

		.search {
			border: 1px solid #357ae1;
			background: #fff;
			min-width: 75px;
			border-radius: 8px;
			color: #357ae1;
			padding: 10px 16px;
			margin-right: 8px;
			transition: all 0.2s;

			&:hover:not(:disabled) {
				background: #f0f7ff;
			}

			&:disabled {
				background: #f1f1f1;
				color: #aaa;
				border: none;
			}
		}

		.submit-btn {
			border: none;
			background: #357ae1;
			min-width: 120px;
			border-radius: 8px;
			color: #fff;
			padding: 12px 24px;
			font-weight: 500;
			transition: all 0.2s;

			&:hover {
				background: #2a68c5;
				transform: translateY(-1px);
				box-shadow: 0 4px 8px rgba(53, 122, 225, 0.2);
			}
            &:disabled {
				background: #f1f1f1;
				color: #aaa;
				border: none;
			}

			&:active {
				transform: translateY(0);
			}
		}
	}

	.custom-dropdown {
		position: relative;
		width: 100%;

		.dropdown-header {
			display: flex;
			align-items: center;
			justify-content: space-between;
			height: 44px;
			padding: 0 16px;
			background-color: white;
			border: 1px solid #e0e0e0;
			border-radius: 8px;
			cursor: pointer;
			transition: border-color 0.2s;

			&:hover {
				border-color: #bbb;
			}

			.dropdown-title {
				white-space: nowrap;
				overflow: hidden;
				text-overflow: ellipsis;
				flex: 1;
				font-family: 'IRANYekanfa' !important;
				font-size: 14px;
			}

			.dropdown-arrow {
				margin-right: 8px;
				font-size: 12px;
				transition: transform 0.2s;

				&.dropdown-arrow-up {
					transform: rotate(180deg);
				}
			}
		}

		.dropdown-list {
			position: absolute;
			top: 100%;
			left: 0;
			right: 0;
			z-index: 1000;
			margin-top: 4px;
			background-color: white;
			border-radius: 8px;
			box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
			max-height: 250px;
			overflow-y: auto;
			padding: 8px 0;

			.dropdown-item {
				padding: 8px 16px;

				&:hover {
					background-color: #f8f9fa;
				}
			}

			.checkbox-container {
				display: flex;
				align-items: center;
				position: relative;
				padding-right: 30px;
				cursor: pointer;
				width: 100%;
				font-family: 'IRANYekanfa' !important;
				font-size: 14px;

				input {
					position: absolute;
					opacity: 0;
					cursor: pointer;
					height: 0;
					width: 0;
				}

				.checkmark {
					position: absolute;
					right: 0;
					height: 18px;
					width: 18px;
					background-color: #fff;
					border: 1px solid #ccc;
					border-radius: 4px;
				}

				&:hover input ~ .checkmark {
					background-color: #f8f9fa;
				}

				input:checked ~ .checkmark {
					background-color: #357ae1;
					border-color: #357ae1;
				}

				.checkmark:after {
					content: '';
					position: absolute;
					display: none;
				}

				input:checked ~ .checkmark:after {
					display: block;
					right: 6px;
					top: 2px;
					width: 5px;
					height: 10px;
					border: solid white;
					border-width: 0 2px 2px 0;
					transform: rotate(45deg);
				}

				.item-text {
					display: inline-block;
					margin-right: 8px;
				}
			}
		}
	}
}
input:focus,
select:focus,
textarea:focus,
button:focus {
	outline: none;
}
</style>
