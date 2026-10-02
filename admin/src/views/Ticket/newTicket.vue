<template>
	<div class="containers">
		<div class="warning">
			<div class="d-flex">
				<img src="../../assets/images/iconPack/carbon_warning-square.svg" />
				<span class="text">توجه</span>
			</div>
			<div>
				<ul>
					<li>لطفا عنوان تیکت خود را با جزئیات وارد کنید</li>
					<li>واحد مربوط به تیکت خود را انتخاب کنید</li>
					<li>فرمت‌های مجاز فایل ضمیمه شامل jpg ،png ،jpeg ،zip ،rar می‌باشند</li>
				</ul>
			</div>
		</div>
		<div class="box">
			<div class="row mt-3">
				<div class="col d-flex flex-column">
					<label for="html">واحد مربوطه</label>
					<select v-model="units" class="units" name="unit">
						<option :value="units.id" v-for="units of unitsVal" :key="units.id">
							{{ units.verbose_name }}
						</option>
					</select>
				</div>
				<div class="col d-flex flex-column">
					<label for="html">موضوع</label>
					<input v-model="titleVal" class="inputs" type="text" />
				</div>
				<div class="col d-flex flex-column">
					<label for="html">عنوان</label>
					<input v-model="subjectVal" class="inputs" type="text" />
				</div>
			</div>
			<div>
				<div class="d-flex flex-column">
					<label for="html">متن</label>
					<textarea
						style="border-radius: 4px"
						v-model="descVal"
						class="text-area"
						rows="4"
						cols="50"
					></textarea>
				</div>
			</div>
		</div>
		<div class="box">
			<div class="buttom-container">
				<button @click="sendTicket" :disabled="disableSendTicket" class="send-ticket">
					<img class="icon" src="../../assets/images/iconPack/tabler_send.svg" />
					تیکت جدید
				</button>
				<!-- <button class="choose-file" :disabled="true">
					<img
						class="icon"
						src="../../assets/images/iconPack/material-symbols_folder-open-outline-rounded.svg"
					/>
					انتخاب فایل (بزودی)
				</button> -->
			</div>
		</div>
	</div>
</template>
<script>
export default {
	data() {
		return {
			roleID: null,
			unitsVal: [],
			titleVal: null,
			subjectVal: null,
			descVal: null,
			units: '1',
		};
	},
	computed: {
		disableSendTicket() {
			if (
				this.titleVal === null ||
				this.titleVal === '' ||
				this.subjectVal === null ||
				this.subjectVal === '' ||
				this.descVal === null ||
				this.descVal === ''
			) {
				return true;
			} else {
				return false;
			}
		},
	},
	mounted() {
		this.getAuthRole();
		// this.getTicketMessage();
	},
	methods: {
		async getAuthRole() {
			const res = await this.$ApiServiceLayer.get(
				this.$PATH.RELATIVE_PATH.MULTI.DEFINE_ROLES +
					'?p=' +
					this.$STORE.state.userConfig.setProjectId,
				this.$PATH.SERVICE_NAME.AUTH,
			);
			if (res.status === 200) {
				// this.roleID = res.data[0].role.id;
				this.unitsVal = res.data;
				this.unitsVal;
			}
		},

		// async getTicketMessage() {
		// 	const res = await this.$ApiServiceLayer.get(
		// 		this.$PATH.RELATIVE_PATH.MULTI.TICKET_MESSAGE,
		// 		this.$PATH.SERVICE_NAME.AUTH,
		// 		{},
		// 	);
		// 	if (res.status === 200) {
		// 		('message', res.data);
		// 	}
		// },
		async sendTicket() {
			const res = await this.$ApiServiceLayer.post(
				this.$PATH.RELATIVE_PATH.MULTI.TICKET_LIST +
					'?p=' +
					this.$STORE.state.userConfig.setProjectId,
				this.$PATH.SERVICE_NAME.AUTH,
				{
					id: this.roleID,
					title: this.subjectVal,
					subject: this.titleVal,
					project: this.$STORE.state.userConfig.setProjectId,
					role_assignee: this.units,
				},
			);
			if (res.status === 201) {
				const resp = await this.$ApiServiceLayer.post(
					this.$PATH.RELATIVE_PATH.MULTI.TICKET_MESSAGE +
						'?p=' +
						this.$STORE.state.userConfig.setProjectId,
					this.$PATH.SERVICE_NAME.AUTH,
					{ ticket: res.data.id, body: this.descVal },
				);
				if (resp.status === 201) {
					this.$notify({
						group: 'tc',
						type: 'success',
						text: 'تیکت شما با موفقیت ارسال شد.',
					});
					setTimeout(() => {
						this.$router.push({ name: 'ticketList' });
					}, 2000);
				}
			}
		},
	},
};
</script>
<style lang="scss" scoped>
.containers {
	padding: 24px;
	.warning {
		display: flex;
		flex-direction: column;
		border: 1px solid #ffecb4;
		background: #fff3cd;
		padding: 16px;
		margin-bottom: 32px;
		ul {
			margin-bottom: 0 !important;
			padding: 10px 35px;
		}
		li {
			list-style: disc;
		}
		.text {
			color: #664d03;
			font-size: 16px;
			margin-right: 15px;
		}
	}
	.box {
		// border: 1px solid #c4c4c4;
		background: #fff;
		background: #fff;
		padding: 24px;
		border-radius: 8px;

		.title {
			color: #404041;
			margin-bottom: 12px;
		}
		.units {
			width: 100%;
			padding: 8px 0;
			font-size: 14px;
			border: 1px solid #c4c4c4;
			margin-bottom: 33px;
			height: 42px;
			text-indent: 10px;
			border-radius: 4px;
		}
		.inputs {
			margin-bottom: 33px;
			border: 1px solid #c4c4c4;
			height: 42px;
			width: 100%;
			text-indent: 10px;
			border-radius: 4px;
		}
		.text-area {
			border: 1px solid #c4c4c4;
			text-indent: 10px;
			border-radius: 4px;
			padding: 10px;
		}
		.buttom-container {
			margin-top: 24px;
		}
	}
	.send-ticket {
		background: #285595;
		color: #fff;
		border-radius: 4px;
		padding: 4px 10px;
		border: none;
		&:disabled {
			background: #c4c4c4;
		}
		.icon {
			width: 20px;
		}
	}
	.choose-file {
		border-radius: 4px;
		padding: 4px 10px;
		border: 1px solid #285595;
		color: #285595;
		background: #fff;
		margin-right: 24px;
		&:disabled {
			background: #c4c4c4;
			border: none;
			color: red;
		}
	}

	.persian-number {
		font-family: 'IRANYekanfa' !important;
	}
}
</style>
