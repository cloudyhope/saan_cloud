<template>
	<div class="loading-container" >
		<img src="@/assets/images/Loading/loading.gif" alt="">
	</div>
</template>

<script>
export default {
	data() {
		return {
			show: false
		}
	},
	methods: {
		open() {
			this.show = true;
			document.getElementsByTagName("body")[0].style.overflow = "hidden";
			this.$emit("onOpened");
		},
	}
}
</script>

<style lang="scss" scoped>
.loading-container {
	width: 100%;
	height: 100%;
	background-color: rgba(255, 255, 255, 0.5);
	position: fixed;
	top: 0;
	left: 0;
	opacity: 1;
	
	visibility: visible;
	display: flex;
	justify-content: center;
	align-items: center;
	img {
		width: 100px;
		height: 100px;
		object-fit: contain;
	}
}

</style>