<template>
	<div class="login-container">
		<!-- Logo/Header Section -->
		<div class="header">
			<img :src="this.$PATH.GET_IMAGE_PATH('logo.svg')" alt="Logo" class="logo" />
		</div>

		<div class="content-wrapper">
			<div class="detail-section">
				<span class="detail-title">ورود و ثبت‌‌نام</span>
				<div class="input-section">
					<span class="phone-number">
						شماره کد به شماره
						<span class="persian-number"> {{ phoneNumber }}</span> ارسال شده است.
						<span @click="routeToLogin">
							<!-- <span class="iconify edit-icon" data-icon="akar-icons:edit"></span> -->
							<img
								class="iconify reject-documnets"
								src="https://s3.ir-thr-at1.arvanstorage.ir/pakshooma-bucket/akar-icons_edit.svg"
							/>
						</span>
					</span>
				</div>

				<div class="fake-input-container">
					<input
						type="number"
						class="phone-input"
						v-model="codeOtp"
						maxlength="5"
						@keyup.enter="submitOTP"
						@focus="isFocused = true"
						@input="checkVerify"
					/>
					<div class="fake-item">
						{{ fakeInput[4] }}
					</div>
					<div class="fake-item">
						{{ fakeInput[3] }}
					</div>
					<div class="fake-item">
						{{ fakeInput[2] }}
					</div>
					<div class="fake-item">
						{{ fakeInput[1] }}
					</div>
					<div class="fake-item">
						{{ fakeInput[0] }}
					</div>
				</div>

				<div class="counter">
					<span class="persian-number mt-6">ارسال کد تا {{ timerCount }} ثانیه</span>
				</div>
				<button
					@click="resendCodeClick"
					type="button"
					class="btn register-btn"
					:disabled="resendCode"
				>
					<span v-if="loading === false">ارسال مجدد کد</span>
					<div class="spinner-border spinner-border-sm" role="status" v-if="loading"></div>
				</button>
			</div>
			<div class="login-image">
				<img :src="this.$PATH.GET_IMAGE_PATH('login-img.webp')" alt="Login Illustration" />
			</div>
			<div class="background-decoration"></div>
		</div>
	</div>
</template>

<script>
export default {
	data() {
		return {
			codeOtp: '',
			loading: false,
			isFocused: false,
			timerCount: 120,
			resendCode: true,
		};
	},
	computed: {
		phoneNumber() {
			return this.$STORE.state.userConfig.userPhoneNumber;
		},
		fakeInput() {
			return this.codeOtp;
		},
	},
	methods: {
		routeToLogin() {
			this.$router.push({name:'login'})
		},
		checkVerify() {
			if (this.codeOtp.length == 5) {
				this.submitOTP();
			}
		},
		async resendCodeClick() {
			this.loading = true;
			const res = await this.$ApiServiceLayer.post(
				this.$PATH.RELATIVE_PATH.POST.PHONE_NUMBER_OTP_REQ,
				this.$PATH.SERVICE_NAME.AUTH,
				{ phone_number: this.phoneNumber },
				{},
				false
			);
			if (res.code === 201) {
				this.loading = false;
				this.$STORE.commit('userConfig/setOtpId', res.data.id);
				this.$STORE.commit('userConfig/setLoginTempToken', res.data.verification_token);
				this.timerCount = 30;
				this.resendCode = true;
			}
		},
		async submitOTP() {
			this.loading = true;
			const res = await this.$ApiServiceLayer.post(
				this.$PATH.RELATIVE_PATH.POST.OTP_VERIFY,
				this.$PATH.SERVICE_NAME.AUTH,
				{
					code: this.codeOtp,
					verification_token: this.$STORE.state.userConfig.loginTempToken,
					id: this.$STORE.state.userConfig.otpId,
					phone_number: this.$STORE.state.userConfig.userPhoneNumber,
				},
				{},
				false,
			);
			if (res.status === 200) {
				this.loading = false;
				this.$STORE.commit('userConfig/setAccessToken', 'Bearer ' + res.data.tokens.access);
				this.$STORE.commit('userConfig/setRefreshToken', res.data.tokens.refresh);
				this.$STORE.commit('userConfig/setUserInfo', res.data.user);
				this.$STORE.commit('userConfig/setUserRole', res.data.role.role);
				this.$router.push({ name: 'dashboard' });
			}
			if (res.data.code === 406) {
				this.$notify({
					group: 'tc',
					type: 'danger',
					text: 'کد اشتباه است!',
				});
				this.codeOtp = '';
				this.loading = false;
			}
		},
	},
	watch: {
		timerCount: {
			handler(value) {
				if (value > 0) {
					setTimeout(() => {
						this.timerCount--;
					}, 1000);
				}
				if (value === 0) {
					this.resendCode = false;
				}
			},
			immediate: true, // This ensures the watcher is triggered upon creation
		},
	},
};
</script>

<style scoped>
.login-container {
	min-height: 100vh;
	background: #5d95e7;
	padding: 20px;
}

.header {
	padding: 20px;
}

.logo {
	height: 40px;
}

.content-wrapper {
	max-width: 1200px;
	margin: 40px auto;
	position: relative;
	margin: calc((100vh - 80px - 500px) / 2) auto;
	display: flex;
	justify-content: center;
}

.title {
	text-align: center;
	font-size: 24px;
	margin-bottom: 32px;
}

.login-tabs {
	display: flex;
	gap: 12px;
	margin-bottom: 24px;
}

.tab-btn {
	padding: 8px 16px;
	border-radius: 8px;
	border: none;
	background: transparent;
	cursor: pointer;
}

.tab-btn.active {
	background: #357ae1;
	color: #fff;
}

.login-input {
	width: 100%;
	background: #e6ecf6;
	/* border: 1px solid rgba(255, 255, 255, 0.2); */
	border-radius: 8px;
	color: #fff;
	margin-bottom: 16px;
}

.submit-btn {
	width: 100%;
	background: #357ae1;
	color: white;
	border: none;
	border-radius: 8px;
	padding: 12px;
	margin: 16px 0;
	cursor: pointer;
}

.submit-btn:disabled {
	opacity: 0.7;
	cursor: not-allowed;
}

.divider {
	text-align: center;
	color: white;
	margin: 24px 0;
	position: relative;
}

.divider::before,
.divider::after {
	content: '';
	position: absolute;
	top: 50%;
	width: 45%;
	height: 1px;
	background: rgba(255, 255, 255, 0.2);
}

.divider::before {
	left: 0;
}
.divider::after {
	right: 0;
}

.google-btn {
	width: 100%;
	display: flex;
	align-items: center;
	justify-content: center;
	gap: 8px;
	background: rgba(255, 255, 255, 0.1);
	border: 1px solid rgba(255, 255, 255, 0.2);
	border-radius: 8px;
	padding: 12px;
	color: white;
	cursor: pointer;
}

.links {
	margin-top: 24px;
	display: flex;
	flex-direction: column;
	gap: 12px;
	text-align: center;
}

.links a {
	color: rgba(255, 255, 255, 0.7);
	text-decoration: none;
	font-size: 14px;
}

.login-content {
	display: flex;
	gap: 40px;
	align-items: center;
}

.login-form {
	flex: 1;
	background: #fff;
	backdrop-filter: blur(10px);
	border-radius: 0 16px 16px 0;
	padding: 40px;
	max-width: 480px;
}

.login-image {
	flex: 1;
	/* height: 600px; */
	display: flex;
	align-items: center;
	justify-content: center;
	max-width: 480px;
}

.login-image img {
	width: 100%;
	height: 100%;
	border-radius: 16px 0 0 16px;
}

@media (max-width: 768px) {
	.login-content {
		flex-direction: column-reverse;
		gap: 24px;
	}
	.content-wrapper {
		margin: 20px auto;
		min-height: calc(100vh - 180px);
		align-items: center;
		flex-direction: column-reverse;
	}

	.login-image {
		flex: 0;
	}
	.login-image img {
		border-radius: 16px 16px 0 0;
	}

	.login-form {
		width: 100%;
		max-width: none;
		flex: 0;
		border-radius: 0 0 16px 16px;
	}
}
.background-decoration {
	position: fixed;
	bottom: 0;
	left: 0;
	right: 0;
	height: 40%;
	background: linear-gradient(to top right, #2b3595, #1a1d2e);
	z-index: -1;
}

@media (max-width: 768px) {
	.login-form {
		padding: 24px;
	}

	.title {
		font-size: 20px;
	}
}
.login-container {
	min-height: 100vh;
	background: #5D95E7;
	padding: 20px;
}

.header {
	padding: 20px;
}

.logo {
	height: 40px;
}

.content-wrapper {
	max-width: 1200px;
	margin: 40px auto;
	position: relative;
	margin: calc((100vh - 80px - 500px) / 2) auto; 
	display: flex;
	justify-content: center;

}


.title {
	text-align: center;
	font-size: 24px;
	margin-bottom: 32px;
}

.login-tabs {
	display: flex;
	gap: 12px;
	margin-bottom: 24px;
}

.tab-btn {
	padding: 8px 16px;
	border-radius: 8px;
	border: none;
	background: transparent;
	cursor: pointer;
}

.tab-btn.active {
	background: #357AE1;
	color: #fff;
}

.login-input {
	width: 100%;
	background: #E6ECF6;
	/* border: 1px solid rgba(255, 255, 255, 0.2); */
	border-radius: 8px;
	color: #fff;
	margin-bottom: 16px;
}

.submit-btn {
	width: 100%;
	background: #357AE1;
	color: white;
	border: none;
	border-radius: 8px;
	padding: 12px;
	margin: 16px 0;
	cursor: pointer;
}

.submit-btn:disabled {
	opacity: 0.7;
	cursor: not-allowed;
}

.divider {
	text-align: center;
	color: white;
	margin: 24px 0;
	position: relative;
}

.divider::before,
.divider::after {
	content: '';
	position: absolute;
	top: 50%;
	width: 45%;
	height: 1px;
	background: rgba(255, 255, 255, 0.2);
}

.divider::before {
	left: 0;
}
.divider::after {
	right: 0;
}

.google-btn {
	width: 100%;
	display: flex;
	align-items: center;
	justify-content: center;
	gap: 8px;
	background: rgba(255, 255, 255, 0.1);
	border: 1px solid rgba(255, 255, 255, 0.2);
	border-radius: 8px;
	padding: 12px;
	color: white;
	cursor: pointer;
}

.links {
	margin-top: 24px;
	display: flex;
	flex-direction: column;
	gap: 12px;
	text-align: center;
}

.links a {
	color: rgba(255, 255, 255, 0.7);
	text-decoration: none;
	font-size: 14px;
}


.login-content {
  display: flex;
  gap: 40px;
  align-items: center;
}

.login-form {
  flex: 1;
  background: #fff;
  backdrop-filter: blur(10px);
  border-radius: 0 16px 16px 0;
  padding: 40px;
  max-width: 480px;
}

.login-image {
  flex: 1;
  /* height: 600px; */
  display: flex;
  align-items: center;
  justify-content: center;
  max-width: 480px;
}

.login-image img {
  width: 100%;
  height: 100%;
  border-radius: 16px 0 0 16px;
}

@media (max-width: 768px) {
  .login-content {
    flex-direction: column-reverse;
    gap: 24px;
  }
  .content-wrapper {
		margin: 20px auto; 
		min-height: calc(100vh - 180px); 
		align-items: center;
		flex-direction: column-reverse;
	}

  .login-image {
	flex: 0;
  }
  .login-image img {
		border-radius: 16px 16px 0 0;
	}


  .login-form {
    width: 100%;
    max-width: none;
	flex: 0;
	border-radius: 0 0 16px 16px;
  }
}
.background-decoration {
	position: fixed;
	bottom: 0;
	left: 0;
	right: 0;
	height: 40%;
	background: linear-gradient(to top right, #2b3595, #1a1d2e);
	z-index: -1;
}

@media (max-width: 768px) {
	.login-form {
		padding: 24px;
	}

	.title {
		font-size: 20px;
	}
}
</style>
