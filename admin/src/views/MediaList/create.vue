<template>
	<div class="main-container">
		<div class="box">
			<h2 class="title">ایجاد رسانه</h2>

			<div class="form-container">
				<div class="row">
					<div class="col-md-6 col-12">
						<div class="form-group">
							<label>عنوان (انگلیسی)</label>
							<input
								type="text"
								class="inputs"
								v-model="formData.title"
								placeholder="عنوان انگلیسی را وارد کنید"
							/>
						</div>
					</div>

					<div class="col-md-6 col-12">
						<div class="form-group">
							<label>عنوان (فارسی)</label>
							<input
								type="text"
								class="inputs"
								v-model="formData.title_fa"
								placeholder="عنوان فارسی را وارد کنید"
							/>
						</div>
					</div>
				</div>

				<div class="row">
					<div class="col-md-6 col-12">
						<div class="form-group">
							<label>لینک انتقال</label>
							<input
								type="url"
								class="inputs"
								v-model="formData.redirect_url"
								placeholder="https://example.com"
							/>
						</div>
					</div>
					<div class="col-md-6 col-12">
						<div class="form-group">
							<label>نوع رسانه</label>
							<select class="inputs" v-model="formData.type">
								<option value="">انتخاب کنید...</option>
								<option v-for="type in mediaTypes" :key="type.id" :value="type.id">
									{{ type.title_fa }}
								</option>
							</select>
						</div>
					</div>
				</div>

				<div class="row">
					<div class="col-12">
						<div class="form-group">
							<label>تصویر</label>
							<div class="file-upload-wrapper">
								<input
									type="text"
									class="inputs"
									v-model="formData.image_1"
									placeholder="آدرس تصویر را وارد کنید"
								/>
								<!-- <div class="file-upload-display" @click="$refs.fileInput.click()">
									<img
										v-if="imagePreview"
										:src="imagePreview"
										alt="پیش نمایش"
										class="image-preview"
									/>
									<div v-else class="upload-placeholder">
										<img
											src="@/assets/images/iconPack/upload.svg"
											alt="آپلود"
											class="upload-icon"
										/>
										<span>انتخاب تصویر</span>
									</div>
								</div> -->
							</div>
						</div>
					</div>
				</div>

				<div class="row">
					<div class="col-12">
						<div class="form-group">
							<label>توضیحات</label>
							<textarea
								class="inputs textarea"
								v-model="formData.body_copy"
								placeholder="توضیحات را وارد کنید..."
								rows="4"
							></textarea>
						</div>
					</div>
				</div>

				<div class="form-actions">
					<button type="button" class="btn btn-secondary" @click="resetForm">پاک کردن</button>
					<button type="button" class="btn btn-primary-color" @click="submitForm" :disabled="loading">
						<span v-if="loading">در حال ارسال...</span>
						<span v-else>ایجاد رسانه</span>
					</button>
				</div>
			</div>
		</div>
	</div>
</template>

<script>
export default {
	name: 'MediaListCreate',
	data() {
		return {
			loading: false,
			formData: {
				title: '',
				title_fa: '',
				image_1: null,
				redirect_url: '',
				page_url: '',
				body_copy: '',
				type: null,
			},
			mediaTypes: [],
			imagePreview: null,
		};
	},
	mounted() {
		this.fetchMediaTypes();
	},
	methods: {
		async fetchMediaTypes() {
			const response = await this.$ApiServiceLayer.get(
				this.$PATH.RELATIVE_PATH.GET.MEDIA_TYPES + '?p=' + this.$STORE.state.userConfig.setProjectId,
				'',
			);
			this.mediaTypes = response.data;
		},

		onFileChange(event) {
			const file = event.target.files[0];
			if (file) {
				this.formData.image_1 = file;

				const reader = new FileReader();
				reader.onload = (e) => {
					this.imagePreview = e.target.result;
				};
				reader.readAsDataURL(file);
			}
		},
		validateForm() {
			const errors = [];

			if (!this.formData.title.trim()) {
				errors.push('عنوان انگلیسی الزامی است');
			}

			if (!this.formData.title_fa.trim()) {
				errors.push('عنوان فارسی الزامی است');
			}

			if (!this.formData.type) {
				errors.push('نوع رسانه الزامی است');
			}

			if (!this.formData.body_copy.trim()) {
				errors.push('توضیحات الزامی است');
			}

			return errors;
		},

		async submitForm() {
			const errors = this.validateForm();

			if (errors.length > 0) {
				this.$notify({
					group: 'tc',
					type: 'error',
					text: errors.join('\n'),
				});
				return;
			}

			this.loading = true;

			try {
				const formData = new FormData();
				formData.append('title', this.formData.title);
				formData.append('title_fa', this.formData.title_fa);
				formData.append('redirect_url', this.formData.redirect_url);
				formData.append('body_copy', this.formData.body_copy);
				formData.append('type', this.formData.type);
				formData.append('image_1', this.formData.image_1);
				formData.append('is_active', true);

				// if (this.formData.image_1) {
				// 	formData.append('image_1', this.formData.image_1);
				// }

				const response = await this.$ApiServiceLayer.post(
					this.$PATH.RELATIVE_PATH.MULTI.MEDIA_CREATE + '?p=' + this.$STORE.state.userConfig.setProjectId,
					'',
					formData,
				);

				if (response.status === 200 || response.status === 201) {
					this.$notify({
						group: 'tc',
						type: 'success',
						text: 'رسانه با موفقیت ایجاد شد',
					});

					this.resetForm();
					// this.$router.push({ name: 'MediaList' });
				} else {
					throw new Error('خطا در ایجاد رسانه');
				}
			} catch (error) {
				console.error('خطا در ارسال فرم:', error);
				this.$notify({
					group: 'tc',
					type: 'error',
					text: 'خطا در ایجاد رسانه. لطفاً دوباره تلاش کنید.',
				});
			} finally {
				this.loading = false;
			}
		},

		resetForm() {
			this.formData = {
				title: '',
				title_fa: '',
				image_1: null,
				redirect_url: '',
				page_url: '',
				body_copy: '',
				type: null,
			};
			this.imagePreview = null;

			// if (this.$refs.fileInput) {
			// 	this.$refs.fileInput.value = '';
			// }
		},
	},
};
</script>

<style scoped>
.main-container {
	padding: 20px;
}

.box {
	padding: 24px;
	border-radius: 8px;
	margin-bottom: 16px;
	background: #fff;
	box-shadow: 0px 4px 4px rgba(214, 214, 214, 0.6);
}

.title {
	font-weight: 700;
	font-size: 18px;
	margin-bottom: 24px;
	color: #333;
}

.form-container {
	width: 100%;
}

.row {
	display: flex;
	flex-wrap: wrap;
	margin: 0 -8px;
}

.col-12 {
	width: 100%;
	padding: 0 8px;
}

.col-md-6 {
	width: 50%;
	padding: 0 8px;
}

@media (max-width: 768px) {
	.col-md-6 {
		width: 100%;
	}
}

.form-group {
	margin-bottom: 20px;
}

.form-group label {
	display: block;
	margin-bottom: 8px;
	font-weight: 500;
	color: #333;
	font-family: 'IRANYekanfa';
}

.inputs {
	width: 100%;
	height: 38px;
	border: 1px solid #c4c4c4;
	padding: 0 12px;
	border-radius: 4px;
	font-family: 'IRANYekanfa';
	font-size: 14px;
	transition: border-color 0.3s;
}

.inputs:focus {
	outline: none;
	border-color: #357ae1;
}

.textarea {
	height: auto;
	min-height: 100px;
	padding: 12px;
	resize: vertical;
}

.file-upload-wrapper {
	position: relative;
}

.file-input {
	display: none;
}

.file-upload-display {
	width: 100%;
	height: 120px;
	border: 2px dashed #c4c4c4;
	border-radius: 4px;
	display: flex;
	align-items: center;
	justify-content: center;
	cursor: pointer;
	transition: border-color 0.3s;
}

.file-upload-display:hover {
	border-color: #357ae1;
}

.image-preview {
	max-width: 100%;
	max-height: 100px;
	object-fit: cover;
	border-radius: 4px;
}

.upload-placeholder {
	display: flex;
	flex-direction: column;
	align-items: center;
	color: #666;
	font-family: 'IRANYekanfa';
}

.upload-icon {
	width: 24px;
	height: 24px;
	margin-bottom: 8px;
}

.form-actions {
	display: flex;
	gap: 12px;
	justify-content: flex-end;
	margin-top: 24px;
	padding-top: 24px;
	border-top: 1px solid #eee;
}

.btn {
	padding: 10px 20px;
	border: none;
	border-radius: 4px;
	font-family: 'IRANYekanfa';
	font-size: 14px;
	cursor: pointer;
	transition: all 0.3s;
	min-width: 120px;
}

.btn-primary-color {
	background-color: #357ae1;
	color: #fff;
}

/* .btn-primary-color:hover:not(:disabled) {
	background-color: #2860b3;
} */

.btn-primary-color:disabled {
	background-color: #ccc;
	cursor: not-allowed;
}

.btn-secondary {
	background-color: transparent;
	color: #357ae1;
	border: 1px solid #357ae1 !important;
}



@media (max-width: 576px) {
	.main-container {
		padding: 10px;
	}

	.box {
		padding: 16px;
	}

	.form-actions {
		flex-direction: column;
	}

	.btn {
		width: 100%;
	}
}
</style>
