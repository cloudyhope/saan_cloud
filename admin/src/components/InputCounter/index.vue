<template>
	<div class="counter-container">
		<div class="input-container">
			<input type="number" v-model="count" @input="sendData" />
		</div>
		<div class="arrow-container">
			<div class="arrow up" @click="upper">
				<!-- <span class="iconify" data-icon="akar-icons:chevron-up"></span> -->
							<img class="iconify" src="https://s3.ir-thr-at1.arvanstorage.ir/pakshooma-bucket/akar-icons_chevron-up.svg">

			</div>
			<div class="arrow down" @click="downer">
				<!-- <span class="iconify" data-icon="akar-icons:chevron-down"></span> -->
							<img class="iconify" src="https://s3.ir-thr-at1.arvanstorage.ir/pakshooma-bucket/akar-icons_chevron-down.svg">

			</div>
		</div>
	</div>
</template>

<script>
export default {
	data() {
		return {
			count: null,
		};
	},
	props: {
		countIndex: [String, Number],
	},
	methods: {
		downer() {
			if (this.count <= 0) {
				this.count = 0;
				this.sendData();
			} else {
				this.count = Number(this.count) - 1;
				this.sendData();
			}
		},
		upper() {
			this.count = Number(this.count) + 1;
			this.sendData();
		},
		sendData() {
			this.$emit('sendData', { count: this.count, countIndex: this.countIndex });
		},
	},
};
</script>

<style lang="scss" scoped>
.counter-container {
	width: 110px;
	height: 50px;
	border: 1px solid #c4c4c4;
	position: relative;
	display: flex;
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
