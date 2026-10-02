<template>
	<div class="main-container">
		<div class="vin-input-container">
			<table class="vin-table">
				<thead>
					<tr>
						<th></th>
						<th>عنوان</th>
						<th>مقدار</th>
						<th></th>
						<th></th>
						<th class="delete" @click="deleteAll">حذف همه موارد</th>
					</tr>
				</thead>
				<tbody>
					<tr v-for="(item, index) in itemModel" :key="item.id" class="td-data">
						<td class="line">{{ index + 1 }}.</td>
						<td>
						
							
								<select class="inputNumber">
									<option selected>انتخاب کنید...</option>
									<option v-for="productdetail in productDetailList" :key="productdetail.id" :value="productdetail.id">{{productdetail.key_fa}}</option>
                                   
								</select>


                             <!-- <v-select :value="productDetailList.key_fa" ></v-select> -->
                          
						</td>
						<td>
							<div class="counter-container">
								<div class="input-container">
									<input type="text" v-model="item.Count" />
								</div>
								<!-- <div class="arrow-container">
									<div class="arrow up" @click="item.Count = item.Count + 1">
										<span class="iconify" data-icon="akar-icons:chevron-up"></span>
									</div>
									<div class="arrow down" @click="item.Count = item.Count + -1">
										<span class="iconify" data-icon="akar-icons:chevron-down"></span>
									</div>
								</div> -->
							</div>
						</td>
						<td></td>
						<td>
							<PrimaryButton
								@click.native="addItem"
								v-if="itemModel.length === index + 1"
								title="افزودن"
							/>
						</td>
						<td class="delete" @click="deleteItem(item.id, index)">
							<!-- <span class="iconify delete-border" data-icon="fluent:delete-20-regular"></span> -->
							<img class="iconify delete-border" src="https://s3.ir-thr-at1.arvanstorage.ir/pakshooma-bucket/fluent_delete-24-regular.svg">
							
						</td>
					</tr>
				</tbody>
			</table>
		</div>
	</div>
</template>
<script>
import PrimaryButton from '../../components/Button/Button.vue';

export default {
	data() {
		return {
			itemModel: [{ id: 1, inputNumber: null, Count: null }],
			productDetailList: {},
		};
	},
	props: {
		fromParent: {
			type: Boolean,
			default: false,
		},
		vinParent: {
			type: Array,
		},
	},
	components: {
		PrimaryButton,
	},
	mounted() {
		this.showProductDetail();
	},
	methods: {
		async showProductDetail() {
			await this.$ApiServiceLayer
				.get(this.$PATH.RELATIVE_PATH.GET.PRODUCT_MORE_DETAILS + '?ordering=key_fa', 'market')
				.then((response) => {
					if (response.code === 200) {
						this.productDetailList = response.data;
						(response.data);
					}
				});
		},
		addItem() {
			if (
				!this.itemModel[this.itemModel.length - 1].inputNumber &&
				!this.itemModel[this.itemModel.length - 1].Count
			) {
				this.$notify({
					group: 'tc',
					type: 'danger',
					text: 'عنوان و مقدار وارد نشده !',
				});
			} else {
				this.itemModel.push({ id: this.itemModel.length + 1, inputNumber: '', Count: null });
				this.$emit('sendVin', this.itemModel);
			}
		},
		sendSingleData() {
			if (
				!this.itemModel[this.itemModel.length - 1].inputNumber &&
				!this.itemModel[this.itemModel.length - 1].Count
			) {
				this.$notify({
					group: 'tc',
					type: 'danger',
					text: 'شماره فنی خالی می‌باشد!',
				});
			} else {
				this.$emit('sendVin', this.itemModel);
			}
		},
		getData(value) {
			this.itemModel[value.countIndex].Count = value.Count;
		},
		deleteItem(id, index) {
			if (index === 0 && this.itemModel.length === 1) {
				return false;
			} else {
				this.itemModel.splice(index, 1);
			}
		},
		deleteAll() {
			this.itemModel = [];
			this.itemModel.push({ id: 1, inputNumber: null, Count: null });
			this.$emit('sendVin', this.itemModel);
		},
	},
};
</script>
<style lang="scss" scoped>
.vin-input-container {
	width: 100%;
	margin-bottom: 20px;
	.vin-table {
		width: 100%;
		text-align: right;
		tr {
			width: 100%;
			height: 60px;
			.line {
				border-right: 3px solid #d3dff2;
				font-family: 'IRANYekan';
				padding: 10px;
			}
			th {
				text-align: right;
				padding: 10px;
			}
		}
	}
	.td-data {
		margin-bottom: 20px;
	}
}
.delete {
	color: #d20032;
	cursor: pointer;
	text-align: center !important;
	.iconify {
		font-size: 50px;
	}
	.delete-border {
		border: 1px solid #d20032;
		border-radius: 2px;
		padding: 10px;
	}
}
.inputNumber {
	width: 237px;
	height: 48px;
	border: 1px solid #c4c4c4;
	box-sizing: border-box;
	text-indent: 20px;
}
.title-file-text-container {
	width: 100%;
	display: flex;
	text-align: right;
	margin-top: 100px;
	p,
	span {
		font-size: 14px;
	}
	span {
		color: #d3dff2;
		cursor: pointer;
	}
}
.upload-box {
	width: 100%;
	height: 200px;
	background-color: #f0f0f1;
	margin-top: 24px;
	border-radius: 2px;
	border: 2px dashed #c4c4c4;
	display: flex;
	justify-content: center;
	align-items: center;
	flex-direction: column;
	position: relative;
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
		color: #404041cc;
	}
}
.counter-container {
	width: 237px;
	height: 50px;
	border: 1px solid #c4c4c4;
	position: relative;
	display: flex;
	// margin: 0 auto;
	.input-container {
		width: 100%;
		input {
			width: 100%;
			height: 100%;
			border: none;
			text-indent: 10px;
			&:focus {
				outline: none;
			}
		}
		input[type='number']::-webkit-inner-spin-button,
		input[type='number']::-webkit-outer-spin-button {
			-webkit-appearance: none;
			margin: 0;
		}
	}
	.arrow-container {
		width: 50px;
		flex: 1;
		display: flex;
		flex-direction: column;

		.arrow {
			width: 30px;
			height: 100%;
			border-right: 1px solid #c4c4c4;
			cursor: pointer;
			display: flex;
			justify-content: center;
			align-items: center;
		}
		.up {
			border-bottom: 1px solid #c4c4c4;
		}
	}
}
</style>
