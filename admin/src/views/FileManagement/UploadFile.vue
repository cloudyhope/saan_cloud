<template>
	<div class="p-4">
		<div class="warning-box">
			<img src="@/assets/images/iconPack/warning.svg" />
			<span class="mr-2">توجه</span>
			<ul>
				<li>
					لطفا اطلاعات فایل آپلود شده را به درستی وارد کنید. نام فایل بیشتر از ۴۰ کاراکتر نباشد.
				</li>
				<li>آیکون باید PNG، JPEG یا WebP و حداکثر ۲ مگابایت باشد.</li>
				<li>فایل آموزشی می‌تواند PDF، تصویر یا MP4 تا ۵۰ مگابایت باشد.</li>
			</ul>
		</div>
		<div class="card">
			<div class="card-body">
				<h5 class="mb-4">اطلاعات فایل</h5>
				<div class="d-flex align-items-center mb-4">
					<label for="resource-name" class="ml-2">نام فایل:</label>
					<input id="resource-name" v-model="fileName" class="inputs" maxlength="40" />
				</div>
				<div class="d-flex align-items-center mb-4">
					<label for="resource-type" class="ml-2">نوع فایل:</label>
					<select id="resource-type" class="inputs" v-model="fileType">
						<option value="EDU">آموزش</option>
						<option value="ETC">سایر</option>
					</select>
				</div>
				<div class="d-flex align-items-center mb-4">
					<span class="ml-2">انتخاب آیکون:</span>
					<div class="d-flex align-items-center">
						<input
							type="file"
							ref="fileInput"
							accept=".png,.jpg,.jpeg,.webp"
							aria-label="انتخاب آیکون فایل"
							style="display: none"
							@change="handleFileChange"
						/>
						<button type="button" class="upload-icons-btn" aria-label="انتخاب آیکون" @click="openFileDialog">
							<img class="iconify" src="@/assets/images/iconPack/upload_noback.svg" />
						</button>
						<div class="mr-3" v-if="selectedIcon">
							<img
								class="preview-icon"
								:src="iconPreviewUrl"
								alt="Selected File Preview"
							/>
						</div>
					</div>
				</div>
				<div class="d-flex flex-column">
					<label for="resource-description">توضیحات:</label>
					<textarea id="resource-description" v-model="desc" rows="4" cols="50" class="text-area"></textarea>
				</div>
				<div class="upload-box">
					<input type="file" accept=".pdf,.png,.jpg,.jpeg,.webp,.mp4" aria-label="انتخاب فایل آموزشی" @change="uploadFile" />
					<div class="icon">
						<!-- <span class="iconify" data-icon="ic:outline-file-upload"></span> -->
						<img class="iconify" src="@/assets/images/iconPack/upload.svg" />
					</div>
					<span class="upload-text">آپلود فایل</span>
					<p>{{ uploadedImg ? uploadedImg.name : 'فایل مورد نظر خود را انتخاب کنید' }}</p>
				</div>
				<p v-if="error" class="upload-error" role="alert">{{ error }}</p>
				<div class="button-container">
					<button :disabled="checkEmpty || loading" @click="postData" class="continue">{{ loading ? 'در حال بارگذاری...' : 'ثبت فایل' }}</button>
				</div>
			</div>
		</div>
		<loading v-if="loading" />
	</div>
</template>

<script>
import Loading from '../../components/Loading/index.vue';

export default {
	components: {
		Loading,
	},
	data() {
		return {
			uploadedImg: null,
			fileName: '',
			desc: null,
			fileType: '',
			selectedIcon: null,
			iconPreviewUrl: '',
			error: '',
			loading: false,
		};
	},
	computed: {
		checkEmpty() {
			return !this.uploadedImg || !this.selectedIcon || !this.fileName.trim() || !this.fileType;
		},
	},
	beforeDestroy() {
		if (this.iconPreviewUrl) URL.revokeObjectURL(this.iconPreviewUrl);
	},
	methods: {
		openFileDialog() {
			this.$refs.fileInput.click();
		},
		handleFileChange(event) {
			const file = event.target.files[0];
			this.error = '';
			if (this.iconPreviewUrl) URL.revokeObjectURL(this.iconPreviewUrl);
			this.iconPreviewUrl = '';
			if (file && this.isValidFileType(file) && file.size <= 2 * 1024 * 1024) {
				this.selectedIcon = file;
				this.iconPreviewUrl = URL.createObjectURL(file);
			} else {
				this.selectedIcon = null;
				this.error = 'آیکون باید PNG، JPEG یا WebP و حداکثر ۲ مگابایت باشد.';
			}
		},
		isValidFileType(file) {
			const allowedTypes = ['image/png', 'image/jpeg', 'image/webp'];
			return allowedTypes.includes(file.type);
		},
		async postData() {
			if (this.checkEmpty || this.loading) return;
			this.loading = true;
			this.error = '';
			const formData = new FormData();
			formData.append('file', this.uploadedImg);
			formData.append('name', this.fileName);
			formData.append('description', this.desc);
			formData.append('icon', this.selectedIcon);
			formData.append('type', this.fileType);
			formData.append('project', this.$STORE.state.userConfig.setProjectId);
			try {
			const res = await this.$ApiServiceLayer.post(
				this.$PATH.RELATIVE_PATH.MULTI.UPLOAD_FILE +
					'?p=' +
					this.$STORE.state.userConfig.setProjectId,
				this.$PATH.SERVICE_NAME.EMPTY,
				formData,
				{
					'Content-Type': 'multipart/form-data',
				},
			);
			if (res.status === 201) {
				this.$router.push({ name: 'fileList' });
			} else {
				this.error = 'ثبت فایل انجام نشد. اندازه، نوع فایل و دسترسی پروژه را بررسی کنید.';
			}
			} catch (_) { this.error = 'ارتباط برقرار نشد. دوباره تلاش کنید.'; }
			finally { this.loading = false; }
		},
		async uploadFile(e) {
			const file = e.target.files[0];
			this.error = '';
			if (!file || file.size > 50 * 1024 * 1024 ||
				!['application/pdf', 'image/png', 'image/jpeg', 'image/webp', 'video/mp4'].includes(file.type)) {
				this.uploadedImg = null;
				this.error = 'فایل باید PDF، تصویر یا MP4 و حداکثر ۵۰ مگابایت باشد.';
				return;
			}
			this.uploadedImg = file;
		},
	},
};
</script>
<style lang="scss" scoped>
.upload-error { margin: 12px 0 0; padding: 10px 14px; border-radius: 8px; color: #902f29; background: #fff0ee; }
.warning-box {
	padding: 16px;
	color: #664d03;
	background: #fff3cd;
	border-radius: 8px;
	margin-bottom: 16px;
	li {
		margin: 0px 34px;
		list-style: disc;
	}
}
.card {
	border: none;
	.card-body {
		box-shadow: 0px 4px 4px rgba(214, 214, 214, 0.6);
		.inputs {
			width: 20%;
			height: 38px;
			border: 1px solid #c4c4c4;
			padding: 0 9px;
			border-radius: 4px;
		}
		.text-area {
			border: 1px solid #c4c4c4;
			padding: 0 9px;
			border-radius: 4px;
			margin-top: 16px;
		}
		.upload-icons-btn {
			border: none;
			padding: 10px;
			background: #fff;
		}
		.preview-icon {
			max-width: 60px;
		}
		.upload-box {
			width: 100%;
			height: 200px;
			background: #f8f8f8;
			margin-top: 24px;
			border-radius: 8px;
			border: 2px dashed #357ae1;
			display: flex;
			justify-content: center;
			align-items: center;
			flex-direction: column;
			position: relative;
			.upload-text {
				color: #357ae1;
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
		.button-container {
			display: flex;
			justify-content: flex-end;
			margin-top: 12px;
			.continue {
				border: none;
				background: #357ae1;
				padding: 8px;
				border-radius: 8px;
				color: #fff;
				margin-left: 8px;
				&:disabled {
					background: #f1f1f1;
					color: #535656;
					border-radius: 8px;
					border: none;
					padding: 8px;
				}
			}
		}
	}
}
</style>
