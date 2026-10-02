<template>
	<div>
		<Loading v-if="loading" />
		<div class="recharge-wallet">
			<div class="box">
				<b-row>
					<b-col md="4">
						<b-form-group label="نام" label-for="first-name">
							<b-form-input id="first-name" v-model="firstName"></b-form-input>
						</b-form-group>
					</b-col>
					<b-col md="4">
						<b-form-group label="نام خانوادگی" label-for="last-name">
							<b-form-input id="last-name" v-model="lastName"></b-form-input>
						</b-form-group>
					</b-col>
					<b-col md="4">
						<b-form-group label="کد ملی" label-for="national-code">
							<b-form-input
								id="national-code"
								class="persian-number"
								v-model="nationalCode"
							></b-form-input>
						</b-form-group>
					</b-col>
				</b-row>

				<b-row>
					<b-col md="4">
						<b-form-group label="شماره موبایل" label-for="phone">
							<b-form-input id="phone" class="persian-number" v-model="phone"></b-form-input>
						</b-form-group>
					</b-col>
					<b-col md="4">
						<b-form-group label="شماره کارت" label-for="card-number">
							<b-form-input
								id="card-number"
								class="persian-number"
								v-model="cardNumber"
							></b-form-input>
						</b-form-group>
					</b-col>
					<b-col md="4">
						<b-form-group label="مبلغ" class="persian-number" label-for="amounts">
							<b-form-input
								@input="formatAmount"
								:value="formattedAmount"
								id="amounts"
								v-model="amount"
								class="persian-number"
							></b-form-input>
						</b-form-group>
					</b-col>
				</b-row>
				<div class="d-flex justify-content-end w-100">
					<PrimaryButton :disabled="disabled" @click="submitHandler" :backgroundColor="'#00B14F'"
						>تایید</PrimaryButton
					>
				</div>
			</div>
		</div>
	</div>
</template>

<script>
// import PrimaryButton from '../../components/Button/Btn.vue';
import Loading from '../../components/Loading/index.vue';

export default {
	components: {
		Loading,
		// PrimaryButton,
	},
	data() {
		return {
			firstName: '',
			lastName: '',
			nationalCode: '',
			phone: '',
			cardNumber: '',
			amount: '',
			loading: false,
		};
	},
	computed: {
		formattedAmount() {
			return this.amount.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
		},
		// formattedCardNumber() {
		// 	return this.cardNumber.replace(/(.{4})/g, '$1-').slice(0, -1);
		// },
		disabled() {
			if (
				this.firstName === '' ||
				this.firstName === null ||
				this.lastName === '' ||
				this.lastName === null ||
				this.nationalCode === '' ||
				this.nationalCode === null ||
				this.phone === '' ||
				this.phone === null ||
				this.cardNumber === '' ||
				this.cardNumber === null ||
				this.amount === '' ||
				this.amount === null
			) {
				return true;
			} else {
				return false;
			}
		},
	},
	mounted() {},
	methods: {
		formatAmount(event) {
			let value = event.toString().replace(/,/g, '');
			if (value === '' || isNaN(value)) {
				this.amount = '';
				return;
			}
			this.amount = parseFloat(value);
			if (!isNaN(value)) {
				value = parseFloat(value).toLocaleString('en-US');
			}

			console.log('asd', value);
			this.amount = value;
		},
		// formatCardNumber(event) {
		// 	let value = event.replace(/-/g, '');

		// 	if (value === '') {
		// 		this.cardNumber = '';
		// 		return;
		// 	}

		// 	value = value.replace(/(.{4})/g, '$1-');

		// 	this.cardNumber = value;
		// },
		async submitHandler() {
			this.loading = true;
			try {
				const data = {
					national_code: this.nationalCode,
					phone_number: this.phone,
					first_name: this.firstName,
					last_name: this.lastName,
					card_no: this.cardNumber,
					amount_rials: parseInt(this.amount.replace(/,/g, '')),
					full_name: this.firstName + this.lastName,
					is_test: false,
				};
				const res = await this.$ApiServiceLayer.post(
					this.$PATH.RELATIVE_PATH.MULTI.PROVIDER_CREDIT_LIST_CREATE,
					this.$PATH.SERVICE_NAME.LOYALTY,
					data
				);
				if (res.status === 201) {
					const res1 = await this.$ApiServiceLayer.patch(
						this.$PATH.RELATIVE_PATH.MULTI.BANK_CREDIT_CHARGE_PAYABLE + res.data.id + '/',
						this.$PATH.SERVICE_NAME.LOYALTY,
						{
							is_payable: true,
						}
					);
					if (res1.status === 200) {
						this.$notify({
							group: 'tc',
							type: 'success',
							text: 'شارژ حساب با موفقیت ثبت شد.',
						});
					}
				}
			} finally {
				this.loading = false;
			}
		},
	},
};
</script>
<style lang="scss" scoped>
.recharge-wallet {
	width: 100%;
	padding: 24px;
	min-height: 80vh;

	.box {
		margin-top: 16px;
		padding: 24px;
		border-radius: 2px;
		margin-bottom: 16px;
		background: #fff;
		border-radius: 8px;
		box-shadow: 0px 0px 10px 0px rgba(214, 214, 214, 0.6);
	}
	.persian-number {
		font-family: 'IRANYekanfa' !important;
	}
}
</style>
